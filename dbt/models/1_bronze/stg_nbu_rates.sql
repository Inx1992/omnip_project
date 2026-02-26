{{ config(materialized='view') }}

select
    cast(r030 as int) as currency_id,
    txt as currency_name,
    cast(rate as double) as currency_rate,
    cc as currency_code,
    -- Конвертуємо рядки в правильні типи один раз тут
    try(date_parse(exchangedate, '%d.%m.%Y')) as exchange_date,
    cast(parse_datetime(ingested_at, 'yyyy-MM-dd HH:mm:ss') as timestamp) as ingested_at,
    year, 
    month, 
    day
from {{ source('nbu_api', 'nbu_rates_raw') }}