from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_mail import Mail, Message
import os

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///air_quality.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Email Configuration (Update with valid credentials)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'priyapriyanka78922@gmail.com'  # Change this
app.config['MAIL_PASSWORD'] = 'hiwysxssrnlywjzo'  # Use App Password (See below)
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'  # Default sender
mail = Mail(app)

# Report Model
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    image_url = db.Column(db.String(300), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    points = db.Column(db.Integer, default=0)

# Initialize Database
with app.app_context():
    db.create_all()

# API to Submit a Report
@app.route('/report', methods=['POST'])
def report():
    try:
        data = request.form
        user_id = int(data.get('user_id', 1))  # Default user_id=1 if not provided

        # Check if the user exists, if not create one
        user = User.query.get(user_id)
        if not user:
            user = User(id=user_id, username=f"User{user_id}", points=0)
            db.session.add(user)
            db.session.commit()

        # Create new report
        new_report = Report(
            location=data['location'],
            description=data['description'],
            image_url=data.get('image_url', ""),
            user_id=user_id
        )
        db.session.add(new_report)

        # Reward System: Increase user points
        user.points += 10  # Reward 10 points per report
        db.session.commit()

        # Send Automatic Report to Government
        send_email_to_government(data['location'], data['description'])

        return jsonify({"message": "Report submitted successfully!", "points": user.points})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API to Get User Dashboard (Username & Points)
@app.route('/user-dashboard/<int:user_id>', methods=['GET'])
def user_dashboard(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        return jsonify({"username": user.username, "points": user.points})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Function to Send Email to Government (Governor)
def send_email_to_government(location, description):
    try:
        msg = Message(
            "New Pollution Report",
            recipients=["www.pranavi123@gmail.com"]  # Update the recipient email
        )
        msg.body = f"Location: {location}\nDetails: {description}"
        mail.send(msg)
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Error sending email: {e}")

# Helper Function: AQI Status
def aqi_status(aqi):
    if aqi <= 50:
        return "Good 🟢 - Air quality is excellent!"
    elif 51 <= aqi <= 100:
        return "Moderate 🟡 - Air quality is acceptable, but some pollutants may be a concern for sensitive individuals."
    elif 101 <= aqi <= 150:
        return "Unhealthy for Sensitive Groups 🟠 - People with respiratory conditions should be cautious."
    elif 151 <= aqi <= 200:
        return "Unhealthy 🔴 - Everyone may start experiencing health effects, sensitive groups more severely."
    elif 201 <= aqi <= 300:
        return "Very Unhealthy 🟣 - Health warnings of emergency conditions. Everyone is at risk."
    else:  # AQI > 300
        return "Hazardous ⚫ - Serious health effects. Avoid outdoor activities!"

# New API Endpoint: Get AQI Status
@app.route('/aqi-status', methods=['GET'])
def get_aqi_status():
    try:
        aqi = int(request.args.get('aqi'))  # Get AQI value from query parameter
        status = aqi_status(aqi)
        return jsonify({"aqi": aqi, "status": status})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Run the App
if __name__ == '__main__':
    app.run(debug=True)