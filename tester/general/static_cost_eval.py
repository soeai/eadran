import json
import random

with open("../../apps/water_leak/scenario_1/qod_logs.json") as f:
    qod = json.load(f)['result'][0]['qod']
    # ucost = [5.99, 4.99, 4.99, 5.49, 5.99, 4.99, 4.99, 4.99]
    print(qod)
    for (i,q) in enumerate(qod):
        print(q['dataset_id'])
        print(q['metric'].values())
        # p = ucost[i]
        print(" -- ", round(sum(q['metric'].values()) * 3 * 0.99,2))
        print("----------")