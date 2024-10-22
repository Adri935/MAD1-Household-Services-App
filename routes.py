from flask import render_template,url_for,request,flash,redirect,current_app
from app import app
from models import db,User,Customer,ServiceProfessional,Service
from flask_bcrypt import Bcrypt
from flask_login import login_user,current_user,logout_user,login_required
from dotenv import load_dotenv
import os
import secrets

bc = Bcrypt()
load_dotenv()

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return  render_template('customer_dashboard.html',title='Home')


@app.route("/login", methods=['GET','POST'])
def  login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Please enter your Email and Password to log in','danger')
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Invalid Email. No such user exists.','danger')
            return redirect(url_for('login'))

        if user:
            if bc.check_password_hash(user.password, password):
                login_user(user,remember=True)
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect password. Please try again.','danger')
        return redirect(url_for('login'))
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html',title='Login')

@app.route("/logout") 
def logout():
    logout_user()
    flash("Logged out successfully.",'success')
    return redirect(url_for('login'))

@app.route("/customer_register", methods=['GET','POST'])
def customer_register():
    if request.method=='POST':
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

        user =  User.query.filter_by(email=email).first()
        if user:
            flash('Account already exists. Please login or use a different Email ID.','danger')
            return redirect(url_for('login'))
        
        pwd_hash = bc.generate_password_hash(password)

        new_user = User(email=email,password=pwd_hash,role='customer')
        db.session.add(new_user)
        db.session.commit()
        user = User.query.filter_by(email=email).first()
        new_cust = Customer(user_id=user.id,name=name,phone=phone,address=address,pincode=pincode)
        flash('Account created successfully. Please login to continue.','success')
        return redirect(url_for('login'))

    return render_template('customer_register.html',title='Customer Registration')

    

@app.route("/professional_register",methods=['GET','POST'])
def professional_register():
    services = Service.query.all()
    if request.method=='POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        conf_pwd = request.form.get('confirmpassword')
        phone = request.form.get('mobile')
        service_id = request.form.get('serviceType')
        experience = request.form.get('experience')
        address = request.form.get('address')
        pincode = request.form.get('pincode')

        photo = request.files.get('photo')
        id_proof = request.files.get('idProof')
        certification = request.files.get('certification')

        if not name or not email or not password or not conf_pwd or not phone or not service_id or not experience or not id_proof or not address or not pincode:
            flash('Please fill all the fields','danger')
            return redirect(url_for('professional_register'))

        if conf_pwd!=password:
            flash('Passwords do not match. Please try again.','danger')
            return redirect(url_for('professional_register'))
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Account already exists. Please login or use a different Email ID.','danger')
            return redirect(url_for('login'))

        pwd_hash = bc.generate_password_hash(password)
        new_user = User(email=email,password=pwd_hash,role='professional')
        db.session.add(new_user)
        db.session.commit()
        user = User.query.filter_by(email=email).first()

        photo_path = None
        id_proof_path = None
        certification_path = None

        if photo:
            _ , ext = os.path.splitext(photo.filename)
            filename = secrets.token_hex(8) + ext
            photo_path = os.path.join('static/profile_pics', filename)
            photo.save(os.path.join(current_app.root_path, photo_path))  

        if id_proof:
            _ , ext = os.path.splitext(id_proof.filename)
            filename = secrets.token_hex(8) + ext
            id_proof_path = os.path.join('static/id_proof', filename)
            id_proof.save(os.path.join(current_app.root_path, id_proof_path))  

        if certification:
            _ , ext = os.path.splitext(certification.filename)
            filename = secrets.token_hex(8) + ext
            certification_path = os.path.join('static/certifications', filename)
            certification.save(os.path.join(current_app.root_path, certification_path))  

        new_professional = ServiceProfessional(
            user_id=user.id,
            name=name,
            phone=phone,
            service_id=service_id,
            experience=experience,
            identity_proof=id_proof_path,
            photo=photo_path if photo_path else "static/defaultpfp.jpeg",  # Default photo if not uploaded
            certifications=certification_path if certification_path else None,
            address=address,
            pincode=pincode
        )
        db.session.add(new_professional)
        db.session.commit()
        flash('Account created successfully. Please wait for approval.','success')
        return redirect(url_for('login'))
        

    return render_template('professional_register.html',title='Service Professional Registration',services=services)

