from flask import render_template,url_for,request,flash,redirect,current_app
from app import app
from datetime import datetime
from models import db,User,Customer,ServiceProfessional,Service,ServiceRequest,Review,RequestRejected,ReportCustomer
from sqlalchemy import func, or_
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

        if not name or not email or not password or not conf_pwd or not phone or not service_id or not experience or not id_proof or not address or not pincode or not certification:
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
        requests = ServiceRequest.query.order_by(ServiceRequest.date_of_request.desc()).all()
        reviews = Review.query.order_by(Review.date_submitted.desc()).all()
        return render_template('admin_dashboard.html',title='Admin Dashboard',services=services, customers=customers, professionals=professionals, requests=requests, reviews=reviews, blockedUsers=[user.id for user in User.query.filter_by(blocked=True).all()])
    if current_user.role == 'customer':
        user = Customer.query.filter_by(user_id=current_user.id).first()        
        requests = ServiceRequest.query.filter_by(cust_id=user.id).order_by(ServiceRequest.date_of_request.desc()).all()
        return render_template('customer_dashboard.html',title='Home', user=user, professionals=professionals, requests=requests, services=services, blocked=current_user.blocked)
    if  current_user.role == 'professional':
        user = ServiceProfessional.query.filter_by(user_id=current_user.id).first()
        new_requests = ServiceRequest.query.filter_by(service_id=user.service_id).filter_by(service_status='requested').all()
        prev_requests = ServiceRequest.query.filter_by(prof_id=user.id).order_by(ServiceRequest.date_of_request.desc()).all()
        rej_requests = db.session.query(RequestRejected.service_request_id).filter(RequestRejected.prof_id==user.id).all()
        rejected_requests = [x for (x,) in rej_requests]
        reviews = Review.query.filter_by(professional_id=user.id).order_by(Review.date_submitted.desc()).all()
        return render_template('professional_dashboard.html',title='Home', user=user, new_requests=new_requests, rejected_requests=rejected_requests, prev_requests=prev_requests, reviews=reviews, blocked=current_user.blocked)

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
        rating = Review.query.with_entities(db.func.avg(Review.rating)).filter_by(professional_id=professional.id).first()[0]
        return render_template('profile.html', user=professional, email=email, rating=rating, blocked=current_user.blocked)

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

@app.route('/view_reports')
def view_reports():
    customer_id = request.args.get('customer_id')
    reports = ReportCustomer.query.filter_by(customer_id=customer_id).all()
    return render_template('admin_dashboard.html', title='Admin Dashboard', reports=reports, services=Service.query.all(), customers=Customer.query.all(), professionals=ServiceProfessional.query.all(), blockedUsers= [user.id for user in User.query.filter_by(blocked=True).all()])

### CUSTOMER ROUTES ###
@app.route('/services', methods=['GET', 'POST'])
def services():
    stype = request.args.get('stype')
    userblocked = current_user.blocked if current_user.is_authenticated else False
    if stype == 'cleaning':
        services = Service.query.filter(Service.name.ilike('%cleaning%')).all()
        return render_template('services.html', title='Services', stype=stype, services=services, blocked=userblocked)

    elif stype == 'repair':
        services = Service.query.filter(Service.name.ilike('%repair%')).all()
        return render_template('services.html', title='Services', stype=stype, services=services, blocked=userblocked)

    elif stype == 'salon':
        services = Service.query.filter(Service.name.ilike('%salon%')).all()
        return render_template('services.html', title='Services', stype=stype, services=services, blocked=userblocked)

    elif stype == 'plumbing':
        services = Service.query.filter(Service.name.ilike('%plumbing%')).all()
        return render_template('services.html', title='Services', stype=stype, services=services, blocked=userblocked)

    elif stype == 'electrical':
        services = Service.query.filter(Service.name.ilike('%electrical%')).all()
        return render_template('services.html', title='Services', stype=stype, services=services, blocked=userblocked)

    else:
        services = Service.query.order_by(Service.name).all()
        return render_template('services.html', title='Services', services=services, blocked=userblocked)

