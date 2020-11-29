import json
import math
import sys
import threading
import time
from functools import reduce
from itertools import combinations
from queue import Queue

import numpy as np
import redis
import requests

import regres.regression as regression
import server.config as config
from server.db import ResultRepo, WorkerRepo
from server.logger import logger

log = logger.get_logger('server')
sys.setrecursionlimit(1000000000)

red = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    decode_responses=True)

threadLock = threading.Lock()
# x = np.array([[2., 5.],
#           [9., 4.],
#           [6., 1.],
#           [8., 3.],
#           [1., 7.],
#           [5., 8.]])
#
# y = np.array([7., 9., 1., 6., 4., 5.])
#
#
# h1 = [0, 1, 2]
#
# h2 = [3, 4, 5]
#
# y1 = np.array([7, 9, 1])
# y2 = np.array([6, 4, 5])


class Method:

    def __init__(self, x, y):
        self.y = np.array(y)
        self.x = np.array(x)
        self.a = []
        self.eps = []
        self.e = 0
        self.M = 0  # сумма модулей ошибок
        self.K = 0  # сумма квадратов ошибок
        self.O = 0  # максимальная по модулю ошибка
        self.nz = None

    def _y(self, alfa):
        matrix_a = list(map(lambda item: list(map(lambda x, a: x * a, item, alfa)), self.x))
        matrix_a = list(map(lambda item: reduce(lambda x, y: x + y, item), matrix_a))

        return matrix_a

    def epsilon(self, alfa):
        """
        Расчёт ошибок аппроксимации.
        """
        return list(
            map(lambda x, y: y - x, self._y(alfa), self.y))

    def epsilon_e(self, alfa):
        """
        Расчёт оценки ошибки аппроксимации.
        """
        e = 1 / len(self.y) * reduce(
            lambda x, y: x + y,
            list(map(lambda x, y: math.fabs((y - x) / y),
                     self._y(alfa), self.y))) * 100

        return e

    def calculation_m(self):
        """
        Расчёт суммы модулей ошибок.
        """

        for item in self.eps:
            self.M += abs(item)

    def calculation_k(self):
        """
        Расчёт суммы квадратов ошибок.
        """

        for item in self.eps:
            self.K += item**2

    def calculation_o(self):
        """
        Поиск максимольной по модулю ошибки.
        """

        self.O = max(list(map(lambda x: abs(x), self.eps)))

    def get_result(self):
        return self.a, self.eps, [self.e, self.M, self.K, self.O]

    def get_bias_estimate(self):
        """
        Получает оценку смещения.
        """
        amount = 0
        m = len(self.x)
        try:
            for item in self.x:
                x = math.fsum(item) / len(item)
                amount += math.fabs((self._minus_alfa() * x) / (self.a[0] * x)) / m

            return amount * 100
        except ZeroDivisionError:
            return 'Infinity'

    def _minus_alfa(self):
        a = self.a[0]
        for i in range(1, len(self.a)):
            a -= self.a[i]
        return a


class MNK(Method):

    def __init__(self, x, y):
        super().__init__(x, y)

    def find_a(self):
        return np.dot(
            np.dot(
                np.linalg.inv(np.dot(self.x.T, self.x)),
                self.x.T),
            self.y)

    def run(self):
        a = self.find_a()
        for item in a:
            self.a.append(item)
        eps = self.epsilon(self.a)
        for item in eps:
            self.eps.append(item)
        self.e = self.epsilon_e(self.a)
        self.calculation_m()
        self.calculation_k()
        self.calculation_o()

    def get_result(self):
        return 'МНК', super().get_result()


class MNM(Method):

    def __init__(self, x, y):
        super().__init__(x, y)

    def find_a(self):
        pass

    def run(self):
        task = regression.LpSolveMNM(self.x, self.y)
        task.run()
        self.a, self.eps = task.get_result()
        self.e = self.epsilon_e(self.a)
        self.calculation_m()
        self.calculation_k()
        self.calculation_o()

    def get_result(self):
        return 'МНМ', super().get_result()


class MAO(Method):

    def __init__(self, x, y):
        super().__init__(x, y)

    def find_a(self):
        pass

    def run(self):
        task = regression.LpSolveMAO(self.x, self.y)
        task.run()
        self.a, self.eps = task.get_result()
        self.e = self.epsilon_e(self.a)
        self.calculation_m()
        self.calculation_k()
        self.calculation_o()

    def get_result(self):
        return 'МАО', super().get_result()


class MCO(Method):

    def __init__(self, x, y, h1, h2):
        super().__init__(x, y)
        self.h1 = h1
        self.h2 = h2

    def find_a(self):
        pass

    def run(self):
        task = regression.LpSolveMCO(self.x, self.y, self.h1, self.h2)
        task.run()
        self.a, self.eps = task.get_result()
        self.e = self.epsilon_e(self.a)
        self.calculation_m()
        self.calculation_k()
        self.calculation_o()

    def get_result(self):
        return 'МСО', super().get_result()


