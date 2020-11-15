#!/usr/bin/python3
import Data

def print_results(res_dict:dict) -> None:


def save_results(res_dict:dict) -> None:


def logic(data:Data.Data) -> None:
    res_dict = dict()
    for result in data.results: # Create a dictionary with each script as the key and it's result list as the value.
        if result.check_name not in res_dict.keys():
            res_dict[result.check_name] = list(result)
        else:
            res_dict[result.check_name].append(result)
    
    if data.folder is None:
        print_results(res_dict)
    else:
        save_results(res_dict)    