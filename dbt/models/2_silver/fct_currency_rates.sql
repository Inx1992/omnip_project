{{
  config(
    materialized='incremental',
    incremental_strategy='insert_overwrite',
    partitioned_by=['year', 'month', 'day'],
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
        year,
        month,
        day
    from bronze_data

    {% if is_incremental() %}
      /* Логіка: ми беремо дані, які з'явилися ПІСЛЯ останнього запису в Silver.
         Якщо ти хочеш, щоб повторний запуск у той самий день ТАКОЖ оновлював дані,
         використовуй >= (більше або дорівнює).
      */
      where ingested_at >= (select max(ingested_at) from {{ this }})
    {% endif %}
)

select * from final