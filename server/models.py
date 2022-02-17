#!/usr/bin/python3
import enum
import json

import redis

from regres.regressionAPI import Task
from server.config import REDIS_HOST, REDIS_PORT
from server.logger import logger

log = logger.get_logger('server')


class MenuTypes(enum.Enum):
    MAIN = 'MAIN'
    LOAD = 'LOAD'
    DATA = 'DATA'
    DIV = 'DIV'
    ANSWER = 'ANSWER'
    BIAS = 'BIAS'


class MethodDivMatrixType(str, enum.Enum):
    HAND = 'hand'
    MNK = 'mnk'
    MNM = 'mnm'
    MAO = 'mao'
    NONE = 'None'

    @staticmethod
    def build(value):
        if not value:
            return MethodDivMatrixType.NONE
        return MethodDivMatrixType(value)


class CalculationMode(str, enum.Enum):
    PREDICT = 'PREDICT'  # прогнозирование
    STANDARD = 'STANDARD'

    @staticmethod
    def build(value):
        if not value:
            return CalculationMode.STANDARD
        return CalculationMode(value)


class ShowMatrixMode(str, enum.Enum):
    LOAD = 'LOAD'
    WORK = 'WORK'
    EDIT = 'EDIT'

    @staticmethod
    def build(value):
        if not value:
            return ShowMatrixMode.LOAD
        return ShowMatrixMode(value)


