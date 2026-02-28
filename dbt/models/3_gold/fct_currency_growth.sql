{{ config(materialized='table') }}

with daily_changes as (
    -- Крок 1: Розраховуємо щоденні зміни
    select
        currency_code,
        currency_name,
        exchange_date,
        date_trunc('month', exchange_date) as report_month,
        currency_rate,
        lag(currency_rate) over (
            partition by currency_code 
            order by exchange_date
        ) as prev_day_rate
    from {{ ref('fct_currency_rates') }}
),

daily_metrics as (
    -- Крок 2: Рахуємо дельту та її модуль для аналізу розмаху
    select 
        *,
        (currency_rate - prev_day_rate) as daily_delta,
        abs(currency_rate - prev_day_rate) as abs_daily_delta
    from daily_changes
),

monthly_aggregation as (
    -- Крок 3: Агрегуємо дані з обробкою NULL через COALESCE
    select
        currency_code,
        currency_name,
        report_month,
        min_by(currency_rate, exchange_date) as month_start_rate,
        max_by(currency_rate, exchange_date) as month_end_rate,
        
        -- Середній ріст та падіння (замінюємо NULL на 0.0)
        coalesce(avg(case when daily_delta > 0 then daily_delta end), 0.0) as avg_positive_delta,
        coalesce(avg(case when daily_delta < 0 then daily_delta end), 0.0) as avg_negative_delta,
        
        -- Максимальний стрибок (наскільки сильно штормило валюту за день)
        max(abs_daily_delta) as max_volatility_day,
        
        count(case when daily_delta > 0 then 1 end) as days_of_growth,
        count(case when daily_delta < 0 then 1 end) as days_of_decline,
        count(*) as total_days_measured
    from daily_metrics
    group by 1, 2, 3
)

select
    currency_code,
    currency_name,
    report_month,
    month_start_rate,
    month_end_rate,
    
    -- Загальний ріст/падіння у %
    round(((month_end_rate - month_start_rate) / nullif(month_start_rate, 0)) * 100, 2) as total_monthly_growth_pct,
    
    -- Візуальний індикатор тренду (дуже зручно для швидкого аналізу)
    case 
        when month_end_rate > month_start_rate then '📈 UP'
        when month_end_rate < month_start_rate then '📉 DOWN'
        else '➖ STABLE'
    end as market_trend,

    -- Середні значення коливань (вже без NULL)
    round(avg_positive_delta, 4) as avg_daily_gain,
    round(avg_negative_delta, 4) as avg_daily_loss,
    
    -- Показник стабільності: чим вище значення, тим спокійніша валюта
    round(max_volatility_day, 4) as max_one_day_jump,
    
    days_of_growth,
    days_of_decline,
    total_days_measured
from monthly_aggregation
-- Сортуємо: найсвіжіші місяці та найбільші зміни (по модулю) нагорі
order by report_month desc, abs(total_monthly_growth_pct) desc