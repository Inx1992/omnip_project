{% macro repair_raw_table() %}
    {% set rel = source('omnip', 'nbu_rates_raw') %}
    {% set query %}
        MSCK REPAIR TABLE {{ rel.schema }}.{{ rel.identifier }}
    {% endset %}
    
    {% do run_query(query) %}
{% endmacro %}