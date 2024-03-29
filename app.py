# Importing necessary modules and libraries
from flask import Flask, jsonify, render_template, request,redirect,url_for,session
from flask_sqlalchemy import SQLAlchemy
import numpy as np
import sklearn
import pickle
import bcrypt
import jwt

# Creating a Flask application instance
app = Flask(__name__)
app.secret_key = 'assignment-3'

# Loading a pre-trained machine learning model using pickle
model = pickle.load(open('model.pkl','rb'))

# Configuring the database connection URI and tracking modifications
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Tigers08#@localhost/loanpredictiondb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# Creating a SQLAlchemy database instance
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), unique = True)
    password = db.Column(db.String(255))

    def __init__(self, username, password):
        self.username = username
        self.password = password
        
# Create the users table in the database
with app.app_context():
    db.create_all()

# Rendering Home page
@app.route('/')
def home():
    return render_template('home.html')

## Register API
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form['username']
            password = request.form['password']

            # Check if the username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                 return '''
                    <h1>Username Already Exists!</h1>
                    <button onclick="location.href='/register'">Register</button>
                    <button onclick="location.href='/login'">Login</button>
                '''

            # Hash the password using bcrypt
            hashed_pass = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

            # Create a new User object with hashed password
            new_user = User(username=username, password=hashed_pass)

            # Add the new user to the database
            db.session.add(new_user)
            db.session.commit()

            # Generate JWT token
            token = jwt.encode({'username': username}, app.config['SECRET_KEY'], algorithm='HS256')
            # Redirect to the login page with success token
            return redirect(url_for('login', token=token))
        
        except Exception as e:
            return jsonify({'message': f'Error: {str(e)}'}), 500
    return render_template('register.html')

## Login API
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            #Get form data
            username = request.form['username']
            password = request.form['password']

            # Find the user by username
            user = User.query.filter_by(username=username).first()

            if user:
                # Check if pass matches
                if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                    # Generate JWT token
                    token = jwt.encode({'username': username}, app.config['SECRET_KEY'], algorithm='HS256')
                    return redirect(url_for('predict', token=token))
                else:
                   return '''
                        <h1>Invalid username or password! Please enter correct details</h1>
                        <button onclick="location.href='/login'">Login</button>
                    '''
            else:
                return jsonify({'message': 'User not found'}), 404

        except Exception as e:
            return jsonify({'message': f'Error: {str(e)}'}), 500

    return render_template('login.html')

## Predict API
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        try:
            # Retrieve the entered details from the form
            gender = request.form['gender']
            married = request.form['married']
            dependents = request.form['dependents']
            self_employed = request.form['self_employed']
            education = request.form['education']
            applicant_income = float(request.form['applicant_income'])
            coapplicant_income = float(request.form['coapplicant_income'])
            loan_amount = float(request.form['loan_amount'])
            loan_amount_term = float(request.form['loan_amount_term'])
            credit_history = float(request.form['credit_history'])
            property_area = request.form['property_area']

            # Prepare the input for prediction
            input_data = [[gender, married, dependents, education, self_employed, applicant_income,
                           coapplicant_income, loan_amount, loan_amount_term, credit_history, property_area]]
            
            # Make the prediction
            prediction = model.predict(input_data)
            result_message = "Congrats!! You are eligible for the loan" if prediction > 0.5 else "Sorry, you are not eligible for the loan"

            # Render the template with the prediction result and form data
            return render_template('predict.html', prediction=result_message)
        
        except Exception as e:
            return jsonify({'message': f'Error: {str(e)}'}), 500
        
    return render_template('predict.html')

# Logout API
@app.route('/logout', methods=['POST'])
def logout():
    if request.method == 'POST':
        try:
            # Clear session data
            session.pop('id', None)
            session.clear()
            return jsonify({'message': 'Logout successful'}), 200
        except Exception as e:
            return jsonify({'message': f'Error: {str(e)}'}), 500
    return redirect('/')


with app.app_context():
    db.session.commit()

# Running the Flask application in debug mode
if __name__ == "__main__":
    app.run(debug=True)