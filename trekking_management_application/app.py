from flask import Flask, render_template, request, redirect, url_for, session, abort # marked session, abort
from datetime import datetime, date
from flask import session # marked
from security import login_user_session, logout_user_session, admin_required, staff_required, user_required #marked

from werkzeug.utils import secure_filename
import os
from models import *

UPLOAD_FOLDER = "static/images"

app = Flask(__name__) 
app.config["SECRET_KEY"] = "Trek@2026$MAD_Project#9Xv8Q"  # marked
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking_management.sqlite3'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
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
        user = User.query.filter_by(email=email, role='User').first()
        staff = StaffProfile.query.filter_by(email=email).first()
        admin = User.query.filter_by(email=email, role='Admin').first()
        if user and user.password == password:
            if user.is_blacklisted:
                abort(403)
            login_user_session(user.user_id, "User") # marked

            return redirect(url_for('user_dashboard', user_id=user.user_id))
        
        elif staff and staff.password == password:
            if staff.status == "Pending":
                abort(403)

            if staff.status == "Blacklisted":
                abort(403)

            login_user_session(staff.staff_id, "Staff") # marked

            return redirect(url_for('staff_dashboard', staff_id=staff.staff_id))

        elif admin and admin.password == password:

            login_user_session(admin.user_id, "Admin")  #marked

            return redirect(url_for('admin_dashboard'))
    
    return render_template('login.html')

@app.route("/logout")  #marked whole route
def logout():

    logout_user_session()

    return redirect(url_for("login"))


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
@admin_required
def admin_dashboard():
    trek_count=Trek.query.filter(Trek.status.in_(['Open', 'Closed', 'Started'])).count()
    user_count=User.query.filter_by(role='User', is_blacklisted=False).count()
    staff_count=StaffProfile.query.filter_by(status='Approved').count()
    booking_count=Booking.query.filter_by(status='Booked').count()

    recent_bookings=Booking.query.order_by(Booking.booking_id.desc()).limit(5).all() # tooking the hlep of ai in this query.
    return render_template('adminpages/dashboard.html', trek_count=trek_count, user_count=user_count, staff_count=staff_count, booking_count=booking_count, recent_bookings=recent_bookings)



@app.route('/admin/trek')
@admin_required
def admin_trek_manager():
    staffs = StaffProfile.query.filter_by(status='Approved').all()
    locations = db.session.scalars(db.select(Trek.location).distinct()).all()
    search = request.args.get('search')
    location = request.args.get('location')
    difficulty = request.args.get('difficulty')
    status = request.args.get('status')
    staff = request.args.get('staff')
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
    if staff:
        query = query.filter(Trek.assigned_staff_id==int(staff))

    treks = query.all()
    count = query.count()

    return render_template('adminpages/trek.html', treks=treks, locations=locations, count=count, staffs=staffs)

@app.route('/admin/trek/delete/<int:trek_id>', methods=['POST'])
@admin_required
def delete_trek(trek_id):
    del_trek=Trek.query.filter_by(trek_id=trek_id).first()
    
    if del_trek:
        del_bookings = Booking.query.filter_by(trek_id=trek_id).delete()
        db.session.delete(del_trek)
        db.session.commit()
    return redirect(url_for('admin_trek_manager'))


@app.route('/admin/trek/<int:trek_id>/view')
@admin_required
def view_trek(trek_id):
    trek=Trek.query.filter_by(trek_id=trek_id).first()
    
    active_bookings = Booking.query.filter(
        Booking.trek_id == trek_id, 
        Booking.status.in_(['Booked', 'Completed'])
    ).all()
    count_booking = len(active_bookings)
    return render_template('adminpages/view_trek.html', trek=trek, count_booking=count_booking, active_bookings=active_bookings)

