### DB MODELS FOR HOUSEHOLD SERVICE SYSTEM

from app import app
from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime
from flask_login import LoginManager, UserMixin
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from os import getenv

load_dotenv()
bc = Bcrypt()

login_manager = LoginManager(app)
db = SQLAlchemy(app)
migrate = Migrate(app,db)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model,UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    blocked = db.Column(db.Boolean,default=False)

    customers = db.relationship('Customer', backref='user', cascade='all, delete-orphan')
    service_professionals = db.relationship('ServiceProfessional', backref='user', cascade='all, delete-orphan')

class Service(db.Model):
    __tablename__ = 'service'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250))
    time_required = db.Column(db.String(50))

    service_professionals = db.relationship('ServiceProfessional', backref='service', cascade='all, delete-orphan')
    service_requests = db.relationship('ServiceRequest', backref='service', cascade='all, delete-orphan')

class ServiceProfessional(db.Model):
    __tablename__ = 'service_professional'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100),nullable=True)
    photo = db.Column(db.String(255),default="static/defaultpfp.jpeg")
    phone = db.Column(db.String(10), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    identity_proof = db.Column(db.String(255), nullable=False)
    certifications = db.Column(db.String(255))
    address = db.Column(db.Text, nullable=False)
    pincode = db.Column(db.String(6), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)

    requests = db.relationship('ServiceRequest', backref='professional', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='professional', cascade='all, delete-orphan')
    rejected_requests = db.relationship('RequestRejected', backref='rejected_by', cascade='all, delete-orphan')

class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100),nullable=False)
    phone = db.Column(db.String(10), nullable=False)
    photo = db.Column(db.String(255),default="static/defaultpfp.jpeg")
    address = db.Column(db.Text, nullable=False)
    pincode = db.Column(db.String(6), nullable=False, index=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    requests = db.relationship('ServiceRequest', backref='customer', cascade='all, delete-orphan')

class ServiceRequest(db.Model):
    __tablename__ = 'service_request'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False) 
    cust_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)  
    prof_id = db.Column(db.Integer, db.ForeignKey('service_professional.id'), nullable=True)
    date_of_request = db.Column(db.DateTime, default=datetime.utcnow, index=True)  
    date_of_completion = db.Column(db.DateTime, nullable=True)
    address = db.Column(db.Text, nullable=False)
    pincode = db.Column(db.String(6), nullable=False)
    service_status = db.Column(db.String(50), default='requested')  
    remarks = db.Column(db.Text, nullable=True)  

    review = db.relationship('Review', backref='request', cascade='all, delete-orphan')

class RequestRejected(db.Model):
    __tablename__ = 'request_rejected'
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=False)
    prof_id = db.Column(db.Integer, db.ForeignKey('service_professional.id'))


class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=False)  
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)  
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professional.id'), nullable=False)  
    rating = db.Column(db.Integer, nullable=False) 
    review_text = db.Column(db.Text, nullable=True)  
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)  



with app.app_context():
    db.create_all()
    # check if admin exists
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        pwd = bc.generate_password_hash(getenv('adminpwd'))
        admin = User(id=1000,email='admin.homeease@homeease.com',password=pwd,role='admin',blocked=False)
        db.session.add(admin)
        db.session.commit()
