{{ config({"severity":"Warn","tags":[]}) }}
{{ dbt_utils.test_accepted_range(column_name="total_movements", min_value=0, model=get_where_subquery(ref('mart_airport_operations'))) }}