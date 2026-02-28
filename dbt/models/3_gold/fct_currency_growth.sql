{{ config(materialized='table') }}

with daily_changes as (
    -- Крок 1: Розраховуємо щоденні зміни (дельту)
    select
        currency_code,
        currency_name,
        exchange_date,
        -- Використовуємо date_trunc для групування по місяцях
        date_trunc('month', exchange_date) as report_month,
        currency_rate,
        lag(currency_rate) over (
            partition by currency_code 
            order by exchange_date
        ) as prev_day_rate
    from {{ ref('fct_currency_rates') }}
),

daily_metrics as (
    -- Крок 2: Рахуємо дельту для кожного дня
    select 
        *,
        (currency_rate - prev_day_rate) as daily_delta
    from daily_changes
),

monthly_aggregation as (
    -- Крок 3: Агрегуємо дані за місяць
    select
        currency_code,
        currency_name,
        report_month,
        -- Початковий курс місяця (курс на першу дату місяця)
        min_by(currency_rate, exchange_date) as month_start_rate,
        -- Кінцевий курс місяця (курс на останню дату місяця)
        max_by(currency_rate, exchange_date) as month_end_rate,
        
        -- Середній позитивний приріст (тільки коли валюта росла)
        avg(case when daily_delta > 0 then daily_delta end) as avg_positive_delta,
        
        -- Середнє падіння (тільки коли валюта падала)
        avg(case when daily_delta < 0 then daily_delta end) as avg_negative_delta,
        
        -- Загальна кількість днів росту та падіння
        count(case when daily_delta > 0 then 1 end) as days_of_growth,
        count(case when daily_delta < 0 then 1 end) as days_of_decline
    from daily_metrics
    group by 1, 2, 3
)

select
    currency_code,
    currency_name,
    report_month,
    month_start_rate,
    month_end_rate,
    -- Загальний ріст/падіння за місяць у %
    round(((month_end_rate - month_start_rate) / nullif(month_start_rate, 0)) * 100, 2) as total_monthly_growth_pct,
    -- Середні значення коливань
    round(avg_positive_delta, 4) as avg_daily_gain,
    round(avg_negative_delta, 4) as avg_daily_loss,
    days_of_growth,
    days_of_decline
from monthly_aggregation
order by report_month desc, total_monthly_growth_pct desc