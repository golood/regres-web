import os

SECRET_KEY = os.environ.get('SECRET_KEY') if os.environ.get('SECRET_KEY') is not None else 'A0Zr98j/3yX R~'
SECRET_JWT = os.environ.get('SECRET_JWT') if os.environ.get('SECRET_JWT') is not None else 'A0d/3yX R~'

REDIS_HOST = os.environ.get('REDIS_HOST') if os.environ.get('REDIS_HOST') is not None else 'localhost'
REDIS_PORT = os.environ.get("REDIS_PORT") if os.environ.get('REDIS_PORT') is not None else '6379'

URL_WORKER = os.environ.get("URL_WORKER") if os.environ.get('URL_WORKER') is not None else 'http://localhost:5001/'
WORKER_THREAD = os.environ.get("WORKER_THREAD") if os.environ.get('WORKER_THREAD') is not None else '1'
COUNT_PACKAGE = os.environ.get("COUNT_PACKAGE") if os.environ.get('COUNT_PACKAGE') is not None else '500'

UPLOAD_FOLDER = '/tmp'

SPACE = os.environ.get("SPACE") if os.environ.get('SPACE') is not None else 'dev'
