### DB MODELS FOR HOUSEHOLD SERVICE SYSTEM

from app import app
from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime

db = SQLAlchemy(app)

''' 
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(16),nullable=False)
    role = db.Column(db.String(20), nullable=False)
'''

class Service(db.Model):
    __tablename__ = 'service'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100),nullable=False)
    price = db.Column(db.Float,nullable=False)
    description = db.Column(db.String(250))
    time_required = db.Column(db.String(50))

class ServiceProfessional(db.Model):
    __tablename__ = 'service_professional'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128),nullable=False)
    phone = db.Column(db.String(10), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    experience = db.Column(db.Integer,nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    identity_proof = db.Column(db.LargeBinary, nullable=False)
    certifications = db.Column(db.LargeBinary)
    address = db.Column(db.Text,nullable=False)
    pincode = db.Column(db.String(6),nullable=False)
    is_approved = db.Column(db.Boolean, default=False)

    service = db.relationship('Service',  backref='service_provided')


class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128),nullable=False)
    phone = db.Column(db.String(10),nullable=False)
    address = db.Column(db.Text,nullable=False)
    pincode = db.Column(db.String(6),nullable=False, index=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

class ServiceRequest(db.Model):
    __tablename__ = 'service_request'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False) 
    cust_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)  
    prof_id = db.Column(db.Integer, db.ForeignKey('service_professional.id'), nullable=True)
    date_of_request = db.Column(db.DateTime, default=datetime.utcnow, index=True)  
    date_of_completion = db.Column(db.DateTime, nullable=True)
    pincode = db.Column(db.String(6), db.ForeignKey('customer.pincode'), nullable=False)
    service_status = db.Column(db.String(50), default='requested')  
    remarks = db.Column(db.Text, nullable=True)  
    
    service = db.relationship('Service', foreign_keys=[service_id], backref='requests')
    customer = db.relationship('Customer', foreign_keys=[cust_id], backref='requested_by')
    professional = db.relationship('ServiceProfessional', foreign_keys=[prof_id], backref='accepted_by')
    location = db.relationship('Customer', foreign_keys=[pincode], backref='location')

class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=False)  
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)  
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professional.id'), nullable=False)  
    rating = db.Column(db.Integer, nullable=False)  
    review_text = db.Column(db.Text, nullable=True)  
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)  

    service_request = db.relationship('ServiceRequest', backref='reviews')
    customer = db.relationship('Customer', foreign_keys=[customer_id], backref='customer_reviews')
    professional = db.relationship('ServiceProfessional', foreign_keys=[professional_id], backref='professional_reviews')


with app.app_context():
    db.create_all()