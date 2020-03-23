#!/usr/bin/python3
import json
import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, escape, session, Response
from werkzeug.utils import secure_filename
from server.main import Data, DataEncoder, Test, TestT
import server.utill as utill
import datetime

app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

UPLOAD_FOLDER = '/home/golod/projects/regres-web/static'
ALLOWED_EXTENSIONS = set(['txt'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.permanent_session_lifetime = datetime.timedelta(hours=3)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/')
def main():
    data = None
    if ('data' in session):
        data = Data(json.loads(session['data']))
    else:
      session['data'] = json.dumps(Data(None), cls=DataEncoder)

    return render_template('main.html', data=data)

@app.route('/load', methods=['GET', 'POST'])
def upload_file():
    try:
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
            data.h2_index = None
            data.h1_index = None
            session['data'] = json.dumps(data, cls=DataEncoder)

            return render_template('load_file.html', data=load_matrix, dataLen=range(len(load_matrix[0])),
                                   dataRowLen=range(len(load_matrix)))

      data = Data(json.loads(session['data']))

      if request.args:
        data.freeChlen = utill.get_value_checkbox(request.args['free_chlen'])
      else:
          data.freeChlen = False

      session['data'] = json.dumps(data, cls=DataEncoder)

      return render_template('load_file.html')

    except Exception as e:
      return render_template('error.html', e=e)


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
  try:
    var_y = request.form['var_y']
    data = Data(json.loads(session['data']))

    if var_y == "":
        return render_template('error.html', e='Введите значение зависимой переменной!')
    elif int(var_y) > len(data.loadMatrix[0]):
        return render_template('error.html', e='Значение индекса слишком большое!')
    elif int(var_y) < 0:
        return render_template('error.html', e='Значение индекса не может быть отрицательным!')

    data.set_y(int(var_y))

    session['data'] = json.dumps(data, cls=DataEncoder)

    return redirect(url_for('div_matrix'))

  except Exception as e:
      return render_template('error.html', e=e)

@app.route('/div')
def div_matrix():
  try:
    data = Data(json.loads(session['data']))

    return render_template('div_matrix.html', xLen=range(len(data.x)),
                           h1=data.h1_index, h2=data.h2_index)
  except Exception as e:
      return render_template('error.html', e=e)

@app.route('/answer', methods=['POST'])
def answer():
  try:
    data = Data(json.loads(session['data']))

    h1_index = list(map(lambda x: int(x), request.json['h1']))
    h2_index = list(map(lambda x: int(x), request.json['h2']))

    data.set_h1_h2(h1_index, h2_index)

    test = Test(data)

    data.results = test.getResaults()

    session['data'] = json.dumps(data, cls=DataEncoder)

    return Response(status=200)
  except Exception as e:
      return render_template('error.html', e=e)

@app.route('/answer', methods=['GET'])
def answer1():
  try:
    data = Data(json.loads(session['data']))

    return render_template('answer.html',
                           data=data,
                           aLen=range(len(data.results[0][0])),
                           epsLen=range(len(data.results[0][1])))
  except Exception as e:
      return render_template('error.html', e=e)

@app.route('/auto')
def auto():
  try:
    data = Data(json.loads(session['data']))

    test = TestT(data)
    res = test.getResaults()

    result = []
    for item in res:
        line = []
        line.append(utill.format_numbers(item[0][0]))
        line.append(utill.format_numbers(item[0][1]))
        line.append(utill.format_number(item[0][2]))
        line.append(utill.format_number(item[1]))
        line.append(item[2])
        line.append(item[3])
        result.append(line)

    session['bias_estimates'] = result

    return render_template('div_matrix.html', xLen=range(len(data.x)),
                           h1=data.h1_index, h2=data.h2_index, auto=True, res=result,
                           resLen=range(len(res)))
  except Exception as e:
      return render_template('error.html', e=e)

@app.route('/biasEstimates')
def bias_astimates():
    try:
        if 'bias_estimates' in session:
            result = session['bias_estimates']
        else:
            data = Data(json.loads(session['data']))

            test = TestT(data)
            res = test.getResaults()

            result = []
            for item in res:
                line = []
                line.append(utill.format_numbers(item[0][0]))
                line.append(utill.format_numbers(item[0][1]))
                line.append(utill.format_number(item[0][2]))
                line.append(utill.format_number(item[1]))
                line.append(item[2])
                line.append(item[3])
                result.append(line)

            session['bias_estimates'] = result

        return render_template('bias_estimates.html', auto=True, res=result,
                               resLen=range(len(result)))
    except Exception as e:
        return render_template('error.html', e=e)

if __name__ == '__main__':
    # Will make the server available externally as well
    app.run()
