{{ config(materialized='table') }}

with monthly_data as (
    select
        currency_code,
        currency_name,
        year,
        month,
        exchange_rate
    from {{ ref('stg_nbu_rates') }} -- Переконайся, що тут назва збігається з файлом у Silver
)

select
    currency_code,
    currency_name,
    year,
    month,
    avg(exchange_rate) as avg_monthly_rate,
    max(exchange_rate) as max_rate,
    min(exchange_rate) as min_rate
from monthly_data
group by 1, 2, 3, 4