import eventlet
eventlet.monkey_patch()

import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-very-secret-key-change-me'

database_url = os.environ.get('DATABASE_URL')
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgres://', 'postgresql://', 1)
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'travel_plan.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

socketio = SocketIO(app, async_mode='eventlet')
db = SQLAlchemy(app)

# --- 데이터베이스 모델 정의 ---
class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_id = db.Column(db.String(50), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(50))
    content = db.Column(db.String(200))
    amount = db.Column(db.Float)

class InfoBox(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    box_id = db.Column(db.String(50), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)

# --- 웹 페이지 라우팅 ---
@app.route('/')
def index():
    plans = Plan.query.all()
    expenses_objects = Expense.query.all()
    infoboxes_objects = InfoBox.query.all()

    expenses_list = [{'id': e.id, 'category': e.category, 'date': e.date, 'content': e.content, 'amount': e.amount} for e in expenses_objects]
    infoboxes_list = [{'id': i.id, 'box_id': i.box_id, 'content': i.content} for i in infoboxes_objects]

    return render_template('index.html', plans=plans, expenses=expenses_list, infoboxes=infoboxes_list)

# --- 실시간 통신 (SocketIO) 이벤트 핸들러 ---
@socketio.on('connect')
def handle_connect():
    print('Client connected:', request.sid)

@socketio.on('update_plan')
def handle_plan_update(data):
    with app.app_context():
        plan = Plan.query.filter_by(day_id=data['dayId']).first()
        if plan: plan.content = data['content']
        else: db.session.add(Plan(day_id=data['dayId'], content=data['content']))
        db.session.commit()
    emit('plan_was_updated', data, broadcast=True, include_self=False)

@socketio.on('update_infobox')
def handle_infobox_update(data):
    with app.app_context():
        infobox = InfoBox.query.filter_by(box_id=data['boxId']).first()
        if infobox: infobox.content = data['content']
        else: db.session.add(InfoBox(box_id=data['boxId'], content=data['content']))
        db.session.commit()
    emit('infobox_was_updated', data, broadcast=True, include_self=False)

@socketio.on('add_expense')
def handle_add_expense(data):
    with app.app_context():
        new_expense = Expense(category=data['category'], date='', content='', amount=0)
        db.session.add(new_expense)
        db.session.commit()
        data['id'] = new_expense.id
    emit('expense_was_added', data, broadcast=True)
    
@socketio.on('update_expense')
def handle_update_expense(data):
    with app.app_context():
        expense = db.session.get(Expense, int(data['id']))
        if expense:
            expense.category = data['category']
            expense.date = data['date']
            expense.content = data['content']
            expense.amount = float(data['amount'] or 0)
            db.session.commit()
    emit('expense_was_updated', data, broadcast=True, include_self=False)

@socketio.on('delete_expense')
def handle_delete_expense(data):
    with app.app_context():
        expense = db.session.get(Expense, int(data['id']))
        if expense:
            db.session.delete(expense)
            db.session.commit()
    emit('expense_was_deleted', data, broadcast=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)