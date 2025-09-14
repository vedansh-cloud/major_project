from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from config import Config
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Helper function to get database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Initialize database
def init_db():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    aadhar VARCHAR(12) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    balance DECIMAL(10, 2) DEFAULT 0.00,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    type ENUM('deposit', 'withdraw', 'transfer') NOT NULL,
                    amount DECIMAL(10, 2) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            connection.commit()
            print("Database initialized successfully")
        except Error as e:
            print(f"Error initializing database: {e}")
        finally:
            cursor.close()
            connection.close()

# Initialize the database when the app starts
init_db()

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        aadhar = request.form['aadhar']
        password = request.form['password']
        
        # Validate inputs
        if not username or not aadhar or not password:
            flash('All fields are required!', 'danger')
            return render_template('register.html')
        
        if len(aadhar) != 12 or not aadhar.isdigit():
            flash('Aadhar must be 12 digits!', 'danger')
            return render_template('register.html')
        
        # Hash password
        hashed_password = generate_password_hash(password)
        
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO users (username, aadhar, password) VALUES (%s, %s, %s)",
                    (username, aadhar, hashed_password)
                )
                connection.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            except Error as e:
                if 'Duplicate entry' in str(e):
                    if 'username' in str(e):
                        flash('Username already exists!', 'danger')
                    else:
                        flash('Aadhar already registered!', 'danger')
                else:
                    flash('Registration failed! Please try again.', 'danger')
            finally:
                cursor.close()
                connection.close()
    
    return render_template('register.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                
                if user and check_password_hash(user['password'], password):
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid username or password!', 'danger')
            except Error as e:
                flash('Login failed! Please try again.', 'danger')
            finally:
                cursor.close()
                connection.close()
    
    return render_template('login.html')

# Dashboard page
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT balance FROM users WHERE id = %s", (session['user_id'],))
            user = cursor.fetchone()
            
            return render_template('dashboard.html', username=session['username'], balance=user['balance'])
        except Error as e:
            flash('Error loading dashboard!', 'danger')
        finally:
            cursor.close()
            connection.close()
    
    return redirect(url_for('login'))

# Deposit page
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get current balance for display
    connection = get_db_connection()
    balance = 0.00
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT balance FROM users WHERE id = %s", (session['user_id'],))
            user = cursor.fetchone()
            if user:
                balance = user['balance']
        except Error as e:
            print(f"Error fetching balance: {e}")
        finally:
            cursor.close()
            connection.close()
    
    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
            
            if amount <= 0:
                flash('Amount must be positive!', 'danger')
                return render_template('deposit.html', balance=balance)
            
            connection = get_db_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    # Update balance
                    cursor.execute(
                        "UPDATE users SET balance = balance + %s WHERE id = %s",
                        (amount, session['user_id'])
                    )
                    # Record transaction
                    cursor.execute(
                        "INSERT INTO transactions (user_id, type, amount, description) VALUES (%s, 'deposit', %s, %s)",
                        (session['user_id'], amount, f'Deposited ₹{amount:.2f}')
                    )
                    connection.commit()
                    flash(f'Successfully deposited ₹{amount:.2f}!', 'success')
                    return redirect(url_for('dashboard'))
                except Error as e:
                    flash(f'Deposit failed! Error: {e}', 'danger')
                    print(f"Database error: {e}")
                finally:
                    cursor.close()
                    connection.close()
            else:
                flash('Database connection failed!', 'danger')
        except ValueError:
            flash('Invalid amount! Please enter a valid number.', 'danger')
    
    return render_template('deposit.html', balance=balance)

# Withdraw page
@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get current balance for display
    connection = get_db_connection()
    balance = 0.00
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT balance FROM users WHERE id = %s", (session['user_id'],))
            user = cursor.fetchone()
            if user:
                balance = user['balance']
        except Error as e:
            print(f"Error fetching balance: {e}")
        finally:
            cursor.close()
            connection.close()
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        
        if amount <= 0:
            flash('Amount must be positive!', 'danger')
            return render_template('withdraw.html', balance=balance)
        
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                # Check current balance
                cursor.execute("SELECT balance FROM users WHERE id = %s", (session['user_id'],))
                user = cursor.fetchone()
                
                if user['balance'] < amount:
                    flash('Insufficient balance!', 'danger')
                    return render_template('withdraw.html', balance=balance)
                
                # Update balance
                cursor.execute(
                    "UPDATE users SET balance = balance - %s WHERE id = %s",
                    (amount, session['user_id'])
                )
                # Record transaction
                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, description) VALUES (%s, 'withdraw', %s, %s)",
                    (session['user_id'], amount, f'Withdrew ₹{amount:.2f}')
                )
                connection.commit()
                flash(f'Successfully withdrew ₹{amount:.2f}!', 'success')
                return redirect(url_for('dashboard'))
            except Error as e:
                flash('Withdrawal failed! Please try again.', 'danger')
            finally:
                cursor.close()
                connection.close()
    
    return render_template('withdraw.html', balance=balance)

