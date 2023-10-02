import argparse
import uuid
import pandas as pd
from abc_tabular import ABCTabular
import json
import os
import random as rd

class TabularHandle(ABCTabular):
    def extract(self, features, label, filters, sample_limit, qod, dest_path, method):
        if self.type == 'file':
            # current support csv file
            df = pd.read_csv(self.location)
            # apply filter
            if filters is not None:
                df.query(self.__build_filter_exp(filters), inplace=True)

            features.sort(key=lambda x: x['index'])
            columns = [x['name'] for x in features]
            # add label column
            columns.append(label['name'])
            # get request columns
            df = df[columns]
            row, col = df.shape

            if sample_limit is not None:
                row_limit = sample_limit['number']
                select_method = sample_limit['method']
                if select_method.lower() == 'random' and row_limit < row:
                    idx = rd.choices(range(row), k= row_limit)
                    df = df.iloc[idx]
                    row = row_limit
                else:
                    # not support now
                    pass

            if qod is not None:
                # not support now
                pass

            if method == 'local':
                file_name = str(uuid.uuid4()) + '.csv'
                full_path = os.path.join(dest_path, file_name)
                df.to_csv(full_path, index=False)
            elif method == 's3':
                pass
            return json.dumps(self.__build_response(full_path, row, col, method))
        elif self.type == 'database':
            # not support now
            pass
        elif self.type == 'cloud':
            # not support now
            pass

    def __build_filter_exp(self, filters):
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

    def __build_response(self, filename_url, row, col, method ):
        # {
        #     "dataset_id": "uuid of dataset",
        #     "data_summary": {
        #         "columns": 10,
        #         "rows": 1247
        #     },
        #     "qod": {
        #         "__schema": "http://fed.marketplace.com/qod/schema/v1",
        #         "metric": {
        #             "class_parity": 0.8,
        #             "feature_correlation": 0.94,
        #             "feature_relevance": 0.97,
        #             "completeness": 1
        #         }
        #     },
        #     "download_info": {
        #         "method": "wget|s3|minio|local",
        #         "url": "url for download (i.e., https://s3.xyz.com?uuid=abc;encrypt_token=xyz)",
        #         "data_name": "file name or object name",
        #         "format": "enum[tuple, last] (tuple: features and label are separated as (features, label), last: label is the last column)",
        #         "params": {
        #             "__comment": "optional parameters for download, depend on methods"
        #         }
        #     }
        # }
        res = {
                  "dataset_id": self.dataset_id,
                  "data_summary": {
                    "columns": col,
                    "rows": row
                  },
                  "qod": {
                    "__schema": "http://fed.marketplace.com/qod/schema/v1",
                    "metric": {
                      "class_parity": -1,
                      "feature_correlation": -1,
                      "feature_relevance": -1,
                      "completeness": -1
                    }
                  },
                  "download_info": {
                    "method": method,
                    "url": filename_url,
                    "data_name": "No specify",
                    "format": "last",
                    "params": {
                      "__comment": "No optional parameters"
                    }
                  }
                }
        return res


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple Data Extraction for CSV file')
    parser.add_argument('--request', type=str)
    parser.add_argument('--conf', type=str, default='conf/config.json')
    args = parser.parse_args()

    with open(args.conf) as f_conf:
        conf = json.load(f_conf)['data']
        with open(args.request) as f_req:
            req = json.load(f_req)
            if conf['owner_id'] == req['owner_id'] and conf['dataset_id'] == req['dataset_id']:
                access_info = req['access_info']
                features = req['features']
                label = req['label']
                filters = req['filters'] if 'filters' in req.keys() else None
                qod = req['qod'] if 'qod' in req.keys() else None
                sample = req['sample_limit'] if 'sample_limit' in req.keys() else None
                response_json = TabularHandle(req['dataset_id'],access_info).extract(features,
                                                                                     label,
                                                                                     filters,
                                                                                     sample,
                                                                                     qod,
                                                                                     dest_path=conf['dest_path'],
                                                                                     method=conf['method'])
                print(response_json)
            else:
                raise Exception('Opp! Request is not for me!!!!')
