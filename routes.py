from flask import render_template,url_for,request,flash,redirect,current_app
from app import app
from models import db,User,Customer,ServiceProfessional,Service,ServiceRequest,Review,RequestRejected
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
def login():
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
        db.session.add(new_cust)
        db.session.commit()
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
            identity_proof=id_proof_path.replace('\\', '/'),
            photo=photo_path.replace('\\', '/') if photo_path else "static/defaultpfp.jpeg",
            certifications=certification_path.replace('\\', '/') if certification_path else None,
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
        user = Customer.query.filter_by(user_id=current_user.id).first()        
        requests = ServiceRequest.query.filter_by(cust_id=user.id).all()
        return render_template('customer_dashboard.html',title='Home', user=user, professionals=professionals, requests=requests, services=services, blocked=current_user.blocked)
    if  current_user.role == 'professional':
        user = ServiceProfessional.query.filter_by(user_id=current_user.id).first()
        new_requests = ServiceRequest.query.filter_by(service_id=user.service_id).filter_by(service_status='requested').all()
        prev_requests = ServiceRequest.query.filter_by(prof_id=user.id).all()
        return render_template('professional_dashboard.html',title='Home', user=user, new_requests=new_requests, prev_requests=prev_requests, blocked=current_user.blocked)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        user = db.session.get(User,current_user.id)
        if user.role == 'customer':
            customer = Customer.query.filter_by(user_id=user.id).first()
            customer.name = request.form['name']
            customer.phone = request.form['phone']
            customer.address = request.form['address']
            customer.pincode = request.form['pincode']
            customer.photo = customer.photo

            photo = request.files.get('photo') if request.files.get('photo') else None
            photo_path = customer.photo
            if photo != None:
                _ , ext = os.path.splitext(photo.filename)
                filename = secrets.token_hex(8) + ext
                photo_path = os.path.join('static/profile_pics', filename)
                photo.save(os.path.join(current_app.root_path, photo_path))
                path = customer.photo
                if path!='static/defaultpfp.jpeg' and path!=None:
                    os.remove(os.path.join(current_app.root_path, path))
            customer.photo = photo_path.replace('\\', '/')

            db.session.commit()
            flash('Profile updated successfully.','success')
            return redirect(url_for('profile'))

        elif user.role == 'professional':
            professional = ServiceProfessional.query.filter_by(user_id=user.id).first()
            professional.name = request.form['name']
            professional.phone = request.form['phone']
            professional.address = request.form['address']
            professional.pincode = request.form['pincode']

            photo = request.files.get('photo') if request.files.get('photo') else None
            certifications = request.files.get('certifications') if request.files.get('certifications') else None
            photo_path = professional.photo 
            certifications_path = professional.certifications
            if photo != None:
                _ , ext1 = os.path.splitext(photo.filename)
                filename = secrets.token_hex(8) + ext1
                photo_path = os.path.join('static/profile_pics', filename)
                photo.save(os.path.join(current_app.root_path, photo_path))
                path = professional.photo
                if path!='static/defaultpfp.jpeg':
                    os.remove(os.path.join(current_app.root_path, path))
            professional.photo = photo_path.replace('\\', '/')
            
            if certifications != None:
                _ , ext2 = os.path.splitext(certifications.filename)
                filename = secrets.token_hex(8) + ext2
                certifications_path = os.path.join('static/certifications', filename)
                certifications.save(os.path.join(current_app.root_path, certifications_path))
                path = professional.certifications
                if path!=None:
                    os.remove(os.path.join(current_app.root_path, path))
            professional.certifications = certifications_path.replace('\\', '/')

            db.session.commit()
            flash('Profile updated successfully.','success')
            return redirect(url_for('profile'))

    if current_user.role == 'customer':
        email = User.query.filter_by(id=current_user.id).first().email
        customer = Customer.query.filter_by(user_id=current_user.id).first()
        return render_template('profile.html', user=customer, email=email, blocked=current_user.blocked)

    elif current_user.role == 'professional':
        email = current_user.email
        professional = ServiceProfessional.query.filter_by(user_id=current_user.id).first()
        return render_template('profile.html', user=professional, email=email, blocked=current_user.blocked)

    else:
        return render_template('profile.html', user=current_user, email=current_user.email)

