from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from models import *


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking_management.sqlite3'
db.init_app(app)
app.app_context().push()

# ROUTES
# LOGIN AND REGISTER
@app.route("/")
def home():
    return redirect(url_for('login'))



@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        staff = StaffProfile.query.filter_by(email=email).first()
        admin = User.query.filter_by(email=email, role='Admin').first()
        if user and user.password == password:
            return redirect(url_for('user_dashboard', user_id=user.user_id))
        
        elif staff and staff.password == password:
            return redirect(url_for('staff_dashboard', staff_id=staff.staff_id))

        elif admin and admin.password == password:
            return redirect(url_for('admin_dashboard'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register_form():
    if request.method == 'POST':
        name      = request.form['name']
        email       = request.form['email']
        password    = request.form['password']
        phone       = request.form['phone']
        role        = request.form['role']

        if role=='trekker':
            user = User(name=name, email=email, password=password, phone=phone)
            db.session.add(user)
            db.session.commit()
        elif role=='trek-staff':
            staff = StaffProfile(name=name, email=email, password=password, phone=phone)
            db.session.add(staff)
            db.session.commit()
        return redirect('/login')
    return render_template('register.html')
    
##########################################################################################################################################

# ADMIN PART

@app.route('/admin/dashboard')
def admin_dashboard():
    trek_count=Trek.query.count()
    user_count=User.query.filter_by(role='User').count()
    staff_count=StaffProfile.query.count()
    booking_count=Booking.query.count()

    recent_bookings=Booking.query.order_by(Booking.booking_id.desc()).limit(5).all() # tooking the hlep of ai in this query.
    return render_template('adminpages/dashboard.html', trek_count=trek_count, user_count=user_count, staff_count=staff_count, booking_count=booking_count, recent_bookings=recent_bookings)



@app.route('/admin/trek')
def admin_trek_manager():
    locations = db.session.scalars(db.select(Trek.location).distinct()).all()
    search = request.args.get('search')
    location = request.args.get('location')
    difficulty = request.args.get('difficulty')
    status = request.args.get('status')

    query = Trek.query

    if search:
        if search.isdigit():
            id = int(search)
            query = query.filter(Trek.trek_id == id)
        else:
            query = query.filter(Trek.trek_name.ilike(f"%{search}%"))
    if location:
        query = query.filter(Trek.location == location)
    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)
    if status:
        query = query.filter(Trek.status == status)

    treks = query.all()
    count = query.count()

    return render_template('adminpages/trek.html', treks=treks, locations=locations, count=count)

@app.route('/admin/trek/delete')
def delete_trek():
    trek_id = int(request.args.get('trek_id'))
    del_trek=Trek.query.filter_by(trek_id=trek_id).first()
    if del_trek:
        db.session.delete(del_trek)
        db.session.commit()
    return redirect('/admin/trek')


@app.route('/admin/trek/<int:trek_id>/view')
def view_trek(trek_id):
    trek=Trek.query.filter_by(trek_id=trek_id).first()
    
    active_bookings = Booking.query.filter(
        Booking.trek_id == trek_id, 
        Booking.status.in_(['Booked', 'Completed'])
    ).all()
    count_booking = len(active_bookings)
    return render_template('adminpages/view_trek.html', trek=trek, count_booking=count_booking, active_bookings=active_bookings)

@app.route('/admin/trek/<int:trek_id>/edit', methods=['GET', 'POST'])
def edit_trek(trek_id):
    if request.method=='POST':
        trek = Trek.query.filter_by(trek_id=trek_id).first()
        print(trek.trek_name)

        trek.trek_name = request.form['trek_name']
        trek.location = request.form['location']
        trek.difficulty = request.form['difficulty']
        trek.duration = request.form['duration']
        trek.total_slots = request.form['slot']
        start_date = datetime.strptime(request.form['s_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['e_date'], '%Y-%m-%d').date()
        last_booking_date = datetime.strptime(request.form['b_date'], '%Y-%m-%d').date()
        trek.status = request.form['status']
        trek.description = request.form['description']
        trek.assigned_staff_id = request.form['staff']
        trek.available_slots = int(trek.total_slots) - len(trek.bookings)

        db.session.commit()
        trek = Trek.query.filter_by(trek_id=trek_id).first()
        print(trek.trek_id, trek.trek_name, trek.location, trek.difficulty, trek.duration, trek.total_slots, trek.available_slots, trek.start_date, trek.end_date, trek.status, trek.description, trek.assigned_staff)
        
        return redirect('/admin/trek')

    trek=Trek.query.filter_by(trek_id=trek_id).first()
    staffs=StaffProfile.query.filter_by(status='Approved').all()
    return render_template('adminpages/edit_trek.html', trek=trek, staffs=staffs)

@app.route('/admin/trek/add', methods=['GET', 'POST'])
def add_trek():
    if request.method=='POST':
        trek_name = request.form['trek_name']
        location = request.form['location']
        difficulty = request.form['difficulty']
        duration = request.form['duration']
        total_slots = request.form['slot']
        start_date = datetime.strptime(request.form['s_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['e_date'], '%Y-%m-%d').date()

        if request.form.get('b_date'):
            last_booking_date = datetime.strptime(request.form['b_date'], '%Y-%m-%d').date()
        else:
            last_booking_date = None
            
        status = request.form['status']
        description = request.form['description']
        assigned_staff_id = request.form['staff']

        trek = Trek(trek_name=trek_name, location=location, difficulty=difficulty, duration=duration, total_slots=total_slots, available_slots=total_slots, start_date=start_date, end_date=end_date, last_booking_date=last_booking_date, status=status, description=description, assigned_staff_id=assigned_staff_id)
        db.session.add(trek)
        db.session.commit()
        return redirect('/admin/trek')

    staffs=StaffProfile.query.filter_by(status='Approved').all()
    return render_template('adminpages/add_trek.html', staffs=staffs)




# from sqlalchemy import or_

@app.route('/admin/staff')
def admin_staff():
    current_tab = request.args.get('tab', 'All')
    status = request.args.get("status")
    staff_id = request.args.get("id")
    search = request.args.get('search')
    
    # 1. Handle Status Update Actions safely
    if staff_id and status:
        staff = StaffProfile.query.filter_by(staff_id=staff_id).first()
        if staff:
            staff.status = status
            db.session.commit()
            
    # 2. Build Base Filter Queries depending on Selected Tab
    if current_tab == "All":
        query = StaffProfile.query
    else:
        query = StaffProfile.query.filter_by(status=current_tab)
        
    # 3. FIX: Check StaffProfile properties instead of Trek properties
    if search:
        search = search.strip()
        if search.isdigit():
            # If digit, search by precise ID within our base tab filter constraint
            staffs = query.filter(StaffProfile.staff_id == int(search)).all()
        else:
            # If text string, perform substring matching on the name attribute
            staffs = query.filter(StaffProfile.name.ilike(f"%{search}%")).all()
    else:
        staffs = query.all()
    
    count = [
        len(query.filter_by(status='Pending').all()),
        len(query.filter_by(status='Approved').all()),
        len(query.filter_by(status='Blacklisted').all()),
        len(query.all())
    ]

    return render_template('adminpages/staff.html', staffs=staffs, current_tab=current_tab, count=count)

@app.route('/admin/users')
def admin_user():
    search = request.args.get('search')
    status = request.args.get('status')
    query = User.query
    users =  query.all()
    if search:
        if search.isdigit():
            users = query.filter_by(user_id=search).all()
        else:
            users= query.filter(User.name.ilike(f"%{search}%")).all()
    if status:
        if int(status):
            users = query.filter_by(is_blacklisted=True).all()
        else:
            users = query.filter_by(is_blacklisted=False).all()
    

    return render_template('adminpages/user.html', users=users)


@app.route('/admin/booking')
def admin_booking():
    search = request.args.get('search')
    trek = request.args.get('trek')
    status = request.args.get('status')
    booking_id = request.args.get('booking_id')


    bookings = Booking.query.all()

    if search:
        if search.isdigit():
            bookings = Booking.query.filter_by(booking_id=int(search)).all()
    if trek:
        trek_id = int(trek)
        bookings = Booking.query.filter_by(trek_id=trek_id).all()
    if status:
        bookings = Booking.query.filter_by(status=status).all()
    if booking_id:
        booking = Booking.query.filter_by(booking_id=booking_id).first()
        booking.status = "Canceled"
        db.session.commit()

    treks = Trek.query.all()
    return render_template('adminpages/booking.html', bookings=bookings, treks=treks)

##########################################################################################################################################

# USER PART

@app.route('/user/<int:user_id>')
def user_dashboard(user_id):
    user = User.query.filter_by(user_id=user_id).first()

    return render_template('userpages/dashboard.html', user=user)


##########################################################################################################################################

# STAFF PART 

@app.route('/staff/<int:staff_id>/dashboard')
def staff_dashboard(staff_id):
    staff = StaffProfile.query.filter_by(staff_id=staff_id).first()

    Treklist = {
        "Approved": Trek.query.filter_by(assigned_staff_id=staff_id, status='Approved').all(),
        "Open": Trek.query.filter_by(assigned_staff_id=staff_id, status='Open').all(),
        "Closed": Trek.query.filter_by(assigned_staff_id=staff_id, status='Closed').all()
    }

    from sqlalchemy import func

    participants = db.session.query(func.count(Booking.booking_id))\
        .join(Trek, Booking.trek_id == Trek.trek_id)\
        .filter(Trek.assigned_staff_id == staff_id)\
        .filter(Trek.status.in_(['Open', 'Closed']))\
        .filter(Booking.status == 'Booked')\
        .scalar() or 0

    return render_template('staffpages/dashboard.html', staff=staff, Treklist=Treklist, participants=participants)

@app.route('/staff/<int:staff_id>/trek')
def staff_trek(staff_id):
    staff = StaffProfile.query.filter_by(staff_id=staff_id).first()
    active_treks = Trek.query.filter(Trek.assigned_staff_id == staff_id, Trek.status.in_(['Approved', 'Open', 'Closed', 'Started'])).all()
    search = request.args.get('search')
    filter  = request.args.get('status')

    if search:
        if search.isdigit():
            active_treks = Trek.query.filter_by(trek_id=int(search)).all()
        else:
            active_treks = Trek.query.filter(Trek.trek_name.ilike(f"%{search}%")).all()
    if filter:
        active_treks = Trek.query.filter_by(status=filter, assigned_staff_id=staff_id).all()

    return render_template('staffpages/trek.html', staff=staff, active_treks=active_treks)

@app.route('/staff/<int:staff_id>/trek/<int:trek_id>/manage', methods=['GET', 'POST'])
def staff_trek_manage(staff_id=None, trek_id=None):
    slots = request.args.get('slots')
    status = request.args.get('status')
    start = request.args.get('start')
    complete = request.args.get('complete')

    staff = StaffProfile.query.filter_by(staff_id=staff_id).first()
    
    trek = Trek.query.filter_by(trek_id=trek_id).first()

    active_bookings = Booking.query.join(User, Booking.user_id==User.user_id).join(Trek, Booking.trek_id==Trek.trek_id).filter(Booking.trek_id==trek_id, User.is_blacklisted==False, Booking.status.in_(['Booked', 'Completed'])).all()
    if slots:
        trek.available_slots = int(slots)
        trek.status = status
        db.session.commit()
        return redirect(url_for('staff_trek', staff_id=staff_id))

    if start:
        trek.status = "Started"
        db.session.commit()
        return redirect(url_for('staff_trek', staff_id=staff_id))
    if complete:
        trek.status = "Completed"
        db.session.commit()
        return redirect(url_for('staff_trek', staff_id=staff_id))
    

    return render_template('staffpages/staff_trek_manage.html', staff=staff, trek=trek, active_bookings=active_bookings)


@app.route('/staff/<int:staff_id>/trek_history')
def staff_trek_history(staff_id):
    staff = StaffProfile.query.filter_by(staff_id=staff_id).first()
    locations = Trek.query.filter_by(assigned_staff_id=staff_id, status='Completed').all()
    query = Trek.query.filter_by(assigned_staff_id=staff_id, status='Completed')
    location = request.args.get('location')
    difficulty = request.args.get('difficulty')
    search = request.args.get('search')
    if search:
        if search.isdigit():
            query = query.filter_by(trek_id=int(search))
        else:
            query = query.filter(Trek.trek_name.ilike(f"%{search}%"))
    if location:
        query = query.filter_by(assigned_staff_id=staff_id, status='Completed', location=location)
    if difficulty:
        query = query.filter_by(assigned_staff_id=staff_id, status='Completed', difficulty=difficulty)

    completed_treks = query.all()
    
    
    return render_template('staffpages/staff_trek_history.html', staff=staff, completed_treks=completed_treks, locations=locations)

@app.route('/staff/<int:staff_id>/trek_history/<int:trek_id>/view_trek')
def staff_trek_view(staff_id, trek_id):

    staff = StaffProfile.query.filter_by(staff_id=staff_id).first()
    
    trek = Trek.query.filter_by(trek_id=trek_id).first()
    active_bookings = Booking.query.filter(
        Booking.trek_id == trek_id, 
        Booking.status.in_(['Booked', 'Completed'])
    ).all()
    return render_template('staffpages/staff_trek_view.html',staff=staff, trek=trek, active_bookings=active_bookings)

@app.route('/staff/<int:staff_id>/participants')
def staff_participant(staff_id):
    staff = StaffProfile.query.filter_by(staff_id=staff_id).first()
    query = (
        Booking.query
        .join(User, Booking.user_id == User.user_id)
        .join(Trek, Booking.trek_id == Trek.trek_id)
        .filter(
            Trek.assigned_staff_id == staff_id,
            Trek.status.in_(['Open', 'Closed', 'Started']),
            Booking.status == 'Booked',
            User.is_blacklisted.is_(False)
        )
    )
    search = request.args.get('search')
    trek_status = request.args.get('status')

    if search:
        if search.isdigit():
            query = query.filter(User.user_id==int(search))
        else:
            query = query.filter(User.name.ilike(f"%{search}%"))
    if trek_status:
        query = query.filter(Trek.status==trek_status)
    
    participants = query.all()
            
    return render_template('staffpages/staff_participant.html', staff=staff, participants=participants)

@app.route('/testing')
def testing():

    return render_template('side_nav_bar.html')

if __name__ == "__main__":
    app.run(debug=True)