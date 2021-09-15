from server.models import MetaData, MethodDivMatrixType
from server.main import Test


def _division_mnk(data: MetaData):
    test = Test(
        tasks=[True, False, False, False],
        x=data.get_matrix(data.matrix_x_index),
        y=data.get_row(data.matrix_y_index))

    results = test.get_results()

    h1, h2 = [], []
    for index in range(len(results[0][1][1])):
        if (abs(results[0][1][1][index]) / results[0][1][3][index]) > results[0][1][2][0] + data.delta:
            h2.append(index)
        else:
            h1.append(index)

    return h1, h2


def _division_mao(data: MetaData):
    pass


def _division_mnm(data: MetaData):
    test = Test(
        tasks=[False, True, False, False],
        x=data.get_matrix(data.matrix_x_index),
        y=data.get_row(data.matrix_y_index))

    results = test.get_results()

    h1, h2 = [], []
    for index in range(len(results[0][1][1])):
        if results[0][1][1][index] == 0:
            h1.append(index)
        else:
            h2.append(index)

    return h1, h2


def division(data: MetaData):
    if data.method_div_matrix_type == MethodDivMatrixType.MNK.value:
        return _division_mnk(data)
    elif data.method_div_matrix_type == MethodDivMatrixType.MAO.value:
        return _division_mao(data)
    elif data.method_div_matrix_type == MethodDivMatrixType.MNM.value:
        return _division_mnm(data)
