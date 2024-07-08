# import os
# import numpy as np
# # print(os.path.abspath("../../data_samples"))
# size = 27
# y = np.random.randint(1, 50,size)
# x = np.random.randint(1,50, (size, 10))
# print(y)
# idx = np.arange(size)
# np.random.shuffle(idx)
# print(idx)
#
# step = size // 5
# start = 0
# end = step
# repeat = size//step
# pred = []
# for i in range(repeat):
#     if i == repeat-1:
#         end = size+1
#     print(idx[start:end])
#     print(x[idx[start:end]])
#     y_fit = np.concatenate([idx[:start], idx[end:]])
#     print(y_fit)
#     pred.append(x[idx[start:end]])
#     start = end
#     end += step
# print(np.concatenate(pred, axis=0))

# import docker
# dockerClient = docker.DockerClient()
# containers = dockerClient.containers.list(all=True)
# for container in containers:
#     status = container.stats(decode=None, stream = False)
#     print(status)
import subprocess
import json
res = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{ json . }}"], capture_output=True)
if res.returncode ==0:
    for line in res.stdout.decode("utf-8").split("\n"):
        if len(line) > 0:
            stats = json.loads(line)
            print(stats['MemPerc'])
            print(stats['MemUsage'])
            print(stats['CPUPerc'])
            print(stats['Name'])
            print('------------')