@app.route('/professional_details', methods=['GET', 'POST'])
def professional_details():
    prof_id = request.args.get('prof_id')
    prof = db.session.get(ServiceProfessional,prof_id)
    rating = Review.query.with_entities(db.func.avg(Review.rating)).filter_by(professional_id=prof_id).first()[0]
    reviews = Review.query.filter_by(professional_id=prof_id).order_by(Review.rating.desc()).all()
    user = Customer.query.filter_by(user_id=current_user.id).first()        
    requests = ServiceRequest.query.filter_by(cust_id=user.id).all()
    return render_template('customer_dashboard.html', title='Professional Details', view_professional=prof, rating=rating, reviews=reviews, user=user, requests=requests, blocked=current_user.blocked)        

@app.route('/book_service', methods=['GET', 'POST'])
def book_service():
    if not current_user.is_authenticated:
        flash('Please login to book a service.','danger')
        return redirect(url_for('services'))
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

@app.route('/cancel_request', methods=['GET', 'POST'])
def cancel_request():
    if request.method == 'POST':
        request_id = request.form.get('id')
        req = db.session.get(ServiceRequest,request_id)
        db.session.delete(req)
        db.session.commit()
        flash('Request cancelled successfully.','success')
        return redirect(url_for('dashboard'))

    request_id = request.args.get('request_id')
    req = db.session.get(ServiceRequest,request_id)
    user = Customer.query.filter_by(user_id=current_user.id).first()        
    requests = ServiceRequest.query.filter_by(cust_id=user.id).all()
    return render_template('customer_dashboard.html',title='Home', user=user, requests=requests, cancel_request=req, blocked=current_user.blocked)

@app.route('/close_request', methods=['GET', 'POST'])
def close_request():
    if request.method == 'POST':
        request_id = request.form.get('id')
        req = db.session.get(ServiceRequest,request_id)
        req.service_status = 'completed'
        req.date_of_completion = datetime.utcnow()
        rating = request.form.get('star')
        if not rating:
            flash('Please provide a rating.','danger')
            return redirect(url_for('close_request',request_id=request_id))
        review_text = request.form.get('review')
        new_review = Review(
            service_request_id=request_id,
            customer_id=req.cust_id,
            professional_id=req.prof_id,
            rating=rating,
            review_text=review_text
        )
        db.session.add(new_review)
        db.session.commit()
        flash('Request closed successfully.','success')
        return redirect(url_for('dashboard'))

    request_id = request.args.get('request_id')
    req = db.session.get(ServiceRequest,request_id)
    user = Customer.query.filter_by(user_id=current_user.id).first()        
    requests = ServiceRequest.query.filter_by(cust_id=user.id).all()
    return render_template('customer_dashboard.html',title='Home', user=user, requests=requests, close_request=req, blocked=current_user.blocked)

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

@app.route('/edit_review', methods=['GET', 'POST'])
def edit_review():
    if request.method == 'POST':
        review_id = request.form.get('id')
        review = db.session.get(Review,review_id)
        rating = request.form.get('star')
        if rating:
            review.rating = rating
        review.review_text = request.form.get('review')
        db.session.commit()
        flash('Review updated successfully.','success')
        return redirect(url_for('dashboard'))

    request_id = request.args.get('request_id')
    review = Review.query.filter_by(service_request_id=request_id).first()
    user = Customer.query.filter_by(user_id=current_user.id).first()        
    requests = ServiceRequest.query.filter_by(cust_id=user.id).all()
    return render_template('customer_dashboard.html',title='Home', user=user, requests=requests, services=services, edit_review=review, blocked=current_user.blocked)


