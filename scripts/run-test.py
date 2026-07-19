#!/usr/bin/env python3
"""
Скрипт для запуска k6-тестов и сохранения отчётов в формате JSON.
Создаёт папку с меткой времени и именем теста, сохраняет результаты и обновляет историю.
"""

import os
import sys
import json
import subprocess
import yaml
from datetime import datetime
from pathlib import Path

def load_config():
    """Загрузка конфигурации из config.yaml"""
    config_path = Path(__file__).parent.parent / 'config.yaml'
    if not config_path.exists():
        print(f"Error: config.yaml not found at {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def normalize_test_path(test_script):
    """
    Нормализация пути к тесту для поддержки Windows/Unix путей и коротких имён.
    
    Принимает:
    - Полный путь: k6/tests/basic-web-test.js или k6\tests\basic-web-test.js
    - Короткое имя: basic-web-test.js или basic-web-test
    
    Возвращает нормализованный путь относительно корня проекта (в Unix-стиле).
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
    """Извлечение имени теста из пути к файлу"""
    return Path(test_script).stem

def create_results_folder(test_name):
    """Создание папки с результатами с меткой времени и именем теста"""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    folder_name = f"{timestamp}_{test_name}"
    results_base = Path(__file__).parent.parent / 'results'
    results_base.mkdir(exist_ok=True)
    
    results_folder = results_base / folder_name
    results_folder.mkdir(exist_ok=True)
    
    return results_folder

def validate_summary(results_folder, test_name):
    """Проверка результатов теста по summary JSON.
    Возвращает (is_pass: bool, details: str) — прошли ли пороги и что не так.
    """
    summary_file = results_folder / f"{test_name}-summary.json"
    if not summary_file.exists():
        return False, "Файл summary JSON не найден"

    try:
        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return False, f"Ошибка чтения summary JSON: {e}"

    metrics = data.get('metrics', {})
    details = []
    any_fail = False

    # 1. Проверка checks — доля успешных проверок
    checks = metrics.get('checks', {})
    passes = checks.get('passes', 0)
    fails = checks.get('fails', 0)
    total = passes + fails
    if total > 0:
        check_rate = passes / total
        if check_rate < 0.99:
            details.append(f"  [FAIL] Checks: {passes}/{total} (99%) — доля успешных {check_rate:.1%} < 99%")
            any_fail = True
        else:
            details.append(f"  [OK] Checks: {passes}/{total} ({check_rate:.1%})")

    # 2. Проверка доли ошибок (http_req_failed)
    req_failed = metrics.get('http_req_failed', {})
    error_rate = req_failed.get('value', 0)
    if error_rate > 0.01:
        details.append(f"  [FAIL] Ошибки: {error_rate:.2%} — превышает порог 1%")
        any_fail = True
    else:
        details.append(f"  [OK] Ошибки: {error_rate:.2%} (порог < 1%)")

    # 3. Проверка P95 времени ответа
    duration = metrics.get('http_req_duration', {})
    p95 = duration.get('p(95)', 0)
    if p95 > 5000:
        details.append(f"  [FAIL] P95: {p95:.0f} мс — превышает порог 5000 мс")
        any_fail = True
    else:
        details.append(f"  [OK] P95: {p95:.0f} мс (порог < 5000 мс)")

    # 4. Проверка средних значений (предупреждение, не критично)
    avg_duration = duration.get('avg', 0)
    if avg_duration > 3000:
        details.append(f"  [WARN] Среднее время: {avg_duration:.0f} мс — выше 3000 мс")

    # 5. Проверка max (предупреждение)
    max_duration = duration.get('max', 0)
    if max_duration > 10000:
        details.append(f"  [WARN] Макс. время: {max_duration:.0f} мс — выше 10 секунд")

    result = "PASS" if not any_fail else "FAIL"
    return not any_fail, f"[{result}]\n" + "\n".join(details)


def run_k6_test(test_script, results_folder, test_name, config):
    """Запуск k6-теста и экспорт результатов в CSV и JSON"""
    test_path = Path(__file__).parent.parent / test_script
    if not test_path.exists():
        print(f"Ошибка: файл теста не найден: {test_path}")
        print(f"  Искали для: {test_script}")
        print(f"  Доступные тесты в k6/tests/:")
        tests_dir = Path(__file__).parent.parent / 'k6' / 'tests'
        if tests_dir.exists():
            for test_file in sorted(tests_dir.glob('*.js')):
                print(f"    - {test_file.name}")
        sys.exit(1)
    
    # Проверка запущенных контейнеров
    check_cmd = ['docker', 'compose', 'ps', '--status', 'running']
    check_result = subprocess.run(check_cmd, capture_output=True, text=True, check=False)
    if 'k6' not in check_result.stdout.lower():
        print("Ошибка: контейнер k6 не запущен. Подними инфраструктуру:")
        print("  docker compose up -d")
        print("Или запусти k6 напрямую: k6 run " + str(test_path))
        return False
    
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
        '-o', 'statsd',
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
    
    if not generate_csv:
        print("[ВНИМАНИЕ] CSV-отчёт ОТКЛЮЧЁН. Установите results.generate_csv: true в config.yaml для детальных данных по каждому запросу.")

    print(f"Запуск k6-теста: {test_script}")
    print(f"Результаты будут сохранены в: {results_folder}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, check=False, env=env, capture_output=False, text=True)
        
        if result.returncode == 0:
            return True, None
        elif result.returncode == 99:
            return True, None
        else:
            print(f"Ошибка запуска k6-теста: код выхода {result.returncode}")
            print("Логи из контейнера k6:")
            try:
                logs = subprocess.run(
                    ['docker', 'compose', 'logs', 'k6', '--tail', '50'],
                    capture_output=True, text=True, check=False
                )
                print(logs.stdout or logs.stderr)
            except Exception:
                pass
            return False, None
    except Exception as e:
        print(f"Ошибка запуска k6-теста: {e}")
        return False, None

def save_test_history(results_folder, test_name, config, status):
    """Сохранение метаданных теста в history.json"""
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
        print("Использование: python run-test.py <test-script>")
        print("Примеры:")
        print("  python run-test.py k6/tests/basic-web-test.js")
        print("  python run-test.py basic-web-test.js")
        print("  python run-test.py basic-web-test")
        sys.exit(1)
    
    test_script_input = sys.argv[1]
    test_script = normalize_test_path(test_script_input)
    config = load_config()
    test_name = get_test_name(test_script)
    
    print("=" * 60)
    print("k6 — Загрузочное тестирование")
    print("=" * 60)
    
    results_folder = create_results_folder(test_name)
    print(f"Создана папка результатов: {results_folder.name}")
    k6_success, k6_error = run_k6_test(test_script, results_folder, test_name, config)
    
    # Валидация результатов
    summary_pass, summary_details = validate_summary(results_folder, test_name)
    if summary_details:
        print(summary_details)
    
    # Тест провален если: k6 не запустился / не удалось прочитать summary / пороги не выполнены
    success = k6_success and summary_pass
    status = 'completed' if success else 'failed'
    entry = save_test_history(results_folder, test_name, config, status)
    
    print("-" * 60)
    csv_file = results_folder / f"{test_name}.csv"
    json_file = results_folder / f"{test_name}-summary.json"
    generate_csv = config.get('results', {}).get('generate_csv', True)
    
    if success:
        print("Тест завершён успешно!")
        print(f"  Результаты: {results_folder}")
        if generate_csv:
            print(f"  CSV: {test_name}.csv")
        else:
            print(f"  CSV: отключён")
        print(f"  JSON Summary: {test_name}-summary.json")
        print(f"  История обновлена: results/history.json")
    else:
        print("Тест провален. Проверьте логи выше.")
    
    print("=" * 60)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
