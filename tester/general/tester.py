import os
import numpy as np
# print(os.path.abspath("../../data_samples"))
size = 27
y = np.random.randint(1, 50,size)
x = np.random.randint(1,50, (size, 10))
print(y)
idx = np.arange(size)
np.random.shuffle(idx)
print(idx)

step = size // 5
start = 0
end = step
repeat = size//step
pred = []
for i in range(repeat):
    if i == repeat-1:
        end = size+1
    print(idx[start:end])
    print(x[idx[start:end]])
    y_fit = np.concatenate([idx[:start], idx[end:]])
    print(y_fit)
    pred.append(x[idx[start:end]])
    start = end
    end += step
print(np.concatenate(pred, axis=0))
