{{ config({"tags":[],"where":"flight_status_clean = 'landed'"}) }}
{{ test_not_null(column_name="actual_arrival_time_utc", model=get_where_subquery(ref('int_flight_routes_metrics'))) }}