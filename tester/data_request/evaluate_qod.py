from sklearn.datasets import make_classification
from cloud.orchestrator.build_docker.qod.evaluate import *

X, y = make_classification(n_classes=5, class_sep=2,
weights=[0.2, 0.21, 0.19, 0.25, 0.15], n_informative=3, n_redundant=1, flip_y=0,
n_features=20, n_clusters_per_class=1, n_samples=1000, random_state=10)


# y = np.array([1,2,3,4,3,2,1,2,3,4,4,1,1,2,3,4,5])
print(class_parity(y))
print(feature_relevance(X, y, .9))