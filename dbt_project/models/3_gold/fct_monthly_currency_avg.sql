{{ config(materialized='table') }}

with monthly_data as (
    select
        currency_code,
        currency_name,
        year,
        month,
        currency_rate 
    from {{ ref('stg_nbu_rates') }}
)

select
    currency_code,
    currency_name,
    year,
    month,
    round(avg(currency_rate), 4) as avg_monthly_rate,
    max(currency_rate) as max_rate,
    min(currency_rate) as min_rate,
    count(*) as days_count 
from monthly_data
group by 1, 2, 3, 4
order by year desc, month desc, avg_monthly_rate desc