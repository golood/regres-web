import datetime
import json
import numpy as np
from functools import reduce
import regres.rrrr as rrr
import sys
import math
from itertools import combinations
import threading
from server.db import ResultRepo, WorkerRepo, ServiceRepo
import time

sys.setrecursionlimit(1000000000)

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
        A = list(map(lambda item:
                     list(map(lambda x, a: x * a, item,
                              alfa)),
                     self.x))
        A = list(map(lambda item:
                     reduce(lambda x, y: x + y, item), A))

        return A

    def epselon(self, alfa):
        return list(
            map(lambda x, y: y - x, self._y(alfa), self.y))

    def Epselon(self, alfa):
        mod = lambda x: x if (x > 0) else x * -1

        E = 1 / len(self.y) * reduce(
            lambda x, y: x + y,
            list(map(lambda x, y: mod((y - x) / y),
                     self._y(alfa), self.y))) * 100

        return E

    def calculation_m(self):
        '''
        Расчет суммы модулей ошибок.
        '''

        for item in self.eps:
            self.M += abs(item)

    def calculation_k(self):
        '''
        Расчет суммы квадратов ошибок.
        '''

        for item in self.eps:
            self.K += item**2

    def calculation_o(self):
        '''
        Поиск максимольной по модулю ошибки.
        '''

        self.O = max(list(map(lambda x: abs(x), self.eps)))

    def getResaul(self):
        return self.a, self.eps, [self.e, self.M, self.K, self.O]

    def getSmeshenir(self):
        sum = 0
        m = len(self.x)
        try:
          for item in self.x:
            x = math.fsum(item) / len(item)
            sum += math.fabs((self._minusAlfa() * x) / (self.a[0] * x)) / m

          return sum * 100
        except ZeroDivisionError:
          return 'Infinity'

    def _minusAlfa(self):
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
        eps = self.epselon(self.a)
        for item in eps:
            self.eps.append(item)
        self.e = self.Epselon(self.a)
        self.calculation_m()
        self.calculation_k()
        self.calculation_o()

    def getResaul(self):
        return 'МНК', super().getResaul()


class MNM(Method):

    def __init__(self, x, y):
        super().__init__(x, y)

    def find_a(self):
        pass

    def run(self):
        task = rrr.LpSolve_MNM(self.x, self.y)
        task.run()
        self.a, self.eps = task.getResault()
        self.e = self.Epselon(self.a)
        self.calculation_m()
        self.calculation_k()
        self.calculation_o()

    def getResaul(self):
        return 'МНМ', super().getResaul()


class MAO(Method):

    def __init__(self, x, y):
        super().__init__(x, y)

    def find_a(self):
        pass

    def run(self):
        task = rrr.LpSolve_MAO(self.x, self.y)
        task.run()
        self.a, self.eps = task.getResault()
        self.e = self.Epselon(self.a)
        self.calculation_m()
        self.calculation_k()
        self.calculation_o()

    def getResaul(self):
        return 'МАО', super().getResaul()


class MCO(Method):

    def __init__(self, x, y, h1, h2):
        super().__init__(x, y)
        self.h1 = h1
        self.h2 = h2

    def find_a(self):
        pass

    def run(self):
        task = rrr.LpSolve_MCO(self.x, self.y, self.h1, self.h2)
        task.run()
        self.a, self.eps = task.getResault()
        self.e = self.Epselon(self.a)
        self.calculation_m()
        self.calculation_k()
        self.calculation_o()

    def getResaul(self):
        return 'МСО', super().getResaul()


class Task:

    def __init__(self, tasks, x, y, h1=None, h2=None):
        self.methods = []
        if (tasks[0]):
          self.methods.append(MNK(x, y))
        if (tasks[1]):
          self.methods.append(MNM(x, y))
        if (tasks[2]):
          self.methods.append(MAO(x, y))
        if (tasks[3]):
          self.methods.append(MCO(x, y, h1, h2))

    def run(self):

        for item in self.methods:
            item.run()

    def getResaults(self):
        resaults = []

        for item in self.methods:
            resaults.append(item.getResaul())

        return resaults


class TaskMCO:

    def __init__(self, x, y, h1=None, h2=None):
        self.method = MCO(x, y, h1, h2)

    def run(self):
        self.method.run()

    def getResaults(self):
        resaults = []

        resaults.append(self.method.getResaul())
        resaults.append(self.method.getSmeshenir())
        resaults.append(self.method.h1)
        resaults.append(self.method.h2)

        return resaults


class TaskPerebor:
    '''
    Класс задачи для решения задачи поиска критерия смещения, перебором
    комбинаций подматриц Н1, Н2.
    '''

    def __init__(self, x, y, massiv):
        self.x = x
        self.y = y
        self.massiv = massiv
        self.tasks = []
        self.repoRes = ResultRepo()
        self.task_id = self.repoRes.createTask()

        repo = ServiceRepo()
        self.serviceIds = repo.getRuningServiceIds()

    def run(self):
        self.getAllComb()

    def addTasksInService(self, serviceId):
        '''
        Добавляет собранные задач ЛП в очередь сервисов.
        '''

        tasksDTO = []
        for item in self.tasks:
            tasksDTO.append(json.dumps(item, cls=self.TaskDTO.DataEncoder))

        serviceRepo = ServiceRepo()
        serviceRepo.addQueueTask(tasksDTO, self.task_id, self.percent, serviceId)

        del tasksDTO
        self.tasks = []

    def getAllComb(self):
        '''
        Перебор всех комбинаций Н1, Н2. Решение задачи методом СМО. Сохранение
        результатов решений в БД. Запись происходит порционно по n решений
        задачи.
        '''

        len_x = len(self.massiv)
        k = len_x // 2
        size = math.factorial(len_x) / (math.factorial(len_x - k) * math.factorial(k))
        step = 1000

        self.percent = step / (size / 100)
        if self.percent > 100:
            self.percent = 100

        indexService = 0
        maxIndex = len(self.serviceIds) - 1
        counter = 0
        for h1 in combinations(self.massiv, k):
            counter += 1
            h2 = tuple(filter(lambda x: (x not in h1), self.massiv))

            self.tasks.append(self.TaskDTO(self.x, self.y, h1, h2))

            if counter % step == 0:
                self.addTasksInService(self.serviceIds[indexService])
                counter = 0
                if indexService == maxIndex:
                    indexService = 0
                else:
                    indexService += 1

        if counter != 0:
            self.addTasksInService(self.serviceIds[indexService])

        while True:
            repoWorker = WorkerRepo()
            if repoWorker.isComplete(self.task_id):
                repoWorker.complete(self.task_id)
                break
            time.sleep(5)

    def getResult(self):
        resaults = []

        for task in self.tasks:
            resaults.append(task.getResaults())

        return resaults

    class TaskDTO:
        def __init__(self, x, y, h1, h2):
            self.x = x
            self.y = y
            self.h1 = h1
            self.h2 = h2

        class DataEncoder(json.JSONEncoder):
            '''
            Класс кодирует модель Data в JSON формат.
            '''

            def default(self, obj):
                if isinstance(obj, TaskPerebor.TaskDTO):
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