# Grafana Dashboards

Дашборды из этой папки автоматически загружаются при запуске контейнера Grafana через provisioning.

## Добавление нового дашборда

1. Скачайте JSON файл дашборда с https://grafana.com/grafana/dashboards/
2. Сохраните его в эту папку (`grafana/provisioning/dashboards/`)
3. Перезапустите контейнер Grafana: `docker compose restart grafana`

Дашборд появится автоматически — ручной импорт через UI не требуется.
