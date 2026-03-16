{{ config(materialized='view') }}

select
    cast(r030 as int) as currency_id,
    txt as currency_name,
    cast(rate as double) as currency_rate,
    cc as currency_code,
    -- Парсимо дату обміну (API НБУ дає її як DD.MM.YYYY)
    try(date_parse(exchangedate, '%d.%m.%Y')) as exchange_date,
    -- Парсимо мітку часу завантаження
    cast(parse_datetime(ingested_at, 'yyyy-MM-dd HH:mm:ss') as timestamp) as ingested_at,
    -- Колонки партицій (зберігаємо їх для fct_currency_rates)
    cast(year as int) as year,
    cast(month as int) as month,
    cast(day as int) as day
from {{ source('nbu_api', 'nbu_rates_raw') }}