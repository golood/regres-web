#!/usr/bin/python3
import json
from threading import Thread
from regres.regr import Task, TaskPerebor
from server import db


class Data:
    def __init__(self, data):
        if data is None:
            self.freeChlen = False

            self.loadMatrix = None
            self.workMatrix = None

            self.y = None
            self.x = None

            self.h1_index = None
            self.h2_index = None
            self.h1 = None
            self.h2 = None

            self.results = None
        else:
            self.freeChlen = data['freeChlen']

            self.loadMatrix = data['loadMatrix']
            self.workMatrix = data['workMatrix']

            self.y = data['y']
            self.x = data['x']

            self.h1_index = data['h1_index']
            self.h2_index = data['h2_index']
            self.h1 = data['h1']
            self.h2 = data['h2']

            self.results = data['results']

    def set_y(self, index_y):
        y = []
        for items in self.loadMatrix:
            index = 0
            for item in items:
                if index == index_y:
                    y.append(item)
                index += 1

        self.y = y
        self._render_x(index_y)

    def _render_x(self, index_y):
        x = []
        for items in self.loadMatrix:
            line = []
            index = 0
            for item in items:
                if index != index_y:
                    line.append(item)
                index += 1
            x.append(line)

        self.x = self.append_freeChlen(x)

    def append_freeChlen(self, x):

        if self.freeChlen:
            new_x = []
            for items in x:
                line = [1]
                for item in items:
                    line.append(item)
                new_x.append(line)
            return new_x

        return x

    def set_h1_h2(self, h1_index=None, h2_index=None):

        h1 = []
        h2 = []

        index = 0
        for items in self.x:
            if (index in h1_index):
                h1.append(items)
                index += 1
                continue
            if (index in h2_index):
                h2.append(items)
                index += 1
                continue

        self.h1 = h1
        self.h1_index = h1_index
        self.h2 = h2
        self.h2_index = h2_index


class DataEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Data):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)


class Result:

    def __init__(self, data):
        if data is None:
            self.results = []
        else:
            self.results = []
            self._res(data)

    def _res(self, data):
        for item in data:
            self.results.append(TaskRes(item))


class TaskRes:

    def __init__(self, data):
        if data is None:
            self.name = None
            self.alfa = None
            self.eps = None
            self.E = None
        else:
            self.name = data['name']
            self.alfa = data['alfa']
            self.eps = data['eps']
            self.E = data['E']


class Test:

    def __init__(self, tasks=None, x=None, y=None, h1=None, h2=None):
        self._build(tasks, x, y, h1, h2)
        self._run()

    def _build(self, tasks, x, y, h1, h2):
        self.tasks = Task(tasks=tasks, x=x, y=y, h1=h1, h2=h2)

    def _run(self):
        self.tasks.run()

    def getResaults(self):
        return self.tasks.getResaults()


class WorkerTaskPerebor(Thread):
    """
    Поток для решения задачи вычисления критерия смещения.
    """

    def __init__(self, userId=None, name=None, x=None, y=None):
        """Инициализация потока"""
        Thread.__init__(self)
        self.__createWorker(userId)
        self.name = name
        self.x = x
        self.y = y
        self.massiv = self._initList(len(x))
        self.task = TaskPerebor(x=self.x, y=self.y, massiv=self.massiv)
        self.task_id = self.task.task_id
        self.__buildWorker()

    def run(self):
        """Запуск потока"""
        repo = db.WorkerRepo()
        if repo.runWorker(self.id):
            self.task.run()

    def _initList(self, len):
        m = []
        for item in range(len):
            m.append(item)

        return m

    def __createWorker(self, userId):
        '''
        Создаёт в БД нового работника. Получает идентификатор работника.
        :param userId: идентификатор пользователя.
        '''

        repo = db.WorkerRepo()
        self.id = repo.createNewWorker(userId)

    def __buildWorker(self):
        '''
        Собирает работника. Получает задачу для работника. Привязывает её к
        себе в БД.
        '''

        repo = db.WorkerRepo()
        repo.buildWorker(self.id, self.name, self.task_id)


class TestT:

    def __init__(self, x=None, y=None):
        self._build(x, y)
        self._run()

    def _build(self, x, y):
        self.tasks = TaskPerebor(x=x, y=y, massiv=self._initList(len(x)))

    def _initList(self, len):
        m = []
        for item in range(len):
            m.append(item)

        return m

    def _run(self):
        self.tasks.run()

    def getResaults(self):
        return self.tasks.getResult()
