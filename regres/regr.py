import datetime

import numpy as np
from functools import reduce
from pulp import LpVariable, LpMinimize, LpProblem
import regres.rrrr as rrr
import sys
import math
from itertools import combinations
import threading
from queue import Queue
from server import utill
from server.db import ResultRepo, WorkerRepo

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

    def getResaul(self):
        return self.a, self.eps, self.e

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
        self.methods = []
        self.methods.append(MCO(x, y, h1, h2))

    def run(self):

        for item in self.methods:
            item.run()

    def getResaults(self):
        resaults = []

        for item in self.methods:
            resaults.append(item.getResaul())
            resaults.append(item.getSmeshenir())
            resaults.append(item.h1)
            resaults.append(item.h2)

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

    def run(self):
        self.getAllComb()

    def runTasks(self):
        '''
        Запускает вычисления собранных задач ЛП.
        Сохраняет результаты вычислений.
        '''

        queue = Queue()

        # Запускаем поток и очередь
        for i in range(2):
            t = self.MyThread(queue)
            t.start()

        # Даем очереди нужные нам задачи для решения
        for task in self.tasks:
            queue.put(task)

        # Ждем завершения работы очереди
        queue.join()

        res = self.getResult()

        result = []
        for item in res:
            line = []
            line.append(utill.format_numbers(item[0][1][0]))
            line.append(utill.format_numbers(item[0][1][1]))
            line.append(utill.format_number(item[0][1][2]))
            line.append(utill.format_number(item[1]))
            line.append(utill.appendOneForNumber(item[2]))
            line.append(utill.appendOneForNumber(item[3]))
            result.append(line)

        self.repoRes.addResults(result, self.task_id, self.percent)

        del result
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
        step = 100
        self.percent = step / (size / 100)
        counter = 0
        for h1 in combinations(self.massiv, k):
            counter += 1
            h2 = tuple(filter(lambda x: (x not in h1), self.massiv))

            self.tasks.append(TaskMCO(self.x, self.y, h1, h2))

            if counter % step == 0:
                self.runTasks()
                counter = 0

        if counter != 0:
            self.runTasks()

        repoWorker = WorkerRepo()
        repoWorker.complete(self.task_id)

    def getResult(self):
        resaults = []

        for task in self.tasks:
            resaults.append(task.getResaults())

        return resaults

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