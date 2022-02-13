from pulp import *


class LpSolve:
    def __init__(self, x, y, ):
        self.x = x
        self.y = y
        self.var = {}
        self.problem = pulp.LpProblem('0', pulp.const.LpMinimize)
        self._create_variable_a()
        self._create_variable_u_v()
        self._create_variable_r()

    def create_c(self):
        """
        Создание целевой функции.
        """
        pass

    def build_task_lp(self):
        """
        Создание задачи линейного программирования.
        """
        pass

    def _create_variable_a(self):
        i = 1
        for _ in self.x[0]:
            var_name = 'a{}{}'.format(str(i), '1')
            self.var.setdefault(var_name, LpVariable(var_name, lowBound=0))
            var_name = 'a{}{}'.format(str(i), '2')
            self.var.setdefault(var_name, LpVariable(var_name, lowBound=0))
            i += 1

    def _create_variable_u_v(self):
        i = 1
        for _ in self.x:
            var_name_u = 'u{}'.format(str(i))
            var_name_v = 'v{}'.format(str(i))
            self.var.setdefault(var_name_u, LpVariable(var_name_u, lowBound=0))
            self.var.setdefault(var_name_v, LpVariable(var_name_v, lowBound=0))
            i += 1

    def _create_variable_r(self):
        self.var.setdefault('r', LpVariable('r', lowBound=0))

    def _get_a_by_ij(self, i, j):
        return self.var.get('a{}{}'.format(i, j))

    def _get_u_by_i(self, i):
        return self.var.get('u{}'.format(i))

    def _get_v_by_i(self, i):
        return self.var.get('v{}'.format(i))

    def _get_r(self):
        return self.var.get('r')

    @staticmethod
    def _create_tuples(var, cof):
        return (var, cof)

    def _init_list(self, index_line):
        my_list = []

        i = 1
        for item in self.x[index_line]:
            my_list.append(self._create_tuples(self._get_a_by_ij(i, 1), item))
            my_list.append(self._create_tuples(self._get_a_by_ij(i, 2), -item))
            i += 1

        my_list.append(self._create_tuples(self._get_u_by_i(index_line + 1), 1))
        my_list.append(self._create_tuples(self._get_v_by_i(index_line + 1), -1))

        return my_list

    def _init_list_u_v(self, index_line):
        my_list = [self._create_tuples(self._get_u_by_i(index_line + 1), 1),
                   self._create_tuples(self._get_v_by_i(index_line + 1), 1),
                   self._create_tuples(self._get_r(), -1)]

        return my_list

    def build_problem_a(self, index_line):
        self.problem += LpAffineExpression(self._init_list(index_line)) == self.y[index_line], str(index_line + 1)

    def build_problem_u_v(self, index_line, iteration):
        self.problem += LpAffineExpression(self._init_list_u_v(index_line)) <= 0, str(iteration)

    def run(self):
        self.problem.solve()

    def _get_var_u_v(self):
        _vars = self.problem.variablesDict()
        u, v = [], []
        for index in range(1, len(self.x) + 1):
            u.append(_vars[f'u{index}'].value())
            v.append(_vars[f'v{index}'].value())
        return u, v

    def _get_var_a(self):
        _vars = self.problem.variablesDict()
        a = []
        for index in range(1, len(self.x[0]) + 1):
            a.append(_vars[f'a{index}{1}'].value() - _vars[f'a{index}{2}'].value())
        return a

    def get_result(self):
        a = self._get_var_a()
        u, v = self._get_var_u_v()

        eps = []
        for index in range(len(u)):
            eps.append(u[index] - v[index])

        return a, eps


class LpSolveMNM(LpSolve):

    def __init__(self, x, y):
        super().__init__(x, y)

    def create_c(self):
        self.problem += self._get_func_c(self._build_func_c()), 'Функция цели'

    def _build_func_c(self):
        params = []

        for index in range(1, len(self.x)+1):
            params.append(self._create_tuples(self._get_u_by_i(index), 1))
            params.append(self._create_tuples(self._get_v_by_i(index), 1))

        return params

    @staticmethod
    def _get_func_c(params):
        return LpAffineExpression(params)

    def build_task_lp(self):
        self.create_c()

        for index in range(len(self.x)):
            self.build_problem_a(index)

    def run(self):
        self.build_task_lp()
        super().run()


class LpSolveMAO(LpSolve):

    def __init__(self, x, y):
        super().__init__(x, y)

    def create_c(self):
        self.problem += LpAffineExpression(self._build_func_c()), 'Функция цели'

    def _build_func_c(self):
        return [self._create_tuples(self._get_r(), 1)]

    def build_task_lp(self):
        self.create_c()

        for index in range(len(self.x)):
            self.build_problem_a(index)

        for index in range(len(self.x)):
            self.build_problem_u_v(index, index + 1 + len(self.x))

    def run(self):
        self.build_task_lp()
        super().run()


