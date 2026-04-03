{{ config({"severity":"Warn","tags":[]}) }}
{{ dbt_utils.test_accepted_range(column_name="total_routes_served", min_value=1, model=get_where_subquery(ref('mart_airline_performance'))) }}