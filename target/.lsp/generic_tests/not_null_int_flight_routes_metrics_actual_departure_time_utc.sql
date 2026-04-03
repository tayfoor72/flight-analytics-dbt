{{ config({"tags":[],"where":"is_cancelled = false"}) }}
{{ test_not_null(column_name="actual_departure_time_utc", model=get_where_subquery(ref('int_flight_routes_metrics'))) }}