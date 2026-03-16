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

-- 1. Створюємо блок для видалення дублікатів
deduplicated as (
    select * from (
        select 
            *,
            -- Нумеруємо записи для кожної валюти в межах одного дня
            row_number() over (
                partition by exchange_date, currency_code 
                order by ingested_at desc -- Пріоритет найсвіжішому запису
            ) as rn
        from bronze_data
    )
    where rn = 1 -- Залишаємо тільки по одному унікальному запису
),

final as (
    select 
        currency_id,
        currency_name,
        currency_rate,
        currency_code,
        exchange_date,
        ingested_at,
        day,           
        year,          
        month          
    from deduplicated -- Важливо: тепер беремо дані з deduplicated, а не з bronze_data

    {% if is_incremental() %}
      -- Беремо дані за останні 3 дні, щоб перестрахуватися від затримок API
      where exchange_date >= (select date_add('day', -3, max(exchange_date)) from {{ this }})
    {% endif %}
)

select * from final