class MetaData:
    """
    Класс для хранения мета данных пользователя.
    Используется для представления данных в барузере.
    """

    menu_active_main: bool
    menu_active_load: bool
    menu_active_data: bool
    menu_active_div: bool
    menu_active_answer: bool
    menu_active_bias: bool

    menu_lock_load: bool
    menu_lock_data: bool
    menu_lock_div: bool
    menu_lock_answer: bool
    menu_lock_bias: bool

    mode: CalculationMode
    show_matrix_mode: ShowMatrixMode

    range_value: int

    mnk: bool
    mnm: bool
    mao: bool
    mco: bool

    method_div_matrix_type: MethodDivMatrixType

    load_data: list
    work_data: list

    bias_filter: int
    bias_sorting: int

    h1: list
    h2: list

    index_y: int

    results: list

    is_run_background_task: bool
    is_run_bias_estimates: bool
    is_done_bias_estimates: bool

    def __init__(self, data=None):
        self.menu_active_main = MetaData.get_value_bool(data, 'menu_active_main')
        self.menu_active_load = MetaData.get_value_bool(data, 'menu_active_load')
        self.menu_active_data = MetaData.get_value_bool(data, 'menu_active_data')
        self.menu_active_div = MetaData.get_value_bool(data, 'menu_active_div')
        self.menu_active_answer = MetaData.get_value_bool(data, 'menu_active_answer')
        self.menu_active_bias = MetaData.get_value_bool(data, 'menu_active_bias')

        self.menu_lock_load = MetaData.get_value_bool(data, 'menu_lock_load')
        self.menu_lock_data = MetaData.get_value_bool(data, 'menu_lock_data')
        self.menu_lock_div = MetaData.get_value_bool(data, 'menu_lock_div')
        self.menu_lock_answer = MetaData.get_value_bool(data, 'menu_lock_answer')
        self.menu_lock_bias = MetaData.get_value_bool(data, 'menu_lock_bias')

        self.mode = CalculationMode.build(
            MetaData.get_value(data, 'mode'))
        self.show_matrix_mode = ShowMatrixMode.build(
            MetaData.get_value(data, 'show_matrix_mode'))

        self.range_value = MetaData.get_value(data, 'range_value')

        self.session_id = MetaData.get_value(data, 'session_id')
        self.user_session_id = MetaData.get_value(data, 'user_session_id')

        self.method_div_matrix_type = MethodDivMatrixType.build(
            MetaData.get_value(data, 'method_div_matrix_type'))
        self.delta = MetaData.get_value(data, 'delta')

        self.mnk = MetaData.get_value_bool(data, 'mnk')
        self.mnm = MetaData.get_value_bool(data, 'mnm')
        self.mao = MetaData.get_value_bool(data, 'mao')
        self.mco = MetaData.get_value_bool(data, 'mco')

        self.freeChlen = MetaData.get_value_bool(data, 'freeChlen')

        self.load_data = MetaData.get_value(data, 'load_data')
        self.work_data = MetaData.get_value(data, 'work_data')

        self.bias_filter = MetaData.get_value(data, 'bias_filter')
        self.bias_sorting = MetaData.get_value(data, 'bias_sorting')

        self.h1 = MetaData.get_value(data, 'h1')
        self.h2 = MetaData.get_value(data, 'h2')

        self.results = MetaData.get_value(data, 'results')

        self.is_run_background_task = MetaData.get_value_bool(data, 'is_run_background_task')
        self.is_run_bias_estimates = MetaData.get_value_bool(data, 'is_run_bias_estimates')
        self.is_done_bias_estimates = MetaData.get_value_bool(data, 'is_done_bias_estimates')

        self.file_id = MetaData.get_value(data, 'file_id')
        self.load_matrix_id = MetaData.get_value(data, 'load_matrix_id')
        self.work_matrix_id = MetaData.get_value(data, 'work_matrix_id')

        self.len_x_load_matrix = MetaData.get_value(data, 'len_x_load_matrix')
        self.len_load_matrix = MetaData.get_value(data, 'len_load_matrix')
        self.len_x_work_matrix = MetaData.get_value(data, 'len_x_work_matrix')
        self.len_work_matrix = MetaData.get_value(data, 'len_work_matrix')

        self.index_y = MetaData.get_value(data, 'index_y')

        self.matrix_y_index = MetaData.get_value(data, 'matrix_y_index')
        self.matrix_x_index = MetaData.get_value(data, 'matrix_x_index')

        self.index_h1 = MetaData.get_value(data, 'index_h1')
        self.index_h2 = MetaData.get_value(data, 'index_h2')

        self.answer = MetaData.get_value_bool(data, 'answer')

    @staticmethod
    def get_value(data, key):
        try:
            return data[key]
        except KeyError:
            return None
        except TypeError:
            return None

    @staticmethod
    def get_value_bool(data, key):
        try:
            return data[key]
        except KeyError:
            return False
        except TypeError:
            return False

    def x_predict(self) -> list:
        x = []
        i = 0
        for item in self.work_data:

            if i < self.range_value:
                i += 1
                continue

            line = [] if not self.freeChlen else [1]
            for index in range(len(item)):
                if index != self.index_y:
                    line.append(item[index])
            x.append(line)
            i += 1
        return x

    def x(self) -> list:
        x = []
        if self.mode == CalculationMode.STANDARD:
            for item in self.work_data:
                line = [] if not self.freeChlen else [1]
                for index in range(len(item)):
                    if index != self.index_y:
                        line.append(item[index])
                x.append(line)
        elif self.mode == CalculationMode.PREDICT:
            i = 0
            for item in self.work_data:

                if i == self.range_value:
                    return x

                line = [] if not self.freeChlen else [1]
                for index in range(len(item)):
                    if index != self.index_y:
                        line.append(item[index])
                x.append(line)
                i += 1

        return x

    def y_all(self):
        y = []
        for item in self.work_data:
            for index in range(len(item)):
                if index == self.index_y:
                    y.append(item[index])
                    break
        return y

    def y_predict(self):
        y = []
        i = 0
        for item in self.work_data:

            if i < self.range_value:
                i += 1
                continue

            for index in range(len(item)):
                if index == self.index_y:
                    y.append(item[index])
                    i += 1
                    break
        return y

    def y(self) -> list:
        y = []
        if self.mode == CalculationMode.STANDARD:
            for item in self.work_data:
                for index in range(len(item)):
                    if index == self.index_y:
                        y.append(item[index])
                        break
            return y
        elif self.mode == CalculationMode.PREDICT:
            i = 0
            for item in self.work_data:

                if i == self.range_value:
                    return y

                for index in range(len(item)):
                    if index == self.index_y:
                        y.append(item[index])
                        i += 1
                        break
            return y

    def get_load_data_len(self) -> list:
        """
        Получает массив индексов столбцов загруженной матрицы.
        Значения в массиве начинается с 1.
        """
        return list(map(int, range(1, len(self.load_data[0]) + 1)))

    def get_load_data_rows_len(self) -> list:
        """
        Получает массив индексов строк загруженной матрицы.
        Значения в массиве начинается с 1.
        """
        return list(map(int, range(1, len(self.load_data) + 1)))

    def get_work_data_len(self) -> list:
        """
        Получает массив индексов столбцов рабочей матрицы.
        Значения в массиве начинается с 1.
        """
        return list(map(int, range(1, len(self.work_data[0]) + 1)))

    def get_work_data_rows_len(self) -> list:
        """
        Получает массив индексов строк рабочей матрицы.
        Значения в массиве начинается с 1.
        """
        return list(map(int, range(1, len(self.work_data) + 1)))

    def len_work_data(self):
        return len(self.work_data)

    def get_alfa_len(self):
        """
        Получает массив индексов альф.
        """
        if self.freeChlen:
            return list(map(int, range(len(self.results[0][1][0]))))
        else:
            return list(map(int, range(1, len(self.results[0][1][0]) + 1)))

    def get_epselon_len(self):
        return list(map(int, range(1, len(self.results[0][1][1]) + 1)))

    def get_selected_methods(self):
        """
        Получает выбранные методы решения задачи ЛП.
        :return: массив с выбранными методами решения задачи.
        """

        return [self.mnk, self.mnm, self.mao, self.mco]

    def run_bias_estimates(self):
        self.is_run_background_task = True
        self.is_run_bias_estimates = True
        self.is_done_bias_estimates = False

    def done_bias_estimates(self):
        self.is_run_background_task = False
        self.is_run_bias_estimates = False
        self.is_done_bias_estimates = True

    def stop_bias_estimates(self):
        self.is_run_background_task = False
        self.is_run_bias_estimates = False
        self.is_done_bias_estimates = False

    def set_lock_menu(self):
        self.menu_lock_load = True
        self.menu_lock_data = True
        self.menu_lock_div = True
        self.menu_lock_answer = True
        self.menu_lock_bias = True

        if self._is_select_method():
            self.menu_lock_load = False
        if self.load_data:
            self.menu_lock_data = False
        if self.index_y is not None or self.index_h1 or self.index_h2:
            self.menu_lock_div = False
        if self.answer:
            self.menu_lock_answer = False
        if self.matrix_y_index is not None:
            self.menu_lock_bias = False

    def set_active_menu(self, menu_type: MenuTypes):
        self._drop_active_menu()
        self.set_lock_menu()

        if menu_type == MenuTypes.MAIN:
            self.menu_active_main = True
        elif menu_type == MenuTypes.LOAD:
            self.menu_active_load = True
        elif menu_type == MenuTypes.DATA:
            self.menu_active_data = True
        elif menu_type == MenuTypes.DIV:
            self.menu_active_div = True
        elif menu_type == MenuTypes.ANSWER:
            self.menu_active_answer = True
        elif menu_type == MenuTypes.BIAS:
            self.menu_active_bias = True

    def set_params(self, form):
        self.freeChlen = True if self.get_value(form, 'free_chlen') else False
        self.mnk = True if self.get_value(form, 'check_MNK') else False
        self.mnm = True if self.get_value(form, 'check_MNM') else False
        self.mao = True if self.get_value(form, 'check_MAO') else False
        self.mco = True if self.get_value(form, 'check_MCO') else False
        self.method_div_matrix_type = MethodDivMatrixType.build(self.get_value(form, 'method'))
        self.delta = float(self.get_value(form, 'delta')) if self.get_value(form, 'delta') else 0
        self.mode = CalculationMode.build(self.get_value(form, 'mode'))

    def set_file(self, file):
        _list = []
        for line in file.stream.readlines():
            _list.append(list(map(float, line.decode('utf-8').split())))
        file.close()
        self.load_data = _list
        self.work_data = _list
        del _list

        # self.add_load_matrix(load_matrix)
        # meta_data.index_h1 = None
        # meta_data.index_h2 = None

    def set_var_y(self, var_y):
        self.index_y = int(var_y) - 1

    def edit_work_matrix(self, form):
        indexes_work_matrix = self._read_indexes_work_matrix(form)

        work_matrix = []
        for items in self.load_data:
            index = 0
            row = []
            for item in items:
                if index in indexes_work_matrix:
                    row.append(item)
                index += 1
            work_matrix.append(row)

        self.work_data = work_matrix
        del work_matrix

    def set_h(self, _json):
        self.h1 = list(map(lambda x: int(x), _json['h1']))
        self.h2 = list(map(lambda x: int(x), _json['h2']))

    def verification_load_data(self):
        return len(self.load_data) > len(self.load_data[0])

    def verification_h(self):
        return len(self.work_data) / 2 > len(self.work_data[0])

    def _is_select_method(self):
        return self.mnk or self.mnm or self.mao or self.mco

    def _drop_active_menu(self):
        self.menu_active_main = False
        self.menu_active_load = False
        self.menu_active_data = False
        self.menu_active_div = False
        self.menu_active_answer = False
        self.menu_active_bias = False

    def _read_indexes_work_matrix(self, form):
        indexes_work_matrix = []
        for item in range(len(self.load_data[0])):
            if 'check_{}'.format(item) in form:
                indexes_work_matrix.append(item)
        return indexes_work_matrix

    def __eq__(self, other):
        return (isinstance(other, MetaData) and
                self.session_id == other.session_id and
                self.user_session_id == other.user_session_id and
                self.mnk == other.mnk and
                self.mnm == other.mnm and
                self.mao == other.mao and
                self.mco == other.mco and
                self.method_div_matrix_type == other.method_div_matrix_type and
                self.delta == other.delta and
                self.freeChlen == other.freeChlen and
                self.file_id == other.file_id and
                self.load_matrix_id == other.load_matrix_id and
                self.work_matrix_id == other.work_matrix_id and
                self.len_x_load_matrix == other.len_x_load_matrix and
                self.len_load_matrix == other.len_load_matrix and
                self.len_x_work_matrix == other.len_x_work_matrix and
                self.len_work_matrix == other.len_work_matrix and
                self.index_y == other.index_y and
                self.matrix_y_index == other.matrix_y_index and
                self.matrix_x_index == other.matrix_x_index and
                self.index_h1 == other.index_h1 and
                self.index_h2 == other.index_h2 and
                self.answer == other.answer)

    class DataEncoder(json.JSONEncoder):
        """
        Класс кодирует модель Data в JSON формат.
        """
        def default(self, obj):
            if isinstance(obj, MetaData):
                return obj.__dict__
            return json.JSONEncoder.default(self, obj)


