# Household Services App

It is a multi-user app (requires one admin and other service professionals/ customers) which acts as platform for providing comprehensive home servicing and solutions.

## Technologies Used
- **Flask:** To perform all kinds of backend controller tasks, create different routes, fetch data from the database as well as deciding on what to display on the view. 
- **Flask_sqlalchemy:** To create all the models and perform crud operations on those models.
- **SQLITE3:** To store the data.
- **HTML, CSS:** To create all the templates and style them.
- **Jinja2:** To populate the templates with the data.
- **Flask_login:** For user authorization and authentication.
- **Bcrypt:** For hashing and securely storing passwords in database.

## How to run this project
### Cloning
First, clone the GitHub repository using:
`git clone <url>`

### Installing Requirements
Inside the root directory, you can install the requirements using:
`pip3 install -r requirements.txt`

### Running the App
1. Edit the .env file to replace your secret key and Admin password with actual values
2. Inside the root directory, you can run the app using:
`flask run`
