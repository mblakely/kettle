#!/usr/bin/env python3
import logging
import os

from celery import Celery


# Set orjson as the json (de)serializer
import orjson
from kombu.serialization import register

logging.basicConfig()

register('orjson', orjson.dumps, orjson.loads,
    content_type='application/json',
    content_encoding='utf-8')

core_user=os.environ['CORE_USER']
core_password=os.environ['CORE_PASSWORD']
core_broker_hport=os.environ['CORE_BROKER_HPORT']
core_result_hport=os.environ['CORE_RESULT_HPORT']
core_ir_addr=os.environ['CORE_IP_ADDR']

# Init and config Celery application
app = Celery('kettle', 
    broker='amqp://{user}:{password}@{ip_addr}:{broker_port}//'.format(ip_addr=core_ir_addr, broker_port=core_broker_hport,user=core_user,password=core_password),
    backend='redis://:{password}@{ip_addr}:{result_port}/0'.format(ip_addr=core_ir_addr, result_port=core_result_hport,password=core_password),
    task_serializer='orjson',
    result_serializer='orjson',
    timezone='US/Central'
)

#if config.profile.celery_extra_kwargs:
    # Set profile-specific celery settings
#    app.conf.update(**config.profile.celery_extra_kwargs)


if __name__ == '__main__':
    app.start()