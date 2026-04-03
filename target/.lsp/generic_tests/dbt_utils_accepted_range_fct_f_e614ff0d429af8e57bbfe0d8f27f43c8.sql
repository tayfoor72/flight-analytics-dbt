{{ config({"severity":"Warn","tags":[]}) }}
{{ dbt_utils.test_accepted_range(column_name="arrival_delay_minutes", max_value=1440, min_value=-120, model=get_where_subquery(ref('fct_flights'))) }}