# Фреймворк нагрузочного тестирования — Makefile
#
# Локальная отладка:
#   make up          — поднять инфраструктуру (Prometheus, Grafana, k6)
#   make run         — запустить тест через Python-скрипт (с историей)
#   make logs        — посмотреть логи k6
#   make down        — остановить инфраструктуру
#
# CI / быстрый запуск:
#   make ci          — запустить k6 напрямую (без Docker, без инфраструктуры)
#   make ci-report   — запустить k6 и сохранить summary.json

.PHONY: up down run logs ci ci-report

# ============================================================
# Локальная отладка
# ============================================================

up:
	@echo "Поднимаем инфраструктуру нагрузочного тестирования..."
	docker compose up -d
	@echo ""
	@echo "Инфраструктура запущена:"
	@echo "  Grafana:    http://localhost:3000  (admin / admin123)"
	@echo "  Prometheus: http://localhost:9090"
	@echo ""
	@echo "Запустить тест: make run"

run:
	@echo "Запускаем тест..."
	python scripts/run-test.py $(TEST)
	@echo ""
	@echo "Готово. Результаты в results/"

logs:
	docker compose logs -f k6

down:
	docker compose down

# ============================================================
# CI / быстрый запуск (без Docker)
# ============================================================

ci:
	@echo "Запускаем k6 напрямую (без Docker)..."
	@echo "Использование: make ci TEST_FILE=k6/tests/basic-web-test.js"
	@if [ -z "$(TEST_FILE)" ]; then \
		echo "Ошибка: требуется TEST_FILE. Пример: make ci TEST_FILE=k6/tests/basic-web-test.js"; \
		exit 1; \
	fi
	k6 run $(TEST_FILE)

ci-report:
	@echo "Запускаем k6 и экспортируем summary..."
	@if [ -z "$(TEST_FILE)" ]; then \
		echo "Ошибка: требуется TEST_FILE. Пример: make ci-report TEST_FILE=k6/tests/basic-web-test.js"; \
		exit 1; \
	fi
	k6 run $(TEST_FILE) --summary-export=$(REPORT_NAME)
	@echo ""
	@echo "Summary сохранён в $(REPORT_NAME)"
