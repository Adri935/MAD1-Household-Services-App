### DB MODELS FOR HOUSEHOLD SERVICE SYSTEM

from app import app
from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime

db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(16),nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100),nullable=False)
    price = db.Column(db.Float,nullable=False)
    description = db.Column(db.String(250))
    time_required = db.Column(db.String(50))

class ServiceProfessional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(16),nullable=False)
    service_type = db.Column(db.String(100),nullable=False)
    experience = db.Column(db.Integer,nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    cv = db.Column(db.LargeBinary)
    pincode = db.Column(db.String(10),nullable=False)
    is_approved = db.Column(db.Boolean, default=False)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(16),nullable=False)
    phone = db.Column(db.String(10),nullable=False)
    address = db.Column(db.Text,nullable=False)
    pincode = db.Column(db.String(10),nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False) 
    cust_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  
    prof_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    date_of_request = db.Column(db.DateTime, default=datetime.utcnow)  
    date_of_completion = db.Column(db.DateTime, nullable=True)  
    service_status = db.Column(db.String(50), default='requested')  
    remarks = db.Column(db.Text, nullable=True)  
    
    service = db.relationship('Service', foreign_keys=[service_id], backref='requests')
    customer = db.relationship('Customer', foreign_keys=[cust_id], backref='requested_by')
    professional = db.relationship('Professional', foreign_keys=[prof_id], backref='accepted_by')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=False)  
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  
    professional_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  
    rating = db.Column(db.Integer, nullable=False)  
    review_text = db.Column(db.Text, nullable=True)  
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)  

    service_request = db.relationship('ServiceRequest', backref='reviews')
    customer = db.relationship('User', foreign_keys=[customer_id], backref='customer_reviews')
    professional = db.relationship('User', foreign_keys=[professional_id], backref='professional_reviews')


## EDIT THE NAMES OF COLS