### ADMIN ROUTES ###    

@app.route('/edit_service', methods=['GET', 'POST'])
def edit_service():
    services = Service.query.all()
    if request.method == 'POST':
        service_id = request.form.get('id')
        service = db.session.get(Service,service_id)
        service.name = request.form['name']
        service.description = request.form['description']
        service.price = request.form['price']
        service.time_required = request.form['time_required']
        db.session.commit()
        flash('Service updated successfully.','success')
        return redirect(url_for('dashboard'))

    # If request is GET, load the service to edit
    service_id = request.args.get('service_id')
    service_to_edit = db.session.get(Service,service_id)
    return render_template('admin_dashboard.html', service_to_edit=service_to_edit, title='Admin Dashboard', services=services, customers=Customer.query.all(), professionals=ServiceProfessional.query.all(), blockedUsers= [user.id for user in User.query.filter_by(blocked=True).all()])

@app.route('/delete_service', methods=['GET', 'POST'])
def delete_service():
    services = Service.query.all()
    if request.method == 'POST':
        service_id = request.form.get('id')
        service = db.session.get(Service,service_id)
        db.session.delete(service)
        db.session.commit()
        flash('Service deleted successfully.','success')
        return redirect(url_for('dashboard'))

    # If request is GET, load the service to delete
    service_id = request.args.get('service_id')
    delete_service = db.session.get(Service,service_id)
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
        flash('Service added successfully.','success')
        return redirect(url_for('dashboard'))

    return render_template('admin_dashboard.html', add_service=True, title='Admin Dashboard', services=services, customers=Customer.query.all(), professionals=ServiceProfessional.query.all(), blockedUsers= [user.id for user in User.query.filter_by(blocked=True).all()])

@app.route('/approve_professional', methods=['GET', 'POST'])
def approve_professional():
    professionals = ServiceProfessional.query.all()
    if request.method == 'POST':
        professional_id = request.form.get('prof_id')
        professional = db.session.get(ServiceProfessional,professional_id)
        professional.is_approved = True
        db.session.commit()
        flash('Professional approved successfully.','success')
        return redirect(url_for('dashboard'))

    # If request is GET, load the professional to approve
    professional_id = request.args.get('prof_id')
    approve_professional = db.session.get(ServiceProfessional,professional_id)
    return render_template('admin_dashboard.html', approve_professional=approve_professional, title='Admin Dashboard', services=Service.query.all(), customers=Customer.query.all(), professionals=professionals, blockedUsers= [user.id for user in User.query.filter_by(blocked=True).all()])

@app.route('/block_user', methods=['GET', 'POST'])
def block_user():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = db.session.get(User,user_id)
        user.blocked = True
        db.session.commit()
        flash('User blocked successfully.','success')
        return redirect(url_for('dashboard'))

    # If request is GET, load the user to block
    user_id = request.args.get('user_id')
    block_user = db.session.get(User,user_id)
    return render_template('admin_dashboard.html', block_user=block_user, title='Admin Dashboard', services=Service.query.all(), customers=Customer.query.all(), professionals=ServiceProfessional.query.all(), blockedUsers= [user.id for user in User.query.filter_by(blocked=True).all()])

@app.route('/unblock_user', methods=['GET', 'POST'])
def unblock_user():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = db.session.get(User,user_id)
        user.blocked = False
        db.session.commit()
        flash('User unblocked successfully.','success')
        return redirect(url_for('dashboard'))

    # If request is GET, load the user to block
    user_id = request.args.get('user_id')
    unblock_user = db.session.get(User,user_id)
    return render_template('admin_dashboard.html', unblock_user=unblock_user, title='Admin Dashboard', services=Service.query.all(), customers=Customer.query.all(), professionals=ServiceProfessional.query.all(), blockedUsers= [user.id for user in User.query.filter_by(blocked=True).all()])

