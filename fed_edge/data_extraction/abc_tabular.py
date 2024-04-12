from abc import ABC, abstractmethod


class ABCTabular(ABC):
    def __init__(self, dataset_id, access_info, data_info):
        self.dataset_id = dataset_id
        self.type = access_info['type']
        self.location = access_info['location']
        self.access_key = access_info['access_key']
        self.data_info = data_info

    @abstractmethod
    def extract(self, features, label, filters, sample_limit, qod):
        pass
