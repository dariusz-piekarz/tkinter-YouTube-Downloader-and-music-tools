from codecs import open
import yaml
import json


class DataTree:
    def __init__(self, variables_dict):
        for node, branch in variables_dict.items():
            if isinstance(branch, dict):
                setattr(self, node, DataTree(branch))
            else:
                setattr(self, node, branch)


class Config(DataTree):
    def __init__(self, path_to_config):
        variable_dict = dict()
        if path_to_config[-4:] == 'yaml':
            variable_dict = yaml.safe_load(open(path_to_config))
        elif path_to_config[-4:] == 'JSON':
            variable_dict = json.load(open(path_to_config))
        super().__init__(variable_dict)
