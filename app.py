#!/usr/bin/python3
import datetime
import json
import os
import time
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, Response
from werkzeug.utils import secure_filename

import server.utill as utill
from server import config
from server.db import ResultRepo, WorkerRepo
from server.logger import logger
from server.main import Data, DataEncoder, Test, WorkerTask
from server.models import MetaData

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


def get_meta_data():
    """
    Получает мета данные пользователя сессии.
    :return: мета данные пользователя сессии.
    """

    if is_object_session('meta_data'):
        return MetaData(json.loads(get_object_session('meta_data')))
    else:
        meta_data = MetaData(None)

        meta_data.add_session(
            utill.generate_session_id(request.headers.environ['HTTP_USER_AGENT']
                                      + request.headers.environ['REMOTE_ADDR']),
            request.remote_addr)

        set_object_session('meta_data', json.dumps(meta_data, cls=MetaData.DataEncoder))

        return meta_data


def redirect_to_main(f):
    """
    Перенаправление на домашнюю страницу, если для пользователя нет открытых
    сессий.
    """

    @wraps(f)
    def decorator_function(*args, **kwargs):
        if not is_object_session('meta_data'):
            return redirect(url_for('main'))
        return f(*args, **kwargs)

    return decorator_function


def update_time_active(f):
    """
    Обновляет время последней активности пользователя.
    """

    @wraps(f)
    def decorator_function(*args, **kwargs):
        meta_data = get_meta_data()
        meta_data.update_time_active()
        return f(*args, **kwargs)

    return decorator_function


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def internal_server_error(e):
    return render_template('errors/404.html'), 404


@app.route('/')
@update_time_active
def main():
    """
    Главная страница.
    :return: шаблон с главной страницей.
    """

    meta_data = get_meta_data()

    return render_template('main.html', data=meta_data)


@app.route('/load', methods=['GET', 'POST'])
@redirect_to_main
@update_time_active
def upload_file():
    """
    Экран для загрузки и отображения файлов.
    :return: шаблон с меню загрузки и отображения данных загруженного файла.
    """

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            meta_data = get_meta_data()
            filename = meta_data.add_load_file(secure_filename(file.filename))
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            load_matrix = []
            with open(UPLOAD_FOLDER + '/' + filename, 'r', encoding='utf-8') as f:
                for line in f:
                    load_matrix.append(list(map(float, line.split())))

                log.info('Save new file: {0}'.format(filename))

            meta_data.add_load_matrix(load_matrix)
            meta_data.index_h1 = None
            meta_data.index_h2 = None

            set_object_session('meta_data', json.dumps(meta_data, cls=MetaData.DataEncoder))

            return render_template('load_file.html',
                                   data=load_matrix,
                                   dataLen=range(1, len(load_matrix[0]) + 1),
                                   dataRowLen=range(1, len(load_matrix) + 1),
                                   meta_data=meta_data,
                                   verification=len(load_matrix) > len(load_matrix[0]))

    meta_data = MetaData(json.loads(get_object_session('meta_data')))

    if ('free_chlen' in request.args
            or 'check_MNK' in request.args
            or 'check_MNM' in request.args
            or 'check_MAO' in request.args
            or 'check_MCO' in request.args):
        if 'free_chlen' in request.args:
            meta_data.freeChlen = True
        else:
            meta_data.freeChlen = False
        if 'check_MNK' in request.args:
            meta_data.mnk = True
        else:
            meta_data.mnk = False
        if 'check_MNM' in request.args:
            meta_data.mnm = True
        else:
            meta_data.mnm = False
        if 'check_MAO' in request.args:
            meta_data.mao = True
        else:
            meta_data.mao = False
        if 'check_MCO' in request.args:
            meta_data.mco = True
        else:
            meta_data.mco = False

    set_object_session('meta_data', json.dumps(meta_data, cls=MetaData.DataEncoder))

    return render_template('load_file.html',
                           meta_data=meta_data)


@app.route('/matrix')
@redirect_to_main
@update_time_active
def show_matrix():
    """
    Экран для отображения загруженной матрицы.
    :return: шаблон с загруженной матрицей.
    """

    meta_data = get_meta_data()
    load_matrix = meta_data.get_matrix(meta_data.load_matrix_id)

    return render_template('matrix.html',
                           data=load_matrix,
                           dataLen=range(1, len(load_matrix[0]) + 1),
                           dataRowLen=range(1, len(load_matrix) + 1),
                           meta_data=meta_data,
                           load=True)


