import os

postgres_db = os.environ.get('POSTGRES_DB')
postgres_user = os.environ.get('POSTGRES_USER')
postgres_password = os.environ.get('POSTGRES_PASSWORD')
postgres_host = os.environ.get('POSTGRES_HOST')

secret_key = os.environ.get('SECRET_KEY')

redis_host = os.environ.get('REDIS_HOST')
redis_port = os.environ.get("REDIS_PORT")

url_worker = os.environ.get("URL_WORKER")
worker_thread = os.environ.get("WORKER_THREAD")
count_package = os.environ.get("COUNT_PACKAGE")

UPLOAD_FOLDER = '/tmp'

# postgres_db = 'regres'
# postgres_user = 'web'
# postgres_password = 'web'
# postgres_host = 'localhost'
# postgres_port = '5432'
#
# secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
#
# redis_host = 'localhost'
# redis_port = '6379'
#
# url_worker = 'http://localhost:5001/api'
#
# worker_thread = '1'
# count_package = '500'
