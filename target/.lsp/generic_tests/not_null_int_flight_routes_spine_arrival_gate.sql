{{ config({"severity":"Warn","tags":[]}) }}
{{ test_not_null(column_name="arrival_gate", model=get_where_subquery(ref('int_flight_routes_spine'))) }}