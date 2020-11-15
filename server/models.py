#!/usr/bin/python3
import json

from server import db
from server.logger import logger

import deprecation

log = logger.get_logger('server')


class MetaData:
    '''
    Класс для хранения мета данных пользователя.
    Используется для представления данных в барузере.
    '''

    def __init__(self, data):
        if data is None:
            self.session_id = None
            self.user_session_id = None

            self.mnk = False
            self.mnm = False
            self.mao = False
            self.mco = False

            self.freeChlen = False
            self.file_id = None
            self.load_matrix_id = None
            self.work_matrix_id = None

            self.len_x_load_matrix = None
            self.len_load_matrix = None
            self.len_x_work_matrix = None
            self.len_work_matrix = None

            self.index_y = None

            self.matrix_y_index = None
            self.matrix_x_index = None

            self.index_h1 = None
            self.index_h2 = None

            self.answer = False
        else:
            self.session_id = data['session_id']
            self.user_session_id = data['user_session_id']

            self.mnk = data['mnk']
            self.mnm = data['mnm']
            self.mao = data['mao']
            self.mco = data['mco']

            self.freeChlen = data['freeChlen']
            self.file_id = data['file_id']
            self.load_matrix_id = data['load_matrix_id']
            self.work_matrix_id = data['work_matrix_id']

            self.len_x_load_matrix = data['len_x_load_matrix']
            self.len_load_matrix = data['len_load_matrix']
            self.len_x_work_matrix = data['len_x_work_matrix']
            self.len_work_matrix = data['len_work_matrix']

            self.index_y = data['index_y']

            self.matrix_y_index = data['matrix_y_index']
            self.matrix_x_index = data['matrix_x_index']

            self.index_h1 = data['index_h1']
            self.index_h2 = data['index_h2']

            self.answer = data['answer']

    def add_session(self, session_id, ip):
        """
        Добавляет запись о новой сессии в БД.

        :param session_id: Сгенерированный идентификатор сессии.
        :param ip: Адресс клиента.
        """

        user_session_db = db.UserSessionRepo()

        self.session_id = session_id
        user_session_id = user_session_db.add(session_id, ip)
        self.user_session_id = user_session_id
        log.debug(f'Create new session: {user_session_id}')

    def add_load_file(self, filename):
        """
        Добавляет запись о загрузке нового файла.
        :param filename: имя загруженного файла.
        :return имя файла.
        """

        filename = '{}-{}'.format(self.user_session_id, filename)
        files_repo = db.LoadFilesRepo()
        self.file_id = files_repo.add_file(self.user_session_id, filename)

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

        matrix_repo = db.MatrixRepo()
        self.load_matrix_id = matrix_repo.add_matrix(matrix)
        self.work_matrix_id = self.load_matrix_id

    def add_work_matrix(self, matrix):
        """
        Добавляет новую рабочу матрицу.
        :param matrix: рабочая матрица
        """

        matrix_repo = db.MatrixRepo()
        self.work_matrix_id = matrix_repo.add_matrix(matrix)
        self.len_x_work_matrix = len(matrix[0])
        self.len_work_matrix = len(matrix)

    def set_y(self, index_y):
        """
        Устанавливает зависимую переменную. Сохраняет в БД.
        :param index_y: индекс с столбца с зависимой переменной.
        """

        matrix_repo = db.MatrixRepo()

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

        matrix_repo = db.MatrixRepo()

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

    @staticmethod
    def get_matrix(matrix_id):
        """
        Получает матрицу по идентификатору.
        :param matrix_id: идентификатор матрицы.
        :return: матрицу вида [[],[],].
        """

        matrix_repo = db.MatrixRepo()

        return matrix_repo.get_matrix(matrix_id)

    @staticmethod
    def get_row(row_id):
        """
        Получает вектор по идентификатору.
        :param row_id: идентификатор вектора.
        :return: массив (вектор) в виде листа значений.
        """

        matrix_repo = db.MatrixRepo()

        return matrix_repo.get_row(row_id)

    def set_h1_h2(self, h1, h2):
        """
        Устанавливает подматрицы Н1, Н2.
        :param h1: идентификаторы строк целевой матрицы, образующие подматрицу Н1.
        :param h2: идентификаторы строк целевой матрицы, образующие подматрицу Н2.
        """

        matrix_repo = db.MatrixRepo()

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
        user_session_db = db.UserSessionRepo()
        user_session_db.update_user_active(self.user_session_id)

    class DataEncoder(json.JSONEncoder):
        """
        Класс кодирует модель Data в JSON формат.
        """
        def default(self, obj):
            if isinstance(obj, MetaData):
                return obj.__dict__
            return json.JSONEncoder.default(self, obj)


@deprecation.deprecated(deprecated_in='1.0.2', removed_in='1.2.0')
class Worker:
    """
    Класс описывает сущность, которая выполняет задачи в фоновом режиме.
    """

    def __init__(self, user_id=None):
        self.task = None
        self.name = None
        self.repo = db.WorkerRepo()
        self.__create_worker(user_id)

    def __create_worker(self, user_id):
        """
        Создаёт в БД нового работника. Получает идентификатор работника.
        :param user_id: идентификатор пользователя.
        """

        self.id = self.repo.createNewWorker(user_id)

    def build_worker(self, task, name):
        """
        Собирает работника. Получает задачу для работника. Привязывает её к
        себе в БД.
        :param task: выфполняемая задача.
        :param name: имя задачи.
        """

        self.task = task
        self.name = name
        self.repo.buildWorker(self.id, self.name, self.task.task_id)

    def run(self):
        """
        Запуск работника.
        :return: True, в случае успешного запуска.
                 False, в случае блокировки.
        """
        if not self.repo.runWorker(self.id):
            return False

        self.task.run()
