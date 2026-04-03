{{ config({"severity":"Warn","tags":[]}) }}
{{ test_not_null(column_name="arrival_baggage_claim", model=get_where_subquery(ref('int_flight_routes_spine'))) }}