class TableFilter(str, enum.Enum):
    TEN = 'TEN'
    FIFTY = 'FIFTY'
    ONE_HUNDRED = 'ONE_HUNDRED'
    ONE_THOUSAND = 'ONE_THOUSAND'

    @staticmethod
    def build(value):
        if not value:
            return TableFilter.TEN
        return TableFilter(value)


class TableSorting(str, enum.Enum):
    E_min = 'E_min'
    E_max = 'E_max'
    F_min = 'F_min'
    F_max = 'F_max'

    @staticmethod
    def build(value):
        if not value:
            return TableSorting.F_max
        return TableSorting(value)


class BiasEstimate:
    """
    Сущность набора оценок критерия смещения.
    Вычисляется путем перебора всех возможных комбинация разбиения подматриц N1, N2.
    """

    """
    Формат данных:
        alfa: list
        eps: list
        E: float
        Оценка критерия смещения: float
        N1: list
        N2: list
    """
    data: list
    filter: TableFilter
    sorting: TableSorting

    last_index_dataset: int

    def __init__(self, data=None):
        if data is not None:
            self.filter = TableFilter.build(BiasEstimate.get_value(data, 'filter'))
            self.sorting = TableSorting.build(BiasEstimate.get_value(data, 'sorting'))
            self.last_index_dataset = BiasEstimate.get_value(data, 'last_index_dataset')
            self.data = BiasEstimate.get_value(data, 'data')
        else:
            self.last_index_dataset = None
            self.filter = TableFilter.build(None)
            self.sorting = TableSorting.build(None)
            self.data = []

    def get_len_data_indexes(self):
        if self.data is None:
            self.data = []
        return list(map(int, range(1, len(self.data) + 1)))

    def set_data(self):
        return self.data

    def get_data(self, token):
        if self.last_index_dataset is None:
            return None

        data = []
        r = self._get_redis()

        for index in range(self.last_index_dataset):
            _data = json.loads(r.get(f'{token}_bias_{index}'))

            for item in _data:
                data.append(item)

            if self.sorting == TableSorting.E_max:
                data = sorted(data, key=lambda x: x[2], reverse=True)
            elif self.sorting == TableSorting.E_min:
                data = sorted(data, key=lambda x: x[2])
            elif self.sorting == TableSorting.F_max:
                data = sorted(data, key=lambda x: x[3], reverse=True)
            elif self.sorting == TableSorting.F_min:
                data = sorted(data, key=lambda x: x[3])

            if self.filter == TableFilter.TEN:
                data = data[:10]
            elif self.filter == TableFilter.FIFTY:
                data = data[:50]
            elif self.filter == TableFilter.ONE_HUNDRED:
                data = data[:100]
            elif self.filter == TableFilter.ONE_THOUSAND:
                data = data[:1000]

        return data

    def set_filters(self, form):
        self.filter = form.get('filter') if form.get('filter') is not None else TableFilter.TEN
        self.sorting = form.get('sorting') if form.get('sorting') is not None else TableSorting.F_max

    def get_max_bias(self, token):
        r = self._get_redis()

        return r.get(f'{token}_max_bias')

    @staticmethod
    def get_value(data, key):
        try:
            return data[key]
        except KeyError:
            return None
        except TypeError:
            return None

    @staticmethod
    def get_value_bool(data, key):
        try:
            return data[key]
        except KeyError:
            return False
        except TypeError:
            return False

    @staticmethod
    def _get_redis() -> redis.Redis:
        return redis.Redis(decode_responses=True, host=REDIS_HOST, port=REDIS_PORT)

    class DataEncoder(json.JSONEncoder):
        """
        Класс кодирует модель BiasEstimate в JSON формат.
        """
        def default(self, obj):
            if isinstance(obj, BiasEstimate):
                return obj.__dict__
            return json.JSONEncoder.default(self, obj)


class Data:
    """
    Подготовка данных к вычислениям.
    """

    task: Task

    def __init__(self, meta_data: MetaData):
        self.task = Task(
            tasks=meta_data.get_selected_methods(),
            x=meta_data.x(),
            y=meta_data.y(),
            h1=meta_data.h1,
            h2=meta_data.h2)
        self.task.run()

    def get_result(self):
        return self.task.get_results()
