def build_filter_exp_pandas(filters):
    # {
    #     "operator": "enum[and, or, not]",
    #     "constraints":
    #         [
    #             {
    #                 "feature_name": "trans_date_time",
    #                 "from": "2020-06-21 12:14:25",
    #                 "to": "*"
    #             },
    #             {
    #                 "feature_name": "longitude",
    #                 "from": "*",
    #                 "to": "*"
    #             }
    #         ]
    # }
    op = ' ' + filters['operator'] + ' '
    exp = []
    for c in filters['constraints']:
        query = ""
        if c['from'] != "*" and c['from'] is not None:
            query += c['feature_name'] + ' >= ' + repr(c['from'])
        if c['to'] != "*" and c['to'] is not None:
            query = '(' + query + ' and ' + c['feature_name'] + ' <= ' + repr(c['to']) + ')' if len(query) > 0 else \
                c['feature_name'] + ' <= ' + repr(c['to'])
        exp.append(query)
    return op.join(exp) if len(exp) > 1 else exp[0]


def build_sql_command(params):
    pass