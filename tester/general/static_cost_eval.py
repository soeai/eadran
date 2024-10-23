import json
import random

with open("../../apps/water_leak/scenario_2/qod_logs.json") as f:
    qod = json.load(f)['result'][0]['qod']
    ucost = [4.99, 5.49, 5.99]
    print(qod)
    for q in qod:
        print(q['dataset_id'])
        print(q['metric'].values())
        p = random.choice(ucost)
        print(p, " -- ", round(sum(q['metric'].values()) * 0.443 * p,2))
        print("----------")