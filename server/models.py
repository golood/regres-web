#!/usr/bin/python3
import json
from server import db

class MetaData:
    '''
    Класс для хранения мета данных пользователя.
    Используется для представления данных в барузере.
    '''

    def __init__(self, data):
        if data == None:
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

    def addSession(self, session_id, ip):
        '''
        Добавляет запись о новой сессии в БД.

        :param session_id: Сгенерированный идентификатор сессии.
        :param ip: Адресс клиента.
        '''

        user_session_db = db.UserSessionRepo()

        self.session_id = session_id
        user_session_id = user_session_db.add(session_id, ip)
        self.user_session_id = user_session_id

    def addLoadFile(self, filename):
        '''
        Добавляет запись о загрузке нового файла.
        :param filename: имя загруженного файла.
        :return имя файла.
        '''

        filename = '{}-{}'.format(self.user_session_id, filename)
        filesRepo = db.LoadFilesRepo()
        self.file_id = filesRepo.addFile(self.user_session_id, filename)

        return filename

    def addLoadMatrix(self, matrix):
        '''
        Добавляет созруженную матрицу. Делает загруженную матрицу рабочей.
        :param matrix: загруженная матрица.
        '''

        self.len_x_load_matrix = len(matrix[0])
        self.len_load_matrix = len(matrix)
        self.len_x_work_matrix = self.len_x_load_matrix
        self.len_work_matrix = self.len_load_matrix

        matrixRepo = db.MatrixRepo()
        self.load_matrix_id = matrixRepo.addMatrix(matrix)
        self.work_matrix_id = self.load_matrix_id

    def addWorkMatrix(self, matrix):
        '''
        Добавляет новую рабочу матрицу.
        :param matrix: рабочая матрица
        '''

        matrixRepo = db.MatrixRepo()
        self.work_matrix_id = matrixRepo.addMatrix(matrix)

    def set_y(self, index_y):
        '''
        Устанавливает зависимую переменную. Сохраняет в БД.
        :param index_y: индекс с столбца с зависимой переменной.
        '''

        matrixRepo = db.MatrixRepo()

        self.index_y = index_y
        y = []
        for items in matrixRepo.getMatrix(self.work_matrix_id):
            index = 0
            for item in items:
                if index == index_y:
                    y.append(item)
                index += 1

        self.matrix_y_index = matrixRepo.setRow(y)

        self.setMatrix_x()

    def setMatrix_x(self):
        '''
        Устанавливает матрицу х. Сохраняет в БД.
        '''

        matrixRepo = db.MatrixRepo()

        x = []
        for items in matrixRepo.getMatrix(self.work_matrix_id):
            line = []
            index = 0
            for item in items:
                if index != self.index_y:
                    line.append(item)
                index += 1
            x.append(line)

        self.matrix_x_index = matrixRepo.addMatrix(x)

    def getMetrix(self, matrixId):
        matrixRepo = db.MatrixRepo()

        return matrixRepo.getMatrix(matrixId)

    def getRow(self, rowId):
        matrixRepo = db.MatrixRepo()

        return matrixRepo.getRow(rowId)

    def setH1H2(self, h1, h2):
        matrixRepo = db.MatrixRepo()

        self.index_h1 = matrixRepo.setRow(h1)
        self.index_h2 = matrixRepo.setRow(h2)

    def getCheckTask(self):
        return [self.mnk, self.mnm, self.mao, self.mco]

    def updateTimeActiv(self):
        user_session_db = db.UserSessionRepo()
        user_session_db.updateUserActive(self.user_session_id)

    class DataEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, MetaData):
                return obj.__dict__
            return json.JSONEncoder.default(self, obj)