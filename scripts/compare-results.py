#!/usr/bin/env python3
"""
Script to compare results from two load tests.
Reads test history and compares key metrics from JSON reports.
"""

import json
import sys
from pathlib import Path

def load_json_report(report_path):
    """Load JSON summary report from k6 test results"""
    full_path = Path(__file__).parent.parent / report_path
    
    summary_path = None
    if str(full_path).endswith('.json') and not str(full_path).endswith('-summary.json'):
        summary_path = Path(str(full_path).replace('.json', '-summary.json'))
    elif not str(full_path).endswith('.json'):
        # If it's a directory or test name, try to find summary file
        if full_path.is_dir():
            summary_files = list(full_path.glob('*-summary.json'))
            if summary_files:
                summary_path = summary_files[0]
        else:
            summary_path = Path(str(full_path) + '-summary.json')
    
    if summary_path and summary_path.exists():
        full_path = summary_path
    elif not full_path.exists():
        if not str(full_path).endswith('.json'):
            full_json = Path(str(full_path) + '.json')
            if full_json.exists():
                full_path = full_json
    
    if not full_path.exists():
        print(f"Error: Report not found: {full_path}")
        return None
    
    with open(full_path, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        f.seek(0)
        content = f.read()
    
    lines = content.strip().split('\n')
    if len(lines) > 1 and all(line.strip().startswith('{') for line in lines[:3] if line.strip()):
        print(f"Error: Full JSON format detected (newline-delimited, contains every data point).")
        print(f"  Summary JSON format is required for comparison.")
        print(f"  Please run the test again - new tests use compact summary format automatically.")
        return None
    
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in {full_path}: {e}")
        return None
    
    if 'metrics' not in data:
        print(f"Error: File is not a k6 summary JSON (missing 'metrics' key).")
        return None
    
    return data

def extract_metrics(data):
    """Extract key metrics from k6 JSON summary report"""
    if 'metrics' not in data:
        return None
    
    metrics = data['metrics']
    
    def get_metric_value(metric_name, key, default=0):
        metric = metrics.get(metric_name, {})
        if isinstance(metric, dict):
            return metric.get(key, default)
        return default
    
    http_req_duration = None
    for key in metrics.keys():
        if key.startswith('http_req_duration'):
            http_req_duration = metrics[key]
            break
    
    return {
        'http_reqs': {
            'count': get_metric_value('http_reqs', 'count', 0),
            'rate': get_metric_value('http_reqs', 'rate', 0),
        },
        'http_req_duration': {
            'avg': http_req_duration.get('avg', 0) if http_req_duration else 0,
            'min': http_req_duration.get('min', 0) if http_req_duration else 0,
            'max': http_req_duration.get('max', 0) if http_req_duration else 0,
            'p95': http_req_duration.get('p(95)', 0) if http_req_duration else 0,
            'p99': http_req_duration.get('p(99)', 0) if http_req_duration else 0,
        },
        'http_req_failed': {
            'rate': get_metric_value('http_req_failed', 'rate', 0),
            'pct': get_metric_value('http_req_failed', 'value', 0),
        },
        'vus': {
            'max': get_metric_value('vus_max', 'value', 0) or get_metric_value('vus', 'max', 0),
            'avg': get_metric_value('vus', 'avg', 0) or get_metric_value('vus', 'value', 0),
        },
    }

def format_duration(ms):
    """Format duration in milliseconds"""
    if ms < 1000:
        return f"{ms:.2f}ms"
    return f"{ms/1000:.2f}s"

def format_percent(value):
    """Format percentage"""
    return f"{value * 100:.2f}%"

def compare_metrics(metrics1, metrics2, name1, name2):
    """Compare two sets of metrics and print differences"""
    print("=" * 80)
    print(f"Comparison: {name1} vs {name2}")
    print("=" * 80)
    print("\nHTTP Requests:")
    print(f"  Total Requests:")
    print(f"    {name1}: {metrics1['http_reqs']['count']:,}")
    print(f"    {name2}: {metrics2['http_reqs']['count']:,}")
    diff = metrics2['http_reqs']['count'] - metrics1['http_reqs']['count']
    pct_diff = (diff / metrics1['http_reqs']['count'] * 100) if metrics1['http_reqs']['count'] > 0 else 0
    print(f"    Difference: {diff:+,} ({pct_diff:+.2f}%)")
    
    print(f"  Requests per Second:")
    print(f"    {name1}: {metrics1['http_reqs']['rate']:.2f} req/s")
    print(f"    {name2}: {metrics2['http_reqs']['rate']:.2f} req/s")
    diff = metrics2['http_reqs']['rate'] - metrics1['http_reqs']['rate']
    print(f"    Difference: {diff:+.2f} req/s")
    print("\nResponse Time:")
    print(f"  Average:")
    print(f"    {name1}: {format_duration(metrics1['http_req_duration']['avg'])}")
    print(f"    {name2}: {format_duration(metrics2['http_req_duration']['avg'])}")
    diff = metrics2['http_req_duration']['avg'] - metrics1['http_req_duration']['avg']
    print(f"    Difference: {diff:+.2f}ms")
    
    print(f"  95th Percentile:")
    print(f"    {name1}: {format_duration(metrics1['http_req_duration']['p95'])}")
    print(f"    {name2}: {format_duration(metrics2['http_req_duration']['p95'])}")
    diff = metrics2['http_req_duration']['p95'] - metrics1['http_req_duration']['p95']
    print(f"    Difference: {diff:+.2f}ms")
    
    print(f"  99th Percentile:")
    print(f"    {name1}: {format_duration(metrics1['http_req_duration']['p99'])}")
    print(f"    {name2}: {format_duration(metrics2['http_req_duration']['p99'])}")
    diff = metrics2['http_req_duration']['p99'] - metrics1['http_req_duration']['p99']
    print(f"    Difference: {diff:+.2f}ms")
    print("\nError Rate:")
    print(f"  {name1}: {format_percent(metrics1['http_req_failed']['rate'])}")
    print(f"  {name2}: {format_percent(metrics2['http_req_failed']['rate'])}")
    diff = metrics2['http_req_failed']['rate'] - metrics1['http_req_failed']['rate']
    print(f"  Difference: {format_percent(diff)}")
    print("\nVirtual Users:")
    print(f"  Max VUs:")
    print(f"    {name1}: {metrics1['vus']['max']}")
    print(f"    {name2}: {metrics2['vus']['max']}")
    print(f"  Average VUs:")
    print(f"    {name1}: {metrics1['vus']['avg']:.2f}")
    print(f"    {name2}: {metrics2['vus']['avg']:.2f}")
    
    print("\n" + "=" * 80)

def list_tests():
    """List all tests from history"""
    history_file = Path(__file__).parent.parent / 'results' / 'history.json'
    if not history_file.exists():
        print("No test history found. Run some tests first.")
        return []
    
    with open(history_file, 'r', encoding='utf-8') as f:
        history = json.load(f)
    
    print("Available tests:")
    for i, entry in enumerate(history, 1):
        print(f"  {i}. {entry['timestamp']} - {entry['test_name']} ({entry.get('status', 'unknown')})")
    
    return history

def main():
    if len(sys.argv) < 3:
        print("Usage: python compare-results.py <test1_path> <test2_path>")
        print("   or: python compare-results.py <index1> <index2> (from history)")
        print("\nTo see available tests, run without arguments:")
        print("  python compare-results.py")
        print()
        list_tests()
        sys.exit(1)
    
    arg1, arg2 = sys.argv[1], sys.argv[2]
    history_file = Path(__file__).parent.parent / 'results' / 'history.json'
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        try:
            idx1, idx2 = int(arg1) - 1, int(arg2) - 1
            if 0 <= idx1 < len(history) and 0 <= idx2 < len(history):
                entry1 = history[idx1]
                entry2 = history[idx2]
                path1 = Path(entry1['results_path']) / f"{entry1['test_name']}-summary.json"
                path2 = Path(entry2['results_path']) / f"{entry2['test_name']}-summary.json"
                name1 = f"{entry1['test_name']} ({entry1['timestamp']})"
                name2 = f"{entry2['test_name']} ({entry2['timestamp']})"
            else:
                print("Error: Invalid test indices")
                sys.exit(1)
        except ValueError:
            path1, path2 = arg1, arg2
            if not str(path1).endswith('.json'):
                summary_path1 = Path(str(path1).replace('.json', '-summary.json'))
                if summary_path1.exists():
                    path1 = summary_path1
            if not str(path2).endswith('.json'):
                summary_path2 = Path(str(path2).replace('.json', '-summary.json'))
                if summary_path2.exists():
                    path2 = summary_path2
            name1, name2 = Path(path1).parent.name, Path(path2).parent.name
    else:
        path1, path2 = arg1, arg2
        name1, name2 = Path(arg1).parent.name, Path(arg2).parent.name
    
    # Load reports
    data1 = load_json_report(path1)
    data2 = load_json_report(path2)
    
    if not data1 or not data2:
        sys.exit(1)
    
    metrics1 = extract_metrics(data1)
    metrics2 = extract_metrics(data2)
    
    if not metrics1 or not metrics2:
        print("Error: Could not extract metrics from reports")
        sys.exit(1)
    
    compare_metrics(metrics1, metrics2, name1, name2)

if __name__ == '__main__':
    main()
