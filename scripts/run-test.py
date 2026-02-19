#!/usr/bin/env python3
"""
Script to run k6 load tests and generate reports in JSON and CSV formats.
Creates a folder with timestamp and test name, saves reports, and updates history.
"""

import os
import sys
import json
import subprocess
import yaml
from datetime import datetime
from pathlib import Path

def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent / 'config.yaml'
    if not config_path.exists():
        print(f"Error: config.yaml not found at {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def normalize_test_path(test_script):
    """
    Normalize test script path to handle Windows/Unix paths and short names.
    
    Accepts:
    - Full paths: k6/tests/basic-web-test.js or k6\tests\basic-web-test.js
    - Short names: basic-web-test.js or basic-web-test
    
    Returns normalized path relative to project root (Unix style).
    """
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / 'k6' / 'tests'
    
    input_str = str(test_script).strip()
    
    if '\t' in input_str:
        parts = input_str.split('\t')
        if len(parts) >= 2 and parts[0].endswith('k6'):
            rest = '\t'.join(parts[1:])
            if rest.startswith('ests'):
                rest = rest[4:]
            rest = rest.lstrip('\\').lstrip('/')
            input_str = 'k6/tests/' + rest
        else:
            input_str = input_str.replace('\t', '/t')
    
    if '\b' in input_str:
        input_str = input_str.replace('\b', '')
    
    input_str = input_str.replace('\\', '/')
    has_separators = '/' in input_str
    
    if not has_separators:
        if input_str.startswith('k6') and 'test' in input_str.lower():
            test_idx = input_str.lower().find('test')
            if test_idx > 0 and test_idx + 4 < len(input_str):
                filename_part = input_str[test_idx + 4:]
                if filename_part.startswith('s'):
                    filename_part = filename_part[1:]
                filename_part = filename_part.lstrip('\\').lstrip('/')
                reconstructed = f"k6/tests/{filename_part}"
                test_path = project_root / reconstructed
                if test_path.exists() and test_path.is_file():
                    return reconstructed
        
        filename = input_str
        if not filename.endswith('.js'):
            filename = filename + '.js'
        test_file = tests_dir / filename
        if test_file.exists():
            return f"k6/tests/{filename}"
        return f"k6/tests/{filename}"
    
    normalized_str = input_str.lstrip('/').lstrip('.')
    
    test_path = project_root / normalized_str
    if test_path.exists() and test_path.is_file():
        rel_path = test_path.relative_to(project_root)
        return '/'.join(rel_path.parts)
    
    if '/' in normalized_str:
        filename = normalized_str.split('/')[-1]
    else:
        filename = normalized_str
    
    if not filename.endswith('.js'):
        filename = filename + '.js'
    
    test_file = tests_dir / filename
    if test_file.exists():
        return f"k6/tests/{filename}"
    return normalized_str

def get_test_name(test_script):
    """Extract test name from script path"""
    return Path(test_script).stem

def create_results_folder(test_name):
    """Create results folder with timestamp and test name"""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    folder_name = f"{timestamp}_{test_name}"
    results_base = Path(__file__).parent.parent / 'results'
    results_base.mkdir(exist_ok=True)
    
    results_folder = results_base / folder_name
    results_folder.mkdir(exist_ok=True)
    
    return results_folder

def run_k6_test(test_script, results_folder, test_name, config):
    """Run k6 test and export results to CSV and JSON"""
    test_path = Path(__file__).parent.parent / test_script
    if not test_path.exists():
        print(f"Error: Test script not found: {test_path}")
        print(f"  Searched for: {test_script}")
        print(f"  Available tests in k6/tests/:")
        tests_dir = Path(__file__).parent.parent / 'k6' / 'tests'
        if tests_dir.exists():
            for test_file in sorted(tests_dir.glob('*.js')):
                print(f"    - {test_file.name}")
        sys.exit(1)
    
    test_script_in_container = test_script.replace('k6/', '/scripts/')
    results_folder_name = results_folder.name
    generate_csv = config.get('results', {}).get('generate_csv', True)
    
    create_folder_cmd = ['docker', 'compose', 'exec', '-T', 'k6', 'mkdir', '-p', f'/results/{results_folder_name}']
    subprocess.run(create_folder_cmd, check=False, capture_output=True)

    summary_json_path = f'/results/{results_folder_name}/{test_name}-summary.json'
    exec_env = ['-e', 'K6_STATSD_ADDR=statsd-exporter:9125']
    if 'test' in config and 'url' in config['test']:
        exec_env.extend(['-e', f"TEST_URL={config['test']['url']}"])
    cmd = [
        'docker', 'compose', 'exec', '-T', *exec_env, 'k6',
        '/usr/bin/k6', 'run',
        '-o', 'output-statsd',
        test_script_in_container,
        '--summary-export', summary_json_path,
    ]
    
    if generate_csv:
        csv_path = f'/results/{results_folder_name}/{test_name}.csv'
        cmd.extend(['--out', f'csv={csv_path}'])
    else:
        csv_path = None
    
    env = os.environ.copy()
    if 'test' in config and 'url' in config['test']:
        env['TEST_URL'] = config['test']['url']
    
    print(f"Running k6 test: {test_script}")
    print(f"Results will be saved to: {results_folder}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, check=False, env=env, capture_output=False, text=True)
        summary_json_local = results_folder / f"{test_name}-summary.json"
        json_created = summary_json_local.exists() and summary_json_local.stat().st_size > 0
        
        if result.returncode == 0:
            return True
        elif result.returncode == 99:
            return True
        else:
            print(f"Error running k6 test: exit code {result.returncode}")
            return False
    except Exception as e:
        print(f"Error running k6 test: {e}")
        return False

def save_test_history(results_folder, test_name, config, status):
    """Save test metadata to history.json"""
    history_file = Path(__file__).parent.parent / 'results' / 'history.json'
    
    history = []
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    
    entry = {
        'timestamp': datetime.now().isoformat(),
        'test_name': test_name,
        'config': {
            'vus': config.get('test', {}).get('vus', 5),
            'duration': config.get('test', {}).get('duration', '60s'),
            'url': config.get('test', {}).get('url', 'https://httpbin.org'),
        },
        'results_path': str(results_folder.relative_to(Path(__file__).parent.parent)),
        'status': status,
    }
    
    history.append(entry)
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    
    return entry

def main():
    if len(sys.argv) < 2:
        print("Usage: python run-test.py <test-script>")
        print("Examples:")
        print("  python run-test.py k6/tests/basic-web-test.js")
        print("  python run-test.py basic-web-test.js")
        print("  python run-test.py basic-web-test")
        sys.exit(1)
    
    test_script_input = sys.argv[1]
    test_script = normalize_test_path(test_script_input)
    config = load_config()
    test_name = get_test_name(test_script)
    
    print("=" * 60)
    print("k6 Load Testing - Test Runner")
    print("=" * 60)
    
    results_folder = create_results_folder(test_name)
    print(f"Created results folder: {results_folder.name}")
    success = run_k6_test(test_script, results_folder, test_name, config)
    status = 'completed' if success else 'failed'
    entry = save_test_history(results_folder, test_name, config, status)
    
    print("-" * 60)
    csv_file = results_folder / f"{test_name}.csv"
    json_file = results_folder / f"{test_name}-summary.json"
    generate_csv = config.get('results', {}).get('generate_csv', True)
    
    if success:
        print("Test completed successfully!")
        print(f"  Results: {results_folder}")
        if generate_csv:
            print(f"  CSV: {test_name}.csv")
        else:
            print(f"  CSV: disabled")
        print(f"  JSON Summary: {test_name}-summary.json")
        print(f"  History updated: results/history.json")
    else:
        print("Test failed. Check logs above.")
    
    print("=" * 60)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
