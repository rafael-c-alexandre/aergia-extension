import random
import logging
from torch.utils.data import DistributedSampler, Dataset, ConcatDataset
from typing import Iterator
import numpy as np


class DistributedSamplerWrapper(DistributedSampler):
    indices = []
    epoch_size = 1.0
    def __init__(self, dataset: Dataset, num_replicas = None,
                 rank = None, seed = 0) -> None:
        super().__init__(dataset, num_replicas=num_replicas, rank=rank)

        self.client_id = max(0,rank - 1)
        self.n_clients = num_replicas - 1
        if hasattr(dataset, 'classes'):
            self.n_labels = len(dataset.classes)
        else:
            if isinstance(dataset, ConcatDataset) and hasattr(dataset.datasets[0], 'classes'):
                self.n_labels = len(dataset.datasets[0].classes)
            else:
                self.n_labels = 0
        self.seed = seed


    def order_by_label(self, dataset):
        # order the indices by label
        ordered_by_label = [[] for i in range(self.n_labels)]
        
        if isinstance(dataset, ConcatDataset) and hasattr(dataset.datasets[0], 'classes'):
            dataset_list = dataset.datasets
            concat_targets = []
            for ds in dataset_list:
                concat_targets.extend(ds.targets)
            for index, target in enumerate(concat_targets):
                ordered_by_label[target].append(index)
        
        else:
            for index, target in enumerate(dataset.targets):
                ordered_by_label[target].append(index)

        return ordered_by_label

    def set_epoch_size(self, epoch_size: float) -> None:
        """ Sets the epoch size as relative to the local amount of data.
        1.5 will result in the __iter__ function returning the available
        indices with half appearing twice.

        Args:
            epoch_size (float): relative size of epoch
        """
        self.epoch_size = epoch_size

    def __iter__(self) -> Iterator[int]:
        random.seed(self.rank+self.epoch)
        epochs_todo = self.epoch_size
        indices = []
        while(epochs_todo > 0.0):
            random.shuffle(self.indices)
            if epochs_todo >= 1.0:
                indices.extend(self.indices)
            else:
                end_index = int(round(len(self.indices)*epochs_todo))
                indices.extend(self.indices[:end_index])

            epochs_todo = epochs_todo - 1

        ratio = len(indices)/float(len(self.indices))
        np.testing.assert_almost_equal(ratio, self.epoch_size, decimal=2)

        return iter(indices)

    def __len__(self) -> int:
        return len(self.indices)