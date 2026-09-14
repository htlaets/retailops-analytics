# RetailOps Analytics

Небольшой проект для анализа продаж интернет-магазина. Скрипт на Python создаёт тестовые заказы, проверяет данные и загружает их в SQLite. Результат можно посмотреть в Superset или в веб-дашборде из папки `dashboard`.

## Стек

- Python 3
- SQL
- SQLite
- Apache Superset
- Docker Compose
- HTML, JavaScript

## Как устроено

`CSV → Python → SQLite → Superset / web dashboard`

Таблицы в SQLite:

- `fact_orders` — заказы и рассчитанные показатели;
- `dim_date` — календарь;
- `dim_product` — товары и категории;
- `dim_customer` — клиенты, сегменты и регионы;
- `bi_order_performance` — готовая витрина для BI.

## Запуск

```bash
python3 pipeline/run_pipeline.py
```

Скрипт создаст:

- `data/raw/orders.csv` — исходные данные;
- `data/warehouse/retailops.db` — хранилище SQLite;
- `dashboard/data.json` — агрегаты для веб-дашборда.

### Superset

```bash
docker compose -f docker-compose.superset.yml up
```

Открыть `http://localhost:8088`. Логин и пароль: `admin` / `admin`. Подключение к SQLite добавляется при запуске. Графики описаны в [`superset/README.md`](superset/README.md).

### Веб-дашборд

```bash
python3 -m http.server 8000 -d dashboard
```

Открыть `http://localhost:8000`.

## Проверки

```bash
python3 -m unittest discover -s tests -v
```

Проверяются дубликаты `order_id`, даты, количество, цены, внешние ключи и итоговая сумма выручки.

## Структура

```text
pipeline/              генерация данных и загрузка хранилища
sql/                   SQL-запросы для аналитики
superset/              конфигурация Apache Superset
dashboard/             веб-дашборд
data/                  исходные данные и SQLite
tests/                 тесты пайплайна
.github/workflows/     CI и публикация GitHub Pages
```
