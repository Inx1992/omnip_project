{{
  config(
    materialized='incremental',
    incremental_strategy='append',
    on_schema_change='append_fields',
    format='parquet'
  )
}}

with source_data as (
    select
        cast(r030 as int) as currency_id,
        txt as currency_name,
        cast(currency_rate as double) as currency_rate, -- Тільки це ім'я!
        cc as currency_code,
        try(date_parse(exchangedate, '%d.%m.%Y')) as exchange_date,
        cast(parse_datetime(ingested_at, 'yyyy-MM-dd HH:mm:ss') as timestamp) as ingested_at,
        year, month, day
    from {{ source('omnip', 'nbu_rates_raw') }}
)

select * from source_data

{% if is_incremental() %}
  where ingested_at > (select max(ingested_at) from {{ this }})
{% endif %}