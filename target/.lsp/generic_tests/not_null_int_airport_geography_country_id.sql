{{ config({"severity":"Warn","tags":[]}) }}
{{ test_not_null(column_name="country_id", model=get_where_subquery(ref('int_airport_geography'))) }}