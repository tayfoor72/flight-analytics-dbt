{{ config({"severity":"Warn","tags":[],"where":"is_cancelled = false"}) }}
{{ test_not_null(column_name="arrival_delay_minutes", model=get_where_subquery(ref('fct_flights'))) }}