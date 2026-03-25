from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'USERS'
    user_id = db.Column(db.Integer, primary_key=True) # [cite: 140]
    student_number = db.Column(db.String(20), nullable=True) # [cite: 141]
    staff_number = db.Column(db.String(20), nullable=True) # [cite: 141]
    name = db.Column(db.String(100), nullable=False) # [cite: 142]
    email = db.Column(db.String(120), unique=True, nullable=False) # [cite: 143]
    role = db.Column(db.String(20), nullable=False) # 'student', 'staff', 'driver'
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    vehicle_details = db.Column(db.String(200), nullable=True)

    # Relationships
    rides_offered = db.relationship('Ride', backref='driver', lazy=True)
    bookings = db.relationship('Booking', backref='passenger', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

class Ride(db.Model):
    __tablename__ = 'RIDES'
    ride_id = db.Column(db.Integer, primary_key=True) # [cite: 148]
    driver_id = db.Column(db.Integer, db.ForeignKey('USERS.user_id'), nullable=False) # [cite: 149]
    pickup_location = db.Column(db.String(200), nullable=False) # [cite: 150]
    destination = db.Column(db.String(200), nullable=False) # [cite: 151]
    date = db.Column(db.Date, nullable=False) # [cite: 152]
    time = db.Column(db.Time, nullable=False) # [cite: 153]
    available_seats = db.Column(db.Integer, nullable=False) # [cite: 154]
    status = db.Column(db.String(50), nullable=False, default='Available')
    
    # Relationship
    bookings = db.relationship('Booking', backref='ride', lazy=True)

class Booking(db.Model):
    __tablename__ = 'BOOKINGS'
    booking_id = db.Column(db.Integer, primary_key=True) # [cite: 156]
    ride_id = db.Column(db.Integer, db.ForeignKey('RIDES.ride_id'), nullable=False) # [cite: 157]
    passenger_id = db.Column(db.Integer, db.ForeignKey('USERS.user_id'), nullable=False) # [cite: 159]
    status = db.Column(db.String(20), default='Pending') # e.g., Pending, Confirmed, Cancelled [cite: 160]

class Notification(db.Model):
    __tablename__ = 'NOTIFICATIONS'
    notification_id = db.Column(db.Integer, primary_key=True) # [cite: 162]
    user_id = db.Column(db.Integer, db.ForeignKey('USERS.user_id'), nullable=False) # [cite: 162]
    message = db.Column(db.String(500), nullable=False) # [cite: 163]
    date_sent = db.Column(db.DateTime, default=datetime.utcnow) # [cite: 164]

class Review(db.Model):
    __tablename__ = 'REVIEWS'
    review_id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('USERS.user_id'), nullable=False)
    passenger_id = db.Column(db.Integer, db.ForeignKey('USERS.user_id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # e.g., 1 to 5 stars
    comment = db.Column(db.Text, nullable=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

    driver = db.relationship('User', foreign_keys=[driver_id], backref='reviews_received')
    passenger = db.relationship('User', foreign_keys=[passenger_id], backref='reviews_given')

class Bus(db.Model):
    __tablename__ = 'BUSES'
    bus_id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(50), nullable=False, unique=True)
    capacity = db.Column(db.Integer, nullable=False)
    # The driver assigned to this bus (optional, can be updated by admin)
    driver_id = db.Column(db.Integer, db.ForeignKey('USERS.user_id'), nullable=True)
    
    driver = db.relationship('User', backref='assigned_buses')

class Location(db.Model):
    __tablename__ = 'LOCATIONS'
    location_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50), nullable=False) # e.g. 'Campus', 'Residence'