@app.route('/workMatrix')
@redirect_to_main
@update_time_active
def get_work_matrix():
    """
    Экран для отображения рабочей матрицы.
    :return: шаблон с рабочей матрицей.
    """

    meta_data = get_meta_data()
    work_matrix = meta_data.get_matrix(meta_data.work_matrix_id)

    return render_template('matrix.html',
                           data=work_matrix,
                           dataLen=range(1, len(work_matrix[0]) + 1),
                           dataRowLen=range(1, len(work_matrix) + 1),
                           meta_data=meta_data,
                           load=False)


@app.route('/editWorkMatrix', methods=['GET', 'POST'])
@redirect_to_main
@update_time_active
def edit_work_matrix():
    """
    Экран для редактирования загруженной матрицы.
    :return: шаблон с рабочей матрицей.
    """

    if request.method == 'GET':
        meta_data = get_meta_data()
        load_matrix = meta_data.get_matrix(meta_data.load_matrix_id)

        return render_template('matrix.html',
                               data=load_matrix,
                               dataLen=range(1, len(load_matrix[0]) + 1),
                               dataRowLen=range(1, len(load_matrix) + 1),
                               meta_data=meta_data,
                               load=True,
                               edit=True)
    else:
        meta_data = get_meta_data()
        load_matrix = meta_data.get_matrix(meta_data.load_matrix_id)

        indexes_work_matrix = []
        for item in range(len(load_matrix[0])):
            if 'check_{}'.format(item) in request.form:
                indexes_work_matrix.append(item)

        work_matrix = []
        for items in load_matrix:
            index = 0
            row = []
            for item in items:
                if index in indexes_work_matrix:
                    row.append(item)
                index += 1
            work_matrix.append(row)

        meta_data.add_work_matrix(work_matrix)

        set_object_session('meta_data', json.dumps(meta_data, cls=MetaData.DataEncoder))

        return redirect(url_for('get_work_matrix'))


@app.route('/key', methods=['POST'])
@redirect_to_main
@update_time_active
def get_key():
    """
    API для установки зависимой переменной.
    :return: перенаправляет на экран деления матрицы.
    """

    var_y = request.form['var_y']
    meta_data = MetaData(json.loads(get_object_session('meta_data')))

    if var_y == "":
        log.warn('Dependent variable value (y) not set')
        return render_template('error.html',
                               e='Введите значение зависимой переменной!')
    elif int(var_y) > meta_data.len_x_work_matrix:
        log.warn('Index value exceeds limit: {0} - {1}'
                 .format(var_y, meta_data.len_x_work_matrix))
        return render_template('error.html',
                               e='Значение индекса слишком большое!')
    elif int(var_y) < 0:
        log.warn('Index value cannot be negative: {0}'.format(var_y))
        return render_template('error.html',
                               e='Значение индекса не может быть '
                                 'отрицательным!')

    meta_data.set_y(int(var_y) - 1)

    set_object_session('meta_data', json.dumps(meta_data, cls=MetaData.DataEncoder))

    return redirect(url_for('div_matrix'))


@app.route('/div', methods=['GET', 'POST'])
@redirect_to_main
@update_time_active
def div_matrix():
    """
    Экран деления матрицы.
    :return: шаблон с набором идентификаторов строк используемой матрицы.
    """

    meta_data = MetaData(json.loads(get_object_session('meta_data')))

    task_id = WorkerRepo.get_task_in_last_worker_by_user(meta_data.user_session_id)

    filter_id = 0 if request.form.get('filter') is None else int(request.form.get('filter'))
    sorting_id = 0 if request.form.get('sorting') is None else int(request.form.get('sorting'))

    result = ResultRepo.get_task_by_best_bias_estimates(task_id, filter_id, sorting_id)

    is_auto = False
    if len(result) != 0:
        is_auto = True

    return render_template('div_matrix.html',
                           xLen=range(1, meta_data.len_work_matrix + 1),
                           h1=utill.format_to_int(meta_data.get_row(meta_data.index_h1)),
                           h2=utill.format_to_int(meta_data.get_row(meta_data.index_h2)),
                           meta_data=meta_data,
                           verification=meta_data.len_work_matrix / 2 > meta_data.len_x_work_matrix,
                           auto=is_auto,
                           res=result,
                           resLen=range(1, len(result) + 1),
                           params={'filterId': 0, 'sortingId': 0})


