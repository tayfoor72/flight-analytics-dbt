{{ config({"severity":"Warn","tags":[]}) }}
{{ dbt_utils.test_accepted_range(column_name="codeshare_rate", max_value=1, min_value=0, model=get_where_subquery(ref('mart_codeshare_complexity'))) }}