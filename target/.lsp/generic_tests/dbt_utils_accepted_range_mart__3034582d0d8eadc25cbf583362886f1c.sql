{{ config({"severity":"Warn","tags":[]}) }}
{{ dbt_utils.test_accepted_range(column_name="cancellation_rate", max_value=1, min_value=0, model=get_where_subquery(ref('mart_route_performance'))) }}