### SEARCH ROUTES ###
@app.route('/search', methods=['GET'])
def search():
    if not current_user.is_authenticated:
        search_by=request.args.get('search_by')
        search_term=request.args.get('search_term') or ''
        if search_by == 'name':
            services = Service.query.filter(Service.name.ilike(f'%{search_term}%')).all()
        elif search_by == 'price':
            if not search_term.isdigit():
                flash('Please enter a valid number.','danger')
                return redirect(url_for('search',search_term='',search_by='price'))
            services = Service.query.filter(Service.price<=int(search_term)).order_by(Service.price.desc()).all()
        else:
            services = Service.query.all()
        return render_template('customer_search.html', title='Search', services=services,search_term=search_term,search_by=search_by)
    elif current_user.role == 'customer':
        search_by=request.args.get('search_by')
        search_term=request.args.get('search_term') or ''
        if search_by == 'name':
            services = Service.query.filter(Service.name.ilike(f'%{search_term}%')).all()
        elif search_by == 'price':
            if not search_term.isdigit():
                flash('Please enter a valid number.','danger')
                return redirect(url_for('search',search_term='',search_by='price'))
            services = Service.query.filter(Service.price<=int(search_term)).order_by(Service.price.desc()).all()
        else:
            services = Service.query.all()
        return render_template('customer_search.html', title='Search', services=services, search_term=search_term, search_by=search_by, blocked=current_user.blocked)
    elif current_user.role == 'admin':
        search_for = request.args.get('search_for')
        search_by = request.args.get('search_by')
        search_term = request.args.get('search_term') or ''
        if search_for == 'serviceprofessionals':
            approval_status = request.args.get('approval_status')
            if approval_status == 'approved':
                if search_by == 'name':
                    results = ServiceProfessional.query.filter(ServiceProfessional.name.ilike(f'%{search_term}%')).filter_by(is_approved=True).all()
                elif search_by == 'service':
                    results = ServiceProfessional.query.filter(ServiceProfessional.service.has(Service.name.ilike(f'%{search_term}%'))).filter_by(is_approved=True).all()
                elif search_by == 'city':
                    results = ServiceProfessional.query.filter(ServiceProfessional.address.ilike(f'%{search_term}%')).filter_by(is_approved=True).all()
                else:
                    results = ServiceProfessional.query.filter_by(is_approved=True).all()
            elif approval_status == 'unapproved':
                if search_by == 'name':
                    results = ServiceProfessional.query.filter(ServiceProfessional.name.ilike(f'%{search_term}%')).filter_by(is_approved=False).all()
                elif search_by == 'service':
                    results = ServiceProfessional.query.filter(ServiceProfessional.service.has(Service.name.ilike(f'%{search_term}%'))).filter_by(is_approved=False).all()
                elif search_by == 'city':
                    results = ServiceProfessional.query.filter(ServiceProfessional.address.ilike(f'%{search_term}%')).filter_by(is_approved=False).all()
                else:
                    results = ServiceProfessional.query.filter_by(is_approved=False).all()
            else:
                if search_by == 'name':
                    results = ServiceProfessional.query.filter(ServiceProfessional.name.ilike(f'%{search_term}%')).all()
                elif search_by == 'service':
                    results = ServiceProfessional.query.filter(ServiceProfessional.service.has(Service.name.ilike(f'%{search_term}%'))).all()
                elif search_by == 'city':
                    results = ServiceProfessional.query.filter(ServiceProfessional.address.ilike(f'%{search_term}%')).all()
                else:
                    results = ServiceProfessional.query.all()
        elif search_for == 'customers':
            if search_by == 'name':
                customers = Customer.query.filter(Customer.name.ilike(f'%{search_term}%'))
            elif search_by == 'city':
                customers = Customer.query.filter(Customer.address.ilike(f'%{search_term}%'))
            if request.args.get('user_blocked'):
                customers = customers.filter(Customer.user.has(User.blocked==True))
            if request.args.get('user_reported'):
                customers = customers.filter(Customer.reports.any())
            results = customers.all()
        elif search_for == 'services':
            results = Service.query.filter(Service.name.ilike(f'%{search_term}%')).all()
        elif search_for == 'requests':
            if request.args.get("request_status") == "open":
                if search_by == 'service':
                    results = ServiceRequest.query.filter(ServiceRequest.service.has(Service.name.ilike(f'%{search_term}%'))).filter(or_(ServiceRequest.service_status==x for x in ('requested','accepted','in progress'))).order_by(ServiceRequest.date_of_request.desc()).all()
                elif search_by == 'customer':
                    results = ServiceRequest.query.filter(ServiceRequest.customer.has(Customer.name.ilike(f'%{search_term}%'))).filter(or_(ServiceRequest.service_status==x for x in ('requested','accepted','in progress'))).order_by(ServiceRequest.date_of_request.desc()).all()
                elif search_by == 'serviceprofessional':
                    results = ServiceRequest.query.filter(ServiceRequest.professional.has(ServiceProfessional.name.ilike(f'%{search_term}%'))).filter(or_(ServiceRequest.service_status==x for x in ('requested','accepted','in progress'))).order_by(ServiceRequest.date_of_request.desc()).all()
            elif request.args.get("request_status") == "completed":
                if search_by == 'service':
                    results = ServiceRequest.query.filter(ServiceRequest.service.has(Service.name.ilike(f'%{search_term}%'))).filter(ServiceRequest.service_status=='completed').order_by(ServiceRequest.date_of_request.desc()).all()
                elif search_by == 'customer':
                    results = ServiceRequest.query.filter(ServiceRequest.customer.has(Customer.name.ilike(f'%{search_term}%'))).filter(ServiceRequest.service_status=='completed').order_by(ServiceRequest.date_of_request.desc()).all()
                elif search_by == 'serviceprofessional':
                    results = ServiceRequest.query.filter(ServiceRequest.professional.has(ServiceProfessional.name.ilike(f'%{search_term}%'))).filter(ServiceRequest.service_status=='completed').order_by(ServiceRequest.date_of_request.desc()).all()
            else:
                if search_by == 'service':
                    results = ServiceRequest.query.filter(ServiceRequest.service.has(Service.name.ilike(f'%{search_term}%'))).order_by(ServiceRequest.date_of_request.desc()).all()
                elif search_by == 'customer':
                    results = ServiceRequest.query.filter(ServiceRequest.customer.has(Customer.name.ilike(f'%{search_term}%'))).order_by(ServiceRequest.date_of_request.desc()).all()
                elif search_by == 'serviceprofessional':
                    results = ServiceRequest.query.filter(ServiceRequest.professional.has(ServiceProfessional.name.ilike(f'%{search_term}%'))).order_by(ServiceRequest.date_of_request.desc()).all()
        else:
            results = None

        return render_template('admin_search.html', title='Search', results=results, search_for=search_for, search_by=search_by, search_term=search_term)
    elif current_user.role == 'professional':
        return redirect(url_for('search_new_requests'))