# Transfer page
@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get current balance for display
    connection = get_db_connection()
    balance = 0.00
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT balance FROM users WHERE id = %s", (session['user_id'],))
            user = cursor.fetchone()
            if user:
                balance = user['balance']
        except Error as e:
            print(f"Error fetching balance: {e}")
        finally:
            cursor.close()
            connection.close()
    
    if request.method == 'POST':
        receiver_username = request.form['receiver_username']
        amount = float(request.form['amount'])
        
        if amount <= 0:
            flash('Amount must be positive!', 'danger')
            return render_template('transfer.html', balance=balance)
        
        if receiver_username == session['username']:
            flash('Cannot transfer to yourself!', 'danger')
            return render_template('transfer.html', balance=balance)
        
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                # Check if receiver exists
                cursor.execute("SELECT id, username FROM users WHERE username = %s", (receiver_username,))
                receiver = cursor.fetchone()
                
                if not receiver:
                    flash('Receiver not found!', 'danger')
                    return render_template('transfer.html', balance=balance)
                
                # Check current balance
                cursor.execute("SELECT balance FROM users WHERE id = %s", (session['user_id'],))
                sender = cursor.fetchone()
                
                if sender['balance'] < amount:
                    flash('Insufficient balance!', 'danger')
                    return render_template('transfer.html', balance=balance)
                
                # Update sender balance
                cursor.execute(
                    "UPDATE users SET balance = balance - %s WHERE id = %s",
                    (amount, session['user_id'])
                )
                # Update receiver balance
                cursor.execute(
                    "UPDATE users SET balance = balance + %s WHERE id = %s",
                    (amount, receiver['id'])
                )
                # Record transaction for sender
                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, description) VALUES (%s, 'transfer', %s, %s)",
                    (session['user_id'], amount, f'Transferred ₹{amount:.2f} to {receiver_username}')
                )
                # Record transaction for receiver
                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, description) VALUES (%s, 'transfer', %s, %s)",
                    (receiver['id'], amount, f'Received ₹{amount:.2f} from {session["username"]}')
                )
                connection.commit()
                flash(f'Successfully transferred ₹{amount:.2f} to {receiver_username}!', 'success')
                return redirect(url_for('dashboard'))
            except Error as e:
                flash('Transfer failed! Please try again.', 'danger')
            finally:
                cursor.close()
                connection.close()
    
    return render_template('transfer.html', balance=balance)

# Transaction history page
@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT type, amount, description, created_at FROM transactions WHERE user_id = %s ORDER BY created_at DESC",
                (session['user_id'],)
            )
            transactions = cursor.fetchall()
            
            # Format date for display
            for txn in transactions:
                txn['date'] = txn['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return render_template('history.html', transactions=transactions)
        except Error as e:
            flash('Error loading transaction history!', 'danger')
        finally:
            cursor.close()
            connection.close()
    
    return redirect(url_for('dashboard'))

# About page
@app.route('/about')
def about():
    return render_template('about.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'info')
    return redirect(url_for('index'))

# Add this at the end of the file to run the application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)