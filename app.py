from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import Config
from models import db, User, Ride, Booking, Notification, Review, Bus, Location

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

with app.app_context():
    db.create_all()  # Creates tables if they don't exist
    
    # Ensure default admin exists
    admin_user = User.query.filter_by(email='admin@gmail.com').first()
    if not admin_user:
        admin_user = User(
            name='System Administrator',
            email='admin@gmail.com',
            phone='0000000000',
            role='admin',
            password=generate_password_hash('12345678'),
            staff_number='ADMIN001'
        )
        db.session.add(admin_user)
        db.session.commit()

# --- AUTHENTICATION ROUTES ---

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        # Check password using werkzeug security
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.user_id
            session['role'] = user.role
            session['name'] = user.name
            
            # Route based on role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'driver':
                return redirect(url_for('driver_dashboard'))
            else:
                return redirect(url_for('passenger_dashboard'))
        else:
            flash('Invalid email or password. Please try again.')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Check if user already exists
        existing_user = User.query.filter_by(email=request.form.get('email')).first()
        if existing_user:
            flash('Email already registered. Please log in.')
            return redirect(url_for('login'))

        # Create new user with hashed password
        new_user = User(
            name=request.form.get('name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            role='passenger',
            password=generate_password_hash(request.form.get('password')),
            student_number=request.form.get('id_number')
        )

        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))


# --- ADMIN ROUTES ---

def is_admin():
    return session.get('role') == 'admin'

@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_admin(): return redirect(url_for('login'))
    drivers = User.query.filter_by(role='driver').all()
    locations = Location.query.all()
    buses = Bus.query.all()
    return render_template('admin/dashboard.html', drivers=drivers, locations=locations, buses=buses)

@app.route('/admin/manage-drivers', methods=['GET', 'POST'])
def manage_drivers():
    if not is_admin(): return redirect(url_for('login'))
    if request.method == 'POST':
        email = request.form.get('email')
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered.')
        else:
            new_driver = User(
                name=request.form.get('name'),
                email=email,
                phone=request.form.get('phone'),
                role='driver',
                password=generate_password_hash(request.form.get('password')),
                staff_number=request.form.get('staff_number')
            )
            db.session.add(new_driver)
            db.session.commit()
            flash('Driver created successfully.')
        return redirect(url_for('manage_drivers'))
    
    drivers = User.query.filter_by(role='driver').all()
    return render_template('admin/manage_drivers.html', drivers=drivers)

@app.route('/admin/manage-locations', methods=['GET', 'POST'])
def manage_locations():
    if not is_admin(): return redirect(url_for('login'))
    if request.method == 'POST':
        new_loc = Location(
            name=request.form.get('name'),
            latitude=request.form.get('latitude', type=float),
            longitude=request.form.get('longitude', type=float),
            type=request.form.get('type')
        )
        db.session.add(new_loc)
        try:
            db.session.commit()
            flash('Location added successfully.')
        except:
            db.session.rollback()
            flash('Error adding location (maybe duplicate name).')
        return redirect(url_for('manage_locations'))
        
    locations = Location.query.all()
    return render_template('admin/manage_locations.html', locations=locations)

@app.route('/admin/manage-buses', methods=['GET', 'POST'])
def manage_buses():
    if not is_admin(): return redirect(url_for('login'))
    if request.method == 'POST':
        new_bus = Bus(
            registration_number=request.form.get('registration_number'),
            capacity=request.form.get('capacity', type=int),
            driver_id=request.form.get('driver_id', type=int) or None
        )
        db.session.add(new_bus)
        db.session.commit()
        flash('Bus added successfully.')
        return redirect(url_for('manage_buses'))
        
    buses = Bus.query.all()
    drivers = User.query.filter_by(role='driver').all()
    return render_template('admin/manage_buses.html', buses=buses, drivers=drivers)

# --- PASSENGER (STUDENT/STAFF) ROUTES ---

