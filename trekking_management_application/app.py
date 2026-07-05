from flask import Flask, render_template, request, redirect, url_for
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

@app.route('/admin/trek', methods=['GET', 'POST'])
@app.route('/admin/trek/<int:trek_id>', methods=['POST'], endpoint='trek_delete_action')
def admin_trek_manager(trek_id=None):
    if request.method=='POST':
        delete=False
        if request.form['delete_clicked'] == 'True':
            delete=True
            print(trek_id)
        if delete:
            del_trek=Trek.query.filter_by(trek_id=trek_id).first()
            db.session.delete(del_trek)
            db.session.commit()
    treks = Trek.query.all()
    return render_template('adminpages/trek.html', treks=treks)


@app.route('/admin/trek/<int:trek_id>/view')
def view_trek(trek_id):
    trek=Trek.query.filter_by(trek_id=trek_id).first()
    return render_template('adminpages/view_trek.html', trek=trek)

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
        trek.start_date = request.form['s_date']
        trek.end_date = request.form['e_date']
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
        start_date = request.form['s_date']
        end_date = request.form['e_date']
        status = request.form['status']
        description = request.form['description']
        assigned_staff_id = request.form['staff']

        trek = Trek(trek_name=trek_name, location=location, difficulty=difficulty, duration=duration, total_slots=total_slots, available_slots=total_slots, start_date=start_date, end_date=end_date, status=status, description=description, assigned_staff_id=assigned_staff_id)
        db.session.add(trek)
        db.session.commit()
        return redirect('/admin/trek')

    staffs=StaffProfile.query.filter_by(status='Approved').all()
    return render_template('adminpages/add_trek.html', staffs=staffs)




@app.route('/admin/staff')
def admin_staff():
    current_tab = request.args.get('tab', 'Pending')
    status = request.args.get("status")
    staff_id = request.args.get("id")
    staff = StaffProfile.query.filter_by(staff_id=staff_id).first()
    print(status, staff_id)
    if status:
        staff.status=status
        db.session.commit()
    
    staffs=StaffProfile.query.filter_by(status=current_tab).all()
    return render_template('adminpages/staff.html', staffs=staffs, status=status, current_tab=current_tab)

##########################################################################################################################################

# USER PART

@app.route('/user/<int:user_id>')
def user_dashboard(user_id):
    user = User.query.filter_by(user_id=user_id).first()

    return render_template('userpages/dashboard.html', user=user)


##########################################################################################################################################

# STAFF PART 

@app.route('/staff/<int:staff_id>')
def staff_dashboard(staff_id):
    staff = StaffProfile.query.filter_by(staff_id=staff_id).first()
    return render_template('staffpages/dashboard.html', staff=staff)


@app.route('/testing')
def testing():
    return render_template('side_nav_bar.html')

if __name__ == "__main__":
    app.run(debug=True)