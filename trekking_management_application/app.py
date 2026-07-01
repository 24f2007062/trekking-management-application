from flask import Flask, render_template, request, redirect, url_for
from models import *


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking_management.db'
db.init_app(app)
app.app_context().push()


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
    


@app.route('/admin')
def admin_dashboard():
    return render_template('adminpages/dashboard.html')


@app.route('/user/<int:user_id>')
def user_dashboard(user_id):
    user = User.query.filter_by(user_id=user_id).first()

    return render_template('userpages/dashboard.html', user=user)

@app.route('/staff/<int:staff_id>')
def staff_dashboard(staff_id):
    staff = StaffProfile.query.filter_by(staff_id=staff_id).first()
    return render_template('staffpages/dashboard.html', staff=staff)


@app.route('/testing')
def testing():
    return render_template('side_nav_bar.html')

if __name__ == "__main__":
    app.run(debug=True)