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

    def get_result(self):
        a, u, v = [], [], []

        variables = self.problem.variables()
        index = 0
        while index < len(variables):
            if 'a' in variables[index].name:
                a.append(variables[index].varValue - variables[index + 1].varValue)
                index += 2
                continue
            if 'u' in variables[index].name:
                u.append(variables[index].varValue)
                index += 1
                continue
            if 'v' in variables[index].name:
                v.append(variables[index].varValue)
                index += 1
                continue
            if 'r' in variables[index].name:
                index += 1
                continue

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
# problem = pulp.LpProblem('0', pulp.LpMinimize)
#
# problem += u1+v1+u2+v2+u3+v3+u4+v4+u5+v5+u6+v6, 'Функция цели'
# problem += 2*a11-2*a12+5*a21-5*a22+u1-v1==7, '1'
# problem += 9*a11-9*a12+4*a21-4*a22+u2-v2==9, '2'
# problem += 6*a11-6*a12+1*a21-1*a22+u3-v3==1, '3'
# problem += 8*a11-8*a12+3*a21-3*a22+u4-v4==6, '4'
# problem += 1*a11-1*a12+7*a21-7*a22+u5-v5==4, '5'
# problem += 5*a11-5*a12+8*a21-8*a22+u6-v6==5, '6'
#
# problem.solve()
#
# for variable in problem.variables():
#     print (variable.name, "=", variable.varValue)
#
# problem = pulp.LpProblem('0', pulp.LpMinimize)
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
