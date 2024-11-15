from flask import Flask, request, jsonify, render_template, redirect, url_for
from dotenv import load_dotenv
import os
import logging
from flask_migrate import Migrate
from models import db, User, Log
from sqlalchemy import func

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

        new_log = Log(user_id=user.id)
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
    logs = Log.query.all()
    dates = {}
    unique_dates = Log.query.with_entities(func.date(Log.timestamp)).distinct().all()

    for date in unique_dates:
        records = []
        date = date[0]
        total_users = User.query.count()

        for i in range(1, total_users+1):
            user = User.query.filter_by(id=i).first()
            if user:
                record_user = Log.query.filter_by(user_id=user.id).all()
                time_list = []
                for record in record_user:
                    if record.timestamp.date() == date:
                        time_list.append(record.timestamp)
                
                min_time = min(time_list) if time_list != [] else 0
                max_time = max(time_list) if time_list != [] else 0
                records.append({
                    'name': user.name,
                    'rollNo': user.rollNo,
                    'login_time': min_time.strftime('%I:%M:%S %p') if min_time != 0 else 'Absent',
                    'logout_time': max_time.strftime('%I:%M:%S %p') if max_time != 0 else 'Absent',
                })
        dates[date.strftime('%d/%m/%Y')] = records

    return render_template('index.html', dates=dates)

if __name__ == '__main__':
    app.run(debug=True)