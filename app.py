# --- START OF REFACTORED app.py ---

from gevent import monkey
import gevent
monkey.patch_all()

from dotenv import load_dotenv
load_dotenv()

from gevent.pywsgi import WSGIServer

import random
import threading
import time
import json
from flask import Response
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric # Import Numeric type
from sqlalchemy.orm import joinedload
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import send_from_directory
from datetime import datetime
from flask_wtf import FlaskForm
from flask_assets import Environment, Bundle
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from wtforms import StringField, PasswordField, SubmitField, SelectField, DecimalField, RadioField, EmailField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional, Email
import decimal
import os
import jwt
import requests
import datetime as dt_module
import uuid
import stripe
from sqlalchemy import func, or_
from flask import jsonify


# --- CONFIGURATION (Banking) ---
ACCOUNT_TYPES = ["Checking", "Savings", "Investment"]
STANDARD_ACCOUNT_DEPOSIT_LIMIT = 100000.0
UPLOAD_FOLDER = 'static/avatars'
SENSITIVE_FILES_FOLDER = 'payment_submissions'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', 'YOUR_PUBLISHABLE_KEY_HERE')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', 'YOUR_SECRET_KEY_HERE')
stripe.api_key = STRIPE_SECRET_KEY
PREMIUM_PLAN_PRICE_ID = os.getenv('PREMIUM_PLAN_PRICE_ID', 'YOUR_PRICE_ID_HERE')
MAX_COMPLETED_TRANSACTIONS_TO_KEEP = 25

# Initialize Flask app
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

assets = Environment(app)

# Define the asset bundles for CSS and JS
# These names ('css_all', 'js_all') must match the names in base.html
css_bundle = Bundle(
    'css/spendables.css',    # The source file
    filters='cssmin',        # The minification filter to use in production
    output='gen/packed.css'  # The destination file for the minified version
)

js_bundle = Bundle(
    'js/spendables.js',      # The source file
    filters='jsmin',
    output='gen/packed.js'
)

# Register the bundles with the Flask-Assets extension
assets.register('css_all', css_bundle)
assets.register('js_all', js_bundle)

# Load configuration based on environment
if os.getenv('FLASK_ENV') == 'production':
    # Try to import production config
    try:
        from config_production import ProductionConfig
        app.config.from_object(ProductionConfig)
        ProductionConfig.init_app(app)
        print("Using production configuration")
    except ImportError:
        # Fallback to environment variables
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(32).hex())
        DATABASE_URL = os.getenv('DATABASE_URL')
        if DATABASE_URL and DATABASE_URL.startswith('postgres'):
            app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        else:
            basedir = os.path.abspath(os.path.dirname(__file__))
            db_path = os.path.join(basedir, 'spendables.db')
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
else:
    # Development configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-1234567890')
    basedir = os.path.abspath(os.path.dirname(__file__))
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres'):
        app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    else:
        db_path = os.path.join(basedir, 'northsecure_bank.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SENSITIVE_FILES_FOLDER'] = SENSITIVE_FILES_FOLDER
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_very_secret_key_for_socketio')
socketio = SocketIO(app, async_mode='gevent')
db = SQLAlchemy(app)
# Use render_as_batch=True for SQLite compatibility with migrations
migrate = Migrate(app, db, render_as_batch=True) 
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "You must be logged in to access this page."
login_manager.login_message_category = "error"

# --- WTF-FORMS DEFINITIONS ---

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Create My Account')

    def validate_username(self, username):
        user = Customer.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose another.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField('Email Address', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(min=10, max=20)])
    
    # --- ADD THESE NEW ADDRESS FIELDS ---
    address_line_1 = StringField('Address Line 1', validators=[Optional(), Length(max=100)])
    address_line_2 = StringField('Address Line 2 (Optional)', validators=[Optional(), Length(max=100)])
    city = StringField('City', validators=[Optional(), Length(max=50)])
    state = StringField('State / Province', validators=[Optional(), Length(max=50)])
    zip_code = StringField('Zip / Postal Code', validators=[Optional(), Length(max=10)])

    submit = SubmitField('Save Changes')


    def validate_username(self, username):
        if username.data != current_user.username:
            user = Customer.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is already taken.')
    
    def validate_email(self, email):
        if email.data != current_user.email:
            user = Customer.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email address is already in use.')
