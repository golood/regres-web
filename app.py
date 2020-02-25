#!/usr/bin/python3
import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = '/home/golod/projects/regres-web/static'
ALLOWED_EXTENSIONS = set(['txt'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # return redirect(url_for('uploaded_file', filename=filename))

            data = []
            with open(UPLOAD_FOLDER + '/' + filename, 'r', encoding='utf-8') as f:
                for line in f:
                    data.append(list(map(float, line.split())))

            return render_template('main.html', data=data, dataLen=range(len(data[0])),
                                   dataRowLen=range(len(data)))

    return render_template('main.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

if __name__ == '__main__':
    # Will make the server available externally as well
    app.run()