@app.route('/answer', methods=['POST'])
@redirect_to_main
@update_time_active
def answer():
    """
    API для начала вычислений.
    :return: статус об окончании вычислений.
    """
    meta_data = MetaData(json.loads(get_object_session('meta_data')))

    h1_index = list(map(lambda x: int(x), request.json['h1']))
    h2_index = list(map(lambda x: int(x), request.json['h2']))

    meta_data.set_h1_h2(h1_index, h2_index)

    try:
        test = Test(
            tasks=meta_data.get_check_task(),
            x=meta_data.get_matrix(meta_data.matrix_x_index),
            y=meta_data.get_row(meta_data.matrix_y_index),
            h1=meta_data.get_row(meta_data.index_h1),
            h2=meta_data.get_row(meta_data.index_h2))

        data = Data(None)
        data.results = test.get_results()

        meta_data.answer = True
        set_object_session('meta_data', json.dumps(meta_data, cls=MetaData.DataEncoder))
        set_object_session('data', json.dumps(data, cls=DataEncoder))

        return Response(status=200)
    except Exception as e:
        return Response(status=500)


@app.route('/answer', methods=['GET'])
@redirect_to_main
@update_time_active
def answer1():
    """
    Экран для отображения результатов вычислений.
    :return: шаблон с результатами вычисленений.
    """
    meta_data = MetaData(json.loads(get_object_session('meta_data')))
    data = Data(json.loads(get_object_session('data')))

    if meta_data.freeChlen:
        a_len = range(len(data.results[0][1][0]))
    else:
        a_len = range(1, len(data.results[0][1][0]) + 1)
    return render_template('answer.html',
                           data=data,
                           aLen=a_len,
                           epsLen=range(1, len(data.results[0][1][1]) + 1),
                           yLen=range(1, len(data.results[0][1][3]) + 1),
                           meta_data=meta_data)


@app.route('/auto')
@redirect_to_main
@update_time_active
def auto():
    """
    Экран для отображения данных решения задачи поиска критерия смещения.
    :return: шаблон с результатами поиска критерия смещения на экране
             раздерения матрицы.
    """

    meta_data = MetaData(json.loads(get_object_session('meta_data')))

    task = WorkerTask(
        user_id=meta_data.user_session_id,
        name="biasEstimates",
        x=meta_data.get_matrix(meta_data.matrix_x_index),
        y=meta_data.get_row(meta_data.matrix_y_index),
        is_free_chlen=str(meta_data.freeChlen))

    task.start()
    time.sleep(1)

    is_run = WorkerRepo.is_run(worker_id=task.id)

    return render_template('div_matrix.html',
                           isRun=is_run,
                           xLen=range(1, meta_data.len_work_matrix + 1),
                           h1=utill.format_to_int(
                               meta_data.get_row(meta_data.index_h1)),
                           h2=utill.format_to_int(
                               meta_data.get_row(meta_data.index_h2)),
                           meta_data=meta_data,
                           verification=meta_data.len_work_matrix / 2 > meta_data.len_x_work_matrix,
                           params={'filterId': 0, 'sortingId': 0})


@app.route('/biasEstimates', methods=['GET', 'POST'])
@redirect_to_main
@update_time_active
def bias_estimates():
    """
    Экран для отображения данных решения задачи поиска критерия смещения.
    :return: шаблон с результатами поиска критерия смещения.
    """

    meta_data = MetaData(json.loads(get_object_session('meta_data')))

    task_id = WorkerRepo.get_task_in_last_worker_by_user(meta_data.user_session_id)

    if task_id is None:
        return redirect(url_for('div_matrix'))

    filter_id = 0 if request.form.get('filter') is None else int(request.form.get('filter'))
    sorting_id = 0 if request.form.get('sorting') is None else int(request.form.get('sorting'))

    result = ResultRepo.get_task_by_best_bias_estimates(task_id, filter_id, sorting_id)

    return render_template('bias_estimates.html',
                           auto=True,
                           res=result,
                           resLen=range(len(result)),
                           meta_data=meta_data,
                           params={'filterId': filter_id,
                                   'sortingId': sorting_id})


@app.route('/checkProgress', methods=['POST'])
def check_progress():
    """
    Проверяет завершение расчета оценки смещения.
    :return: возвращает статус и процент прогресса завершения вычислений.
    """

    meta_data = MetaData(json.loads(get_object_session('meta_data')))

    task_id = WorkerRepo.get_task_in_last_worker_by_user(meta_data.user_session_id)
    status, count = WorkerRepo.is_done(task_id)

    return {'status': status, 'count': float('{:.2f}'.format(count))}


if __name__ == '__main__':
    if config.SPACE == 'dev':
        app.run(host='0.0.0.0', debug=True)
    else:
        from waitress import serve
        serve(app, host="0.0.0.0", port=5000)