# Dependency hook to ensure only passengers access these routes
def is_passenger():
    return session.get('role') == 'passenger'

@app.route('/passenger/dashboard')
def passenger_dashboard():
    if not is_passenger(): return redirect(url_for('login'))
    user_id = session.get('user_id')
    active_bookings = Booking.query.filter_by(passenger_id=user_id).filter(Booking.status.in_(['Pending', 'Confirmed'])).all()
    return render_template('passenger/dashboard.html', bookings=active_bookings)

@app.route('/passenger/find-ride', methods=['GET', 'POST'])
def find_ride():
    if not is_passenger(): return redirect(url_for('login'))
    
    locations = Location.query.all()
    if request.method == 'POST':
        pickup = request.form.get('pickup')
        destination = request.form.get('destination')
        # Search matching rides using ilike for partial matches
        matches = Ride.query.filter(Ride.pickup_location.ilike(f'%{pickup}%'), Ride.destination.ilike(f'%{destination}%')).all()
        return render_template('passenger/find_ride.html', rides=matches, locations=locations)
        
    return render_template('passenger/find_ride.html', rides=None, locations=locations)

@app.route('/passenger/book-ride/<int:ride_id>', methods=['POST'])
def book_ride(ride_id):
    if not is_passenger(): return redirect(url_for('login'))
    user_id = session.get('user_id')
    
    existing = Booking.query.filter_by(ride_id=ride_id, passenger_id=user_id).first()
    if existing:
        flash('You have already booked this ride.')
        return redirect(url_for('passenger_bookings'))
        
    ride = Ride.query.get_or_404(ride_id)
    if ride.available_seats > 0:
        new_booking = Booking(ride_id=ride_id, passenger_id=user_id, status='Pending')
        # Also notify driver
        notification = Notification(user_id=ride.driver_id, message=f"{session.get('name')} requested to book your ride to {ride.destination}.")
        db.session.add(new_booking)
        db.session.add(notification)
        db.session.commit()
        flash('Ride booked successfully! Waiting for driver confirmation.')
    else:
        flash('Sorry, this ride is fully booked.')
        
    return redirect(url_for('passenger_dashboard'))

@app.route('/passenger/shuttle')
def passenger_shuttle():
    if not is_passenger(): return redirect(url_for('login'))
    active_rides = Ride.query.filter(Ride.status.in_(['Available', 'Incoming', 'On a road to destination'])).all()
    locations = {loc.name: {'lat': loc.latitude, 'lng': loc.longitude} for loc in Location.query.all()}
    return render_template('passenger/shuttle.html', rides=active_rides, locations=locations)

@app.route('/passenger/bus-pass')
def passenger_bus_pass():
    if not is_passenger(): return redirect(url_for('login'))
    rides = Ride.query.filter(Ride.date >= datetime.today().date()).order_by(Ride.date.asc(), Ride.time.asc()).all()
    return render_template('passenger/bus_pass.html', rides=rides)

@app.route('/passenger/bookings')
def passenger_bookings():
    if not is_passenger(): return redirect(url_for('login'))
    user_id = session.get('user_id')
    bookings = Booking.query.filter_by(passenger_id=user_id).order_by(Booking.booking_id.desc()).all()
    return render_template('passenger/bookings.html', bookings=bookings)