class LpSolveMCO(LpSolve):

    def __init__(self, x, y, h1, h2):
        super().__init__(x, y)
        self.H1 = h1
        self.H2 = h2

    def create_c(self):
        self.problem += LpAffineExpression(self._build_func_c()), 'Функция цели'

    def _build_func_c(self):
        params = []

        for index in range(len(self.x)):
            if index in self.H1:
                params.append(self._create_tuples(self._get_u_by_i(index + 1), 1 / len(self.H1)))
                params.append(self._create_tuples(self._get_v_by_i(index + 1), 1 / len(self.H1)))

        params.append(self._create_tuples(self._get_r(), 1))

        return params

    def build_task_lp(self):
        self.create_c()

        for index in range(len(self.x)):
            self.build_problem_a(index)

        i = 1 + len(self.x)
        for index in range(len(self.x)):
            if index in self.H2:
                self.build_problem_u_v(index, i)
                i += 1

    def run(self):
        self.build_task_lp()
        super().run()

# import time
# start = time.time()
# a01 = pulp.LpVariable('a01', lowBound=0)
# a02 = pulp.LpVariable('a02', lowBound=0)
#
# a11 = pulp.LpVariable('a11', lowBound=0)
# a12 = pulp.LpVariable('a12', lowBound=0)
# a21 = pulp.LpVariable('a21', lowBound=0)
# a22 = pulp.LpVariable('a22', lowBound=0)
# u1 = pulp.LpVariable('u1', lowBound=0)
# u2 = pulp.LpVariable('u2', lowBound=0)
# u3 = pulp.LpVariable('u3', lowBound=0)
# u4 = pulp.LpVariable('u4', lowBound=0)
# u5 = pulp.LpVariable('u5', lowBound=0)
# u6 = pulp.LpVariable('u6', lowBound=0)
# v1 = pulp.LpVariable('v1', lowBound=0)
# v2 = pulp.LpVariable('v2', lowBound=0)
# v3 = pulp.LpVariable('v3', lowBound=0)
# v4 = pulp.LpVariable('v4', lowBound=0)
# v5 = pulp.LpVariable('v5', lowBound=0)
# v6 = pulp.LpVariable('v6', lowBound=0)
# r = pulp.LpVariable('r', lowBound=0)
#
# problem = pulp.LpProblem('0', pulp.const.LpMinimize)
# #
# problem += u1+v1+u2+v2+u3+v3+u4+v4+u5+v5+u6+v6, 'Функция цели'
# problem += 2*a11-2*a12+5*a21-5*a22+u1-v1==7, '1'
# problem += 9*a11-9*a12+4*a21-4*a22+u2-v2==9, '2'
# problem += 6*a11-6*a12+1*a21-1*a22+u3-v3==1, '3'
# problem += 8*a11-8*a12+3*a21-3*a22+u4-v4==6, '4'
# problem += 1*a11-1*a12+7*a21-7*a22+u5-v5==4, '5'
# problem += 5*a11-5*a12+8*a21-8*a22+u6-v6==5, '6'
#
# problem.solve()
# stop = time.time()
# print ("Время :")
# print(stop - start)
# for variable in problem.variables():
#     print(variable.name, "=", variable.varValue)
# print (abs(value(problem.objective)))
#
# problem = pulp.LpProblem('0', pulp.const.LpMinimize)
#
# problem += u1+v1+u2+v2+u3+v3+u4+v4+u5+v5+u6+v6, 'Функция цели'
# problem += a01-a02+2*a11-2*a12+5*a21-5*a22+u1-v1==7, '1'
# problem += a01-a02+9*a11-9*a12+4*a21-4*a22+u2-v2==9, '2'
# problem += a01-a02+6*a11-6*a12+1*a21-1*a22+u3-v3==1, '3'
# problem += a01-a02+8*a11-8*a12+3*a21-3*a22+u4-v4==6, '4'
# problem += a01-a02+1*a11-1*a12+7*a21-7*a22+u5-v5==4, '5'
# problem += a01-a02+5*a11-5*a12+8*a21-8*a22+u6-v6==5, '6'
#
# problem.solve()
#
# for variable in problem.variables():
#     print (variable.name, "=", variable.varValue)
# print (abs(value(problem.objective)))

