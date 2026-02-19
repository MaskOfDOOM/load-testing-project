# Grafana Dashboards

Эта папка содержит дашборды для Grafana, которые автоматически загружаются при запуске контейнера.

## Использование готового дашборда

### Способ 1: Скачать готовый дашборд с Grafana Labs

1. Откройте https://grafana.com/grafana/dashboards/
2. Найдите дашборд для k6 (например, поиск "k6")
3. Нажмите "Copy ID to clipboard" или скачайте JSON файл
4. Если используете ID:
   - Откройте Grafana: http://localhost:3000
   - Перейдите в Dashboards → Import
   - Вставьте ID и нажмите Load
   - Выберите Prometheus datasource
   - Нажмите Import

5. Если скачали JSON:
   - Сохраните файл в эту папку (`grafana/provisioning/dashboards/`)
   - Перезапустите контейнер Grafana: `docker compose restart grafana`

### Способ 2: Импорт через UI Grafana

1. Откройте Grafana: http://localhost:3000
2. Войдите (admin/admin)
3. Нажмите "+" → "Import dashboard"
4. Загрузите JSON файл или вставьте ID дашборда с Grafana Labs
5. Выберите datasource (Prometheus)
6. Нажмите "Import"

### Рекомендуемые дашборды для k6

- **k6 Load Testing Dashboard**: ID 2587 (официальный дашборд от Grafana)
- Поиск на grafana.com: "k6 performance testing"