@app.route('/passenger/cancel-booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if not is_passenger(): return redirect(url_for('login'))
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.passenger_id == session.get('user_id'):
        # FIX: Restore the available seat if the ride was already confirmed
        if booking.status == 'Confirmed':
            booking.ride.available_seats += 1
            
        db.session.delete(booking)
        
        # Notify driver
        notification = Notification(user_id=booking.ride.driver_id, message=f"{session.get('name')} cancelled their booking for your ride.")
        db.session.add(notification)
        db.session.commit()
        flash('Booking cancelled successfully.')
        
    return redirect(url_for('passenger_bookings'))

@app.route('/passenger/rate-driver', methods=['GET', 'POST'])
def rate_driver():
    if not is_passenger(): return redirect(url_for('login'))
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        driver_id = request.form.get('driver_id')
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        
        review = Review(driver_id=driver_id, passenger_id=user_id, rating=rating, comment=comment)
        db.session.add(review)
        db.session.commit()
        
        flash('Thank you! Your review has been submitted.')
        return redirect(url_for('passenger_dashboard'))
    
    # Get all drivers the passenger has travelled with (status='Confirmed')
    past_bookings = Booking.query.filter_by(passenger_id=user_id, status='Confirmed').all()
    # Unique drivers
    drivers = list({b.ride.driver for b in past_bookings})
    
    return render_template('passenger/rate_driver.html', drivers=drivers)

@app.route('/passenger/notifications')
def passenger_notifications():
    if not is_passenger(): return redirect(url_for('login'))
    user_id = session.get('user_id')
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.date_sent.desc()).all()
    return render_template('passenger/notifications.html', notifications=notifications)

@app.route('/passenger/profile', methods=['GET', 'POST'])
def passenger_profile():
    if not is_passenger(): return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if request.method == 'POST':
        new_name = request.form.get('name')
        new_phone = request.form.get('phone')
        
        if new_name and new_phone:
            user.name = new_name
            user.phone = new_phone
            db.session.commit()
            session['name'] = user.name 
            flash('Profile updated successfully!')
            return redirect(url_for('passenger_profile'))
        else:
            flash('Please fill out all fields.')
            
    return render_template('passenger/profile.html', user=user)


# --- DRIVER ROUTES ---

# Dependency hook to ensure only drivers access these routes
def is_driver():
    return session.get('role') == 'driver'

@app.route('/driver/dashboard')
def driver_dashboard():
    if not is_driver(): return redirect(url_for('login'))
    user_id = session.get('user_id')
    active_rides = Ride.query.filter_by(driver_id=user_id).order_by(Ride.date.desc()).all()
    return render_template('driver/dashboard.html', rides=active_rides)

@app.route('/driver/offer-ride', methods=['GET', 'POST'])
def offer_ride():
    if not is_driver(): return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            new_ride = Ride(
                driver_id=session.get('user_id'),
                pickup_location=request.form.get('pickup'),
                destination=request.form.get('destination'),
                date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
                time=datetime.strptime(request.form.get('time'), '%H:%M').time(),
                available_seats=int(request.form.get('seats')),
                status='Available'
            )
            db.session.add(new_ride)
            db.session.commit()
            flash('Ride posted successfully!')
            return redirect(url_for('driver_dashboard'))
        except Exception as e:
            flash(f'Error posting ride: {str(e)}')
            
    locations = Location.query.all()
    return render_template('driver/offer_ride.html', locations=locations)

@app.route('/driver/update-ride-status/<int:ride_id>', methods=['POST'])
def update_ride_status(ride_id):
    if not is_driver(): return redirect(url_for('login'))
    ride = Ride.query.get_or_404(ride_id)
    if ride.driver_id != session.get('user_id'):
        flash('Unauthorized.')
        return redirect(url_for('driver_dashboard'))
    
    new_status = request.form.get('status')
    if new_status in ['Available', 'Incoming', 'Busy', 'Not Available', 'On a road to destination']:
        ride.status = new_status
        db.session.commit()
        flash(f'Ride status updated to {new_status}')
    return redirect(url_for('driver_dashboard'))

@app.route('/driver/bookings')
def driver_bookings():
    if not is_driver(): return redirect(url_for('login'))
    user_id = session.get('user_id')
    rides = Ride.query.filter_by(driver_id=user_id).all()
    ride_ids = [r.ride_id for r in rides]
    bookings = Booking.query.filter(Booking.ride_id.in_(ride_ids)).order_by(Booking.booking_id.desc()).all()
    return render_template('driver/bookings.html', bookings=bookings)

