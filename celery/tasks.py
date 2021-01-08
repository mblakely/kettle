from kettle.celery.app import app
from kettle.celery.oci_lib import oci, gatk_image, gatk_cmd, oci_io_fp, mount_dict

@app.task
def add(x, y):
    return x + y

@app.task
def gatk_test():
    #initialization of environment
    client = oci.from_env()

    #gatk run parameters
    input_file = 'NA12878.chr17_69k_70k.dictFix.bam'
    output_file = 'output.bam'
    cmd = gatk_cmd('PrintReads', input_file=oci_io_fp('static', input_file), output_file=oci_io_fp('tmp', output_file))

    #attached mode
    result=client.containers.run(gatk_image, cmd, volumes=mount_dict, remove=True)
    return result.decode('utf-8')