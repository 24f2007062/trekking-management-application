from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='User')  # 'User' or 'Admin'
    is_blacklisted = db.Column(db.Boolean, default=False)
    
    # Relationship to track a trekker's bookings
    bookings = db.relationship('Booking', backref='trekker')

class StaffProfile(db.Model):
    __tablename__ = 'staff_profiles'
    staff_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')  # 'Pending', 'Approved', 'Blacklisted'
    
    # Relationship to find what treks this staff member manages
    assigned_treks = db.relationship('Trek', backref='assigned_staff')

class Trek(db.Model):
    __tablename__ = 'treks'
    trek_id = db.Column(db.Integer, primary_key=True)
    trek_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # 'Easy', 'Moderate', 'Hard'
    duration = db.Column(db.Integer, nullable=False)       # in days
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    end_date = db.Column(db.String(10), nullable=False)    # YYYY-MM-DD
    status = db.Column(db.String(20), nullable=False, default='Pending') # 'Pending', 'Approved', 'Open', 'Closed', 'Completed'
    description = db.Column(db.String(2000), nullable=True)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('staff_profiles.staff_id'), nullable=True)
    image_file = db.Column(db.String(100), nullable=False, default='default_trek.jpg')
    bookings = db.relationship('Booking', backref='trek')

class Booking(db.Model):
    __tablename__ = 'bookings'
    booking_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.trek_id'), nullable=False)
    booking_date = db.Column(db.String(10), nullable=False) # YYYY-MM-DD
    status = db.Column(db.String(20), nullable=False, default='Booked') # 'Booked', 'Cancelled', 'Completed'