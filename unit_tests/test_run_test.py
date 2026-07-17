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

    def test_config_has_thresholds(self):
        """Конфигурация должна содержать раздел 'thresholds' с порогами SLA."""
        config = load_config()
        assert 'thresholds' in config

    def test_config_has_results(self):
        """Конфигурация должна содержать раздел 'results' с настройками отчётов."""
        config = load_config()
        assert 'results' in config