@app.route("/dashboard")
@login_required
def dashboard():
    services = Service.query.all()
    customers = Customer.query.all()
    professionals = ServiceProfessional.query.all()
    if current_user.role == 'admin':
        return render_template('admin_dashboard.html',title='Admin Dashboard',services=services, customers=customers, professionals=professionals, blockedUsers=[user.id for user in User.query.filter_by(blocked=True).all()])
    if current_user.role == 'customer':
        return render_template('customer_dashboard.html',title='Home')
    if  current_user.role == 'professional':
        return render_template('professional_dashboard.html',title='Home')
    

@app.route('/edit_service', methods=['GET', 'POST'])
def edit_service():
    services = Service.query.all()
    if request.method == 'POST':
        service_id = request.form.get('id')
        service = Service.query.get(service_id)
        service.name = request.form['name']
        service.description = request.form['description']
        service.price = request.form['price']
        service.time_required = request.form['time_required']
        db.session.commit()
        return redirect(url_for('dashboard'))

    # If request is GET, load the service to edit
    service_id = request.args.get('service_id')
    service_to_edit = Service.query.get(service_id)
    return render_template('admin_dashboard.html', service_to_edit=service_to_edit, title='Admin Dashboard', services=services, customers=Customer.query.all(), professionals=ServiceProfessional.query.all(), blockedUsers= [user.id for user in User.query.filter_by(blocked=True).all()])

@app.route('/delete_service', methods=['GET', 'POST'])
def delete_service():
    services = Service.query.all()
    if request.method == 'POST':
        service_id = request.form.get('id')
        service = Service.query.get(service_id)
        db.session.delete(service)
        db.session.commit()
        return redirect(url_for('dashboard'))

    # If request is GET, load the service to delete
    service_id = request.args.get('service_id')
    delete_service = Service.query.get(service_id)
    return render_template('admin_dashboard.html', delete_service=delete_service, title='Admin Dashboard', services=services, customers=Customer.query.all(), professionals=ServiceProfessional.query.all(), blockedUsers= [user.id for user in User.query.filter_by(blocked=True).all()])

@app.route('/add_service', methods=['GET', 'POST'])
def add_service():
    services = Service.query.all()
    if request.method == 'POST':
        new_service = Service(
            name=request.form['name'],
            description=request.form['description'],
            price=request.form['price'],
            time_required=request.form['time_required']
        )
        db.session.add(new_service)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('admin_dashboard.html', add_service=True, title='Admin Dashboard', services=services, customers=Customer.query.all(), professionals=ServiceProfessional.query.all(), blockedUsers= [user.id for user in User.query.filter_by(blocked=True).all()])

@app.route('/approve_professional', methods=['GET', 'POST'])
def approve_professional():
    professionals = ServiceProfessional.query.all()
    if request.method == 'POST':
        professional_id = request.form.get('prof_id')
        professional = ServiceProfessional.query.get(professional_id)
        professional.is_approved = True
        db.session.commit()
        return redirect(url_for('dashboard'))

    # If request is GET, load the professional to approve
    professional_id = request.args.get('prof_id')
    approve_professional = ServiceProfessional.query.get(professional_id)
    return render_template('admin_dashboard.html', approve_professional=approve_professional, title='Admin Dashboard', services=Service.query.all(), customers=Customer.query.all(), professionals=professionals, blockedUsers= [user.id for user in User.query.filter_by(blocked=True).all()])

@app.route('/block_user', methods=['GET', 'POST'])
def block_user():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        user.blocked = True
        db.session.commit()
        return redirect(url_for('dashboard'))

    # If request is GET, load the user to block
    user_id = request.args.get('user_id')
    block_user = User.query.get(user_id)
    return render_template('admin_dashboard.html', block_user=block_user, title='Admin Dashboard', services=Service.query.all(), customers=Customer.query.all(), professionals=ServiceProfessional.query.all(), blockedUsers= [user.id for user in User.query.filter_by(blocked=True).all()])

@app.route('/unblock_user', methods=['GET', 'POST'])
def unblock_user():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        user.blocked = False
        db.session.commit()
        return redirect(url_for('dashboard'))

    # If request is GET, load the user to block
    user_id = request.args.get('user_id')
    unblock_user = User.query.get(user_id)
    return render_template('admin_dashboard.html', unblock_user=unblock_user, title='Admin Dashboard', services=Service.query.all(), customers=Customer.query.all(), professionals=ServiceProfessional.query.all(), blockedUsers= [user.id for user in User.query.filter_by(blocked=True).all()])