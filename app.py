#!/usr/bin/python3
import json
import os
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, send_from_directory, escape, session, Response
from werkzeug.utils import secure_filename
from server.main import Data, DataEncoder, Test, TestT
import server.utill as utill
from server.models import MetaData
from server import config
import datetime

app = Flask(__name__)
app.secret_key = config.secret_key

UPLOAD_FOLDER = config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = set(['txt'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.permanent_session_lifetime = datetime.timedelta(hours=3)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def getMetaData():
    if 'meta_data' in session:
        return MetaData(json.loads(session['meta_data']))
    else:
        meta_data = MetaData(None)

        meta_data.addSession(
            utill.generateSessionId(request.headers.environ['HTTP_USER_AGENT']
                                    + request.headers.environ['REMOTE_ADDR']),
            request.remote_addr)

        return meta_data

def redirect_to_main(f):
    @wraps(f)
    def decorator_function(*args, **kwargs):
        if 'meta_data' not in session:
            return redirect(url_for('main'))
        return f(*args, **kwargs)
    return decorator_function

def update_time_active(f):
    @wraps(f)
    def decorator_function(*args, **kwargs):
        meta_data = getMetaData()
        meta_data.updateTimeActiv()
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
    meta_data = getMetaData()

    session['meta_data'] = json.dumps(meta_data, cls=MetaData.DataEncoder)

    return render_template('main.html',
                           data=meta_data)

@app.route('/load', methods=['GET', 'POST'])
@redirect_to_main
@update_time_active
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            meta_data = getMetaData()
            filename = meta_data.addLoadFile(secure_filename(file.filename))
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            load_matrix = []
            with open(UPLOAD_FOLDER + '/' + filename, 'r', encoding='utf-8') as f:
                for line in f:
                    load_matrix.append(list(map(float, line.split())))


            meta_data.addLoadMatrix(load_matrix)
            meta_data.index_h1 = None
            meta_data.index_h2 = None

            session['meta_data'] = json.dumps(meta_data, cls=MetaData.DataEncoder)

            return render_template('load_file.html',
                                   data=load_matrix,
                                   dataLen=range(1, len(load_matrix[0])+1),
                                   dataRowLen=range(1, len(load_matrix)+1),
                                   meta_data=meta_data,
                                   verification=len(load_matrix) > len(load_matrix[0]))

    meta_data = MetaData(json.loads(session['meta_data']))

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

    session['meta_data'] = json.dumps(meta_data, cls=MetaData.DataEncoder)

    return render_template('load_file.html',
                            meta_data=meta_data)

@app.route('/matrix')
@redirect_to_main
@update_time_active
def show_matrix():
    meta_data = getMetaData()
    load_matrix = meta_data.getMetrix(meta_data.load_matrix_id)

    return render_template('matrix.html',
                            data=load_matrix,
                            dataLen=range(1, len(load_matrix[0]) + 1),
                            dataRowLen=range(1, len(load_matrix) + 1),
                            meta_data=meta_data)

@app.route('/uploads/<filename>')
@redirect_to_main
@update_time_active
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/key', methods=['POST'])
@redirect_to_main
@update_time_active
def getKey():
    var_y = request.form['var_y']
    meta_data = MetaData(json.loads(session['meta_data']))

    if var_y == "":
        return render_template('error.html', e='Введите значение зависимой переменной!')
    elif int(var_y) > meta_data.len_x_work_matrix:
        return render_template('error.html', e='Значение индекса слишком большое!')
    elif int(var_y) < 0:
        return render_template('error.html', e='Значение индекса не может быть отрицательным!')

    meta_data.set_y(int(var_y)-1)

    session['meta_data'] = json.dumps(meta_data, cls=MetaData.DataEncoder)

    return redirect(url_for('div_matrix'))

@app.route('/div')
@redirect_to_main
@update_time_active
def div_matrix():
    meta_data = MetaData(json.loads(session['meta_data']))

    return render_template('div_matrix.html',
                            xLen=range(1, meta_data.len_work_matrix + 1),
                            h1=utill.formatToInt(meta_data.getRow(meta_data.index_h1)),
                            h2=utill.formatToInt(meta_data.getRow(meta_data.index_h2)),
                            meta_data=meta_data,
                            verification=meta_data.len_work_matrix/2 > meta_data.len_x_work_matrix)

@app.route('/answer', methods=['POST'])
@redirect_to_main
@update_time_active
def answer():
    meta_data = MetaData(json.loads(session['meta_data']))

    h1_index = list(map(lambda x: int(x), request.json['h1']))
    h2_index = list(map(lambda x: int(x), request.json['h2']))

    meta_data.setH1H2(h1_index, h2_index)

    test = Test(
        tasks=meta_data.getCheckTask(),
        x=meta_data.getMetrix(meta_data.matrix_x_index),
        y=meta_data.getRow(meta_data.matrix_y_index),
        h1=meta_data.getRow(meta_data.index_h1),
        h2=meta_data.getRow(meta_data.index_h2))

    data = Data(None)
    data.results = test.getResaults()

    meta_data.answer = True
    session['meta_data'] = json.dumps(meta_data, cls=MetaData.DataEncoder)
    session['data'] = json.dumps(data, cls=DataEncoder)

    return Response(status=200)

@app.route('/answer', methods=['GET'])
@redirect_to_main
@update_time_active
def answer1():
    meta_data = MetaData(json.loads(session['meta_data']))
    data = Data(json.loads(session['data']))

    if meta_data.freeChlen:
        aLen = range(len(data.results[0][1][0]))
    else:
        aLen = range(1, len(data.results[0][1][0])+1)
    return render_template('answer.html',
                            data=data,
                            aLen=aLen,
                            epsLen=range(1, len(data.results[0][1][1])+1),
                            meta_data=meta_data)

@app.route('/auto')
@redirect_to_main
@update_time_active
def auto():
    meta_data = MetaData(json.loads(session['meta_data']))

    test = TestT(
        x=meta_data.getMetrix(meta_data.matrix_x_index),
        y=meta_data.getRow(meta_data.matrix_y_index))

    res = test.getResaults()

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

    return render_template('div_matrix.html',
                           xLen=range(1, meta_data.len_work_matrix + 1),
                           h1=utill.formatToInt(meta_data.getRow(meta_data.index_h1)),
                           h2=utill.formatToInt(meta_data.getRow(meta_data.index_h2)),
                           auto=True,
                           res=result,
                           resLen=range(1, len(res)+1),
                           meta_data=meta_data)

@app.route('/biasEstimates')
@redirect_to_main
@update_time_active
def bias_astimates():
    meta_data = MetaData(json.loads(session['meta_data']))

    test = TestT(
        x=meta_data.getMetrix(meta_data.matrix_x_index),
        y=meta_data.getRow(meta_data.matrix_y_index))

    res = test.getResaults()

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

    return render_template('bias_estimates.html',
                            auto=True,
                            res=result,
                            resLen=range(len(result)),
                            meta_data=meta_data)

if __name__ == '__main__':
    # Will make the server available externally as well
    app.run()