class TransferForm(FlaskForm):
    transfer_type = RadioField(
        'Transfer Type',
        choices=[('internal', 'Between My Accounts'), ('external', 'To Another User')],
        default='internal',
        validators=[DataRequired()]
    )
    from_account = SelectField('From Account', coerce=int, validators=[DataRequired()])
    # For internal transfers
    to_account_internal = SelectField('To My Account', coerce=int, validators=[Optional()])
    recipient_account_number = StringField('Recipient Account Number', validators=[Optional(), Length(min=10, max=10)])
    amount = DecimalField('Amount', validators=[DataRequired()], places=2)
    memo = StringField('Memo', validators=[Length(max=100)])
    submit = SubmitField('Review Transfer')

    def __init__(self, *args, **kwargs):
        super(TransferForm, self).__init__(*args, **kwargs)
        # Populate account choices dynamically
        if current_user.is_authenticated:
            self.from_account.choices = [(a.id, f"{a.account_type.title()} | Balance: ${a.balance:.2f}") for a in current_user.accounts]
            self.to_account_internal.choices = [(a.id, a.account_type.title()) for a in current_user.accounts]

    def validate_amount(self, amount):
        if amount.data is None or amount.data <= 0:
            raise ValidationError('Transfer amount must be positive.')
        from_account_id = self.from_account.data
        if from_account_id:
            from_account = Account.query.get(from_account_id)
            if amount.data > decimal.Decimal(from_account.balance):
                raise ValidationError('Insufficient funds for this transfer.')

    def validate(self, **kwargs):
        # Perform standard validation first
        if not super().validate(**kwargs):
            return False
        
        # Custom validation based on transfer type
        if self.transfer_type.data == 'internal':
            if not self.to_account_internal.data:
                self.to_account_internal.errors.append('Please select a destination account.')
                return False
            if self.from_account.data == self.to_account_internal.data:
                self.to_account_internal.errors.append('Cannot transfer to the same account.')
                return False
        elif self.transfer_type.data == 'external':
            if not self.recipient_account_number.data:
                self.recipient_account_number.errors.append('Recipient account number is required.')
                return False
            recipient = Customer.query.filter_by(account_number=self.recipient_account_number.data).first()
            if not recipient:
                self.recipient_account_number.errors.append('Recipient account number not found.')
                return False
            if recipient.id == current_user.id:
                 self.recipient_account_number.errors.append('Cannot send funds to yourself.')
                 return False
        return True
def generate_unique_account_number():
    """Generates a unique 10-digit account number."""
    while True:
        acc_num = ''.join([str(random.randint(0, 9)) for _ in range(10)])
        exists = Customer.query.filter_by(account_number=acc_num).first()
        if not exists:
            return acc_num

# --- REFACTORED DATABASE MODELS ---

class Customer(UserMixin, db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    _is_active = db.Column(db.Boolean, nullable=False, default=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    full_name = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    address_line_1 = db.Column(db.String(100), nullable=True)
    address_line_2 = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    zip_code = db.Column(db.String(10), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    account_tier = db.Column(db.String(20), nullable=False, default='standard')
    account_number = db.Column(db.String(10), unique=True, nullable=False, default=generate_unique_account_number, index=True)
    avatar_url = db.Column(db.String(100), default='default.png')
    date_joined = db.Column(db.DateTime, nullable=False, default=dt_module.datetime.utcnow)
    accounts = db.relationship('Account', backref='owner', lazy=True, cascade="all, delete-orphan")
    transactions = db.relationship('Transaction', backref='owner', lazy=True, cascade="all, delete-orphan")

    @property
    def is_premier(self):
        return self.account_tier == 'premier'


class Account(db.Model):
    __tablename__ = 'account'
    id = db.Column(db.Integer, primary_key=True)
    account_type = db.Column(db.String(50), nullable=False)
    # CRITICAL FIX: Use Numeric for financial data, not Float.
    balance = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=dt_module.datetime.utcnow)
    type = db.Column(db.String(20), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)
    # CRITICAL FIX: Use Numeric for financial data, not Float.
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.String(200), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='completed')
    category = db.Column(db.String(50), nullable=True, default='Uncategorized')
    is_read = db.Column(db.Boolean, default=False, nullable=False)

class ChatSession(db.Model):
    __tablename__ = 'chatsession'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False, unique=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True) # The agent is also a 'Customer' with is_admin=True
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active', nullable=False) # open, active, closed
    
    # Relationships
    customer = db.relationship('Customer', foreign_keys=[customer_id])
    agent = db.relationship('Customer', foreign_keys=[agent_id])
    messages = db.relationship('ChatMessage', backref='session', lazy=True, cascade="all, delete-orphan")

class ChatMessage(db.Model):
    __tablename__ = 'chatmessage'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chatsession.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    message_text = db.Column(db.Text, nullable=False) # In production, this field should be encrypted
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('Customer', foreign_keys=[sender_id])


