# Load Testing Project

Проект для нагрузочного тестирования веб-приложений с использованием k6, Grafana и Prometheus. Проект обеспечивает визуализацию метрик в реальном времени и автоматическое создание отчётов в формате JSON.

## Архитектура

```
k6 → StatsD Exporter → Prometheus → Grafana
```

- **k6** - инструмент для нагрузочного тестирования
- **StatsD Exporter** - приём метрик от k6 и экспорт в Prometheus формат
- **Prometheus** - сбор и хранение метрик
- **Grafana** - визуализация метрик в реальном времени

## Структура проекта

```
load-testing-project/
├── docker-compose.yml          # Оркестрация всех сервисов
├── config.yaml                 # Конфигурация тестов
├── prometheus/
│   ├── prometheus.yml          # Конфигурация Prometheus
│   └── statsd-mapping.yml      # Маппинг StatsD метрик в Prometheus
├── grafana/
│   ├── grafana.ini             # Конфигурация Grafana
│   └── provisioning/
│       ├── datasources/
│       │   └── prometheus.yml  # Подключение Prometheus
│       └── dashboards/
│           ├── dashboard.yml   # Config для автозагрузки дашбордов
│           └── k6-dashboard.json # Dashboard для метрик
├── k6/
│   └── tests/
│       └── basic-web-test.js   # Базовый тест
├── scripts/
│   └── run-test.py             # Скрипт запуска теста
├── unit_tests/
│   └── test_run_test.py        # Unit-тесты скриптов
└── results/                    # Результаты тестов (автоматически создаётся)
```

## Требования

- Docker Desktop (установлен и запущен)
- Python 3.7+ (для скриптов)
- PyYAML (установить через `pip install pyyaml`)
- pytest (для unit-тестов: `pip install pytest`)
- Git Bash или другой терминал Bash для Windows

## Установка

1. Клонируйте репозиторий или скачайте проект
2. Установите зависимости Python:
   ```bash
   pip install pyyaml pytest
   ```

3. Скопируйте `.env.example` в `.env` и настройте переменные окружения:
   ```bash
   cp .env.example .env
   ```
   Файл `.env` содержит пароли для Grafana. По умолчанию используются значения из `.env.example`.

## Запуск проекта

### 1. Запуск контейнеров

Запустите все сервисы (Prometheus, Grafana):

```bash
docker compose up -d
```

После запуска будут доступны:
- **Grafana**: http://localhost:3000 (логин: `admin`, пароль: `admin`)
- **Prometheus**: http://localhost:9090

### 2. Запуск теста

Запустите нагрузочный тест. Скрипт поддерживает разные форматы путей:

```bash
# Полный путь (Unix стиль)
python scripts/run-test.py k6/tests/basic-web-test.js

# Полный путь (Windows стиль - автоматически нормализуется)
python scripts/run-test.py k6\tests\basic-web-test.js

# Короткое имя файла (автоматически ищется в k6/tests/)
python scripts/run-test.py basic-web-test.js

# Короткое имя без расширения (автоматически добавляется .js)
python scripts/run-test.py basic-web-test
```