@app.route('/search/block_user', methods=['GET', 'POST'])
def search_block_user():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = db.session.get(User,user_id)
        user.blocked = True
        db.session.commit()
        flash('User blocked successfully.','success')
        return redirect(url_for('search'))

    user_id = request.args.get('user_id')
    user = db.session.get(User,user_id)
    return render_template('admin_search.html', block_user=user, title='Search')

@app.route('/search/unblock_user', methods=['GET', 'POST'])
def search_unblock_user():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = db.session.get(User,user_id)
        user.blocked = False
        db.session.commit()
        flash('User unblocked successfully.','success')
        return redirect(url_for('search'))

    user_id = request.args.get('user_id')
    user = db.session.get(User,user_id)
    return render_template('admin_search.html', unblock_user=user, title='Search')

@app.route('/search/view_reports')
def search_view_reports():
    customer_id = request.args.get('customer_id')
    reports = ReportCustomer.query.filter_by(customer_id=customer_id).all()
    return render_template('admin_search.html', title='Search', reports=reports)

@app.route('/search/approve_professional', methods=['GET', 'POST'])
def search_approve_professional():
    if request.method == 'POST':
        professional_id = request.form.get('prof_id')
        professional = db.session.get(ServiceProfessional,professional_id)
        professional.is_approved = True
        db.session.commit()
        flash('Professional approved successfully.','success')
        return redirect(url_for('search'))

    professional_id = request.args.get('prof_id')
    professional = db.session.get(ServiceProfessional,professional_id)
    return render_template('admin_search.html', approve_professional=professional, title='Search')

