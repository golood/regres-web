import numpy as np
from functools import reduce
from pulp import LpVariable, LpMinimize, LpProblem
import regres.rrrr as rrr
import sys

sys.setrecursionlimit(1000000000)

x = np.array([[2., 5.],
          [9., 4.],
          [6., 1.],
          [8., 3.],
          [1., 7.],
          [5., 8.]])

y = np.array([7., 9., 1., 6., 4., 5.])
#
#
h1 = [0, 1, 2]

h2 = [3, 4, 5]
#
y1 = np.array([7, 9, 1])
y2 = np.array([6, 4, 5])


class Method:

    def __init__(self, x, y):
        self.y = np.array(y)
        self.x = np.array(x)
        self.a = []
        self.eps = []
        self.e = 0

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


class Task:

    def __init__(self, x, y, h1=None, h2=None):
        self.methods = []
        self.methods.append(MNK(x, y))
        self.methods.append(MNM(x, y))
        self.methods.append(MAO(x, y))
        self.methods.append(MCO(x, y, h1, h2))

    def run(self):

        for item in self.methods:
            item.run()

    def getResaults(self):
        resaults = []

        for item in self.methods:
            resaults.append(item.getResaul())

        return resaults

# test = Task(x, y, h1, h2)
# test.run()
# test.getResaults()