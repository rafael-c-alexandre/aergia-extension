import copy
from dataclasses import dataclass, Field
from enum import Enum, EnumMeta
from pathlib import Path, PosixPath
from typing import Type
import pathlib
import torch
import yaml
from fltk.util.log import getLogger

from fltk.util.definitions import Dataset, Nets, DataSampler, Optimizations, LogLevel, Aggregations, Algorithm


@dataclass
class Config:
    # optimizer: Optimizations
    batch_size: int = 16
    test_batch_size: int = 1000
    rounds: int = 2
    epochs: int = 1
    lr: float = 0.001
    momentum: float = 0.1
    cuda: bool = False
    shuffle: bool = False
    use_profiler: bool = True
    log_interval: int = 50
    scheduler_step_size: int = 50
    scheduler_gamma: float = 0.5
    min_lr: float = 1e-10

    # @TODO: Set seed from configuration
    rng_seed = 0
    # Enum
    optimizer: Optimizations = Optimizations.adam
    optimizer_args = {
        'lr': lr,
        #'momentum': momentum
    }
    loss_function = torch.nn.CrossEntropyLoss
    # Enum
    log_level: LogLevel = LogLevel.DEBUG

    num_clients: int = 10
    clients_per_round: int = 2
    distributed: bool = True
    single_machine: bool = False
    # Enum
    aggregation: Aggregations = Aggregations.fedavg
    # Enum
    dataset_name: Dataset = Dataset.mnist
    # Enum
    net_name: Nets = Nets.mnist_cnn
    default_model_folder_path: str = "default_models"
    data_path: str = "data"
    # Enum
    data_sampler: DataSampler = DataSampler.uniform
    data_sampler_args = []

    rank: int = 0
    world_size: int = 0

    replication_id: int = None
    experiment_prefix: str = ''

    real_time : bool = False

    # Save data in append mode. Thereby flushing on every append to file.
    # This could be useful when a system is likely to crash midway an experiment
    save_data_append: bool = True
    output_path: Path = Path('output_test_2')

    algorithm_name: Algorithm = Algorithm.vanilla

    ## Algorithm specific parameters:
    # All parameters specific to an algorithm are prefixed with the name of the algorithm
    # TiFL specific configuration
    tifl_I: int = None # cycle when to update the tier probabilities
    tifl_n_tiers: int = 2 # Number of tiers used by the TiFL algorithm

    # Parameters for deadline based algorithms such as Deadline and Offloading
    deadline_time: float = 0

    # Parameters for the Offloading based algorithms
    # Choices:
    # 0 Aggregate offloaded models using FedAvg
    # 1 Aggregate offloaded models using glue method
    # 2 Aggregate offloaded models using Part FedAvg and glue method
    offloading_option: int = 0
    # Using a factor of 0 only matches on performance, not on data similarity
    offloading_similarity_factor: float = 1
    
    # Percentage of clients that will be shown in stats for best and worst
    fairness_percentage = 0.2


    def __init__(self, **kwargs) -> None:
        enum_fields = [x for x in self.__dataclass_fields__.items() if isinstance(x[1].type, Enum) or isinstance(x[1].type, EnumMeta)]
        if 'dataset' in kwargs and 'dataset_name' not in kwargs:
            kwargs['dataset_name'] = kwargs['dataset']
        if 'net' in kwargs and 'net_name' not in kwargs:
            kwargs['net_name'] = kwargs['net']
        for name, field in enum_fields:
            if name in kwargs and isinstance(kwargs[name], str):
                kwargs[name] = field.type(kwargs[name])
        for name, value in kwargs.items():
            self.__setattr__(name, value)
            if name == 'output_location':
                self.output_path = Path(value)
        self.update_rng_seed()


    def update_rng_seed(self):
        torch.manual_seed(self.rng_seed)
    def get_default_model_folder_path(self):
        return self.default_model_folder_path

    def get_distributed(self):
        return self.distributed

    def get_sampler(self):
        return self.data_sampler

    def get_world_size(self):
        return self.world_size

    def get_rank(self):
        return self.rank

    def get_sampler_args(self):
        return tuple(self.data_sampler_args)

    def get_data_path(self):
        return self.data_path

    def get_loss_function(self):
        return self.loss_function

    @classmethod
    def FromYamlFile(cls, path: Path, loglevel = LogLevel.DEBUG):
        getLogger(__name__, loglevel).debug(f'Loading yaml from {path.absolute()}')
        with open(path) as file:
            content = yaml.safe_load(file)
            for k, v in content.items():
                getLogger(__name__, loglevel).debug(f'Inserting key "{k}" into config')
            return cls(**content)

    @classmethod
    def ToYamlFile(cls, config, path: Path):
        getLogger(__name__, config.log_level).debug(f'Saving config to {path.absolute()}')
        with open(path, mode='w+') as file:
            dict_data = copy.deepcopy(config.__dict__)
            enum_fields = [x for x in config.__dataclass_fields__.items() if
                           isinstance(x[1].type, Enum) or isinstance(x[1].type, EnumMeta)]
            for name, field in enum_fields:
                dict_data[name] = config.__getattribute__(name).value
            path_fields = [x for x in config.__dataclass_fields__.keys() if isinstance(config.__getattribute__(x), Path)]
            for path_field in path_fields:
                dict_data[path_field] = str(config.__getattribute__(path_field))
            yaml.dump(dict_data, file)
