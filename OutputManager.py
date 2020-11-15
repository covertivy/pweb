#!/usr/bin/python3
import Data
import os
from os import path

def print_results(res_dict:dict) -> None:
    pass


def save_results(res_dict:dict, path:str, clean_save:bool) -> None:
    """
    A function that saves the results to the output folder.
    Args:
        res_dict (dict): The dictionary of each script and it's results.
        path (str): The output folder's path.
        clean_save (bool): A flag to indicate if the save is occuring on a clean folder (True) or an existing one (False).
    """
    pass



def logic(data:Data.Data) -> None:
    res_dict = dict()
    for result in data.results: # Create a dictionary with each script as the key and it's result list as the value.
        if result.check_name not in res_dict.keys():
            res_dict[result.check_name] = list(result)
        else:
            res_dict[result.check_name].append(result)
    
    # dict might look like : {'xss':[res, res, res], 'bf': [res], 'sqli': []}
    
    if data.folder is None: # Check if output folder was given.
        print_results(res_dict)
    elif not path.exists(data.folder): # Check if given output folder exists
        print(f"Creating Output Folder ({data.folder})...")
        os.makedirs(data.folder) # Create non existant dir tree.
        save_results(res_dict, data.folder, True)
    else: # Output folder exists.
        print(f"Saving to existing Output Folder ({data.folder})...")
        save_results(res_dict, data.folder, False)