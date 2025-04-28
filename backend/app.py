from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_secret_key_here')

# Database configuration from environment variables
DB_HOST = os.environ.get('DATABASE_HOST', 'mydb-postgres-service')  # Use the service name
DB_PORT = int(os.environ.get('DATABASE_PORT', '5432'))
DB_NAME = os.environ.get('DATABASE_NAME', 'mydatabase')
DB_USER = os.environ.get('DATABASE_USER', 'myuser')
DB_PASSWORD = os.environ.get('DATABASE_PASSWORD')

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("Successfully connected to the database!") # Add this line
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        # Consider raising an exception here to fail fast in a containerized environment
        return None  # Explicitly return None for consistency
    return conn

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                if user:
                    user_id, stored_password = user
                    # In a real application, use a secure password hashing library (e.g., bcrypt, argon2)
                    if password == stored_password:  # Replace with secure password check!
                        session['user_id'] = user_id
                        session['username'] = username
                        return redirect(url_for('dashboard'))
                    else:
                        error = 'Invalid username or password'
                else:
                    error = 'Invalid username or password'
            except psycopg2.Error as e:
                print(f"Error querying the database: {e}")
                error = 'An error occurred during login'
                error = "Database error during login.  Please check the logs." # More user-friendly
            finally:
                cursor.close()
                conn.close()
        else:
            error = 'Could not connect to the database'
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        conn = get_db_connection()
        if conn:
          cursor = conn.cursor()
          try:
            now = datetime.now()
            cursor.execute("SELECT CURRENT_TIMESTAMP")
            db_time = cursor.fetchone()[0]
            return render_template('dashboard.html', username=session['username'], db_time=db_time, now=now)
          except psycopg2.Error as e:
            print(f"Error querying the database: {e}")
            return render_template('dashboard.html', username=session['username'], db_error="Failed to get server time.")
          finally:
            cursor.close()
            conn.close()
        else:
          return render_template('dashboard.html', username=session['username'], db_error="No database connection.")
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/health')
def health_check():
    """
    Endpoint for Kubernetes liveness and readiness probes.
    Returns 200 if the app is healthy, 500 otherwise.
    """
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({"status": "healthy"}), 200
    else:
        return jsonify({"status": "unhealthy"}), 500

if __name__ == '__main__':
    # This block is typically used for development only when running directly.
    # In a containerized environment, Gunicorn will be the entry point.
    app.run(debug=True, host='0.0.0.0', port=5000)