### CUSTOMER ROUTES ###
@app.route('/services', methods=['GET', 'POST'])
def services():
    stype = request.args.get('stype')
    if stype == 'cleaning':
        services = Service.query.filter(Service.name.ilike('%cleaning%')).all()
        return render_template('services.html', title='Services', stype=stype, services=services)

    elif stype == 'repair':
        services = Service.query.filter(Service.name.ilike('%repair%')).all()
        return render_template('services.html', title='Services', stype=stype, services=services)

    elif stype == 'salon':
        services = Service.query.filter(Service.name.ilike('%salon%')).all()
        return render_template('services.html', title='Services', stype=stype, services=services)

    elif stype == 'plumbing':
        services = Service.query.filter(Service.name.ilike('%plumbing%')).all()
        return render_template('services.html', title='Services', stype=stype, services=services)

    elif stype == 'electrical':
        services = Service.query.filter(Service.name.ilike('%electrical%')).all()
        return render_template('services.html', title='Services', stype=stype, services=services)

    else:
        services = Service.query.order_by(Service.name).all()
        return render_template('services.html', title='Services', services=services)
        

@app.route('/book_service', methods=['GET', 'POST'])
def book_service():
    if request.method == 'POST':
        stype = request.form.get('stype')
        service_id = request.form.get('id')
        cust_id = Customer.query.filter_by(user_id=current_user.id).first().id
        pincode = Customer.query.filter_by(user_id=current_user.id).first().pincode
        address = Customer.query.filter_by(user_id=current_user.id).first().address
        remarks = request.form.get('remarks')
        new_request = ServiceRequest(
            service_id=service_id,
            cust_id=cust_id,
            pincode=pincode,
            address=address,
            remarks=remarks
        )
        db.session.add(new_request)
        db.session.commit()
        flash('Service booked successfully.','success')
        return redirect(url_for('services',stype=stype))

    stype = request.args.get('stype')
    if stype == 'cleaning':
        services = Service.query.filter(Service.name.ilike('%cleaning%')).all()
    elif stype == 'repair':
        services = Service.query.filter(Service.name.ilike('%repair%')).all()
    elif stype == 'salon':
        services = Service.query.filter(Service.name.ilike('%salon%')).all()
    elif stype == 'plumbing':
        services = Service.query.filter(Service.name.ilike('%plumbing%')).all()
    elif stype == 'electrical':
        services = Service.query.filter(Service.name.ilike('%electrical%')).all()
    else:
        services = Service.query.order_by(Service.name).all()
    service_id = request.args.get('service_id')
    service = db.session.get(Service,service_id)
    customer = Customer.query.filter_by(user_id=current_user.id).first()
    return render_template('services.html', title='Services', stype=stype, services=services, bookservice=service, customer=customer)

@app.route('/edit_remarks', methods=['GET', 'POST'])
def edit_remarks():
    if request.method == 'POST':
        request_id = request.form.get('id')
        req = db.session.get(ServiceRequest,request_id)
        req.remarks = request.form['remarks']
        db.session.commit()
        flash('Remarks updated successfully.','success')
        return redirect(url_for('dashboard'))

    request_id = request.args.get('request_id')
    req = db.session.get(ServiceRequest,request_id)
    user = Customer.query.filter_by(user_id=current_user.id).first()        
    requests = ServiceRequest.query.filter_by(cust_id=user.id).all()
    return render_template('customer_dashboard.html',title='Home', user=user, requests=requests, services=services, edit_remarks=req, blocked=current_user.blocked)


### SEARCH ROUTES ###
@app.route('/search', methods=['GET', 'POST'])
def search():
    if not current_user.is_authenticated:
        search_by=request.args.get('search_by')
        search_term=request.args.get('search_term')
        if search_by == 'name':
            services = Service.query.filter(Service.name.ilike(f'%{search_term}%')).all()
        elif search_by == 'price':
            services = Service.query.filter(Service.price<=int(search_term)).order_by(Service.price.desc()).all()
        else:
            services = Service.query.all()
        return render_template('customer_search.html', title='Search', services=services)
    elif current_user.role == 'customer':
        search_by=request.args.get('search_by')
        search_term=request.args.get('search_term')
        if search_by == 'name':
            services = Service.query.filter(Service.name.ilike(f'%{search_term}%')).all()
        elif search_by == 'price':
            services = Service.query.filter(Service.price<=int(search_term)).order_by(Service.price.desc()).all()
        else:
            services = Service.query.all()
        return render_template('customer_search.html', title='Search', services=services)
    elif current_user.role == 'admin':
        return render_template('admin_search.html', title='Search')

    elif current_user.role == 'professional':
        return render_template('professional_search.html', title='Search')

