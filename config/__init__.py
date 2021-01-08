import os
import yaml
from pathlib import PurePath

def load_config_dict(path):
    config_dict={}

    for dirpath, dirnames, filenames in os.walk(path):
        if should_skip_dir(dirpath):
            continue

        rel_config_dict = match_config_dict_depth(config_dict, path, dirpath)
        for dirname in dirnames:
            if should_skip_dir(dirname):
                continue
            rel_config_dict[dirname]={}
        
        add_configs(rel_config_dict, filenames, dirpath)
    
    return config_dict   

def should_skip_dir(path):
    should_skip = False
    skip_list = ['__pycache__']
    
    for skip_dir in skip_list:
        if skip_dir in path:
            should_skip = True
            break
    
    return should_skip


#loads each file in the filenames list and adds it to the config dictionary
def add_configs(config_dict, filenames, dirpath):
    for filename in (fname for fname in filenames if ('.yml' in fname) or ('.yaml' in fname)):
        root, ext = os.path.splitext(filename)
        config_dict[root]=load_yaml_file(os.path.join(dirpath, filename))


#given a configuration dictionary and a dirpath which is being processed by walk,
#returns a config dictionary shifted to the same level as the directory being processed
def match_config_dict_depth(config_dict, path, dirpath):
    relative_config_dict = config_dict
    path_extension = parse_path_extension(path, dirpath)
    
    #shifts the relatitive dictionary deeper based on the current directory level
    for dirname in path_extension:
        relative_config_dict = relative_config_dict[dirname]
    
    return relative_config_dict

#comapres a path and an extension of that path to determine which directories are extended from the root path
#returns an ordered list of the extended directory names
def parse_path_extension(root_path, extension_path):
    root_depth = len(PurePath(root_path).parts)
    extension_parts = PurePath(extension_path).parts
    #returns a slice of the extension parts with the root portion removed
    return extension_parts[root_depth:]

#loads yaml file into python object
def load_yaml_file(filename):
    with open(filename, 'r') as stream:
        #could thorw yaml errors for poorly formatted files, but these files are required
        yaml_info = yaml.safe_load(stream)
    return yaml_info
        
#if __name__ == '__main__':
#    print(load_config_dict('./config'))