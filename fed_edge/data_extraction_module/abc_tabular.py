from abc import ABC, abstractmethod


class ABCTabular(ABC):
    def __init__(self, dataset_id, access_info, reader_module):
        self.dataset_id = dataset_id
        self.type = access_info['type']
        self.location = access_info['location']
        self.access_key = access_info['access_key']
        self.reader_module = reader_module

    @abstractmethod
    def extract(self, features, label, filters, sample_limit, qod):
        pass
