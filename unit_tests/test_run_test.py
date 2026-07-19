"""
Unit-тесты для функций run-test.py.
Проверяют нормализацию путей, извлечение имени теста и загрузку конфигурации.
"""

import pytest
import importlib.util
import os
from pathlib import Path

# Импорт run-test.py (дефис в имени файла не позволяет использовать обычный import)
_spec = importlib.util.spec_from_file_location(
    "run_test",
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'run-test.py')
)
_run_test = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_run_test)

normalize_test_path = _run_test.normalize_test_path
get_test_name = _run_test.get_test_name
load_config = _run_test.load_config
validate_summary = _run_test.validate_summary


class TestNormalizeTestPath:
    """Тесты функции normalize_test_path — преобразования путей к тестам."""

    def test_full_unix_path(self):
        """Полный Unix-путь (через '/') должен нормализоваться без изменений."""
        result = normalize_test_path("k6/tests/basic-web-test.js")
        assert result == "k6/tests/basic-web-test.js"

    def test_full_windows_path(self):
        """Windows-путь (через '\') должен быть преобразован в Unix-формат."""
        result = normalize_test_path(r"k6	ests\basic-web-test.js")
        assert result == "k6/tests/basic-web-test.js"

    def test_short_name_with_extension(self):
        """Короткое имя файла с расширением должно разрешаться в полный путь."""
        result = normalize_test_path("basic-web-test.js")
        assert result == "k6/tests/basic-web-test.js"

    def test_short_name_without_extension(self):
        """Короткое имя без расширения должно автоматически дополняться до .js."""
        result = normalize_test_path("basic-web-test")
        assert result == "k6/tests/basic-web-test.js"

    def test_leading_dot_slash(self):
        """Ведущий './' должен быть удалён из пути."""
        result = normalize_test_path("./k6/tests/basic-web-test.js")
        assert result == "k6/tests/basic-web-test.js"

    def test_leading_slash(self):
        """Ведущий '/' должен быть удалён из пути."""
        result = normalize_test_path("/k6/tests/basic-web-test.js")
        assert result == "k6/tests/basic-web-test.js"


class TestGetTestName:
    """Тесты функции get_test_name — извлечения имени теста из пути."""

    def test_basic_name(self):
        """Из полного пути должно извлекаться базовое имя без расширения."""
        assert get_test_name("k6/tests/basic-web-test.js") == "basic-web-test"

    def test_short_path(self):
        """Из короткого имени файла должно извлекаться базовое имя."""
        assert get_test_name("basic-web-test.js") == "basic-web-test"

    def test_with_directory(self):
        """Имя теста должно извлекаться корректно при любом формате пути."""
        assert get_test_name("k6/tests/my-test.js") == "my-test"


class TestLoadConfig:
    """Тесты функции load_config — загрузки и валидации config.yaml."""

    def test_config_loads(self):
        """Конфигурация должна загружаться без ошибок."""
        config = load_config()
        assert config is not None

    def test_config_has_test_section(self):
        """Конфигурация должна содержать раздел 'test' с параметрами теста."""
        config = load_config()
        assert 'test' in config

    def test_config_has_url(self):
        """В разделе 'test' должен быть указан URL для тестирования."""
        config = load_config()
        assert 'url' in config['test']

    def test_thresholds_in_test_file(self):
        """Thresholds должны быть в файле теста, а не в config.yaml."""
        import os
        test_file = os.path.join(
            os.path.dirname(__file__),
            '..', 'k6', 'tests', 'basic-web-test.js'
        )
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'thresholds' in content

    def test_config_has_results(self):
        """Конфигурация должна содержать раздел 'results' с настройками отчётов."""
        config = load_config()
        assert 'results' in config


class TestValidateSummary:
    """Тесты функции validate_summary — проверки порогов по summary JSON."""

    def test_pass_all_metrics(self, tmp_path):
        """Все метрики в норме — тест проходит."""
        summary = {
            'metrics': {
                'checks': {'passes': 990, 'fails': 10, 'value': 0.99},
                'http_req_failed': {'value': 0.005},
                'http_req_duration': {'p(95)': 200, 'avg': 150, 'max': 800},
            }
        }
        summary_file = tmp_path / 'test-summary.json'
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f)
        
        passed, details = validate_summary(tmp_path, 'test')
        assert passed is True
        assert 'PASS' in details

    def test_fail_error_rate(self, tmp_path):
        """Доля ошибок превышает 1% — тест провален."""
        summary = {
            'metrics': {
                'checks': {'passes': 900, 'fails': 100, 'value': 0.90},
                'http_req_failed': {'value': 0.05},
                'http_req_duration': {'p(95)': 200, 'avg': 150, 'max': 800},
            }
        }
        summary_file = tmp_path / 'test-summary.json'
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f)
        
        passed, details = validate_summary(tmp_path, 'test')
        assert passed is False
        assert 'FAIL' in details
        assert 'Ошибки' in details

    def test_fail_p95(self, tmp_path):
        """P95 превышает 5000 мс — тест провален."""
        summary = {
            'metrics': {
                'checks': {'passes': 990, 'fails': 10, 'value': 0.99},
                'http_req_failed': {'value': 0.001},
                'http_req_duration': {'p(95)': 6000, 'avg': 4500, 'max': 9000},
            }
        }
        summary_file = tmp_path / 'test-summary.json'
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f)
        
        passed, details = validate_summary(tmp_path, 'test')
        assert passed is False
        assert 'P95' in details

    def test_fail_checks(self, tmp_path):
        """Доля успешных проверок ниже 99% — тест провален."""
        summary = {
            'metrics': {
                'checks': {'passes': 500, 'fails': 500, 'value': 0.50},
                'http_req_failed': {'value': 0.001},
                'http_req_duration': {'p(95)': 200, 'avg': 150, 'max': 800},
            }
        }
        summary_file = tmp_path / 'test-summary.json'
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f)
        
        passed, details = validate_summary(tmp_path, 'test')
        assert passed is False
        assert 'Checks' in details

    def test_missing_summary_file(self, tmp_path):
        """Файл summary не найден — тест провален."""
        passed, details = validate_summary(tmp_path, 'nonexistent')
        assert passed is False
        assert 'не найден' in details

    def test_invalid_json(self, tmp_path):
        """Невалидный JSON — тест провален."""
        summary_file = tmp_path / 'test-summary.json'
        summary_file.write_text('not valid json{{{')
        
        passed, details = validate_summary(tmp_path, 'test')
        assert passed is False
        assert 'Ошибка' in details

