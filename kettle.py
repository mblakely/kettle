import os
import yaml
from config import load_config_dict
import subprocess
import argparse
import docker

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


docker_cmd_list = ['up', 'down', 'build']
job_type_list = ['core', 'worker', 'driver']

job_options={job: [job] for job in job_type_list}
job_options['all']=job_type_list
job_options['backend']=['core', 'worker']
job_options['frontend']=['core', 'driver']

config_dir = './config'
docker_dir = './docker'
docker_env_file = os.path.join(docker_dir, '.env')

def parse_args(node_list):    
    parser = argparse.ArgumentParser()
    parser.add_argument('job', choices=job_options.keys(), help='the type of job to run')
    parser.add_argument('cmd', choices=docker_cmd_list, help='the docker command to run')
    parser.add_argument('--hostname', required=False, choices={node.name for node in node_list},  help='node to run the commands on')
    return parser.parse_args()



def main():
    logger.info('loading config information')
    config_dict = load_config_dict(config_dir)
    node_list = parse_nodes(config_dict)

    lead_node = [node for node in node_list if node.rank == 'lead'].pop()
    follower_nodes = [node for node in node_list if node.rank != 'lead']
    node_dict = {node.name: node for node in node_list}

    args = parse_args(node_list)
    logger.info(f'running with docker command: {args.cmd} job type: {args.job} hostname: {args.hostname}')

    logger.info('setting docker environments')
    env_dict = parse_docker_env(config_dict, node_list, lead_node)
    write_docker_env(env_dict)

    for node in node_list:
        node.run_docker_cmds(args.cmd, args.job)





def parse_docker_env(config_dict, node_list, lead_node):
    env_dict = {}
    
    merge_env_variables(config_dict['core'], env_dict)
    merge_env_variables(config_dict['driver'], env_dict)

    env_dict['DRIVER_MIN_NUM_WORKERS'] = sum([node.required_workers for node in node_list])
    env_dict['CORE_IP_ADDR'] = lead_node.ip_addr
    env_dict['KETTLE_ROOT_DIR'] = config_dict['kettle']['KETTLE_ROOT_DIR']
    env_dict['KETTLE_MOUNT_ROOT'] = config_dict['kettle']['KETTLE_MOUNT_ROOT']

    env_dict['CORE_TMP_MOUNT'] = os.path.join(config_dict['kettle']['KETTLE_MOUNT_ROOT'], config_dict['core']['CORE_TMP_MOUNT'])

    return env_dict

def write_docker_env(env_dict):
    with open(docker_env_file, 'w') as f:
        env_line='{}={}\n'
        for key, value in env_dict.items():
            f.write(env_line.format(key, value))
    


def parse_nodes(config_dict):
    nodes = config_dict['nodes']
    kettle = config_dict['kettle']

    node_list = list()
    lead_node = config_dict['kettle']['lead_node']

    for node_dict in kettle['nodes']:
        node_name, ip_addr = node_dict.popitem()
        job = nodes[node_name]['job']
        k_node = kettle_node(ip_addr, node_name, job)

        if node_name == lead_node:
            k_node.rank = 'lead'

        for queue_dict in nodes[node_name]['worker_queue']:
            k_node.add_queue(*queue_dict.popitem())


        node_list.append(k_node)
    return node_list

def merge_env_variables(config_dict, env_dict):
    env_dict.update(config_dict)



def create_compose_cmd_str(cmd, job):
    compose_yml_dict = {
        'core': 'docker-compose-core.yml',
        'worker': 'docker-compose-worker.yml',
        'driver': 'docker-compose-driver.yml'
    }

    compose_cmd_dict = {
        'up': 'up --force-recreate -d',
        'build': 'build',
        'down': 'down'
    }

    compose_cmd = compose_cmd_dict[cmd]
    compose_yml_file = compose_yml_dict[job]
    
    #return f'docker-compose -f {compose_yml_file} --env {docker_env_file} {compose_cmd}'
    return f'docker-compose -f {compose_yml_file} {compose_cmd}'



class kettle_node():
    def __init__(self, ip_addr, name, job):
        self.ip_addr = ip_addr
        self.name = name
        self.job = job
        self.job_list = job_options[job]
        self.queue_list = list()
        self.rank = 'worker'
        self.oci = docker.from_env()
        
        self.docker_cmds ={}
        for cmd in docker_cmd_list:
            self.docker_cmds[cmd]={}
        self.set_docker_cmds()

    def set_docker_cmds(self):
        for job in self.job_list:
            for cmd in self.docker_cmds.keys():
                if job not in  self.docker_cmds[cmd]:
                    self.docker_cmds[cmd][job]=list()

                self.docker_cmds[cmd][job].append(create_compose_cmd_str(cmd, job))
    
    def run_docker_cmds(self, cmd, selected_job):
        job_list = list(set(self.job_list).intersection(job_options[selected_job]))
        logger.info(f'running command: {cmd} for job: {str(job_list)} ')
        for job in job_list:    
            for docker_cmds in self.docker_cmds[cmd][job]:
                logger.debug(f'running docker command: {docker_cmds}')
                subprocess.run(docker_cmds, shell=True, check=False, cwd=docker_dir)
    
    def add_queue(self, queue, num_workers):
        self.queue_list.append((queue, num_workers))
    
    @property
    def required_workers(self):
        return sum([num_worker for _, num_worker in self.queue_list])
    
    def __repr__(self):
        return 'kettle_node(' + self.__str__()+')'

    def __str__(self):
        return 'name: {}, ip_addr {}, job: {}'.format(self.name, self.ip_addr, self.job)




if __name__ == '__main__':
    main()
    