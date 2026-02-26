{{ config(materialized='table') }}

with deduplicated_silver as (
    -- Крок 1: Беремо тільки ОДИН (останній) запис для кожної валюти на кожен день
    select
        currency_code,
        currency_name,
        exchange_date,
        currency_rate,
        row_number() over (
            partition by currency_code, exchange_date 
            order by ingested_at desc
        ) as rn
    from {{ ref('fct_currency_rates') }}
),

daily_rates as (
    -- Крок 2: Фільтруємо дублікати
    select
        currency_code,
        currency_name,
        exchange_date,
        currency_rate
    from deduplicated_silver
    where rn = 1
),

ordered_rates as (
    -- Крок 3: Розраховуємо попередній курс (lag)
    select
        *,
        lag(currency_rate) over (
            partition by currency_code 
            order by exchange_date
        ) as prev_rate
    from daily_rates
)

select
    currency_code,
    currency_name,
    exchange_date,
    currency_rate as current_rate,
    prev_rate as previous_rate,
    -- рахуємо різницю
    round(currency_rate - prev_rate, 4) as delta_abs,
    -- рахуємо % (nullif для безпеки)
    round(((currency_rate - prev_rate) / nullif(prev_rate, 0)) * 100, 2) as growth_percentage
from ordered_rates
where prev_rate is not null -- зазвичай для росту нам потрібне порівняння
order by exchange_date desc, growth_percentage desc