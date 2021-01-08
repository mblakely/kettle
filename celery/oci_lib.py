import docker as oci
import os


#linux_working_dir = r'\\wsl$\Ubuntu-20.04\home\ubuntu\ioGenetics'
linux_working_dir = os.environ['KETTLE_MOUNT_ROOT']
gatk_image = 'broadinstitute/gatk:latest'

io_map = {
    'static': '/mnt/io_static',
    'tmp': '/mnt/io_tmp',
    'persist': '/mnt/io_persist'
}

mount_dict = {
    os.path.join(linux_working_dir,'mounts','io_static'): {'bind': io_map['static'], 'mode':'ro'},
    os.path.join(linux_working_dir,'mounts','io_tmp'): {'bind': io_map['tmp'], 'mode':'rw'},
    os.path.join(linux_working_dir,'mounts','io_persist'): {'bind': io_map['persist'], 'mode':'rw'},

}

def gatk_cmd(tool, **kwargs):
    cmd_map = {
        'PrintReads': './gatk PrintReads -I {input_file} -O {output_file}'
    }
    return cmd_map[tool].format(**kwargs)

def oci_io_fp(root, file_name):
    return io_map[root]+'/'+file_name

def cleanup(client):
    print(client.containers.prune())