@app.route('/search/edit_service', methods=['GET', 'POST'])
def search_edit_service():
    if request.method == 'POST':
        service_id = request.form.get('id')
        service = db.session.get(Service,service_id)
        service.name = request.form['name']
        service.description = request.form['description']
        service.price = request.form['price']
        service.time_required = request.form['time_required']
        db.session.commit()
        flash('Service updated successfully.','success')
        return redirect(url_for('search'))

    service_id = request.args.get('service_id')
    service_to_edit = db.session.get(Service,service_id)
    return render_template('admin_search.html', service_to_edit=service_to_edit, title='Search')

@app.route('/search/delete_service', methods=['GET', 'POST'])
def search_delete_service():
    if request.method == 'POST':
        service_id = request.form.get('id')
        service = db.session.get(Service,service_id)
        db.session.delete(service)
        db.session.commit()
        flash('Service deleted successfully.','success')
        return redirect(url_for('search'))

    service_id = request.args.get('service_id')
    delete_service = db.session.get(Service,service_id)
    return render_template('admin_search.html', delete_service=delete_service, title='Search')

@app.route('/search_new_requests')
@login_required
def search_new_requests():
    if current_user.role != 'professional':
        return redirect(url_for('dashboard'))
    
    user = ServiceProfessional.query.filter_by(user_id=current_user.id).first()
    rej_requests = db.session.query(RequestRejected.service_request_id).filter(RequestRejected.prof_id==user.id).all()
    rejected_requests = [x for (x,) in rej_requests]
    search_by = request.args.get('search_by')
    search_term = request.args.get('search_term') or ''
    search_date = request.args.get('search_date') or ''
    if search_by == 'pincode':
        if not search_term.isdigit():
            flash('Please enter a valid pincode.','danger')
            return redirect(url_for('search_new_requests'))

        new_requests = ServiceRequest.query.filter_by(pincode=int(search_term)).filter_by(service_status='requested').filter_by(service_id=user.service_id).order_by(ServiceRequest.date_of_request.desc()).all()

    elif search_by == 'date':
        new_requests = ServiceRequest.query.filter(func.date(ServiceRequest.date_of_request)==search_date).filter_by(service_status='requested').filter_by(service_id=user.service_id).order_by(ServiceRequest.date_of_request.desc()).all()

    elif search_by == 'city':
        new_requests = ServiceRequest.query.filter(ServiceRequest.address.ilike(f'%{search_term}%')).filter_by(service_status='requested').filter_by(service_id=user.service_id).order_by(ServiceRequest.date_of_request.desc()).all()

    else:
        new_requests = ServiceRequest.query.filter(ServiceRequest.service_status=='requested').filter_by(service_id=user.service_id).order_by(ServiceRequest.date_of_request.desc()).all()
    return render_template('professional_search1.html', title='Search', user=user, rejected_requests=rejected_requests, new_requests=new_requests, search_by=search_by, search_term=search_term, blocked=current_user.blocked)


