import os
from flask import Flask, request, redirect, url_for, render_template
from datetime import datetime, timezone
import redis
import pickle
import matplotlib.pyplot as plt

app = Flask(__name__)
app.config.from_object('config')
db = redis.StrictRedis(host='redis', port=6379, db=0)
temp_name = None
ALLOWED_EXTENSIONS = set(['png', 'jpg'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.form['choose'] == 'Write':
            return redirect( url_for('new_note') )
        if request.form['choose'] == 'Show':
            return redirect( url_for('show_all') )
    return render_template('index.html')


@app.route('/new_note/', methods=['GET', 'POST'])
def new_note():
    if request.method == 'POST':
        note_id = str(db.incr('id'))
        filename = None
        file = request.files['photo']
        if file and allowed_file(file.filename):
            filename = 'img_' + note_id + '.png'
            file.save(os.path.join('static', filename))
        db.set('note'+note_id, pickle.dumps(dict(
                                        time=datetime.strftime(datetime.now(tz=timezone.utc), '%d.%m.%y %H:%M:%S'),
                                        place=request.form['place'],
                                        temp=request.form['temp'],
                                        wind=request.form['wind'],
                                        fallout=request.form['fallout'],
                                        cloud=request.form['cloud'],
                                        phenomenon=request.form['phenomenon'],
                                        comment=request.form['comment'],
                                        photo=filename
                                        )))
        db.lpush('history', note_id)
        return redirect(url_for('index'))
    return render_template('form.html')


@app.route('/history')
def show_all():
    global temp_name
    notes = db.lrange('history', 0, -1)
    history = []
    temp_history = []
    time_history = []
    for id in notes:
        note = db.get('note'+str(int(id)))
        data = pickle.loads(note)
        for key in data.keys():
            if key != 'photo':
                if len(data[key]) == 0:
                    data[key] = '---'
        try:
            temperature = int(data['temp'])
            temp_history.append(temperature)
            time_history.append(datetime.strptime(data['time'], '%d.%m.%y %H:%M:%S'))
        except:
            pass
        history.append(data)
    if temp_name:
        os.remove('static/temp'+temp_name+'.png')
    if len(temp_history) != 0:
        temp_name = str(int(datetime.timestamp(datetime.now())))
        plt.plot(time_history[::-1], temp_history[::-1], 'ro-')
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.savefig('static/temp' + temp_name + '.png', bbox_inches='tight')
        picture_name = 'temp' + temp_name + '.png'
    else:
        picture_name = None
    return render_template('history.html', history=history, name_temp=picture_name)
