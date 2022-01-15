#!/usr/bin/python3
import enum
import json

from server.db import MatrixRepo, LoadFilesRepo, UserSessionRepo
from server.logger import logger

log = logger.get_logger('server')


class MenuTypes(enum.Enum):
    MAIN = 'MAIN'
    LOAD = 'LOAD'
    DATA = 'DATA'
    DIV = 'DIV'
    ANSWER = 'ANSWER'
    BIAS = 'BIAS'


class MethodDivMatrixType(enum.Enum):
    HAND = 'hand'
    MNK = 'mnk'
    MNM = 'mnm'
    MAO = 'mao'
    NONE = None


class CalculationMode(str, enum.Enum):
    PREDICT = 'PREDICT'  # прогнозирование
    STANDARD = 'STANDARD'


class MetaData:
    """
    Класс для хранения мета данных пользователя.
    Используется для представления данных в барузере.
    """

    # method_div_matrix_type: MethodDivMatrixType

    menu_active_main: bool
    menu_active_load: bool
    menu_active_data: bool
    menu_active_div: bool
    menu_active_answer: bool
    menu_active_bias: bool

    menu_lock_load: bool
    menu_lock_data: bool
    menu_lock_div: bool
    menu_lock_answer: bool
    menu_lock_bias: bool

    mode: CalculationMode

    range_value: int

    def __init__(self, data):
        if data is not None:
            self.menu_active_main = MetaData.get_value_bool(data, 'menu_active_main')
            self.menu_active_load = MetaData.get_value_bool(data, 'menu_active_load')
            self.menu_active_data = MetaData.get_value_bool(data, 'menu_active_data')
            self.menu_active_div = MetaData.get_value_bool(data, 'menu_active_div')
            self.menu_active_answer = MetaData.get_value_bool(data, 'menu_active_answer')
            self.menu_active_bias = MetaData.get_value_bool(data, 'menu_active_bias')

            self.menu_lock_load = MetaData.get_value_bool(data, 'menu_lock_load')
            self.menu_lock_data = MetaData.get_value_bool(data, 'menu_lock_data')
            self.menu_lock_div = MetaData.get_value_bool(data, 'menu_lock_div')
            self.menu_lock_answer = MetaData.get_value_bool(data, 'menu_lock_answer')
            self.menu_lock_bias = MetaData.get_value_bool(data, 'menu_lock_bias')

            self.mode = MetaData.get_value(data, 'mode')

            self.range_value = MetaData.get_value(data, 'range_value')

            self.session_id = MetaData.get_value(data, 'session_id')
            self.user_session_id = MetaData.get_value(data, 'user_session_id')

            self.method_div_matrix_type = MetaData.get_value(data, 'method_div_matrix_type')
            self.delta = MetaData.get_value(data, 'delta')

            self.mnk = MetaData.get_value_bool(data, 'mnk')
            self.mnm = MetaData.get_value_bool(data, 'mnm')
            self.mao = MetaData.get_value_bool(data, 'mao')
            self.mco = MetaData.get_value_bool(data, 'mco')

            self.freeChlen = MetaData.get_value_bool(data, 'freeChlen')
            self.file_id = MetaData.get_value(data, 'file_id')
            self.load_matrix_id = MetaData.get_value(data, 'load_matrix_id')
            self.work_matrix_id = MetaData.get_value(data, 'work_matrix_id')

            self.len_x_load_matrix = MetaData.get_value(data, 'len_x_load_matrix')
            self.len_load_matrix = MetaData.get_value(data, 'len_load_matrix')
            self.len_x_work_matrix = MetaData.get_value(data, 'len_x_work_matrix')
            self.len_work_matrix = MetaData.get_value(data, 'len_work_matrix')

            self.index_y = MetaData.get_value(data, 'index_y')

            self.matrix_y_index = MetaData.get_value(data, 'matrix_y_index')
            self.matrix_x_index = MetaData.get_value(data, 'matrix_x_index')

            self.index_h1 = MetaData.get_value(data, 'index_h1')
            self.index_h2 = MetaData.get_value(data, 'index_h2')

            self.answer = MetaData.get_value_bool(data, 'answer')

    @staticmethod
    def get_value(data, key):
        try:
            return data[key]
        except KeyError:
            return None

    @staticmethod
    def get_value_bool(data, key):
        try:
            return data[key]
        except KeyError:
            return False

    def set_lock_menu(self):
        self.menu_lock_load = True
        self.menu_lock_data = True
        self.menu_lock_div = True
        self.menu_lock_answer = True
        self.menu_lock_bias = True

        if self._is_select_method():
            self.menu_lock_load = False
        if self.file_id:
            self.menu_lock_data = False
        if self.index_y is not None or self.index_h1 or self.index_h2:
            self.menu_lock_div = False
        if self.answer:
            self.menu_lock_answer = False
        if self.matrix_y_index is not None:
            self.menu_lock_bias = False

    def set_active_menu(self, menu_type: MenuTypes):
        self._drop_active_menu()
        self.set_lock_menu()

        if menu_type == MenuTypes.MAIN:
            self.menu_active_main = True
        elif menu_type == MenuTypes.LOAD:
            self.menu_active_load = True
        elif menu_type == MenuTypes.DATA:
            self.menu_active_data = True
        elif menu_type == MenuTypes.DIV:
            self.menu_active_div = True
        elif menu_type == MenuTypes.ANSWER:
            self.menu_active_answer = True
        elif menu_type == MenuTypes.BIAS:
            self.menu_active_bias = True

    def add_session(self, session_id, ip):
        """
        Добавляет запись о новой сессии в БД.

        :param session_id: Сгенерированный идентификатор сессии.
        :param ip: Адресс клиента.
        """

        self.session_id = session_id
        user_session_id = UserSessionRepo.add(session_id, ip)
        self.user_session_id = user_session_id
        log.debug(f'Create new session: {user_session_id}')

    def add_load_file(self, filename):
        """
        Добавляет запись о загрузке нового файла.
        :param filename: имя загруженного файла.
        :return имя файла.
        """

        filename = '{}-{}'.format(self.user_session_id, filename)
        self.file_id = LoadFilesRepo.add_file(self.user_session_id, filename)

        return filename

    def add_load_matrix(self, matrix):
        """
        Добавляет созруженную матрицу. Делает загруженную матрицу рабочей.
        :param matrix: загруженная матрица.
        """

        self.len_x_load_matrix = len(matrix[0])
        self.len_load_matrix = len(matrix)
        self.len_x_work_matrix = self.len_x_load_matrix
        self.len_work_matrix = self.len_load_matrix

        matrix_repo = MatrixRepo()
        self.load_matrix_id = matrix_repo.add_matrix(matrix)
        self.work_matrix_id = self.load_matrix_id

    def add_work_matrix(self, matrix):
        """
        Добавляет новую рабочу матрицу.
        :param matrix: рабочая матрица
        """

        matrix_repo = MatrixRepo()
        self.work_matrix_id = matrix_repo.add_matrix(matrix)
        self.len_x_work_matrix = len(matrix[0])
        self.len_work_matrix = len(matrix)

    def set_y(self, index_y):
        """
        Устанавливает зависимую переменную. Сохраняет в БД.
        :param index_y: индекс с столбца с зависимой переменной.
        """

        matrix_repo = MatrixRepo()

        self.index_y = index_y
        y = []
        for items in matrix_repo.get_matrix(self.work_matrix_id):
            index = 0
            for item in items:
                if index == index_y:
                    y.append(item)
                index += 1

        self.matrix_y_index = matrix_repo.set_row(y)

        self.set_matrix_x()

    def set_matrix_x(self):
        """
        Устанавливает матрицу х. Сохраняет в БД.
        """

        matrix_repo = MatrixRepo()

        x = []
        for items in matrix_repo.get_matrix(self.work_matrix_id):
            line = []
            index = 0
            for item in items:
                if index != self.index_y:
                    line.append(item)
                index += 1
            x.append(line)

        if self.freeChlen:
            new_x = []
            for items in x:
                line = [1]
                for item in items:
                    line.append(item)
                new_x.append(line)

            self.matrix_x_index = matrix_repo.add_matrix(new_x)
            return

        self.matrix_x_index = matrix_repo.add_matrix(x)

    def get_matrix_x(self):
        """
        Получает матрицу х.
        :return: матрицу вида [[],[],].
        """

        matrix_repo = MatrixRepo()

        return matrix_repo.get_matrix(self.matrix_x_index)

    def get_matrix_y(self):
        """
        Получает матрицу y.
        :return: массив (вектор) в виде листа значений.
        """

        return MatrixRepo.get_row(self.matrix_y_index)

    @staticmethod
    def get_matrix(matrix_id):
        """
        Получает матрицу по идентификатору.
        :param matrix_id: идентификатор матрицы.
        :return: матрицу вида [[],[],].
        """

        matrix_repo = MatrixRepo()

        return matrix_repo.get_matrix(matrix_id)

    @staticmethod
    def get_row(row_id):
        """
        Получает вектор по идентификатору.
        :param row_id: идентификатор вектора.
        :return: массив (вектор) в виде листа значений.
        """

        return MatrixRepo.get_row(row_id)

    def set_h1_h2(self, h1, h2):
        """
        Устанавливает подматрицы Н1, Н2.
        :param h1: идентификаторы строк целевой матрицы, образующие подматрицу Н1.
        :param h2: идентификаторы строк целевой матрицы, образующие подматрицу Н2.
        """

        matrix_repo = MatrixRepo()

        self.index_h1 = matrix_repo.set_row(h1)
        self.index_h2 = matrix_repo.set_row(h2)

    def get_check_task(self):
        """
        Получает лист с состояниями выбора методов решения задачи.
        Выбранные методы для решения задачи помечены как True,
        в противном случае False

        :return: лист с состояниями выбора задач.
        """

        return [self.mnk, self.mnm, self.mao, self.mco]

    def update_time_active(self):
        """
        Обновляет время активности клиента.
        """

        log.info('updateTimeActive')
        UserSessionRepo.update_user_active(self.user_session_id)

    def _is_select_method(self):
        return self.mnk or self.mnm or self.mao or self.mco

    def _drop_active_menu(self):
        self.menu_active_main = False
        self.menu_active_load = False
        self.menu_active_data = False
        self.menu_active_div = False
        self.menu_active_answer = False
        self.menu_active_bias = False

    def __eq__(self, other):
        return (isinstance(other, MetaData) and
                self.session_id == other.session_id and
                self.user_session_id == other.user_session_id and
                self.mnk == other.mnk and
                self.mnm == other.mnm and
                self.mao == other.mao and
                self.mco == other.mco and
                self.method_div_matrix_type == other.method_div_matrix_type and
                self.delta == other.delta and
                self.freeChlen == other.freeChlen and
                self.file_id == other.file_id and
                self.load_matrix_id == other.load_matrix_id and
                self.work_matrix_id == other.work_matrix_id and
                self.len_x_load_matrix == other.len_x_load_matrix and
                self.len_load_matrix == other.len_load_matrix and
                self.len_x_work_matrix == other.len_x_work_matrix and
                self.len_work_matrix == other.len_work_matrix and
                self.index_y == other.index_y and
                self.matrix_y_index == other.matrix_y_index and
                self.matrix_x_index == other.matrix_x_index and
                self.index_h1 == other.index_h1 and
                self.index_h2 == other.index_h2 and
                self.answer == other.answer)

    class DataEncoder(json.JSONEncoder):
        """
        Класс кодирует модель Data в JSON формат.
        """
        def default(self, obj):
            if isinstance(obj, MetaData):
                return obj.__dict__
            return json.JSONEncoder.default(self, obj)
