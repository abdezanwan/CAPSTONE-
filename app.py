from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_migrate import Migrate
from datetime import time  # Import the time class
from twilio.rest import Client
from flask import request
from sqlalchemy import text


app = Flask(__name__)
app.debug = True  

app.config['SECRET_KEY'] = '1991992'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://ycosgnii:dd-Vsa3f9IssXPOeQK6x0mevfsgTfnKJ@suleiman.db.elephantsql.com/ycosgnii'
app.add_url_rule('/static/<filename>', 'static', build_only=True)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    phone_number = db.Column(db.String(15))  # Add a field for the phone number

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')
     
    def __init__(self, date, time, customer_id, status):
        self.date = date
        self.time = time
        self.customer_id = customer_id
        self.status = status
# Define a Product model in your app

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False)

# Define a Cart model to store the selected products

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)


account_sid = 'ACa2f4ea048719d0c38a697f31f0ec33ed'
auth_token = 'addf8b0e91b43847d69a14dad99698d7'
print("Twilio Account SID:", account_sid)
print("Twilio Auth Token:", auth_token)
client = Client(account_sid, auth_token)

@app.route('/')
def home():
    return render_template('home.html')
# Import necessary libraries and models
from datetime import datetime, timedelta

# ...

@app.route('/schedule_appointment', methods=['GET', 'POST'])
@login_required
def schedule_appointment():
    if request.method == 'POST':
        selected_date = request.form['date']
        selected_time = request.form['time']
        
        # Check if the user already has an appointment for the selected date and time.
        existing_appointment = Appointment.query.filter_by(
            date=selected_date,
            time=selected_time,
            customer_id=current_user.id
        ).first()
        
        if existing_appointment:
            flash('You already have an appointment at this date and time.', 'danger')
        else:
            # Create a new Appointment record for the user.
            appointment = Appointment(date=selected_date, time=selected_time, customer_id=current_user.id, status='Pending')
            db.session.add(appointment)
            db.session.commit()
            if confirm_appointment(appointment.id):
                return redirect(url_for('confirm_appointment', appointment_id=appointment.id))
            else:
                flash('Appointment requested successfully.', 'success')
    
    # Generate available time slots.
    # For example, create time slots at 25-minute intervals with a limit of 4 customers per hour.
    available_appointments = []
    current_time = datetime.strptime("09:00 AM", "%I:%M %p")
    end_time = datetime.strptime("06:00 PM", "%I:%M %p")
    while current_time < end_time:
        time_slot = current_time.strftime("%I:%M %p")
        available_appointments.append(time_slot)
        current_time += timedelta(minutes=25)

    # Create a list of scheduled appointments for each day
    appointments_by_day = {}  # Dictionary to store appointments by day
    appointments = Appointment.query.all()
    for appointment in appointments:
        date = appointment.date.strftime("%Y-%m-%d")  # Convert date to string
        time = appointment.time.strftime("%I:%M %p")  # Convert time to string
        if date not in appointments_by_day:
            appointments_by_day[date] = []
        appointments_by_day[date].append(time)
    
    return render_template('schedule_appointment.html', available_appointments=available_appointments, appointments_by_day=appointments_by_day)


