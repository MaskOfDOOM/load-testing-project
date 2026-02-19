# Load Testing Project

Проект для нагрузочного тестирования веб-приложений с использованием k6, Grafana, Prometheus и InfluxDB. Проект обеспечивает визуализацию метрик в реальном времени и автоматическое создание отчётов в форматах JSON и CSV.

## Архитектура

```
k6 → StatsD Exporter → Prometheus → Grafana
```

- **k6** - инструмент для нагрузочного тестирования
- **StatsD Exporter** - приём метрик от k6 и экспорт в Prometheus формат
- **Prometheus** - сбор и хранение метрик
- **Grafana** - визуализация метрик в реальном времени
- **InfluxDB** - опционально, для дополнительного хранения (retention 7 дней)

## Структура проекта

```
load-testing-project/
├── docker-compose.yml          # Оркестрация всех сервисов
├── config.yaml                  # Конфигурация тестов
├── prometheus/
│   └── prometheus.yml          # Конфигурация Prometheus
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── prometheus.yml  # Подключение Prometheus
│       └── dashboards/
│           └── k6-dashboard.json # Dashboard для метрик
├── k6/
│   └── tests/
│       └── basic-web-test.js   # Базовый тест
├── scripts/
│   ├── run-test.py             # Скрипт запуска теста
│   └── compare-results.py      # Сравнение результатов
└── results/                    # Результаты тестов (автоматически создаётся)
```

## Требования

- Docker Desktop (установлен и запущен)
- Python 3.7+ (для скриптов)
- PyYAML (установить через `pip install pyyaml`)
- Git Bash или другой терминал Bash для Windows

## Установка

1. Клонируйте репозиторий или скачайте проект
2. Установите зависимости Python:
   ```bash
   pip install pyyaml
   ```

3. (Опционально) Скопируйте `.env.example` в `.env` и настройте переменные окружения:
   ```bash
   cp .env.example .env
   ```

## Запуск проекта

### 1. Запуск контейнеров

Запустите все сервисы (InfluxDB, Prometheus, Grafana):

```bash
docker compose up -d
```

После запуска будут доступны:
- **Grafana**: http://localhost:3000 (логин: `admin`, пароль: `admin`)
- **Prometheus**: http://localhost:9090
- **InfluxDB**: http://localhost:8086

### 2. Настройка InfluxDB (первый запуск)

При первом запуске необходимо настроить InfluxDB:

1. Откройте http://localhost:8086
2. Войдите с учётными данными:
   - Username: `admin`
   - Password: `admin123`
3. Создайте Bucket:
   - Name: `k6`
   - Retention: `7 days`
4. Создайте API Token:
   - Description: `k6-token`
   - Permissions: `Read/Write` для bucket `k6`
   - Скопируйте токен (он должен быть `k6-token` если использованы настройки по умолчанию)

**Примечание**: Если вы изменили токен, обновите его в `config.yaml` и в k6 тесте.

### 3. Запуск теста

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
3. Результаты сохраняются в форматах JSON и CSV в созданной папке
4. Метаданные теста сохраняются в `results/history.json`

### 4. Просмотр результатов

**Текущая конфигурация:**
Метрики сохраняются в CSV и JSON отчётах после завершения теста. Real-time визуализация в Grafana требует дополнительной настройки.

**Для включения real-time метрик в Grafana:**

Встроенный StatsD output был удалён из k6 v0.55.0+. Для real-time метрик доступны варианты:

1. **xk6-output-statsd** (требует доработки):
   - Кастомный образ k6 уже собран в проекте (Dockerfile.k6)
   - Расширение установлено, но требует правильной настройки формата
   - Нужно использовать формат: `--out statsd=statsd-exporter:9125` (но расширение может использовать другой формат)

2. **k6 Cloud** (самый простой вариант):
   - Требует регистрации на k6.io (бесплатный план доступен)
   - Простая настройка: добавьте `--out cloud` в команду k6
   - Метрики доступны в реальном времени на k6.io

3. **Prometheus Remote Write** (экспериментально):
   - Требует настройки Prometheus для приёма remote write
   - Может работать нестабильно

**Текущее состояние:** Тесты запускаются успешно, метрики сохраняются в CSV и JSON. Real-time визуализация требует дополнительной настройки одного из вариантов выше.

**Просмотр отчётов:**
1. Откройте Grafana: http://localhost:3000
2. Войдите (admin/admin)
3. Импортируйте готовый дашборд:
   - Нажмите "+" → "Import dashboard"
   - Введите ID: **2587** (официальный k6 дашборд)
   - Выберите datasource: **Prometheus**
   - Нажмите "Import"
4. Или используйте CSV/JSON файлы из папки результатов для анализа

### 5. Просмотр отчётов

После завершения теста результаты доступны в папке:
```
results/YYYY-MM-DD_HH-MM-SS_test-name/
├── test-name-summary.json  # Компактный JSON с агрегированными метриками
└── test-name.csv           # Детальный CSV с данными по каждому запросу
```

**Формат отчётов:**
- **JSON Summary** - содержит только агрегированные метрики (средние, процентили, итоги), размер ~10-50 KB
- **CSV** - содержит детальные данные по каждому запросу (время, длительность, статус), размер зависит от количества запросов

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
docker compose logs -f influxdb     # Логи InfluxDB
```

### Запуск тестов

```bash
# Можно использовать любой формат пути
python scripts/run-test.py k6/tests/basic-web-test.js    # Полный путь
python scripts/run-test.py basic-web-test.js              # Короткое имя
python scripts/run-test.py basic-web-test                 # Без расширения
```

### Сравнение результатов

Сравнить два теста по индексам из истории:
```bash
python scripts/compare-results.py 14 15
```

Или по путям к JSON summary файлам:
```bash
python scripts/compare-results.py results/path1/test-summary.json results/path2/test-summary.json
```

Для просмотра доступных тестов:
```bash
python scripts/compare-results.py
```

**Примечание:** Сравнение работает только с summary JSON файлами (компактный формат). Старые тесты с полным JSON форматом не поддерживаются для сравнения - перезапустите тест для получения summary формата.

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

thresholds:
  p95_duration: 500            # 95% запросов должны быть < 500ms
  error_rate: 0.01             # Ошибок должно быть < 1%

influxdb:
  url: "http://localhost:8086"
  token: "k6-token"
  org: "k6"
  bucket: "k6"
```

### Создание собственного теста

1. Создайте новый файл в `k6/tests/`, например `my-test.js`
2. Используйте базовый шаблон из `basic-web-test.js`
3. Настройте параметры нагрузки и thresholds
4. Запустите тест (можно использовать любой формат пути):
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
- `root_group` - результаты проверок и групп
- `state` - состояние теста

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

1. Проверьте, что Prometheus подключён к InfluxDB
2. Убедитесь, что k6 тест отправляет метрики в InfluxDB
3. Проверьте настройки datasource в Grafana

### k6 тест не запускается

1. Убедитесь, что контейнеры запущены: `docker compose ps`
2. Проверьте путь к тесту
3. Просмотрите логи: `docker compose logs k6`

### InfluxDB не принимает метрики

1. Проверьте токен в `config.yaml` и в k6 тесте
2. Убедитесь, что bucket `k6` создан
3. Проверьте подключение: откройте http://localhost:8086

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
- **InfluxDB документация**: https://docs.influxdata.com/

## Лицензия

Этот проект создан для образовательных целей.