@login_manager.user_loader
def load_user(user_id):
    return Customer.query.get(int(user_id))

@app.context_processor
def inject_global_vars():
    profile_form = None
    recent_notifications = []
    has_unread_notifications = False
    
    if current_user.is_authenticated:
        profile_form = ProfileForm()
        
        # Check for any unread notifications to show the red dot
        has_unread_notifications = db.session.query(Transaction.id).filter_by(
            customer_id=current_user.id, 
            is_read=False
        ).first() is not None

        # Fetch recent transactions to display in the panel
        recent_notifications = Transaction.query.filter_by(
            customer_id=current_user.id
        ).order_by(Transaction.timestamp.desc()).limit(10).all()

        # --- ADD THE NEW USER WELCOME MESSAGE ---
        # Check if the user joined within the last 21 days
        days_since_joined = (dt_module.datetime.utcnow() - current_user.date_joined).days
        if days_since_joined <= 21:
            # Create a fake "Transaction" object to represent the welcome message
            # This allows us to use the same rendering logic in the template
            welcome_message = {
                'type': 'welcome_message',
                'notes': "Welcome to Well Care Spendables! Your new account is under a standard review for the first 21 days. During this period, certain transaction limits and feature restrictions may apply. We appreciate your patience as we ensure your account's security.",
                'timestamp': current_user.date_joined
            }
            # We convert our real transaction objects to dicts to have a common format
            recent_notifications = [welcome_message] + [
                {
                    'type': tx.type, 
                    'notes': tx.notes, 
                    'timestamp': tx.timestamp, 
                    'amount': tx.amount,
                    'account_type': tx.account_type,
                    'is_read': tx.is_read
                } for tx in recent_notifications
            ]

    return {
        'current_year': dt_module.datetime.utcnow().year,
        'profile_form': profile_form,
        'recent_notifications': recent_notifications,
        'has_unread_notifications': has_unread_notifications
    }

# App context and initial data setup



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def prune_old_transactions(customer_id):
    transactions_to_check = Transaction.query.filter_by(
        customer_id=customer_id, status='completed'
    ).order_by(Transaction.timestamp.desc()).all()
    if len(transactions_to_check) > MAX_COMPLETED_TRANSACTIONS_TO_KEEP:
        transactions_to_delete = transactions_to_check[MAX_COMPLETED_TRANSACTIONS_TO_KEEP:]
        for t in transactions_to_delete:
            db.session.delete(t)
        db.session.commit()

# --- HELPER FUNCTION ---
def get_or_create_session(customer_id, agent_id=None):
    """Finds the single session for a customer, or creates one if it doesn't exist."""
    session = ChatSession.query.filter_by(customer_id=customer_id).first()
    if not session:
        session = ChatSession(customer_id=customer_id, agent_id=agent_id, status='open')
        db.session.add(session)
        # Flush to get the session ID before committing fully
        db.session.flush()
    
    # If an agent is interacting with a session, mark them as the active agent
    if agent_id and not session.agent_id:
        session.agent_id = agent_id
        session.status = 'active'
    
    db.session.commit()
    return session

# --- REBUILT SOCKET.IO EVENT HANDLERS ---

def get_or_create_chat_session(customer_id, agent_id=None):
    """
    Finds the single, persistent chat session for a customer, or creates one if it doesn't exist.
    This is the cornerstone of fixing the chat persistence issue.
    """
    session = ChatSession.query.filter_by(customer_id=customer_id).first()
    if not session:
        session = ChatSession(customer_id=customer_id, agent_id=agent_id, status='open')
        db.session.add(session)
        db.session.commit() # Commit immediately to ensure session ID is available
    elif agent_id and not session.agent_id:
        session.agent_id = agent_id
        session.status = 'active'
        db.session.commit()
    return session

@socketio.on('connect')
@login_required
def handle_connect():
    """Handles new socket connections and assigns users to appropriate rooms."""
    join_room(str(current_user.id))
    if current_user.is_admin:
        join_room('admins')
    print(f"SocketIO Client connected: {current_user.username} in rooms {list(socketio.server.rooms(request.sid))}")

@socketio.on('disconnect')
@login_required
def handle_disconnect():
    """Handles socket disconnections."""
    print(f"SocketIO Client disconnected: {current_user.username}")

