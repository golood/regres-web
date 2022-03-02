#!/usr/bin/python3
import datetime
import json
import time

from flask import Flask, render_template, request, redirect, url_for, session, Response

from server import config
from server.logger import logger
from server.main import WorkerTaskAsync, WorkerTask
from server.models import MenuTypes, ShowMatrixMode, Data, MethodDivMatrixType
from server.services import divisionService, workerService, predictService
from server.session import Session

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
log = logger.get_logger('server')

UPLOAD_FOLDER = config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = set(['txt'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.permanent_session_lifetime = datetime.timedelta(hours=3)


def allowed_file(filename):
    """
    Проверяет соответсвие расширений файлов к разрешённым.
    :param filename: имя загруженного файла.
    :return: True, если файл соовтетствует маске,
             False, если файл не соответствует маске.
    """

    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def is_object_session(name):
    """
    Проверяет наличие объекта в сессии.
    :param name: имя объекта.
    :return: True, если объект есть в данных сессии,
             False, в противном случае.
    """

    if name in session:
        return True

    return False


def get_object_session(name):
    """
    Получает объект из данных сессии.
    :param name: имя объекта.
    :return: объект.
    """

    return session[name]


def set_object_session(name, value):
    """
    Добавляет объект в данные сессии.
    :param name: имя объекта.
    :param value: объект.
    """

    session[name] = value


def get_session():
    """
    Получает кастомную сущность сессии. Если токен протух, то создает новый.
    Все токены протухаю в 4:00 +08 UTC.
    """

    if is_object_session('token'):
        s = Session.get_session(get_object_session('token'))
        set_object_session('token', s.token.body)
        return s
    return Session()


def save_session(_session: Session):
    set_object_session('token', _session.token.body)


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def internal_server_error(e):
    return render_template('errors/404.html'), 404


@app.route('/')
def main():
    """
    Главная страница.
    :return: шаблон с главной страницей.
    """

    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_active_menu(MenuTypes.MAIN)

    _session.meta_data = meta_data
    return render_template('main.html', meta_data=meta_data)


@app.route('/load')
def load_get():
    """
    Экран для загрузки и отображения файлов.
    :return: шаблон с меню загрузки и отображения данных загруженного файла.
    """

    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_active_menu(MenuTypes.LOAD)

    _session.meta_data = meta_data
    return render_template('load_file.html', meta_data=meta_data)


@app.route('/matrix')
def show_matrix():
    """
    Экран для отображения загруженной матрицы.
    :return: шаблон с загруженной матрицей.
    """

    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_active_menu(MenuTypes.DATA)

    meta_data.show_matrix_mode = ShowMatrixMode.LOAD

    _session.meta_data = meta_data
    return render_template('matrix.html', meta_data=meta_data)


@app.route('/workMatrix')
def get_work_matrix():
    """
    Экран для отображения рабочей матрицы.
    :return: шаблон с рабочей матрицей.
    """

    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_active_menu(MenuTypes.DATA)

    meta_data.show_matrix_mode = ShowMatrixMode.WORK

    _session.meta_data = meta_data
    return render_template('matrix.html', meta_data=meta_data)


@app.route('/editWorkMatrix')
def edit_work_matrix():
    """
    Экран для редактирования загруженной матрицы.
    :return: шаблон с рабочей матрицей.
    """

    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_active_menu(MenuTypes.DATA)

    meta_data.show_matrix_mode = ShowMatrixMode.EDIT

    _session.meta_data = meta_data
    return render_template('matrix.html', meta_data=meta_data)


@app.route('/div')
def div_matrix():
    """
    Экран деления матрицы.
    :return: шаблон с набором идентификаторов строк используемой матрицы.
    """

    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_active_menu(MenuTypes.DIV)
    _session.meta_data = meta_data

    bias = _session.bias
    bias.data = bias.get_data(_session.token.body)
    _session.bias = bias

    return render_template('div_matrix.html',
                           meta_data=meta_data,
                           bias=bias,
                           biasLen=range(1, len(bias.data) + 1) if bias.data is not None else [])


@app.route('/answer')
def answer():
    """
    Экран для отображения результатов вычислений.
    :return: шаблон с результатами вычисленений.
    """

    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_active_menu(MenuTypes.ANSWER)

    _session.meta_data = meta_data
    return render_template('answer.html', meta_data=meta_data)


# todo обновить логику.
@app.route('/biasEstimates', methods=['GET', 'POST'])
def bias_estimates():
    """
    Экран для отображения данных решения задачи поиска критерия смещения.
    :return: шаблон с результатами поиска критерия смещения.
    """
    return 'Страница временно не доступна...'

    # meta_data = MetaData(json.loads(get_object_session('meta_data')))
    # meta_data.set_active_menu(MenuTypes.BIAS)
    #
    # task_id = WorkerRepo.get_task_in_last_worker_by_user(meta_data.user_session_id)
    #
    # if task_id is None:
    #     return redirect(url_for('div_matrix'))
    #
    # filter_id = 0 if request.form.get('filter') is None else int(request.form.get('filter'))
    # sorting_id = 0 if request.form.get('sorting') is None else int(request.form.get('sorting'))
    #
    # result = ResultRepo.get_task_by_best_bias_estimates(task_id, filter_id, sorting_id)

    # return render_template('bias_estimates.html',
    #                        auto=True,
    #                        res=result,
    #                        resLen=range(len(result)),
    #                        meta_data=meta_data,
    #                        params={'filterId': filter_id,
    #                                'sortingId': sorting_id})


@app.route('/checkProgress', methods=['POST'])
def check_progress():
    """
    Проверяет завершение расчета оценки смещения.
    :return: возвращает статус и процент прогресса завершения вычислений.
    """

    _session = get_session()
    save_session(_session)

    count = _session.get_percent()

    meta_data = _session.meta_data
    return {'status': meta_data.is_done_bias_estimates, 'count': float('{:.2f}'.format(float(count)))}


@app.route('/form/set_params', methods=['POST'])
def form_set_params():
    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_params(request.form)

    _session.meta_data = meta_data
    return redirect(url_for('load_get'))


@app.route('/form/load_file', methods=['POST'])
def form_load_file():
    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data

    file = request.files['file']
    if file and allowed_file(file.filename):
        meta_data.set_file(file)

    _session.meta_data = meta_data
    return redirect(url_for('load_get'))


@app.route('/form/edit_work_matrix', methods=['POST'])
def form_edit_work_matrix():
    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.edit_work_matrix(request.form)

    _session.meta_data = meta_data
    return redirect(url_for('get_work_matrix'))


@app.route('/form/set_var_y', methods=['POST'])
def form_set_var_y():
    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data

    var_y = request.form['var_y']

    if var_y == "":
        log.warn('Dependent variable value (y) not set')
        return render_template('error.html',
                               e='Введите значение зависимой переменной!')
    elif int(var_y) > len(meta_data.get_work_data_len()):
        log.warn('Index value exceeds limit: {0} - {1}'
                 .format(var_y, meta_data.get_work_data_len))
        return render_template('error.html',
                               e='Значение индекса слишком большое!')
    elif int(var_y) < 0:
        log.warn('Index value cannot be negative: {0}'.format(var_y))
        return render_template('error.html',
                               e='Значение индекса не может быть отрицательным!')

    meta_data.set_var_y(var_y)

    _session.meta_data = meta_data
    return redirect(url_for('div_matrix'))


@app.route('/form/bias_filter', methods=['POST'])
def form_bias_filter():
    _session = get_session()
    save_session(_session)

    # meta_data = _session.meta_data

    bias = _session.bias
    bias.set_filters(request.form)
    _session.bias = bias
    # meta_data.set_bias_filter_and_sorting_types(request.form)

    # _session.meta_data = meta_data
    return redirect(url_for('div_matrix'))


@app.route('/form/calculation', methods=['POST'])
def form_calculation():
    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data

    meta_data.set_h(request.json)

    try:
        data = Data(meta_data)
        results = data.get_result()

        if meta_data.mco:
            mco_res = workerService.mco_api(meta_data)

            for item in results:
                if item[0] == 'МСО':
                    item[1][2].append(mco_res['answer'][1])

        meta_data.results = results

        _session.meta_data = meta_data
        return Response(status=200)
    except Exception as e:
        return Response(str(e), status=500)


@app.route('/form/calculation_auto_div', methods=['POST'])
def calculation_with_auto_div():
    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data

    var_y = request.form['var_y']

    if var_y == "":
        log.warn('Dependent variable value (y) not set')
        return render_template('error.html',
                               e='Введите значение зависимой переменной!')
    elif int(var_y) > len(meta_data.get_work_data_len()):
        log.warn('Index value exceeds limit: {0} - {1}'
                 .format(var_y, meta_data.get_work_data_len))
        return render_template('error.html',
                               e='Значение индекса слишком большое!')
    elif int(var_y) < 0:
        log.warn('Index value cannot be negative: {0}'.format(var_y))
        return render_template('error.html',
                               e='Значение индекса не может быть отрицательным!')

    meta_data.set_var_y(var_y)

    meta_data.h1, meta_data.h2 = divisionService.division(meta_data)

    try:
        data = Data(meta_data)
        results = data.get_result()

        if meta_data.mco:
            mco_res = workerService.mco_api(meta_data)

            for item in results:
                if item[0] == 'МСО':
                    item[1][2].append(mco_res['answer'][1])

        meta_data.results = results

        _session.meta_data = meta_data
        return redirect(url_for('answer'))
    except Exception as e:
        return Response(str(e), status=500)


@app.route('/form/calculation_predict', methods=['POST'])
def form_calculation_predict():
    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.range_value = int(request.form.get('range_value'))

    if meta_data.method_div_matrix_type == MethodDivMatrixType.HAND:
        task = WorkerTask(
            session=_session,
            name="calculation_predict",
            x=meta_data.x(),
            y=meta_data.y())
        task.start()

        _data = json.loads(_session.bias.get_max_bias(_session.token.body))
        meta_data.h1 = list(map(lambda x: x - 1, _data[4]))
        meta_data.h2 = list(map(lambda x: x - 1, _data[5]))
    else:
        meta_data.h1, meta_data.h2 = divisionService.division(meta_data)

    try:
        data = Data(meta_data)
        results = data.get_result()

        if meta_data.mco:
            mco_res = workerService.mco_api(meta_data)

            for item in results:
                if item[0] == 'МСО':
                    item[1][2].append(mco_res['answer'][1])
                else:
                    item[1][2].append(None)

        predictService.calculation_predict(results, meta_data)

        meta_data.results = results

        _session.meta_data = meta_data
        return redirect(url_for('answer'))
    except Exception as e:
        return Response(str(e), status=500)


@app.route('/form/calculation_bias_estimates', methods=['GET'])
def form_calculation_bias_estimates():
    _session = get_session()
    save_session(_session)

    bias = _session.bias
    bias.data = []
    bias.last_index_dataset = None
    _session.bias = bias

    meta_data = _session.meta_data
    task = WorkerTaskAsync(
        session=_session,
        name="biasEstimates",
        x=meta_data.x(),
        y=meta_data.y())

    try:
        task.start()
        time.sleep(1)
        meta_data.run_bias_estimates()
    except Exception as e:
        meta_data.stop_bias_estimates()
        log.error(e, exc_info=True, stack_info=True)

    _session.meta_data = meta_data
    return redirect(url_for('div_matrix'))


@app.route('/form/set_x', methods=['POST'])
def form_set_x():
    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data

    meta_data.start_x = int(request.form.get('start'))
    _session.meta_data = meta_data

    return redirect(url_for('answer'))


if __name__ == '__main__':
    if config.SPACE == 'dev':
        app.run(host='0.0.0.0', debug=True)
    else:
        from waitress import serve
        serve(app, host="0.0.0.0", port=5000)