@app.route('/book_searched_service', methods=['GET', 'POST'])
def book_search_service():
    if request.method == 'POST':
        service_id = request.form.get('id')
        cust_id = Customer.query.filter_by(user_id=current_user.id).first().id
        pincode = Customer.query.filter_by(user_id=current_user.id).first().pincode
        address = Customer.query.filter_by(user_id=current_user.id).first().address
        remarks = request.form.get('remarks')
        new_request = ServiceRequest(
            service_id=service_id,
            cust_id=cust_id,
            pincode=pincode,
            address=address,
            remarks=remarks
        )
        db.session.add(new_request)
        db.session.commit()
        flash('Service booked successfully.','success')
        return redirect(url_for('search'))

    service_id = request.args.get('service_id')
    service = db.session.get(Service,service_id)
    customer = Customer.query.filter_by(user_id=current_user.id).first()
    return render_template('customer_search.html', title='Book Service', bookservice=service, customer=customer)

### PROFESSIONAL ROUTES ###
@app.route('/accept_request', methods=['GET', 'POST'])
def accept_request():
    if request.method == 'POST':
        request_id = request.form.get('id')
        req = db.session.get(ServiceRequest,request_id)
        req.prof_id = ServiceProfessional.query.filter_by(user_id=current_user.id).first().id
        req.service_status = 'accepted'
        db.session.commit()
        flash('Request accepted successfully.','success')
        return redirect(url_for('dashboard'))

    request_id = request.args.get('request_id')
    user = ServiceProfessional.query.filter_by(user_id=current_user.id).first()
    new_requests = ServiceRequest.query.filter_by(service_id=user.service_id).filter_by(service_status='requested').all()
    prev_requests = ServiceRequest.query.filter_by(prof_id=user.id).all()
    req = db.session.get(ServiceRequest,request_id)
    return render_template('professional_dashboard.html', title='Home', accept_request=req, user=user, new_requests=new_requests, prev_requests=prev_requests, blocked=current_user.blocked)


@app.route('/reject_request', methods=['GET', 'POST'])
def reject_request():
    if request.method == 'POST':
        request_id = request.form.get('id')
        prof_id = ServiceProfessional.query.filter_by(user_id=current_user.id).first().id
        new_reject = RequestRejected(service_request_id=request_id, prof_id=prof_id)
        db.session.add(new_reject)
        db.session.commit()
        flash('Request rejected successfully.','success')
        return redirect(url_for('dashboard'))

    request_id = request.args.get('request_id')
    user = ServiceProfessional.query.filter_by(user_id=current_user.id).first()
    new_requests = ServiceRequest.query.filter_by(service_id=user.service_id).filter_by(service_status='requested').all()
    prev_requests = ServiceRequest.query.filter_by(prof_id=user.id).all()
    req = db.session.get(ServiceRequest,request_id)
    return render_template('professional_dashboard.html', title='Home', reject_request=req, user=user, new_requests=new_requests, prev_requests=prev_requests, blocked=current_user.blocked)

@app.route('/in_progress', methods=['GET', 'POST'])
def in_progress():
    if request.method == 'POST':
        request_id = request.form.get('id')
        req = db.session.get(ServiceRequest,request_id)
        req.service_status = 'in progress'
        db.session.commit()
        flash('Request status updated successfully.','success')
        return redirect(url_for('dashboard'))

    request_id = request.args.get('request_id')
    user = ServiceProfessional.query.filter_by(user_id=current_user.id).first()
    new_requests = ServiceRequest.query.filter_by(service_id=user.service_id).filter_by(service_status='requested').all()
    prev_requests = ServiceRequest.query.filter_by(prof_id=user.id).all()
    req = db.session.get(ServiceRequest,request_id)
    return render_template('professional_dashboard.html', title='Home', in_progress=req, user=user, new_requests=new_requests, prev_requests=prev_requests, blocked=current_user.blocked)
