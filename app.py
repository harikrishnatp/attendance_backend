from flask import Flask, request, jsonify
import logging
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from models import db, User, Log

load_dotenv()

app = Flask(__name__)

DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_URL = os.getenv('DB_URL')

# Set the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_URL}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        if not data or 'name' not in data or 'rollNo' not in data:
            return jsonify({'message': 'Missing required fields'}), 400

        existing_user = User.query.filter_by(rollNo=data['rollNo']).first()
        if existing_user:
            return jsonify({'message': 'User with this roll number already exists'}), 400

        new_user = User(name=data['name'], rollNo=data['rollNo'])
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

        user_id = data['user_id']
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404

        new_log = Log(user_id=user_id)
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
        result = []
        for log in logs:
            result.append({
                'log_id': log.id,
                'user_name': log.user.name,
                'timestamp': log.timestamp
            })
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return jsonify({'message': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
