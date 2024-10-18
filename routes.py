from flask import render_template,url_for,request,flash,redirect
from app import app
from models import db,Customer,ServiceProfessional
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os

bc = Bcrypt()

@app.route("/")
@app.route("/login")
def login():
    return render_template('login.html',title='Login')

@app.route("/login", methods=['POST'])
def  login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    if not email or not password:
        flash('Please enter your Email and Password to log in','danger')
    
    if email == 'admin.homeease@homeease.com' and password == os.getenv('adminpwd'):
        return redirect(url_for('admin_dashboard'))

    user1 = Customer.query.filter_by(email=email).first()
    user2 = ServiceProfessional.query.filter_by(email=email).first()

    if not user1 and not user2:
        flash('Invalid Email. No such user exists.','danger')
        return redirect(url_for('login'))

    if user1 and bc.check_password_hash(user1.password, password):
        return redirect(url_for('customer_dashboard'))

    if user2 and bc.check_password_hash(user2.password, password):
        return redirect(url_for('professional_dashboard'))

    

@app.route("/customer_register")
def customer_register():
    return render_template('customer_register.html',title='Customer Registration')

@app.route("/customer_register", methods=['POST'])
def customer_register_post():
    password = request.form.get('password')
    email = request.form.get('email')
    conf_pwd = request.form.get('confirmpassword')
    name = request.form.get('name')
    phone = request.form.get('mobile')
    address = request.form.get('address')
    pincode = request.form.get('pincode')

    if not name or not email or not password or not conf_pwd  or not phone or not address or not pincode:
        flash('Please fill all the fields', 'danger')
        return redirect(url_for('customer_register'))

    if conf_pwd!=password:
        flash('Passwords do not match. Please try again.','danger')
        return redirect(url_for('customer_register'))

    user =  Customer.query.filter_by(email=email).first()
    if user:
        flash('Account already exists. Please login or use a different Email ID.','danger')
        return redirect(url_for('login'))
    
    pwd_hash = bc.generate_password_hash(password)

    new_user = Customer(name=name,password=pwd_hash,email=email,phone=phone,address=address,pincode=pincode)
    db.session.add(new_user)
    db.session.commit()
    flash('Account created successfully. Please login to continue.','success')
    return redirect(url_for('login'))


@app.route("/professional_register")
def professional_register():
    return render_template('professional_register.html',title='Service Professional Registration')

@app.route("/admin_dashboard")
def admin_dashboard():
    return render_template('admin_dashboard.html',title='Admin Dashboard')

@app.route("/customer_dashboard")
def customer_dashboard():
    return render_template('customer_dashboard.html',title='Customer Dashboard')

@app.route("/professional_dashboard")
def professional_dashboard():
    return render_template('professional_dashboard.html',title='Service Professional Dashboard')