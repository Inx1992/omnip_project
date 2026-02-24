{{ config(materialized='view') }}

with source as (
    select * from {{ source('nbu_api', 'nbu_rates_raw') }}
)

select
    cc as currency_code,
    txt as currency_name,
    cast(rate as double) as exchange_rate,
    cast(exchangedate as date) as rate_date,
    cast(ingested_at as timestamp) as ingested_at,
    year,
    month
from source