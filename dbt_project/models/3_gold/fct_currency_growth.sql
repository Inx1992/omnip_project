{{ config(materialized='table') }}

with raw_data as (
    select
        currency_code,
        currency_name,
        -- Беремо дату без часу для чіткого сортування
        date(cast(exchange_date as timestamp)) as ex_date,
        currency_rate
    from {{ ref('stg_nbu_rates') }}
),

ordered_rates as (
    select
        *,
        lag(currency_rate) over (
            partition by currency_code 
            order by ex_date
        ) as prev_rate
    from raw_data
)

select
    currency_code,
    currency_name,
    ex_date as exchange_date,
    currency_rate as current_rate,
    prev_rate as previous_rate,
    -- рахуємо різницю
    round(currency_rate - prev_rate, 4) as delta_abs,
    -- рахуємо % (додаємо nullif щоб не ділити на нуль)
    round(((currency_rate - prev_rate) / nullif(prev_rate, 0)) * 100, 2) as growth_percentage
from ordered_rates
-- прибираємо коментар нижче, якщо хочеш бачити ТІЛЬКИ ті дні, де є зміна
-- where prev_rate is not null 
order by exchange_date desc, growth_percentage desc