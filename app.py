#!/usr/bin/python3
import json
import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, escape, session, Response
from werkzeug.utils import secure_filename
from server.main import Data, DataEncoder, Test
import server.utill as utill

app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

UPLOAD_FOLDER = '/home/golod/projects/regres-web/static'
ALLOWED_EXTENSIONS = set(['txt'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/')
def main():
    data = None
    if (session['data']):
        data = Data(json.loads(session['data']))
    else:
      session['data'] = json.dumps(Data(None), cls=DataEncoder)

    return render_template('main.html', data=data)

@app.route('/load', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # return redirect(url_for('uploaded_file', filename=filename))

            load_matrix = []
            with open(UPLOAD_FOLDER + '/' + filename, 'r', encoding='utf-8') as f:
                for line in f:
                    load_matrix.append(list(map(float, line.split())))

            data = Data(json.loads(session['data']))
            data.loadMatrix = load_matrix
            session['data'] = json.dumps(data, cls=DataEncoder)

            return render_template('load_file.html', data=load_matrix, dataLen=range(len(load_matrix[0])),
                                   dataRowLen=range(len(load_matrix)))

    data = Data(json.loads(session['data']))

    if request.args:
      data.freeChlen = utill.get_value_checkbox(request.args['free_chlen'])

    session['data'] = json.dumps(data, cls=DataEncoder)

    return render_template('load_file.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

@app.route('/key', methods=['POST'])
def getKey():
    var_y = request.form['var_y']

    data = Data(json.loads(session['data']))

    data.set_y(int(var_y))

    session['data'] = json.dumps(data, cls=DataEncoder)

    return redirect(url_for('div_matrix'))

@app.route('/div')
def div_matrix():

    data = Data(json.loads(session['data']))

    return render_template('div_matrix.html', xLen=range(len(data.x)),
                           h1=data.h1_index, h2=data.h2_index)

@app.route('/answer', methods=['POST'])
def answer():
    data = Data(json.loads(session['data']))

    h1_index = list(map(lambda x: int(x), request.json['h1']))
    h2_index = list(map(lambda x: int(x), request.json['h2']))

    data.set_h1_h2(h1_index, h2_index)

    test = Test(data)

    data.results = test.getResaults()

    session['data'] = json.dumps(data, cls=DataEncoder)

    return Response(status=200)

@app.route('/answer', methods=['GET'])
def answer1():
    data = Data(json.loads(session['data']))

    return render_template('answer.html',
                           data=data,
                           aLen=range(len(data.results[0][0])),
                           epsLen=range(len(data.results[0][1])))

if __name__ == '__main__':
    # Will make the server available externally as well
    app.run()