@app.route('/admin/trek/<int:trek_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_trek(trek_id):
    if request.method=='POST':
        trek = Trek.query.filter_by(trek_id=trek_id).first()
        print(trek.trek_name)

        trek.trek_name = request.form['trek_name']
        trek.location = request.form['location']
        trek.difficulty = request.form['difficulty']
        trek.duration = request.form['duration']
        trek.total_slots = request.form['slot']
        trek.start_date = datetime.strptime(request.form['s_date'], '%Y-%m-%d').date()
        trek.end_date = datetime.strptime(request.form['e_date'], '%Y-%m-%d').date()
        print(request.form['b_date'])
        trek.last_booking_date = datetime.strptime(request.form['b_date'], '%Y-%m-%d').date()
        trek.status = request.form['status']
        trek.description = request.form['description']
        trek.assigned_staff_id = request.form['staff']
        trek.available_slots = int(trek.total_slots) - len(trek.bookings)

        
        if request.files['img']:
            image_file = request.files['img']

            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            trek.image_file = filename
        db.session.commit()    

        print(trek.last_booking_date)

        trek = Trek.query.get(trek_id)

        print(trek.last_booking_date)
                
        return redirect('/admin/trek')

    trek=Trek.query.filter_by(trek_id=trek_id).first()
    staffs=StaffProfile.query.filter_by(status='Approved').all()
    return render_template('adminpages/edit_trek.html', trek=trek, staffs=staffs)

@app.route('/admin/trek/add', methods=['GET', 'POST'])
@admin_required
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
        if request.files['img']:
            image_file = request.files['img']

            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            trek.image_file = filename
            db.session.commit()
        return redirect('/admin/trek')

    staffs=StaffProfile.query.filter_by(status='Approved').all()
    return render_template('adminpages/add_trek.html', staffs=staffs)






@app.route('/admin/staff')
@admin_required
def admin_staff():
    current_tab = request.args.get('tab', 'All')
    search = request.args.get('search')

    if current_tab == "All":
        query = StaffProfile.query
    else:
        query = StaffProfile.query.filter_by(status=current_tab)
        

    if search:
        if search.isdigit():

            staffs = query.filter(StaffProfile.staff_id == int(search)).all()
        else:

            staffs = query.filter(StaffProfile.name.ilike(f"%{search}%")).all()
    else:
        staffs = query.all()
    
    count = [
        len(StaffProfile.query.filter_by(status='Pending').all()),
        len(StaffProfile.query.filter_by(status='Approved').all()),
        len(StaffProfile.query.filter_by(status='Blacklisted').all()),
        len(StaffProfile.query.all())
    ]

    return render_template('adminpages/staff.html', staffs=staffs, current_tab=current_tab, count=count)

@app.route('/admin/staff/<int:staff_id>', methods=['POST'])
@admin_required
def update_staff_status(staff_id):
    staff = StaffProfile.query.filter_by(staff_id=staff_id).first()
    status = request.form.get('status')

    if staff and staff.status != status:
        staff.status = status
        db.session.commit()
    return redirect(url_for('admin_staff'))


@app.route('/admin/users')
@admin_required
def admin_user():
    search = request.args.get('search')
    status = request.args.get('status')
    query = User.query.filter_by(role='User')
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

@app.route('/admin/user/<int:user_id>', methods=['POST'])
@admin_required
def update_user_status(user_id):
    user = User.query.filter_by(user_id=user_id).first()
    status = request.form.get('status')
    if user:
        if status == 'True':
            user.is_blacklisted = True
        else:
            user.is_blacklisted = False

        db.session.commit()
    return redirect(url_for('admin_user'))

@app.route('/admin/booking')
@admin_required
def admin_booking():
    search = request.args.get('search')
    trek = request.args.get('trek')
    status = request.args.get('status')


    bookings = Booking.query.all()

    if search:
        if search.isdigit():
            bookings = Booking.query.filter_by(booking_id=int(search)).all()
    if trek:
        trek_id = int(trek)
        bookings = Booking.query.filter_by(trek_id=trek_id).all()
    if status:
        bookings = Booking.query.filter_by(status=status).all()

    treks = Trek.query.all()
    return render_template('adminpages/booking.html', bookings=bookings, treks=treks)



@app.route('/admin/booking/<int:booking_id>', methods=['POST'])
@admin_required
def admin_cancel_booking(booking_id):
    book_status = request.form['book_status']

    if book_status:
        booking = Booking.query.filter_by(booking_id=booking_id).first()
        booking.trek.available += 1
        booking.status = book_status
        db.session.commit()
    
    return redirect(url_for('admin_booking'))



##########################################################################################################################################

# USER PART

@app.route('/user/<int:user_id>/dashboard')
@user_required
def user_dashboard(user_id):
    user = User.query.filter(User.is_blacklisted==False, User.user_id==user_id, User.role=='User').first()
    open_trek_count = Trek.query.filter_by(status='Open').count()
    my_active_trek_count = Trek.query.join(Booking, Trek.trek_id==Booking.trek_id).filter(Booking.status=='Booked', Booking.user_id==user_id, Trek.status.in_(['Open', 'Closed', 'Started'])).count()
    my_bookings_count = Booking.query.filter_by(status='Booked', user_id=user_id).count()
    open_trek = Trek.query.filter_by(status='Open').limit(5).all()
    return render_template('userpages/dashboard.html', user=user, open_trek_count=open_trek_count, my_active_trek_count=my_active_trek_count, my_bookings_count=my_bookings_count, open_trek=open_trek)


@app.route('/user/<int:user_id>/trek')
@user_required
def user_trek(user_id):
    user = User.query.filter(User.user_id==user_id, User.role=='User', User.is_blacklisted==False).first()
    active_trek = Booking.query.join(User, User.user_id==Booking.user_id).join(Trek, Trek.trek_id==Booking.trek_id).filter(Booking.user_id==user_id, Trek.status.in_(['Open', 'Closed', 'Started']), User.role=="User", Booking.status=='Booked').all()
    if not active_trek:
        return render_template('userpages/empty_trek.html', user=user)
    return render_template('userpages/my_trek.html', user=user, active_trek=active_trek)

@app.route('/user/<int:user_id>/browse_trek')
@user_required
def browse_trek(user_id):
    user = User.query.filter_by(user_id=user_id, role='User', is_blacklisted=False).first()
    search = request.args.get('search')
    location = request.args.get('location')
    difficulty = request.args.get('difficulty')
    max_duration = request.args.get('maxduration', type=int)
    min_duration = request.args.get('minduration', type=int)
    query = Trek.query.filter_by(status='Open')
    if search:
        if search.isdigit():
            query = query.filter_by(trek_id=int(search))
        else:
            query = query.filter(Trek.trek_name.ilike(f"%{search}%"))
    if location:
        query = query.filter_by(location=location)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if max_duration is not None and min_duration is not None:
        query = query.filter(Trek.duration.between(min_duration, max_duration))
    elif min_duration is not None:
        query = query.filter(Trek.duration >= min_duration)
    elif max_duration is not None:
        query = query.filter(Trek.duration <= max_duration)
    treks = query.all()
    locations = db.session.scalars(db.select(Trek.location).where(Trek.status=='Open').distinct().order_by(Trek.location)).all()
    return render_template('userpages/browser_trek.html', user=user, treks=treks, locations=locations)


@app.route('/user/<int:user_id>/trek/<int:trek_id>/view')
@user_required
def user_view_trek(user_id, trek_id):
    user = User.query.filter_by(user_id=user_id, role='User', is_blacklisted=False).first()
    trek = Trek.query.filter_by(trek_id=trek_id).first()
    booking = Booking.query.filter_by(user_id=user_id, trek_id=trek_id, status='Booked').first()
    current_date = date.today()
    return render_template('userpages/view_trek.html', user=user, trek=trek, booking=booking, current_date=current_date)

@app.route('/user/<int:user_id>/trek/<int:trek_id>/book', methods=['POST'])
@user_required
def book_trek(user_id, trek_id):
    trek = Trek.query.filter_by(trek_id=trek_id).first()

    existing = Booking.query.filter_by(user_id=user_id, trek_id=trek_id, status="Booked").first()

    if existing:
        return redirect(url_for('user_view_trek', user_id=user_id, trek_id=trek_id))

    if trek.available_slots > 0:
        trek.available_slots -= 1

    booking = Booking(user_id=user_id, trek_id=trek_id, booking_date=date.today(), status="Booked")

    db.session.add(booking)
    db.session.commit()
    return redirect(url_for('browse_trek', user_id=user_id))

@app.route('/user/<int:user_id>/trek/<int:trek_id>/cancel_booking', methods=["POST"])
@user_required
def cancel_booking(user_id, trek_id):
    booking = Booking.query.filter_by(user_id=user_id, trek_id=trek_id, status='Booked').first()
    if booking:

        booking.status = 'Canceled'
        trek = Trek.query.get(trek_id)
        trek.available_slots += 1
        db.session.commit()
    return redirect(url_for('browse_trek', user_id=user_id))


@app.route('/user/<int:user_id>/bookings')
@user_required
def user_bookings(user_id):
    user = User.query.filter_by(user_id=user_id, role='User', is_blacklisted=False).first()
    bookings = Booking.query.join(User, User.user_id==Booking.user_id).join(Trek, Trek.trek_id==Booking.trek_id).filter(User.user_id==user_id).all()
    return render_template('userpages/user_booking.html', bookings=bookings, user=user)

@app.route('/user/<int:user_id>/history')
@user_required
def user_history(user_id):
    user = User.query.filter_by(user_id=user_id, role='User', is_blacklisted=False).first()
    completed_treks = Booking.query.join(Trek, Trek.trek_id==Booking.trek_id).filter(Booking.user_id==user_id, Trek.status=='Completed').all()
    return render_template('userpages/history.html', user=user, completed_treks=completed_treks)
##########################################################################################################################################

# STAFF PART 

@app.route('/staff/<int:staff_id>/dashboard')
@staff_required
def staff_dashboard(staff_id):
    staff = StaffProfile.query.filter_by(staff_id=staff_id, status='Approved').first()

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
@staff_required
def staff_trek(staff_id):
    staff = StaffProfile.query.filter_by(staff_id=staff_id, status='Approved').first()
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
@staff_required
def staff_trek_manage(staff_id=None, trek_id=None):
    slots = request.args.get('slots')
    status = request.args.get('status')
    start = request.args.get('start')
    complete = request.args.get('complete')

    staff = StaffProfile.query.filter_by(staff_id=staff_id, status='Approved').first()
    
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

@app.route('/staff/<int:staff_id>/trek/<int:trek_id>/submit', methods=['POST'])
@staff_required
def staff_trek_submit(staff_id, trek_id):
    slots = int(request.form.get('slots'))
    status = request.form.get('status')
    trek = Trek.query.filter_by(trek_id=trek_id).first()
    trek.status = status
    trek.available_slots = slots

    booked_count = Booking.query.filter_by(trek_id=trek_id, status='Booked').count()
    trek.total_slots = slots + booked_count
    db.session.commit()
    return redirect(url_for('staff_trek', staff_id=staff_id))

@app.route('/staff/<int:staff_id>/trek/<int:trek_id>/start', methods=['POST'])
@staff_required
def staff_startTrek_button(staff_id, trek_id):
    trek=Trek.query.filter_by(trek_id=trek_id).first()
    if request.form['start']:
        trek.status = request.form['start']
        db.session.commit()
    return redirect(url_for('staff_trek', staff_id=staff_id))

@app.route('/staff/<int:staff_id>/trek/<int:trek_id>/complete', methods=['POST'])
@staff_required
def staff_completeTrek_button(staff_id, trek_id):
    trek = Trek.query.filter_by(trek_id=trek_id).first()
    if request.form['complete']:
        trek.status = request.form['complete']
        db.session.commit()
    return redirect(url_for('staff_trek', staff_id=staff_id))

@app.route('/staff/<int:staff_id>/trek_history')
@staff_required
def staff_trek_history(staff_id):
    staff = StaffProfile.query.filter_by(staff_id=staff_id, status='Approved').first()
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
@staff_required
def staff_trek_view(staff_id, trek_id):

    staff = StaffProfile.query.filter_by(staff_id=staff_id, status='Approved').first()
    
    trek = Trek.query.filter_by(trek_id=trek_id).first()
    active_bookings = Booking.query.filter(
        Booking.trek_id == trek_id, 
        Booking.status.in_(['Booked', 'Completed'])
    ).all()
    return render_template('staffpages/staff_trek_view.html',staff=staff, trek=trek, active_bookings=active_bookings)

@app.route('/staff/<int:staff_id>/participants')
@staff_required
def staff_participant(staff_id):
    staff = StaffProfile.query.filter_by(staff_id=staff_id, status='Approved').first()
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
##########################################################################################################################################
#  CLOSING THE BOOKING WHENT HE LAST BOOKING DATE IS PASSED
def trek_close_after_last_booking_date():
    for trek in Trek.query.filter(Trek.last_booking_date < date.today()).all():
        trek.status = 'Closed'
    for trek in Trek.query.filter( Trek.end_date <= date.today()).all():
        trek.status = 'Completed'
        for booking in trek.bookings:
            booking.status = 'Completed'
    for trek in Trek.query.filter_by(status='Completed').all():
        for booking in trek.bookings:
            booking.status = 'Completed'
    db.session.commit()


@app.before_request
def update_trek_statuses():
    trek_close_after_last_booking_date()

@app.route('/testing')
def testing():

    return render_template('side_nav_bar.html')

if __name__ == "__main__":
    app.run(debug=True)