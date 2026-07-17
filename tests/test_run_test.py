"""
Unit tests for run-test.py functions.
Tests path normalization, test name extraction, and config loading.
"""

import pytest
import importlib.util
import os
from pathlib import Path

# Import run-test.py (dash in filename prevents normal import)
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
    """Tests for normalize_test_path function"""

    def test_full_unix_path(self):
        """Full Unix-style path should be normalized correctly"""
        result = normalize_test_path("k6/tests/basic-web-test.js")
        assert result == "k6/tests/basic-web-test.js"

    def test_full_windows_path(self):
        """Windows-style path with backslashes should be normalized"""
        result = normalize_test_path(r"k6\tests\basic-web-test.js")
        assert result == "k6/tests/basic-web-test.js"

    def test_short_name_with_extension(self):
        """Short name with .js extension should resolve to full path"""
        result = normalize_test_path("basic-web-test.js")
        assert result == "k6/tests/basic-web-test.js"

    def test_short_name_without_extension(self):
        """Short name without extension should auto-append .js"""
        result = normalize_test_path("basic-web-test")
        assert result == "k6/tests/basic-web-test.js"

    def test_leading_dot_slash(self):
        """Leading ./ should be stripped"""
        result = normalize_test_path("./k6/tests/basic-web-test.js")
        assert result == "k6/tests/basic-web-test.js"

    def test_leading_slash(self):
        """Leading / should be stripped"""
        result = normalize_test_path("/k6/tests/basic-web-test.js")
        assert result == "k6/tests/basic-web-test.js"


class TestGetTestName:
    """Tests for get_test_name function"""

    def test_basic_name(self):
        """Should extract stem from path"""
        assert get_test_name("k6/tests/basic-web-test.js") == "basic-web-test"

    def test_short_path(self):
        """Should extract stem from filename"""
        assert get_test_name("basic-web-test.js") == "basic-web-test"

    def test_with_directory(self):
        """Should extract stem from full path"""
        assert get_test_name("k6/tests/my-test.js") == "my-test"


class TestLoadConfig:
    """Tests for load_config function"""

    def test_config_loads(self):
        """Config should load without error"""
        config = load_config()
        assert config is not None

    def test_config_has_test_section(self):
        """Config should have 'test' section"""
        config = load_config()
        assert 'test' in config

    def test_config_has_url(self):
        """Config should have test.url"""
        config = load_config()
        assert 'url' in config['test']

    def test_config_has_thresholds(self):
        """Config should have 'thresholds' section"""
        config = load_config()
        assert 'thresholds' in config

    def test_config_has_results(self):
        """Config should have 'results' section"""
        config = load_config()
        assert 'results' in config
