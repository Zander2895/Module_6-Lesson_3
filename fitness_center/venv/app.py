from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.exc import IntegrityError
from marshmallow import validates, ValidationError
import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:your_password@localhost/fitness_center_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and Marshmallow
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Define models
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

class WorkoutSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    member = db.relationship('Member', backref=db.backref('workout_sessions', lazy=True))

# Define schemas
class MemberSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Member

    @validates('email')
    def validate_email(self, value):
        if not value or '@' not in value:
            raise ValidationError("Invalid email address")

class WorkoutSessionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = WorkoutSession

# Initialize schemas
member_schema = MemberSchema()
members_schema = MemberSchema(many=True)
workout_session_schema = WorkoutSessionSchema()
workout_sessions_schema = WorkoutSessionSchema(many=True)

# Create database tables
@app.before_first_request
def create_tables():
    db.create_all()

# Member routes
@app.route('/members', methods=['POST'])
def add_member():
    try:
        data = request.get_json()
        errors = member_schema.validate(data)
        if errors:
            return jsonify(errors), 400

        new_member = member_schema.load(data)
        db.session.add(new_member)
        db.session.commit()
        return member_schema.jsonify(new_member), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Email already exists'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/members/<int:id>', methods=['GET'])
def get_member(id):
    try:
        member = Member.query.get_or_404(id)
        return member_schema.jsonify(member)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/members/<int:id>', methods=['PUT'])
def update_member(id):
    try:
        member = Member.query.get_or_404(id)
        data = request.get_json()
        errors = member_schema.validate(data)
        if errors:
            return jsonify(errors), 400

        member.name = data['name']
        member.email = data['email']
        db.session.commit()
        return member_schema.jsonify(member)
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Email already exists'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/members/<int:id>', methods=['DELETE'])
def delete_member(id):
    try:
        member = Member.query.get_or_404(id)
        db.session.delete(member)
        db.session.commit()
        return jsonify({'message': 'Member deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Workout session routes
@app.route('/workout_sessions', methods=['POST'])
def add_workout_session():
    try:
        data = request.get_json()
        if not data.get('date') or not data.get('duration') or not data.get('member_id'):
            return jsonify({'error': 'Date, duration, and member_id are required'}), 400

        data['date'] = datetime.datetime.fromisoformat(data['date'])
        new_session = workout_session_schema.load(data)
        db.session.add(new_session)
        db.session.commit()
        return workout_session_schema.jsonify(new_session), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/workout_sessions/<int:id>', methods=['GET'])
def get_workout_session(id):
    try:
        session = WorkoutSession.query.get_or_404(id)
        return workout_session_schema.jsonify(session)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/workout_sessions/<int:id>', methods=['PUT'])
def update_workout_session(id):
    try:
        session = WorkoutSession.query.get_or_404(id)
        data = request.get_json()
        if 'date' in data:
            data['date'] = datetime.datetime.fromisoformat(data['date'])

        updated_session = workout_session_schema.load(data, instance=session, partial=True)
        db.session.commit()
        return workout_session_schema.jsonify(updated_session)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/members/<int:id>/workout_sessions', methods=['GET'])
def get_member_workout_sessions(id):
    try:
        member = Member.query.get_or_404(id)
        sessions = WorkoutSession.query.filter_by(member_id=id).all()
        return workout_sessions_schema.jsonify(sessions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