@app.route('/confirm_appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def confirm_appointment(appointment_id):
    print("Reached confirm_appointment route") 
    # sql_query = text("SELECT * FROM appointment WHERE id = :appointment_id")
    appointment = Appointment.query.filter_by(id=appointment_id).first()

    print(">>>> appointment<<<< ")
    print(appointment)
    if request.method == 'POST':
        print("Handling confirmation process")
        # Handle the confirmation process, set status to 'Confirmed'
        appointment.status = 'Confirmed'
        db.session.commit()
        flash('Appointment confirmed successfully.', 'success')
        # Send a confirmation message to the customer using Twilio
        customer = User.query.filter_by(id=appointment.customer_id).first()
        if customer.phone_number:
            print("Customer's Phone Number:", customer.phone_number)
            try:
                message = client.messages.create(
                    body='Your appointment has been confirmed. We look forward to seeing you!',
                    from_='+18337658508',
                    to=appointment.customer.phone_number
                )
                flash('Confirmation message sent successfully.', 'success')
            except Exception as e:
                flash('Error sending the confirmation message.', 'danger')
        else:
            flash('No phone number associated with the customer\'s account.', 'danger')
        return render_template('confirmation_page.html', appointment=appointment)
    return render_template('confirm_appointment.html', appointment=appointment)

@app.route('/send-message', methods=['POST'])
@login_required
def send_message():
    print("Reached send_message route")
    if current_user.phone_number:
        print("Sending confirmation message")
        try:
            # Replace 'your_twilio_number' with your Twilio phone number
            message = client.messages.create(
                body='Your appointment has been confirmed. We look forward to seeing you!',
                from_='+18337658508',
                to=current_user.phone_number
            )
            flash('Confirmation message sent successfully.', 'success')
        except Exception as e:
            flash('Error sending the confirmation message.', 'danger')
    else:
        flash('No phone number associated with your account.', 'danger')
    return redirect(url_for('schedule_appointment'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/list_appointments', methods=['GET'])
@login_required  # Ensure that only authorized users (admin/staff) can access this route
def list_appointments():
    # Retrieve a list of appointments from the database
    appointments = Appointment.query.all()
    return render_template('list_appointments.html', appointments=appointments)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone_number = request.form['phone_number']  # Get the phone number from the form

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
        else:
            new_user = User(username=username, password=password, email=email, phone_number=phone_number)  # Save the phone number to the database
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('home'))  # Redirect to the schedule appointment page
        else:
            flash('Login failed. Please check your credentials and try again.', 'danger')
    return render_template('login.html')

@app.route('/products')
def product_list():
    products = Product.query.all()
    print(products)

    products.append({
        "name":"Hair Cream",
        "Price": "20$",
        "Image":"https://m.media-amazon.com/images/I/51eZn9z+E3L._SY300_SX300_.jpg"
    })
    products.append({
        "name":"LATTAFA QAED AL FURSAN",
        "Price": "20$",
        "Image":"https://m.media-amazon.com/images/I/51+kkdlWlAL._SX679_.jpg"
    })
    products.append({
        "name":"SheaMoisture",
        "Price": "13$",
        "Image":"https://m.media-amazon.com/images/I/61xIOun2OIL._SX679_.jpg"
    })
    products.append({
        "name":"Shiva Face & Body Scrub",
        "Price": "10$",
        "Image":"https://m.media-amazon.com/images/I/511w09Z0o9L._AC_SX679_.jpg"
    })
    products.append({
        "name":"Happiness Beauty Hair Color Shampoo",
        "Price": "20$",
        "Image":"https://m.media-amazon.com/images/I/61tHQdtGj4L._AC_SY879_.jpg"
    })
    products.append({
        "name":"Lattafa Ana Abiyedh",
        "Price": "20$",
        "Image":"https://m.media-amazon.com/images/I/41E547cb+eL._SX679_.jpg"
    })
    return render_template('product_list.html', products=products)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    product = Product.query.get(product_id)

    if product:
        existing_cart_item = Cart.query.filter_by(
            customer_id=current_user.id,
            product_id=product.id
        ).first()

        if existing_cart_item:
            existing_cart_item.quantity += quantity
        else:
            cart_item = Cart(
                customer_id=current_user.id,
                product_id=product.id,
                quantity=quantity
            )
            db.session.add(cart_item)

        db.session.commit()
        flash('Product added to cart successfully.', 'success')

    return redirect(url_for('product_list'))


@app.route('/view_cart')
@login_required
def view_cart():
    cart_items = Cart.query.filter_by(customer_id=current_user.id).all()
    return render_template('cart.html', cart_items=cart_items)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    db.create_all()
    app.run()
