from flask import Flask, request, jsonify, render_template, redirect, url_for
from dotenv import load_dotenv
import os
import logging
from flask_migrate import Migrate
from models import db, User, Log
from sqlalchemy import func
from datetime import datetime
import pytz

load_dotenv()

app = Flask(__name__)

DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_URL = os.getenv('DB_URL')

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_URL}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        result = []
        for user in users:
            result.append({
                'user_id': user.id,
                'name': user.name,
                'rollNo': user.rollNo,
                'macaddress': user.macaddress
            })
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        if not data or 'name' not in data or 'rollNo' not in data:
            return jsonify({'message': 'Missing required fields'}), 400

        existing_user = User.query.filter_by(rollNo=data['rollNo']).first()
        if existing_user:
            return jsonify({'message': 'User with this roll number already exists'}), 400

        new_user = User(name=data['name'], rollNo=data['rollNo'], macaddress=data['macaddress'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created', 'user': new_user.name}), 201
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/logs', methods=['POST'])
def create_log():
    try:
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'message': 'Missing required fields'}), 400

        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'message': 'User not found'}), 404

        new_log = Log(user_id=user.id, timestamp=datetime.now(pytz.timezone("Asia/Kolkata")))
        db.session.add(new_log)
        db.session.commit()
        return jsonify({'message': 'Log created', 'log_id': new_log.id}), 201
    except Exception as e:
        logger.error(f"Error creating log: {e}")
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        logs = Log.query.all()
        result = [{'log_id': log.id, 'user_name': log.user.name, 'timestamp': log.timestamp} for log in logs]
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return jsonify({'message': 'Internal Server Error'}), 500

# @app.route('/')
# def home():
#     return render_template('index.html')

@app.route('/create_user', methods=['POST','GET'])
def create_user_form():
    if request.method == 'POST':
        name = request.form['name']
        rollNo = request.form['rollNo']

        existing_user = User.query.filter_by(rollNo=rollNo).first()
        if existing_user:
            return render_template('create_user.html', error="User with this roll number already exists.")

        new_user = User(name=name, rollNo=rollNo)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('create_user.html')

@app.route('/')
def view_logs():
    logs = Log.query.join(User, Log.user_id == User.id).with_entities(
        User.name, User.rollNo, func.date(Log.timestamp).label("date"),
        func.min(func.time(Log.timestamp)).label("login_time"),
        func.max(func.time(Log.timestamp)).label("logout_time")
    ).group_by(User.id, func.date(Log.timestamp)).order_by(func.date(Log.timestamp).desc()).all()
    
    users = User.query.all()
    unique_dates = set(log.date for log in logs)
    grouped_logs = {}
    
    for date in sorted(unique_dates, reverse=True):
        records = []
        for user in users:
            user_logs = [log for log in logs if log.name == user.name and log.date == date]
            if user_logs:
                login_time = min(log.login_time for log in user_logs)
                logout_time = max(log.logout_time for log in user_logs)
                login_time = datetime.strptime(str(login_time), "%H:%M:%S").strftime("%I:%M %p")
                logout_time = datetime.strptime(str(logout_time), "%H:%M:%S").strftime("%I:%M %p")
                records.append({
                    'name': user.name,
                    'rollNo': user.rollNo,
                    'login_time': login_time,
                    'logout_time': logout_time
                })
            else:
                records.append({
                    'name': user.name,
                    'rollNo': user.rollNo,
                    'login_time': 'Absent',
                    'logout_time': 'Absent'
                })
        grouped_logs[date.strftime('%d/%m/%Y')] = records
    
    return render_template('index.html', dates=grouped_logs)


if __name__ == '__main__':
    app.run(debug=True)


