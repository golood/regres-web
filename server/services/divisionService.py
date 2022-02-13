from server.models import MetaData, MethodDivMatrixType
from server.main import Test


def _division_mnk(data: MetaData):
    test = Test(
        tasks=[True, False, False, False],
        x=data.x(),
        y=data.y())

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


def _division_mnm(meta_data: MetaData):
    test = Test(
        tasks=[False, True, False, False],
        x=meta_data.x(),
        y=meta_data.y())

    results = test.get_results()

    h1, h2 = [], []
    for index in range(len(results[0][1][1])):
        if results[0][1][1][index] == 0:
            h1.append(index)
        else:
            h2.append(index)

    return h1, h2


def division(meta_data: MetaData):
    if meta_data.method_div_matrix_type == MethodDivMatrixType.MNK:
        return _division_mnk(meta_data)
    elif meta_data.method_div_matrix_type == MethodDivMatrixType.MAO:
        return _division_mao(meta_data)
    elif meta_data.method_div_matrix_type == MethodDivMatrixType.MNM:
        return _division_mnm(meta_data)