**Примечание:** При копировании пути из VSCode на Windows может получиться Windows-стиль с обратными слешами (`\`). Скрипт автоматически нормализует такие пути, поэтому можно использовать любой формат.

### Что происходит при запуске теста:

1. Создаётся папка с результатами в формате: `results/YYYY-MM-DD_HH-MM-SS_test-name/`
2. Запускается k6 тест с экспортом метрик в StatsD (для визуализации в Grafana в реальном времени)
3. Агрегированные метрики сохраняются в JSON Summary в созданной папке
4. Метаданные теста сохраняются в `results/history.json`

### 3. Визуализация в Grafana

**Real-time визуализация:**
Метрики передаются в Grafana в реальном времени через StatsD → Prometheus. Дашборд и datasource загружаются автоматически через Grafana provisioning при запуске контейнера.

**Просмотр отчётов:**
1. Откройте Grafana: http://localhost:3000
2. Войдите (admin/admin123)
3. Дашборд "k6 Load Testing Dashboard" уже доступен — метрики появляются в реальном времени во время теста

### 4. Файловые отчёты

После завершения теста результаты доступны в папке:
```
results/YYYY-MM-DD_HH-MM-SS_test-name/
└── test-name-summary.json  # Агрегированные метрики (JSON Summary)
```

**Формат отчётов:**
- **JSON Summary** - содержит агрегированные метрики (средние, процентили, итоги), размер ~10-50 KB

> **Примечание:** По умолчанию CSV отключён для экономии места (файлы могут быть сотнями MB). Включите в `config.yaml`: `results.generate_csv: true`.

## Доступные команды

### Управление контейнерами

```bash
docker compose up -d        # Запустить все контейнеры
docker compose down         # Остановить все контейнеры
docker compose restart       # Перезапустить контейнеры
docker compose ps           # Показать статус контейнеров
```

### Просмотр логов

```bash
docker compose logs -f              # Логи всех контейнеров
docker compose logs -f k6          # Логи k6 контейнера
docker compose logs -f grafana      # Логи Grafana
docker compose logs -f prometheus   # Логи Prometheus
```

### Запуск тестов

```bash
# Можно использовать любой формат пути
python scripts/run-test.py k6/tests/basic-web-test.js    # Полный путь
python scripts/run-test.py basic-web-test.js              # Короткое имя
python scripts/run-test.py basic-web-test                 # Без расширения

python scripts/run-test.py (скрипт запуска тестов написан на python, запускаем его)
далее название файла с тестом или путь к нему, любой из вариантов выше. так скрипт запустит тест и сформирует отчёт
```

### Unit-тесты скриптов

Проект включает unit-тесты для Python-скриптов:

```bash
python -m pytest unit_tests/ -v

# Запуск конкретного тест-файла
python -m pytest unit_tests/test_run_test.py -v
```

Тесты покрывают:
- Нормализацию путей (Windows/Unix, короткие имена)
- Извлечение имени теста из пути
- Загрузку и валидацию config.yaml
- Извлечение метрик из JSON summary
- Форматирование длительности и процентов
- Загрузку и валидацию JSON отчётов

### Очистка результатов

Удалить результаты тестов (сохраняет history.json):
```bash
rm -rf results/*/
```

## Конфигурация

### config.yaml

Основной файл конфигурации тестов:

```yaml
test:
  url: "https://httpbin.org"  # URL для тестирования
  vus: 5                       # Количество виртуальных пользователей
  duration: "60s"              # Длительность теста

  # Ступенчатые стадии (опционально, перезаписывает duration):
  stages:
    - duration: "10s"
      target: 5
    - duration: "50s"
      target: 5
    - duration: "10s"
      target: 0

thresholds:
  p95_duration: 500            # 95% запросов должны быть < 500ms
  error_rate: 0.01             # Ошибок должно быть < 1%

results:
  generate_csv: false          # CSV отключён по умолчанию
```

### Создание собственного теста

1. Создайте файл в `k6/tests/`, например `my-test.js` (используйте `basic-web-test.js` как шаблон)
2. Настройте параметры нагрузки и thresholds
3. Запустите тест:
   ```bash
   python scripts/run-test.py k6/tests/my-test.js    # Полный путь
   python scripts/run-test.py my-test.js              # Короткое имя
   python scripts/run-test.py my-test                 # Без расширения
   ```

## Метрики в Grafana

Dashboard включает следующие метрики:

1. **Requests per Second (RPS)** - количество запросов в секунду
2. **Error Rate** - процент ошибок
3. **Response Time (Average)** - среднее время ответа
4. **Response Time (95th Percentile)** - 95-й перцентиль задержки
5. **Virtual Users** - активные виртуальные пользователи
6. **Response Receiving Time** - время получения ответа

## Формат результатов

### JSON Summary отчёт

Содержит агрегированные метрики теста (компактный формат):
- Итоговые значения метрик (средние, минимум, максимум, процентили)
- Результаты проверок (checks) - количество passes/fails
- Результаты thresholds
- Группировка по группам тестов
- Размер файла: ~10-50 KB (вместо сотен MB для полного JSON)

**Структура:**
- `metrics` - агрегированные метрики (http_reqs, http_req_duration, vus и др.)
- `groups` - результаты групп сценариев (если используются)

### CSV отчёт

**По умолчанию отключён** для экономии места на диске (файлы могут быть очень большими - сотни MB).

Содержит детальные данные по каждому запросу:
- Время запроса
- Длительность
- Статус код
- Размер ответа

**Включение CSV:**
Отредактируйте `config.yaml` и установите:
```yaml
results:
  generate_csv: true  # Включить генерацию CSV отчёта
```

**Примечание:** Для большинства случаев достаточно summary JSON, который содержит все агрегированные метрики в компактном формате (~10-50 KB).

### История тестов

Файл `results/history.json` содержит метаданные всех запущенных тестов:
- Дата и время запуска
- Имя теста
- Параметры конфигурации
- Путь к результатам
- Статус выполнения

## Устранение неполадок

### Контейнеры не запускаются

```bash
# Проверьте статус
docker compose ps

# Просмотрите логи
docker compose logs

# Перезапустите контейнеры
docker compose restart
```

### Grafana не показывает метрики

1. Проверьте, что Prometheus собирает метрики со statsd-exporter: `curl -s http://localhost:9090/api/v1/label/__name__/values | grep k6_http`
2. Убедитесь, что k6 тест отправляет метрики через StatsD (в выводе должно быть `output: statsd`)
3. Проверьте настройки datasource в Grafana: http://localhost:3000 → Configuration → Data sources

### k6 тест не запускается

1. Убедитесь, что контейнеры запущены: `docker compose ps`
2. Проверьте путь к тесту
3. Просмотрите логи: `docker compose logs k6`

### StatsD метрики не доходят до Prometheus

1. Проверьте, что statsd-exporter получает метрики: `curl -s http://localhost:9102/metrics | grep k6_http`
2. Убедитесь, что маппинг в `prometheus/statsd-mapping.yml` корректен
3. Проверьте, что Prometheus скрапит statsd-exporter: `curl http://localhost:9090/api/v1/targets`

## Остановка проекта

```bash
docker compose down
```

Это остановит все контейнеры, но сохранит данные (volumes не удаляются).

Для полной очистки (включая данные):
```bash
docker compose down -v
```

## Дополнительная информация

- **k6 документация**: https://k6.io/docs/
- **Grafana документация**: https://grafana.com/docs/
- **Prometheus документация**: https://prometheus.io/docs/

## Лицензия

Этот проект создан для образовательных целей.