@app.route('/search_new_requests/accept_request', methods=['GET', 'POST'])
def search_new_requests_accept():
    if current_user.role != 'professional':
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        request_id = request.form.get('id')
        req = db.session.get(ServiceRequest,request_id)
        req.prof_id = ServiceProfessional.query.filter_by(user_id=current_user.id).first().id
        req.service_status = 'accepted'
        db.session.commit()
        flash('Request accepted successfully.','success')
        return redirect(url_for('search_new_requests'))

    request_id = request.args.get('request_id')
    user = ServiceProfessional.query.filter_by(user_id=current_user.id).first()
    new_requests = ServiceRequest.query.filter_by(service_id=user.service_id).filter_by(service_status='requested').all()
    rej_requests = db.session.query(RequestRejected.service_request_id).filter(RequestRejected.prof_id==user.id).all()
    rejected_requests = [x for (x,) in rej_requests]
    req = db.session.get(ServiceRequest,request_id)
    return render_template('professional_search1.html', title='Search', accept_request=req, user=user, new_requests=new_requests, rejected_requests=rejected_requests, blocked=current_user.blocked)

@app.route('/search_new_requests/reject_request', methods=['GET', 'POST'])
def search_new_requests_reject():
    if current_user.role != 'professional':
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        request_id = request.form.get('id')
        prof_id = ServiceProfessional.query.filter_by(user_id=current_user.id).first().id
        new_reject = RequestRejected(service_request_id=request_id, prof_id=prof_id)
        db.session.add(new_reject)
        db.session.commit()
        flash('Request rejected successfully.','success')
        return redirect(url_for('search_new_requests'))

    request_id = request.args.get('request_id')
    user = ServiceProfessional.query.filter_by(user_id=current_user.id).first()
    new_requests = ServiceRequest.query.filter_by(service_id=user.service_id).filter_by(service_status='requested').all()
    rej_requests = db.session.query(RequestRejected.service_request_id).filter(RequestRejected.prof_id==user.id).all()
    rejected_requests = [x for (x,) in rej_requests]
    req = db.session.get(ServiceRequest,request_id)
    return render_template('professional_search1.html', title='Search', reject_request=req, user=user, new_requests=new_requests, rejected_requests=rejected_requests, blocked=current_user.blocked)

@app.route('/search_your_requests')
@login_required
def search_your_requests():
    if current_user.role != 'professional':
        return redirect(url_for('dashboard'))
    if current_user.service_professionals[0].is_approved == False:
        flash('You need to be approved to view your requests.','danger')
        return redirect(url_for('dashboard'))

    user = ServiceProfessional.query.filter_by(user_id=current_user.id).first()
    search_by = request.args.get('search_by')
    search_term = request.args.get('search_term') or ''
    search_date = request.args.get('search_date') or ''
    if search_by == 'pincode':
        if not search_term.isdigit():
            flash('Please enter a valid pincode.','danger')
            return redirect(url_for('search_new_requests'))

        prev_requests = ServiceRequest.query.filter_by(pincode=int(search_term)).filter_by(prof_id=user.id).order_by(ServiceRequest.date_of_request.desc()).all()

    elif search_by == 'date':
        prev_requests = ServiceRequest.query.filter(func.date(ServiceRequest.date_of_request)==search_date).filter_by(prof_id=user.id).order_by(ServiceRequest.date_of_request.desc()).all()

    elif search_by == 'city':
        prev_requests = ServiceRequest.query.filter(ServiceRequest.address.ilike(f'%{search_term}%')).filter_by(prof_id=user.id).order_by(ServiceRequest.date_of_request.desc()).all()

    else:
        prev_requests = ServiceRequest.query.filter_by(prof_id=user.id).order_by(ServiceRequest.date_of_request.desc()).all()
    
    return render_template('professional_search2.html', title='Search', user=user, prev_requests=prev_requests, search_term=search_term, search_date=search_date, search_by=search_by, blocked=current_user.blocked)

@app.route('/search_your_requests/mark_in_progress', methods=['GET', 'POST'])
def search_your_requests_in_progress():
    if current_user.role != 'professional':
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        request_id = request.form.get('id')
        req = db.session.get(ServiceRequest,request_id)
        req.service_status = 'in progress'
        db.session.commit()
        flash('Request status updated successfully.','success')
        return redirect(url_for('search_your_requests'))

    request_id = request.args.get('request_id')
    user = ServiceProfessional.query.filter_by(user_id=current_user.id).first()
    prev_requests = ServiceRequest.query.filter_by(prof_id=user.id).order_by(ServiceRequest.date_of_request.desc()).all()
    req = db.session.get(ServiceRequest,request_id)
    return render_template('professional_search2.html', title='Search', in_progress=req, user=user, prev_requests=prev_requests, blocked=current_user.blocked)

