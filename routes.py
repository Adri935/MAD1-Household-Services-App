from flask import render_template,url_for,flash
from app import app

@app.route("/")
@app.route("/login")
def login():
    return render_template('login.html',title='Login')

@app.route("/customer_register")
def customer_register():
    return render_template('customer_register.html',title='Customer Registration')

@app.route("/professional_register")
def professional_register():
    return render_template('professional_register.html',title='Service Professional Registration')
