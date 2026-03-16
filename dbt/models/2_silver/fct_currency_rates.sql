{{
  config(
    materialized='incremental',
    incremental_strategy='insert_overwrite',
    partitioned_by=['year', 'month'],
    format='parquet'
  )
}}

with bronze_data as (
    select * from {{ ref('stg_nbu_rates') }}
),

final as (
    select 
        currency_id,
        currency_name,
        currency_rate,
        currency_code,
        exchange_date,
        ingested_at,
        day,           -- Звичайна колонка (має бути ПЕРЕД партиціями)
        year,          -- Перша колонка партиціонування
        month          -- Друга колонка партиціонування
    from bronze_data

    {% if is_incremental() %}
      -- Беремо дані за останні 3 дні, щоб перестрахуватися від затримок API
      where exchange_date >= (select date_add('day', -3, max(exchange_date)) from {{ this }})
    {% endif %}
)

select * from final