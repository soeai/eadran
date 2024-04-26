import argparse
import uuid
import pandas as pd
from abc_tabular import ABCTabular
from utils import build_filter_exp_pandas
import json
import os
import random as rd


class TabularHandle(ABCTabular):
    def extract(self, _features, _label, _filters, _sample_limit, _qod):
        dest_path = self.data_info['dest_path']
        method = self.data_info['method']
        if self.type == 'file':
            # current support csv file
            df = pd.read_csv(self.location)
            # apply filter
            if _filters is not None:
                df.query(build_filter_exp_pandas(_filters), inplace=True)

            _features.sort(key=lambda x: x['index'])
            columns = [x['name'] for x in _features]
            # add label column
            columns.append(_label['name'])
            # get request columns
            df = df[columns]
            row, col = df.shape

            if _sample_limit is not None:
                row_limit = _sample_limit['number']
                select_method = _sample_limit['method']
                if select_method.lower() == 'random' and row_limit < row:
                    idx = rd.choices(range(row), k=row_limit)
                    df = df.iloc[idx]
                    row = row_limit
                else:
                    # not support now
                    pass

            if _qod is not None:
                # not support now
                pass

            if method == 'local':
                file_name = str(uuid.uuid4()) + '.csv'
                full_path = os.path.join(dest_path, file_name)
                # print(full_path)
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

    def __build_response(self, filename_url, row, col, method):
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
        #         "format": "enum[tuple, last]",
        #         "params": "optional object parameters for download, depend on methods",
        #         "module_conf": {
        #             "url": "url to download from storage service",
        #             "module_name": "data_reader",
        #             "function_map": "read_data"
        #       }
        #     }
        # }
        reader_conf = self.data_info['reader_conf']
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
            "data": {
                "method": method,
                "location": filename_url,
                "format": "last",
                "params": "",
                "module_conf": reader_conf
            }
        }
        return res


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple Data Extraction for CSV file')
    parser.add_argument('--request', type=str)
    parser.add_argument('--conf', type=str, default='../conf/config.json')
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
                response_json = TabularHandle(req['dataset_id'], access_info, conf['data']).extract(features,
                                                                                                    label,
                                                                                                    filters,
                                                                                                    sample,
                                                                                                    qod)
                print(response_json)
            else:
                raise Exception('Opp! Request is not for me!!!!')
