from logging import getLogger
logger = getLogger(__name__)

from kettle.celery.app import app as app
from kettle.celery.tasks import add, gatk_test

app.start()
