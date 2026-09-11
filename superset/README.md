# Superset

## Запуск

```bash
python3 pipeline/run_pipeline.py
docker compose -f docker-compose.superset.yml up
```

Открыть `http://localhost:8088`. Логин и пароль для локального запуска: `admin` / `admin`.

## Датасет

1. Открыть **Data → Datasets → + Dataset**.
2. Выбрать подключение **RetailOps Warehouse**.
3. Выбрать `bi_order_performance`.
4. Указать `order_date` как временную колонку.

## Графики

| Название | Тип | Настройка |
|---|---|---|
| Revenue | Big Number | `SUM(revenue)` |
| Gross profit | Big Number | `SUM(gross_profit)` |
| Gross margin | Big Number | `SUM(gross_profit) / SUM(revenue)` |
| Orders | Big Number | `COUNT_DISTINCT(order_id)` |
| Revenue by month | Time-series Line | месяц, revenue, gross profit |
| Revenue by category | Bar Chart | category, `SUM(revenue)` |
| Regions | Table | region, revenue, profit, margin, `AVG(on_time)` |

Фильтры: `region`, `channel`, `order_date`.

## Остановка

```bash
docker compose -f docker-compose.superset.yml down
```