class Task:

    def __init__(self, tasks, x, y, h1=None, h2=None):
        self.methods = []
        if tasks[0]:
            self.methods.append(MNK(x, y))
        if tasks[1]:
            self.methods.append(MNM(x, y))
        if tasks[2]:
            self.methods.append(MAO(x, y))
        if tasks[3]:
            self.methods.append(MCO(x, y, h1, h2))

    def run(self):

        for item in self.methods:
            item.run()

    def get_results(self):
        results = []

        for item in self.methods:
            results.append(item.get_result())

        return results


class RequestWorker(threading.Thread):
    """Потоковый отправитель запросов в воркеры."""

    def __init__(self, queue, counter, percent, task_id):
        threading.Thread.__init__(self)
        self.threadID = counter
        self.queue = queue
        self.x = red.get('x')
        self.y = red.get('y')
        self.percent = percent
        self.task_id = task_id

    def run(self):
        while True:
            start = time.time()
            index = self.queue.get()
            data = self.send_request(index)

            threadLock.acquire()
            if data is not None:
                ResultRepo().add_results(data['answer'], self.task_id,
                                         self.percent)
            threadLock.release()
            self.queue.task_done()

            log.debug('Complete package: {0}, taskId: {1}, lead time: {2}'
                      .format(index, self.task_id, time.time() - start))

    def send_request(self, index):
        data = {'index': index,
                'x': self.x,
                'y': self.y,
                'list_h': red.get(index)}

        try:
            response = requests.post(config.URL_WORKER, json=data)

            if response.status_code >= 400:
                log.error('Exception request to worker: {0}'
                          .format(response.content.decode('utf-8')))
            else:
                return json.loads(response.content.decode('utf-8'))
        except Exception as e:
            log.error('Exception request to worker', exc_info=True,
                      stack_info=True)

        return None


class TaskBiasEstimates:
    """
    Класс задачи для решения задачи поиска критерия смещения, перебором
    комбинаций подматриц Н1, Н2.
    """

    def __init__(self, x, y, indices_x):
        self.percent = 100
        self.x = x
        self.y = y
        red.mset({'x': json.dumps(x)})
        red.mset({'y': json.dumps(y)})
        self.indices_x = indices_x
        self.tasks = []
        self.index = []
        self.task_id = ResultRepo.create_task()

    def run(self):
        self.get_all_combinations()

    def create_task_package(self):
        """
        Собирает в пакет набор задач.
        """

        queue = Queue()
        percent = float('{:.3f}'.format(self.percent))
        for i in range(int(config.WORKER_THREAD)):
            t = RequestWorker(queue, i, percent, self.task_id)
            t.setDaemon(True)
            t.start()
        log.info('Started {0} thread workers'.format(config.WORKER_THREAD))

        for i in self.index:
            queue.put(str(i))

        queue.join()
        self.tasks = []

    def get_all_combinations(self):
        """
        Перебор всех комбинаций Н1, Н2. Решение задачи методом СМО. Сохранение
        результатов решений в БД. Запись происходит порционно по n решений
        задачи.
        """

        len_x = len(self.indices_x)
        k = len_x // 2
        size = (math.factorial(len_x)
                / (math.factorial(len_x - k) * math.factorial(k)))
        step = int(config.COUNT_PACKAGE)

        percent = step / (size / 100)
        if percent < 100:
            self.percent = percent

        counter = 0
        i = 0
        test_list_h1 = []
        test_list_h2 = []
        for h1 in combinations(self.indices_x, k):
            counter += 1
            h2 = tuple(filter(lambda x: (x not in h1), self.indices_x))

            if h2 in test_list_h1:
                continue
            test_list_h1.append(h1)
            test_list_h2.append(h2)
            self.tasks.append({'h1': h1, 'h2': h2})

            if counter % step == 0:
                self.index.append(i)
                red.mset({str(i): json.dumps(self.tasks)})
                i += 1
                counter = 0
                self.tasks = []

        if counter != 0:
            self.index.append(i)
            red.mset({str(i): json.dumps(self.tasks)})
            self.tasks = []

        del test_list_h1
        del test_list_h2

        self.create_task_package()

        while True:
            if WorkerRepo.is_complete(self.task_id):
                WorkerRepo.complete(self.task_id)
                break
            time.sleep(2)

    def clear_redis_data(self):
        for i in self.index:
            red.delete(str(i))

        red.delete('x')
        red.delete('y')

    def get_result(self):
        results = []

        for task in self.tasks:
            results.append(task.get_results())

        return results

    class TaskDTO:
        def __init__(self, x, y, h1, h2):
            self.x = x
            self.y = y
            self.h1 = h1
            self.h2 = h2

        class DataEncoder(json.JSONEncoder):
            """
            Класс кодирует модель Data в JSON формат.
            """

            def default(self, obj):
                if isinstance(obj, TaskBiasEstimates.TaskDTO):
                    return obj.__dict__
                return json.JSONEncoder.default(self, obj)

    class MyThread(threading.Thread):
        def __init__(self, queue):
            """Инициализация потока"""
            threading.Thread.__init__(self)
            self.queue = queue

        def run(self):
            """Запуск потока"""
            while True:
                # Получаем задачу ЛП из очереди
                task = self.queue.get()

                # Решаем задачу
                task.run()

                # Отправляем сигнал о том, что задача завершена
                self.queue.task_done()
