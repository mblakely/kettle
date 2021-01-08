import argparse
import os
import sys
from time import sleep
from kettle.celery.app import app
from kettle.celery.tasks import add, gatk_test
from kettle.celery.utils import wait_for_workers
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

num_workers=os.environ['DRIVER_MIN_NUM_WORKERS']

# Wait for workers
if not wait_for_workers(app, count=int(num_workers), timeout=60):
    logger.error('Cannot find available workers. Exiting...')
    sys.exit(1)

logger.debug('{} workers found'.format(num_workers))

# Send task
logger.info('Sending task to confirm 1 + 1 == 2')
add1s = add.apply_async((1, 1))
logger.info('Waiting for response...\n\n')

result = add1s.get(timeout=10)
correct = (result == add(1,1))

if correct:
    logger.info('addition is correct!')
else:
    logger.error(f'Received different response: `{result}`')




# Send task
logger.info('Sending gatk task to confirm gatk setup')
gatk_hello_world = gatk_test.apply_async()
logger.info('Waiting for response...\n\n')
result = gatk_hello_world.get(timeout=10)
correct = isinstance(result, str)
logger.info('gatk output: {}'.format(result))
if correct:
    logger.info('gatk output is correct!')
else:
    logger.error(f'Received different response: `{result}`')

logger.info('Finished!')
