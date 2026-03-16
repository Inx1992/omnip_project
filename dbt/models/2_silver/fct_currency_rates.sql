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

deduplicated as (
    select * from (
        select 
            *,
            row_number() over (
                partition by exchange_date, currency_code 
                order by ingested_at desc
            ) as rn
        from bronze_data
    )
    where rn = 1
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
    from deduplicated

    {% if is_incremental() %}
      where exchange_date >= (select date_add('day', -3, max(exchange_date)) from {{ this }})
    {% endif %}
)

select * from final