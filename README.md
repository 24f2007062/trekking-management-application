# Trekking Management Application

## Overview

The Trekking Management Application is a role-based web application developed using **Flask**. It provides a centralized platform for managing trekking activities involving three different user roles:

- **Admin**
- **Trek Staff**
- **Trekker (User)**

The application allows administrators to manage treks, approve staff members, assign staff to treks, manage bookings, and monitor users. Trek Staff can manage assigned treks and participants, while Trekkers can browse, search, and book trekking events.

---

# Features

## Admin

- Login as predefined administrator
- Dashboard with statistics
- Create, edit and delete treks
- Approve or blacklist trek staff
- Assign staff to treks
- Manage users
- View bookings
- Search users, staff and treks

---

## Trek Staff

- Registration and Login
- View assigned treks
- Update trek status
- Update available slots
- View participants
- Trek management

---

## Trekker

- Registration and Login
- Browse available treks
- Search and filter treks
- Book and cancel treks
- View booking history
- Dashboard

---

# Technologies Used

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- Jinja2
- HTML5
- CSS3
- Bootstrap 5
- Werkzeug

---

# Database

The application uses **SQLite** and consists of the following tables:

- User
- StaffProfile
- Trek
- Booking

Relationships

- User → Booking (One-to-Many)
- Trek → Booking (One-to-Many)
- StaffProfile → Trek (One-to-Many)

---

# Installation

## 1. Clone the repository

```bash
git clone <repository-url>
cd Trekking-Management-Application
```

---

## 2. Install dependencies

```bash
pip install flask flask-sqlalchemy
```

---

## 3. Create the database

Open Python inside the project folder.

```bash
python
```

Run the following commands.

```python
from app import app, db

with app.app_context():
    db.create_all()
```

Exit Python.

```python
exit()
```

---

## 4. Create the Admin Account

Open Python again.

```bash
python
```

Run

```python
from app import app, db
from models import User

with app.app_context():
    admin = User(
        name="Admin",
        email="admin@example.com",
        password="admin123",
        phone="9999999999",
        role="Admin"
    )

    db.session.add(admin)
    db.session.commit()
```

Exit Python.

---

## 5. Run the Application

```bash
python app.py
```

Open your browser.

```
http://127.0.0.1:5000
```

---

# Default Admin Login

Email

```
admin@example.com
```

Password

```
admin123
```

*(Replace these with your own credentials if different.)*

---

# Staff and User Login
Happens through login page or Registration page

# Project Structure

```
├── app.py
├── models.py
├── security.py
├── static/
│   ├── css/
│   ├── images/
│   └── uploads/
├── templates/
│   ├── adminpages/
│   ├── staffpages/
│   ├── userpages/
│   └── base templates
├── instance/
└── README.md
```

---

# Future Improvements

- Password hashing
- Email verification
- REST APIs
- Charts and analytics
- Online payment integration

---

# Author

**Ahmar Rehan**

BS Degree in Data Science

Indian Institute of Technology Madras