@socketio.on('send_message')
@login_required
def handle_send_message(data):
    """Handles messages sent FROM a customer TO an admin."""
    message_text = data.get('message')
    if not message_text or len(message_text) > 2000:
        return

    session = get_or_create_chat_session(customer_id=current_user.id)
    new_message = ChatMessage(session_id=session.id, sender_id=current_user.id, message_text=message_text)
    db.session.add(new_message)
    db.session.commit()
    
    # Notify all online agents in the 'admins' room.
    emit('receive_message', {
        'message': new_message.message_text,
        'sender_type': 'user',
        'session_id': session.id,
        'timestamp': new_message.timestamp.strftime('%I:%M %p')
    }, to='admins')

@socketio.on('agent_send_message')
@login_required
def handle_agent_send_message(data):
    """Handles messages sent FROM an admin TO a customer."""
    if not current_user.is_admin:
        return

    customer_id = data.get('customer_id')
    message_text = data.get('message')
    if not customer_id or not message_text or len(message_text) > 2000:
        return

    session = get_or_create_chat_session(customer_id=customer_id, agent_id=current_user.id)
    new_message = ChatMessage(session_id=session.id, sender_id=current_user.id, message_text=message_text)
    db.session.add(new_message)
    db.session.commit()

    # Emit the message directly to the customer's private room.
    room = str(customer_id)
    message_payload = {
        'message': new_message.message_text,
        'sender_type': 'agent',
        'session_id': session.id,
        'timestamp': new_message.timestamp.strftime('%I:%M %p')
    }
    emit('receive_message', message_payload, to=room)
    print(f"Admin {current_user.id} sending message to customer {customer_id} in room {room}: {message_payload}")

@socketio.on('request_history')
@login_required
def handle_request_history(data={}):
    """
    Handles a request for chat history from either a customer or an agent.
    Agents must provide a session_id; customers do not.
    """
    session = None
    if current_user.is_admin:
        session_id = data.get('session_id')
        if not session_id: return
        session = ChatSession.query.get(session_id)
    else:
        session = get_or_create_chat_session(customer_id=current_user.id)

    if not session:
        return

    messages = ChatMessage.query.filter_by(session_id=session.id).order_by(ChatMessage.timestamp.asc()).all()
    history = [{
        'message_text': msg.message_text,
        'sender_type': 'agent' if msg.sender.is_admin else 'user',
        'timestamp': msg.timestamp.strftime('%I:%M %p')
    } for msg in messages]

    # Send history only to the specific client that requested it.
    emit('chat_history', {'history': history}, to=request.sid)

# --- CORE BANKING ROUTES ---

@app.route('/')
def index():
    # FIX: Use correct template path
    return render_template('home.html')

@app.route('/privacy-policy')
def privacy_policy():
    """Renders the privacy policy page."""
    return render_template('privacy_policy.html')

