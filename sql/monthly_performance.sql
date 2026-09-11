-- Monthly metrics used by the dashboard.
SELECT
    d.year,
    d.month,
    d.month_name,
    c.region,
    p.category,
    f.channel,
    ROUND(SUM(f.revenue), 2) AS revenue,
    ROUND(SUM(f.gross_profit), 2) AS gross_profit,
    ROUND(100.0 * SUM(f.gross_profit) / NULLIF(SUM(f.revenue), 0), 1) AS gross_margin_pct,
    COUNT(DISTINCT f.order_id) AS orders,
    ROUND(SUM(f.revenue) / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS average_order_value,
    ROUND(100.0 * AVG(f.on_time), 1) AS on_time_delivery_pct
FROM fact_orders AS f
JOIN dim_date AS d ON d.date_key = f.date_key
JOIN dim_product AS p ON p.product_key = f.product_key
JOIN dim_customer AS c ON c.customer_key = f.customer_key
GROUP BY d.year, d.month, d.month_name, c.region, p.category, f.channel
ORDER BY d.year, d.month, c.region, p.category, f.channel;