@app.route('/book_searched_service', methods=['GET', 'POST'])
def book_search_service():
    if not current_user.is_authenticated:
        flash('Please login to book a service.','danger')
        return redirect(url_for('search'))
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

    search_by=request.args.get('search_by')
    search_term=request.args.get('search_term') or ''
    if search_by == 'name':
        services = Service.query.filter(Service.name.ilike(f'%{search_term}%')).all()
    elif search_by == 'price':
        services = Service.query.filter(Service.price<=int(search_term)).order_by(Service.price.desc()).all()
    else:
        services = Service.query.all()
    service_id = request.args.get('service_id')
    service = db.session.get(Service,service_id)
    customer = Customer.query.filter_by(user_id=current_user.id).first()
    return render_template('customer_search.html', title='Book Service', services=services, bookservice=service, customer=customer)

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
    rej_requests = db.session.query(RequestRejected.service_request_id).filter(RequestRejected.prof_id==user.id).all()
    rejected_requests = [x for (x,) in rej_requests]
    req = db.session.get(ServiceRequest,request_id)
    reviews = Review.query.filter_by(professional_id=user.id).order_by(Review.date_submitted.desc()).all()
    return render_template('professional_dashboard.html', title='Home', accept_request=req, user=user, reviews=reviews, new_requests=new_requests, rejected_requests=rejected_requests, prev_requests=prev_requests, blocked=current_user.blocked)


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
    prev_requests = ServiceRequest.query.filter_by(prof_id=user.id).order_by(ServiceRequest.date_of_request.desc()).all()
    rej_requests = db.session.query(RequestRejected.service_request_id).filter(RequestRejected.prof_id==user.id).all()
    rejected_requests = [x for (x,) in rej_requests]
    req = db.session.get(ServiceRequest,request_id)
    reviews = Review.query.filter_by(professional_id=user.id).order_by(Review.date_submitted.desc()).all()
    return render_template('professional_dashboard.html', title='Home', reject_request=req, user=user, reviews=reviews, new_requests=new_requests, rejected_requests=rejected_requests, prev_requests=prev_requests, blocked=current_user.blocked)

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
    prev_requests = ServiceRequest.query.filter_by(prof_id=user.id).order_by(ServiceRequest.date_of_request.desc()).all()
    rej_requests = db.session.query(RequestRejected.service_request_id).filter(RequestRejected.prof_id==user.id).all()
    rejected_requests = [x for (x,) in rej_requests]
    req = db.session.get(ServiceRequest,request_id)
    reviews = Review.query.filter_by(professional_id=user.id).order_by(Review.date_submitted.desc()).all()
    return render_template('professional_dashboard.html', title='Home', in_progress=req, user=user, reviews=reviews, new_requests=new_requests, prev_requests=prev_requests, rejected_requests=rejected_requests, blocked=current_user.blocked)

