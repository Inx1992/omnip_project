{{ config(materialized='table') }}

with daily_deduplicated as (
    -- Крок 1: Отримуємо унікальний курс на кожен день (як ми робили в Gold шарі)
    select
        currency_code,
        currency_name,
        year,
        month,
        currency_rate,
        row_number() over (
            partition by currency_code, exchange_date 
            order by ingested_at desc
        ) as rn
    from {{ ref('fct_currency_rates') }} -- Читаємо з Silver
)

select
    currency_code,
    currency_name,
    year,
    month,
    round(avg(currency_rate), 4) as avg_monthly_rate,
    max(currency_rate) as max_rate,
    min(currency_rate) as min_rate,
    count(*) as days_count -- Скільки днів у цьому місяці ми зафіксували
from daily_deduplicated
where rn = 1 -- Беремо тільки актуальні записи
group by 1, 2, 3, 4
order by year desc, month desc, avg_monthly_rate desc