# problem += r, 'Функция цели'
# problem += 2*a11-2*a12+5*a21-5*a22+u1-v1==7, '1'
# problem += 9*a11-9*a12+4*a21-4*a22+u2-v2==9, '2'
# problem += 6*a11-6*a12+1*a21-1*a22+u3-v3==1, '3'
# problem += 8*a11-8*a12+3*a21-3*a22+u4-v4==6, '4'
# problem += 1*a11-1*a12+7*a21-7*a22+u5-v5==4, '5'
# problem += 5*a11-5*a12+8*a21-8*a22+u6-v6==5, '6'
# problem += u1 + v1 - r <= 0, '7'
# problem += u2 + v2 - r <= 0, '8'
# problem += u3 + v3 - r <= 0, '9'
# problem += u4 + v4 - r <= 0, '10'
# problem += u5 + v5 - r <= 0, '11'
# problem += u6 + v6 - r <= 0, '12'
#
#
# problem.solve()
#
# for variable in problem.variables():
#     print (variable.name, "=", variable.varValue)
# print(abs(value(problem.objective)))

# problem += 1/3 * (u1+u2+u3+v1+v2+v3) + r, 'Функция цели'
# problem += 2*a11-2*a12+5*a21-5*a22+u1-v1==7, '1'
# problem += 9*a11-9*a12+4*a21-4*a22+u2-v2==9, '2'
# problem += 6*a11-6*a12+1*a21-1*a22+u3-v3==1, '3'
# problem += 8*a11-8*a12+3*a21-3*a22+u4-v4==6, '4'
# problem += 1*a11-1*a12+7*a21-7*a22+u5-v5==4, '5'
# problem += 5*a11-5*a12+8*a21-8*a22+u6-v6==5, '6'
# problem += u4 + v4 - r <= 0, '10'
# problem += u5 + v5 - r <= 0, '11'
# problem += u6 + v6 - r <= 0, '12'
#
# problem.solve()
#
# for variable in problem.variables():
#     print (variable.name, "=", variable.varValue)

# from cvxopt.modeling import variable, op
# x = variable(16, 'x')
#
# z=(x[4]+x[5]+x[6]+x[7]+x[8]+x[9]+x[10]+x[11]+x[12]+x[13]+x[14]+x[15])
# mass1 = (2*x[0]-2*x[1]+5*x[2]-5*x[3]+x[4]-x[5] == 7)
# mass2 = (9*x[0]-9*x[1]+4*x[2]-4*x[3]+x[6]-x[7] == 9)
# mass3 = (6*x[0]-6*x[1]+1*x[2]-1*x[3]+x[8]-x[9] == 1)
# mass4 = (8*x[0]-8*x[1]+3*x[2]-3*x[3]+x[10]-x[11] == 6)
# mass5 = (1*x[0]-1*x[1]+7*x[2]-7*x[3]+x[12]-x[13] == 4)
# mass6 = (5*x[0]-5*x[1]+8*x[2]-8*x[3]+x[14]-x[15] == 5)
# problem =op(z,[mass1,mass2,mass3,mass4 ,mass5,mass6])
# problem.solve(solver='glpk')
# problem.status
# print("Результат:")
# print(a.value, u.value, v.value)


# from scipy.optimize import linprog
# start = time.time()
# c = [0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1]
# A_ub = None
# b_ub = None
# A_eq = [[2,-2,5,-5,1,0,0,0,0,0,-1,0,0,0,0,0],
#         [9,-9,4,-4,0,1,0,0,0,0,0,-1,0,0,0,0],
#         [6,-6,1,-1,0,0,1,0,0,0,0,0,-1,0,0,0],
#         [8,-8,3,-3,0,0,0,1,0,0,0,0,0,-1,0,0],
#         [1,-1,7,-7,0,0,0,0,1,0,0,0,0,0,-1,0],
#         [5,-5,8,-8,0,0,0,0,0,1,0,0,0,0,0,-1]]
# b_eq = [7,9,1,6,4,5]



# c = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
# A_ub = [[0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,-1],
#         [0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,-1],
#         [0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,-1],
#         [0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,-1],
#         [0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,-1],
#         [0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,-1]]
# b_ub = [0,0,0,0,0,0,]
# A_eq = [[2,-2,5,-5,1,0,0,0,0,0,-1,0,0,0,0,0,0],
#         [9,-9,4,-4,0,1,0,0,0,0,0,-1,0,0,0,0,0],
#         [6,-6,1,-1,0,0,1,0,0,0,0,0,-1,0,0,0,0],
#         [8,-8,3,-3,0,0,0,1,0,0,0,0,0,-1,0,0,0],
#         [1,-1,7,-1,0,0,0,0,1,0,0,0,0,0,-1,0,0],
#         [5,-5,8,-8,0,0,0,0,0,1,0,0,0,0,0,-1,0]]
# b_eq = [7,9,1,6,4,5]

# x = linprog(c, A_ub, b_ub, A_eq, b_eq,method='revised simplex')
# x = linprog(c, A_ub, b_ub, A_eq, b_eq)
# stop = time.time()
# print ("Время :")
# print(stop - start)
# print(x.fun)
# print(list(map(lambda x: float('{:.2f}'.format(x)), x.x)))