@app.route('/report_customer', methods=['GET', 'POST'])
def report_customer():
    if request.method == 'POST':
        customer_id = request.form.get('id')
        prof_id = ServiceProfessional.query.filter_by(user_id=current_user.id).first().id
        remarks = request.form.get('remarks')
        if not remarks:
            flash('Please provide a reason for reporting.','danger')
            return redirect(url_for('report_customer',customer_id=customer_id))
        new_report = ReportCustomer(customer_id=customer_id, prof_id=prof_id, remarks=remarks)
        db.session.add(new_report)
        db.session.commit()
        flash('Customer reported successfully. The admin will review your report and take necessary steps.','success')
        return redirect(url_for('dashboard'))

    customer_id = request.args.get('customer_id')
    report_cust = Customer.query.filter_by(id=customer_id).first()
    user = ServiceProfessional.query.filter_by(user_id=current_user.id).first()
    new_requests = ServiceRequest.query.filter_by(service_id=user.service_id).filter_by(service_status='requested').all()
    prev_requests = ServiceRequest.query.filter_by(prof_id=user.id).order_by(ServiceRequest.date_of_request.desc()).all()
    rej_requests = db.session.query(RequestRejected.service_request_id).filter(RequestRejected.prof_id==user.id).all()
    rejected_requests = [x for (x,) in rej_requests]
    reviews = Review.query.filter_by(professional_id=user.id).order_by(Review.date_submitted.desc()).all()
    return render_template('professional_dashboard.html', title='Home', report_customer=report_cust, user=user, reviews=reviews, new_requests=new_requests, prev_requests=prev_requests, rejected_requests=rejected_requests, blocked=current_user.blocked)


### SUMMARY ROUTES ###
@app.route('/summary')
def summary():
    if current_user.is_authenticated:
        if current_user.role == 'professional':
            user = ServiceProfessional.query.filter_by(user_id=current_user.id).first()
            rejected = len(RequestRejected.query.filter_by(prof_id=user.id).all())
            accepted = len(ServiceRequest.query.filter_by(prof_id=user.id).filter_by(service_status='accepted').all())
            in_progress = len(ServiceRequest.query.filter_by(prof_id=user.id).filter_by(service_status='in progress').all())
            completed = len(ServiceRequest.query.filter_by(prof_id=user.id).filter_by(service_status='completed').all())
            reqs_nums = [accepted, rejected, in_progress, completed]
            if completed > 0:
                reviews_nums = [len(Review.query.filter_by(professional_id=user.id).filter_by(rating=5).all()), len(Review.query.filter_by(professional_id=user.id).filter_by(rating=4).all()), len(Review.query.filter_by(professional_id=user.id).filter_by(rating=3).all()), len(Review.query.filter_by(professional_id=user.id).filter_by(rating=2).all()), len(Review.query.filter_by(professional_id=user.id).filter_by(rating=1).all())]
            else:
                reviews_nums = None
            return render_template('professional_summary.html', title='Summary', user=user, reqs_nums=reqs_nums, reviews_nums=reviews_nums, blocked=current_user.blocked)
        elif current_user.role == 'customer':
            user = Customer.query.filter_by(user_id=current_user.id).first()
            reqs_nums = [len(ServiceRequest.query.filter_by(cust_id=user.id).filter_by(service_status='requested').all()),len(ServiceRequest.query.filter_by(cust_id=user.id).filter_by(service_status="accepted").all()),len(ServiceRequest.query.filter_by(cust_id=user.id).filter_by(service_status="in progress").all()),len(ServiceRequest.query.filter_by(cust_id=user.id).filter_by(service_status="completed").all())]
            return render_template('customer_summary.html', title='Summary', user=user, reqs_nums=reqs_nums, blocked=current_user.blocked)
        else:
            open_requests = len(ServiceRequest.query.filter_by(service_status='requested').all())
            rejected = len(RequestRejected.query.all())
            accepted = len(ServiceRequest.query.filter_by(service_status='accepted').all())
            in_progress = len(ServiceRequest.query.filter_by(service_status='in progress').all())
            completed = len(ServiceRequest.query.filter_by(service_status='completed').all())
            reqs_nums = [open_requests, accepted, rejected, in_progress, completed]
            reviews_nums = [len(Review.query.filter_by(rating=5).all()), len(Review.query.filter_by(rating=4).all()), len(Review.query.filter_by(rating=3).all()), len(Review.query.filter_by(rating=2).all()), len(Review.query.filter_by(rating=1).all())]
            return render_template('admin_summary.html', title='Summary', reqs_nums=reqs_nums, reviews_nums=reviews_nums)
    else:
        return render_template('customer_summary.html',title='Summary')   


