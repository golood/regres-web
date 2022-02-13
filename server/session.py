
import json
from datetime import datetime, date, timedelta

import jwt
import redis

from server.config import SECRET_JWT, REDIS_HOST, REDIS_PORT
from server.models import MetaData, BiasEstimate


class Token:
    """
    Токен для идентификации сессий пользователей.
    """

    body: str
    create_time: datetime

    def __init__(self, token: str = None):
        if token is None:
            self.create_time = datetime.now()
            self.body = jwt.encode(payload={'create_time': str(self.create_time)}, key=SECRET_JWT, algorithm="HS512")
        else:
            data = Token.decode(token)
            self.body = token
            self.create_time = datetime.fromisoformat(data['create_time'])

    @staticmethod
    def decode(token: str):
        return jwt.decode(jwt=token, key=SECRET_JWT, algorithms="HS512")

    def __str__(self):
        return self.body


class Session:
    """
    Кастомная сессия пользователя.
    """

    token: Token
    _meta_data: MetaData
    _bias: BiasEstimate

    def __init__(self, token: Token = None):
        if token is None:
            self.create_token()
        else:
            self.token = token

        self._meta_data = None
        self._result = None
        self._bias = None

    @property
    def meta_data(self) -> MetaData:
        r = Session._get_redis()
        _data = r.get(f'{self.token.body}_metaData')
        if _data != "" and _data is not None and 'meta_data' in json.loads(_data):
            self._meta_data = MetaData(json.loads(_data)['meta_data'])
        else:
            self._meta_data = MetaData()

        return self._meta_data

    @meta_data.setter
    def meta_data(self, new_meta_data: MetaData):
        self._meta_data = new_meta_data

        self.save_meta_data()

    @property
    def bias(self):
        r = Session._get_redis()
        _data = r.get(f'{self.token.body}_bias')
        if _data != "" and _data is not None and 'bias' in json.loads(_data):
            self._bias = BiasEstimate(json.loads(_data)['bias'])
        else:
            self._bias = BiasEstimate()

        return self._bias

    @bias.setter
    def bias(self, new_bias: BiasEstimate):
        self._bias = new_bias

        self.save_bias()

    @staticmethod
    def get_session(_token: str):
        try:
            token = Token(_token)

            r = Session._get_redis()
            data = r.get(token.body)
            if data is None:
                r.close()
                return Session()
            r.close()
            return Session(token)

        except jwt.exceptions.InvalidSignatureError:
            return Session()

    @staticmethod
    def _get_redis() -> redis.Redis:
        return redis.Redis(decode_responses=True, host=REDIS_HOST, port=REDIS_PORT)

    class DataEncoder(json.JSONEncoder):
        """
        Класс кодирует модель Session в JSON формат.
        """
        def default(self, obj):
            if isinstance(obj, Session):
                return obj.__dict__
            return json.JSONEncoder.default(self, obj)

    def save_meta_data(self):
        r = Session._get_redis()
        r.set(f'{self.token.body}_metaData', f'{{"meta_data":{json.dumps(self._meta_data, cls=MetaData.DataEncoder)}}}')
        r.expireat(
            f'{self.token.body}_metaData',
            datetime.fromisoformat(f'{date.today() + timedelta(days=1)} 04:00:00'))
        r.close()

    def save_bias(self):
        r = Session._get_redis()
        r.set(f'{self.token.body}_bias', f'{{"bias":{json.dumps(self._bias, cls=BiasEstimate.DataEncoder)}}}')
        r.expireat(
            f'{self.token.body}_bias',
            datetime.fromisoformat(f'{date.today() + timedelta(days=1)} 04:00:00'))
        r.close()

    def get_percent(self):
        r = Session._get_redis()
        return r.get(f'{self.token.body}_percent')

    def create_token(self):
        self.token = Token()
        r = Session._get_redis()
        r.set(
            self.token.body, "")
        r.expireat(
            self.token.body,
            datetime.fromisoformat(f'{date.today() + timedelta(days=1)} 04:00:00'))
        r.close()