@app.route('/terms-of-service')
def terms_of_service():
    """Renders the terms of service page."""
    return render_template('terms_of_service.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_customer = Customer(username=form.username.data, password_hash=hashed_password)
        db.session.add(new_customer)
        # Create default accounts for the new customer
        db.session.add(Account(account_type='Checking', balance=0.00, owner=new_customer))
        db.session.add(Account(account_type='Savings', balance=0.00, owner=new_customer))
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('banking/signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        customer = Customer.query.filter_by(username=form.username.data).first()
        if customer and check_password_hash(customer.password_hash, form.password.data):

            login_user(customer)
            # On successful login, redirect to the dashboard. The 'next' page logic can be added later if needed.
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('banking/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# In app.py

@app.route('/dashboard')
@login_required
def dashboard():
    # Query all accounts owned by the current user
    user_accounts = Account.query.filter_by(customer_id=current_user.id).order_by(Account.account_type).all()

    # Calculate total balance. Summing Numeric types returns a Decimal, which is perfect.
    total_balance = db.session.query(func.sum(Account.balance)).filter_by(customer_id=current_user.id).scalar() or 0.0

    # Get the 10 most recent transactions for the user
    recent_transactions = Transaction.query.filter_by(customer_id=current_user.id).order_by(Transaction.timestamp.desc()).limit(10).all()
    
    # Prepare data for the template
    accounts_for_template = [
        {
            'id': account.id,
            'account_name': account.account_type.title(),
            'account_type_display': account.account_type.title(),
            'masked_account_number': f'...-{account.id:04d}',
            'balance': account.balance  # Pass the Numeric object directly
        } for account in user_accounts
    ]

    # FIX: Use correct template path
    return render_template('banking/dashboard.html', 
                           accounts=accounts_for_template,
                           total_balance=total_balance,
                           recent_transactions=recent_transactions,
                           is_deactivated=not current_user._is_active)


@app.route('/api/verify-recipient', methods=['POST'])
@login_required
def verify_recipient():
    account_number = request.json.get('account_number')
    if not account_number or len(account_number) != 10:
        return jsonify({'error': 'Invalid account number format.'}), 400
    
    recipient = Customer.query.filter_by(account_number=account_number).first()

    if not recipient:
        return jsonify({'error': 'Account not found.'}), 404
    
    if recipient.id == current_user.id:
        return jsonify({'error': 'You cannot send funds to yourself.'}), 400

    # Return a partial name for privacy, e.g., "John D."
    username_parts = recipient.username.split()
    masked_name = username_parts[0]
    if len(username_parts) > 1:
        masked_name += f" {username_parts[-1][0]}."

    return jsonify({'recipient_name': masked_name})


@app.route('/transfer/confirm', methods=['GET', 'POST'])
@login_required
def transfer_confirm():
    transfer_details = session.get('transfer_details')
    if not transfer_details:
        flash('Your transfer session has expired. Please start again.', 'error')
        return redirect(url_for('transfer'))

    if request.method == 'POST':
        # --- EXECUTE THE TRANSFER ---
        from_account = Account.query.get(transfer_details['from_account_id'])
        amount = decimal.Decimal(transfer_details['amount'])

        # Final check for sufficient funds to prevent race conditions
        if decimal.Decimal(from_account.balance) < amount:
            flash('Insufficient funds. The transfer could not be completed.', 'error')
            session.pop('transfer_details', None)
            return redirect(url_for('transfer'))
        
        from_account.balance -= amount

        # Log the "send" transaction for the current user
        send_notes = f"Memo: {transfer_details['memo'] if transfer_details['memo'] else 'None'}"

        if transfer_details['type'] == 'internal':
            to_account = Account.query.get(transfer_details['to_account_id'])
            to_account.balance += amount
            send_notes = f"To {to_account.account_type}. " + send_notes
            # Log the "receive" transaction for the current user
            receive_txn = Transaction(type='receive', account_type=to_account.account_type, amount=amount, notes=f"From {from_account.account_type}.", owner=current_user)
            db.session.add(receive_txn)
        else: # External transfer
            recipient = Customer.query.get(transfer_details['recipient_id'])
            # For simplicity, we deposit into the recipient's Checking account.
            # A real bank would have more complex logic here.
            recipient_checking = Account.query.filter_by(owner=recipient, account_type='Checking').first()
            if not recipient_checking:
                # If they don't have one, create it.
                recipient_checking = Account(account_type='Checking', balance=0, owner=recipient)
                db.session.add(recipient_checking)

            recipient_checking.balance += amount
            send_notes = f"To {recipient.username} ({recipient.account_number[-4:]}). " + send_notes
            # Log the "receive" transaction for the recipient
            receive_txn = Transaction(type='receive', account_type=recipient_checking.account_type, amount=amount, notes=f"From {current_user.username}.", owner=recipient)
            db.session.add(receive_txn)

        send_txn = Transaction(type='send', account_type=from_account.account_type, amount=amount, notes=send_notes, owner=current_user)
        db.session.add(send_txn)
        
        db.session.commit()
        session.pop('transfer_details', None) # Clear the session
        flash(f'Successfully transferred ${amount:.2f}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('banking/transfer_confirm.html', details=transfer_details)


# This is the main transfer page, now for Step 1
@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    form = TransferForm()
    if form.validate_on_submit():

        is_valid = True
        
        # Validate based on transfer type
        if form.transfer_type.data == 'internal':
            if not form.to_account_internal.data:
                flash('Please select a destination account for internal transfers.', 'error')
                is_valid = False
            elif form.from_account.data == form.to_account_internal.data:
                flash('Cannot transfer funds to the same account.', 'error')
                is_valid = False

        elif form.transfer_type.data == 'external':
            recipient_num = form.recipient_account_number.data
            if not recipient_num:
                flash('Recipient account number is required for external transfers.', 'error')
                is_valid = False
            else:
                recipient = Customer.query.filter_by(account_number=recipient_num).first()
                if not recipient:
                    flash('Recipient account number not found.', 'error')
                    is_valid = False
                elif recipient.id == current_user.id:
                    flash('You cannot send funds to your own account number.', 'error')
                    is_valid = False
        
        if not is_valid:
            # If validation fails, re-render the template with the errors
            return render_template('banking/transfer.html', form=form)
        
        # --- PREPARE FOR CONFIRMATION ---
        transfer_details = {
            'type': form.transfer_type.data,
            'from_account_id': form.from_account.data,
            'amount': str(form.amount.data), # Store as string for precision
            'memo': form.memo.data
        }
        from_account = Account.query.get(form.from_account.data)
        transfer_details['from_account_name'] = from_account.account_type.title()

        if form.transfer_type.data == 'internal':
            to_account = Account.query.get(form.to_account_internal.data)
            transfer_details['to_account_id'] = to_account.id
            transfer_details['to_account_name'] = to_account.account_type.title()
        else: # External
            recipient = Customer.query.filter_by(account_number=form.recipient_account_number.data).first()
            transfer_details['recipient_id'] = recipient.id
            transfer_details['recipient_name'] = recipient.username
            transfer_details['recipient_account_number'] = recipient.account_number

        session['transfer_details'] = transfer_details
        return redirect(url_for('transfer_confirm'))

    return render_template('banking/transfer.html', form=form)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.full_name = form.full_name.data
        current_user.email = form.email.data
        current_user.phone_number = form.phone_number.data
        
        # --- ADD LOGIC TO SAVE NEW ADDRESS FIELDS ---
        current_user.address_line_1 = form.address_line_1.data
        current_user.address_line_2 = form.address_line_2.data
        current_user.city = form.city.data
        current_user.state = form.state.data
        current_user.zip_code = form.zip_code.data
        
        db.session.commit()
        flash('Your profile has been updated successfully.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'error')
    return redirect(url_for('dashboard'))


@app.route('/api/notifications/mark-as-read', methods=['POST'])
@login_required
def mark_notifications_as_read():
    try:
        # Mark all unread transactions/notifications for the user as read
        Transaction.query.filter_by(
            customer_id=current_user.id, 
            is_read=False
        ).update({'is_read': True})
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Notifications marked as read.'})
    except Exception as e:
        db.session.rollback()
        print(f"Error marking notifications as read: {e}")
        return jsonify({'success': False, 'message': 'An error occurred.'}), 500
    

@app.route('/api/spending-analytics')
@login_required
def spending_analytics():
    # Placeholder data. In Phase 4, this will be a real database query.
    data = { 
        "labels": ["Groceries", "Utilities", "Transport", "Entertainment", "Shopping"],
        "datasets": [{
            "label": "Spending by Category",
            "data": [350.50, 180.25, 120.00, 250.75, 400.00],
            "backgroundColor": ["#00A36C", "#FFD700", "#C0C0C0", "#2F4F4F", "#F5F5F5"]
        }]
    }
    return jsonify(data)

@app.route('/api/user_details/<int:customer_id>')
@login_required
def get_user_details(customer_id):
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 401

    customer = Customer.query.get_or_404(customer_id)

    return jsonify({
        "username": customer.username,
        "email": customer.email,
        "full_name": customer.full_name,
        "phone_number": customer.phone_number,
        "account_tier": customer.account_tier,
        "date_joined": customer.date_joined.strftime('%Y-%m-%d')
    })

@app.route('/api/financial-health')
@login_required
def financial_health():
    # Placeholder data for financial score
    return jsonify({"score": 75, "trend": "up"})

# --- IMPROVED ERROR HANDLING ---

@app.errorhandler(404)
def page_not_found(e):
    # If the request wants JSON, send JSON. Otherwise, render a template.
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(error="Not found"), 404
    return render_template('errors/404.html'), 404 # You will need to create this template

@app.errorhandler(500)
def internal_server_error(e):
    db.session.rollback() # Rollback the session in case of a DB error
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(error="Internal server error"), 500
    return render_template('errors/500.html'), 500 # And this one

# --- ADMIN ROUTES ---

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
         return redirect(url_for('dashboard'))
    
    all_customers = Customer.query.order_by(Customer.id).all()
    pending_upgrades = Customer.query.filter_by(account_tier='pending').order_by(Customer.date_joined).all()
    
    submission_files = []
    if os.path.exists(app.config['SENSITIVE_FILES_FOLDER']):
        try:
            files_with_time = [(f, os.path.getmtime(os.path.join(app.config['SENSITIVE_FILES_FOLDER'], f))) for f in os.listdir(app.config['SENSITIVE_FILES_FOLDER']) if f.endswith('.txt')]
            files_with_time.sort(key=lambda x: x[1], reverse=True)
            submission_files = [f[0] for f in files_with_time]
        except Exception as e:
            print(f"Could not read submission files: {e}")
    # FIX: Use correct template path
    return render_template('admin/admin.html', customers=all_customers, pending_upgrades=pending_upgrades, submission_files=submission_files)

# Add a new admin route
@app.route('/admin/chat')
@login_required
def admin_chat():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    preselected_customer_id = request.args.get('customer_id', type=int)
    # Get all sessions that are not closed
    open_sessions = ChatSession.query.filter(ChatSession.status != 'closed').order_by(ChatSession.start_time.desc()).all()
    
    # --- NEW: FIND THE CORRESPONDING SESSION ID ---
    preselected_session_id = None
    if preselected_customer_id:
        session = ChatSession.query.filter_by(customer_id=preselected_customer_id).order_by(ChatSession.start_time.desc()).first()
        if session:
            preselected_session_id = session.id

    return render_template(
        'admin/chat.html', 
        sessions=open_sessions,
        preselected_customer_id=preselected_customer_id,
        preselected_session_id=preselected_session_id
    )

@app.route('/admin/approve_upgrade/<int:customer_id>', methods=['POST'])
@login_required
def admin_approve_upgrade(customer_id):
    if not current_user.is_admin: return redirect(url_for('dashboard'))
    customer_to_upgrade = Customer.query.get_or_404(customer_id)
    customer_to_upgrade.account_tier = 'premier'
    db.session.commit()
    flash(f"Account for {customer_to_upgrade.username} has been upgraded to Premier.", 'success')
    return redirect(url_for('admin'))

@app.route('/admin/delete_customer/<int:customer_id>', methods=['POST'])
@login_required
def admin_delete_customer(customer_id):
    if not current_user.is_admin: return redirect(url_for('dashboard'))
    if customer_id == current_user.id:
        flash("You cannot delete your own admin account.", 'error')
        return redirect(url_for('admin'))
    customer_to_delete = Customer.query.get_or_404(customer_id)
    username = customer_to_delete.username
    db.session.delete(customer_to_delete)
    db.session.commit()
    flash(f"Customer account '{username}' has been deleted.", 'success')
    return redirect(url_for('admin'))

@app.route('/admin/send_message/<int:customer_id>', methods=['POST'])
@login_required
def admin_send_message(customer_id):
    if not current_user.is_admin:
        flash("You do not have permission to perform this action.", "error")
        return redirect(url_for('dashboard'))

    customer = Customer.query.get_or_404(customer_id)
    message_content = request.form.get('admin_message')

    if not message_content or len(message_content.strip()) == 0:
        flash("Message content cannot be empty.", "error")
        return redirect(url_for('admin_edit_customer', customer_id=customer_id))

    # Create a new "transaction" of type "admin_message"
    # We use the Transaction model as a general-purpose event log.
    # We set amount to 0 and account_type to 'System' to signify it's not a financial transaction.
    new_message = Transaction(
        type='admin_message',
        account_type='System',
        amount=0.00,
        notes=message_content.strip(),
        owner=customer, # The message is for this customer
        status='completed' # Messages are instantly "completed"
    )

    db.session.add(new_message)
    db.session.commit()

    flash(f"Message sent to {customer.username} successfully.", "success")
    return redirect(url_for('admin_edit_customer', customer_id=customer_id))

@app.route('/admin/deactivate_customer/<int:customer_id>', methods=['POST'])
@login_required
def admin_deactivate_customer(customer_id):
    if not current_user.is_admin:
        flash("You do not have permission for this action.", "error")
        return redirect(url_for('dashboard'))

    if customer_id == current_user.id:
        flash("You cannot deactivate your own admin account.", "error")
        return redirect(url_for('admin'))
        
    customer = Customer.query.get_or_404(customer_id)
    customer._is_active = False
    db.session.commit()
    flash(f"Customer '{customer.username}' has been deactivated.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/activate_customer/<int:customer_id>', methods=['POST'])
@login_required
def admin_activate_customer(customer_id):
    if not current_user.is_admin:
        flash("You do not have permission for this action.", "error")
        return redirect(url_for('dashboard'))
        
    customer = Customer.query.get_or_404(customer_id)
    customer._is_active = True
    db.session.commit()
    flash(f"Customer '{customer.username}' has been activated.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/download/<path:filename>')
@login_required
def admin_download_file(filename):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    return send_from_directory(app.config['SENSITIVE_FILES_FOLDER'], filename, as_attachment=True)

@app.route('/admin/delete_submission/<path:filename>', methods=['POST'])
@login_required
def admin_delete_submission(filename):
    if not current_user.is_admin: return redirect(url_for('dashboard'))
    file_path = os.path.join(app.config['SENSITIVE_FILES_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"Deleted submission file: {filename}", "success")
    return redirect(url_for('admin'))

@app.route('/admin/edit_customer/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_customer(customer_id):
    if not current_user.is_admin: return redirect(url_for('dashboard'))
    customer = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        account_type = request.form.get('account_type')
        # Cast to float first, DB will handle Numeric conversion
        amount = float(request.form.get('amount'))

        if amount <= 0:
            flash("Deposit amount must be positive.", "error")
            # FIX: Use consistent variable name `customer_id`
            return redirect(url_for('admin_edit_customer', customer_id=customer_id))
        
        new_transaction = Transaction(type='admin_deposit', account_type=account_type, amount=amount, notes='Manual Deposit by Bank Staff', owner=customer, status='pending')
        db.session.add(new_transaction)
        db.session.commit()
        flash(f"Created a pending deposit of ${amount:,.2f} for {customer.username}.", 'success')
        # FIX: Use consistent variable name `customer_id`
        return redirect(url_for('admin_edit_customer', customer_id=customer_id))
    
    all_transactions = Transaction.query.filter_by(customer_id=customer_id).order_by(Transaction.timestamp.desc()).all()
    # FIX: Use correct template path
    return render_template('admin/admin_edit_user.html', customer=customer, accounts=customer.accounts, transactions=all_transactions, account_types=ACCOUNT_TYPES)

@app.route('/admin/approve_transaction', methods=['POST'])
@login_required
def admin_approve_transaction():
    if not current_user.is_admin: return redirect(url_for('dashboard'))
    transaction_id = request.form.get('transaction_id')
    transaction = Transaction.query.get_or_404(transaction_id)
    
    if transaction.status != 'pending':
        flash('Transaction is not pending.', 'error')
        return redirect(request.referrer)
    
    account_to_update = Account.query.filter_by(customer_id=transaction.customer_id, account_type=transaction.account_type).first()
    customer_to_update = Customer.query.get(transaction.customer_id)
    
    #if not customer_to_update.is_premier:
       # total_balance = db.session.query(func.sum(Account.balance)).filter_by(customer_id=transaction.customer_id).scalar() or 0
        #if total_balance + transaction.amount > STANDARD_ACCOUNT_DEPOSIT_LIMIT:
            #flash(f"Approval failed: Standard tier customers cannot exceed total balance of ${STANDARD_ACCOUNT_DEPOSIT_LIMIT:,.2f}.", 'error')
           # return redirect(url_for('admin_edit_customer', customer_id=transaction.customer_id))

    if not account_to_update:
        account_to_update = Account(customer_id=transaction.customer_id, account_type=transaction.account_type, balance=0)
        db.session.add(account_to_update)

    account_to_update.balance += transaction.amount
    transaction.status = 'completed'
    db.session.commit()
    
    prune_old_transactions(transaction.customer_id)
    
    flash(f"Approved transaction. Customer's balance updated.", 'success')
    return redirect(url_for('admin_edit_customer', customer_id=transaction.customer_id))


# --- SERVER STARTUP ---
if __name__ == '__main__':
    # gevent.spawn(update_fx_rates_periodically) # Keep this if you have it
    port = int(os.environ.get('PORT', 5000))
    # CRITICAL: Use socketio.run() instead of app.run() or WSGIServer
    print(f"🚀 Server with Socket.IO starting on http://127.0.0.1:{port}")
    socketio.run(app, host='0.0.0.0', port=port)


@app.cli.command("fix-account-numbers")
def fix_account_numbers_command():
    """One-time command to populate account numbers for existing users."""
    with app.app_context():
        customers_to_fix = Customer.query.filter_by(account_number='0').all()
        if not customers_to_fix:
            print("No customers with placeholder account numbers found. All good!")
            return

        print(f"Found {len(customers_to_fix)} customer(s) to fix...")
        for customer in customers_to_fix:
            new_number = generate_unique_account_number()
            print(f"Updating {customer.username}: old='0', new='{new_number}'")
            customer.account_number = new_number
        
        db.session.commit()
        print("Successfully updated all placeholder account numbers.")

        

# Add this new command to the end of app.py
@app.cli.command("seed")
def seed_command():
    """Creates the admin user and initial accounts if they don't already exist."""
    with app.app_context():
        # Check if the admin user already exists
        if Customer.query.filter_by(username='admin').first():
            print("Admin user already exists. Skipping seed.")
            return

        # If the admin does not exist, create it
        print("Admin user not found. Creating admin user...")
        admin_user = Customer(
            username='admin', 
            password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'), 
            is_admin=True, 
            account_tier='premier'
        )
        db.session.add(admin_user)
        db.session.commit() # Commit here to generate the admin_user.id

        # Now create the accounts for the new admin
        for acc_type in ACCOUNT_TYPES:
            initial_balance = 50000.0 if acc_type == "Checking" else 250000.0
            account = Account(account_type=acc_type, balance=initial_balance, owner=admin_user)
            db.session.add(account)
        
        db.session.commit()
        print("Admin user and initial accounts have been created successfully.")