{{ config({"severity":"Warn","tags":[]}) }}
{{ dbt_utils.test_accepted_range(column_name="route_distance_km", min_value=0, model=get_where_subquery(ref('int_flight_routes_spine'))) }}