@app.route('/driver/manage-booking/<int:booking_id>/<action>', methods=['POST'])
def manage_booking(booking_id, action):
    if not is_driver(): return redirect(url_for('login'))
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.ride.driver_id != session.get('user_id'):
        flash('Unauthorized.')
        return redirect(url_for('driver_bookings'))
        
    ride_details = f"{booking.ride.pickup_location} to {booking.ride.destination}"
    
    if action == 'accept':
        # FIX: Ensure we don't subtract a seat if it's already confirmed!
        if booking.status != 'Confirmed':
            if booking.ride.available_seats > 0:
                booking.status = 'Confirmed'
                booking.ride.available_seats -= 1
                msg = f"Your booking for {ride_details} has been Confirmed by the driver."
                db.session.add(Notification(user_id=booking.passenger_id, message=msg))
                flash('Booking confirmed.')
            else:
                flash('No available seats left for this ride!')
        else:
            flash('Booking is already confirmed.')
            
    elif action == 'reject':
        # FIX: Restore the seat if the driver changes their mind and rejects an already confirmed booking
        if booking.status == 'Confirmed':
            booking.ride.available_seats += 1
            
        booking.status = 'Cancelled'
        msg = f"Your booking for {ride_details} was Cancelled by the driver."
        db.session.add(Notification(user_id=booking.passenger_id, message=msg))
        flash('Booking rejected/cancelled.')
        
    db.session.commit()
    return redirect(url_for('driver_bookings'))

@app.route('/driver/reports')
def driver_reports():
    if not is_driver(): return redirect(url_for('login'))
    user_id = session.get('user_id')
    rides = Ride.query.filter_by(driver_id=user_id).all()
    ride_ids = [r.ride_id for r in rides]
    confirmed_bookings = Booking.query.filter(Booking.ride_id.in_(ride_ids), Booking.status == 'Confirmed').count()
    
    reviews = Review.query.filter_by(driver_id=user_id).all()
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0
    
    return render_template('driver/reports.html', 
                           total_rides=len(rides), 
                           total_passengers=confirmed_bookings, 
                           avg_rating=round(avg_rating, 1))

@app.route('/driver/reviews')
def driver_reviews():
    if not is_driver(): return redirect(url_for('login'))
    user_id = session.get('user_id')
    reviews = Review.query.filter_by(driver_id=user_id).order_by(Review.date_posted.desc()).all()
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0.0
    return render_template('driver/reviews.html', 
                           reviews=reviews, 
                           avg_rating=round(avg_rating, 1), 
                           total_reviews=len(reviews))

@app.route('/driver/notifications')
def driver_notifications():
    if not is_driver(): return redirect(url_for('login'))
    user_id = session.get('user_id')
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.date_sent.desc()).all()
    return render_template('driver/notifications.html', notifications=notifications)

@app.route('/driver/profile', methods=['GET', 'POST'])
def driver_profile():
    if not is_driver(): return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if request.method == 'POST':
        new_name = request.form.get('name')
        new_phone = request.form.get('phone')
        new_vehicle = request.form.get('vehicle')
        
        if new_name and new_phone:
            user.name = new_name
            user.phone = new_phone
            if new_vehicle is not None:
                user.vehicle_details = new_vehicle
            db.session.commit()
            session['name'] = user.name 
            flash('Profile updated successfully!')
            return redirect(url_for('driver_profile'))
        else:
            flash('Please fill out all required fields.')
            
    return render_template('driver/profile.html', user=user)

@app.route('/driver/shuttle')
def driver_shuttle():
    if not is_driver(): return redirect(url_for('login'))
    active_rides = Ride.query.filter(Ride.status.in_(['Available', 'Incoming', 'On a road to destination'])).all()
    locations = {loc.name: {'lat': loc.latitude, 'lng': loc.longitude} for loc in Location.query.all()}
    return render_template('driver/shuttle.html', rides=active_rides, locations=locations)

if __name__ == '__main__':
    app.run(debug=True)