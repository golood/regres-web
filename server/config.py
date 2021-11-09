import os

POSTGRES_DB = os.environ.get('POSTGRES_DB')
POSTGRES_USER = os.environ.get('POSTGRES_USER')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT')

SECRET_KEY = os.environ.get('SECRET_KEY')

REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get("REDIS_PORT")

URL_WORKER = os.environ.get("URL_WORKER")
WORKER_THREAD = os.environ.get("WORKER_THREAD")
COUNT_PACKAGE = os.environ.get("COUNT_PACKAGE")

UPLOAD_FOLDER = '/tmp'

SPACE = os.environ.get("SPACE")

# POSTGRES_DB = 'regres'
# POSTGRES_USER = 'web'
# POSTGRES_PASSWORD = 'web'
# POSTGRES_HOST = 'localhost'
# POSTGRES_PORT = '5432'
#
# SECRET_KEY = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
#
# REDIS_HOST = 'localhost'
# REDIS_PORT = '6379'
#
# URL_WORKER = 'http://localhost:5001/'
#
# WORKER_THREAD = '1'
# COUNT_PACKAGE = '500'
# SPACE = 'dev'
