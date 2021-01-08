import os
import subprocess

from datetime import datetime
from time import sleep


from logging import getLogger, DEBUG
logger = getLogger(__name__)
logger.setLevel(DEBUG)

LINE_SEP = 50 * '='

def run_command(cmd, **kwargs):
    logger.debug(f'Running command: `{cmd}`...')
    logger.debug(LINE_SEP)

    cp = None
    try:
        cp = subprocess.run(cmd, shell=True, **kwargs)
        if cp.returncode != 0:
            logger.warn(f'Non-zero code [{cp.returncode}] for command `{cmd}`')

    except Exception as err:
        logger.error(err)
        logger.error(f'Error while running command `{cmd}`')

    return cp


def get_cmd_output(cmd):
    cp = None
    out = None
    try:
        cp = subprocess.run(cmd, capture_output=True, shell=True, text=True)
        if cp.returncode != 0:
            logger.warn(f'Non-zero code [{cp.returncode}] for command `{cmd}`')
            subprocess.check_output(cmd, stderr = subprocess.STDOUT, shell = True)
        
        out = cp.stdout
    except Exception as err:
        logger.error(err)
        logger.error(f'Error while running command `{cmd}`')
    return out


def wait_for_workers(app, count=1, timeout=360):
    """ Blocks until either at least a number of available workers has been
        reached or a certain time amount has passed
    """
    i = app.control.inspect(timeout=1)
    start = datetime.now()

    logger.info(f'Waiting for Celery {count} workers....')
    while (datetime.now() - start).total_seconds() < timeout:
        try:
            worker_stats = i.stats()
            if worker_stats and len(worker_stats) >= count:
                # TODO: Check that indeed these workers are up and runing!
                app.control.broadcast('ping', reply=True, timeout=1)

                logger.info(f'Found {len(worker_stats)} available workers! :)')
                return True
        except Exception as err:
            logger.warn(f'Error while waiting for workers: {repr(err)}')

        finally:
            sleep(1)

    logger.warn(f'Cannot find {count} available worker(s) after {timeout} secs.'
                f' Check that workers have been launched properly.. :/')
    return False

