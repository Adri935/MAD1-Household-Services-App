from dotenv import load_dotenv
import os
from app import app

load_dotenv()

from datetime import datetime
from zoneinfo import ZoneInfo

def utc_to_local(time): 
    utc = ZoneInfo('UTC')
    utc_time = time.replace(tzinfo=utc)
    
    # Convert the UTC datetime to the specified local timezone
    local_time = utc_time.astimezone(ZoneInfo('Asia/Kolkata'))
    
    # Return the formatted local time using strftime
    return datetime.strftime(local_time,'%d-%m-%Y %H:%M:%S')

app.jinja_env.filters['utc_to_local'] = utc_to_local

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')