#!/usr/bin/python3
import json
from threading import Thread

from regres.regressionAPI import Task, TaskBiasEstimates
from server.logger import logger

log = logger.get_logger('server')


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

        self.x = self.append_free_member(x)

    def append_free_member(self, x):

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
            if index in h1_index:
                h1.append(items)
                index += 1
                continue
            if index in h2_index:
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


class Test:

    def __init__(self, tasks=None, x=None, y=None, h1=None, h2=None):
        self._build(tasks, x, y, h1, h2)
        self._run()

    def _build(self, tasks, x, y, h1, h2):
        self.tasks = Task(tasks=tasks, x=x, y=y, h1=h1, h2=h2)

    def _run(self):
        self.tasks.run()

    def get_results(self):
        return self.tasks.get_results()


class WorkerTask(Thread):
    """
    Поток для решения, задачи вычисления критерия смещения.
    """

    def __init__(self, session=None, name=None, x=None, y=None):
        """Инициализация потока"""
        Thread.__init__(self)
        self.user_token = session.token.body
        self.name = name
        self.task = TaskBiasEstimates(session=session, x=x, y=y, indices_x=self._init_list(len(x)))
        log.info(f'Create task name: {self.name} for user, token: {self.user_token}')

    def run(self):
        """Запуск потока"""
        try:
            self.task.run()
            log.info(f'The task ({self.name}) start, user token: {self.user_token}')
        except Exception as e:
            log.error(f'The task ({self.name}) did not start. User token: {self.user_token}\nerror: {str(e)}')
            raise e

    @staticmethod
    def _init_list(len_x):
        m = []
        for item in range(len_x):
            m.append(item)

        return m
