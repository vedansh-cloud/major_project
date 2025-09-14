import mysql.connector
from mysql.connector import Error
from config import Config

def recreate_database():
    try:
        # Connect to MySQL without specifying a database
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        
        cursor = connection.cursor()
        
        # Drop database if exists
        cursor.execute(f"DROP DATABASE IF EXISTS {Config.MYSQL_DB}")
        print(f"Dropped database {Config.MYSQL_DB}")
        
        # Create database
        cursor.execute(f"CREATE DATABASE {Config.MYSQL_DB}")
        print(f"Created database {Config.MYSQL_DB}")
        
        # Use the database
        cursor.execute(f"USE {Config.MYSQL_DB}")
        
        # Create users table
        cursor.execute("""
            CREATE TABLE users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                aadhar VARCHAR(12) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                balance DECIMAL(10, 2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Created users table")
        
        # Create transactions table with correct schema
        cursor.execute("""
            CREATE TABLE transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                type ENUM('deposit', 'withdraw', 'transfer') NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        print("Created transactions table")
        
        connection.commit()
        print("Database recreation completed successfully")
        
    except Error as e:
        print(f"Error recreating database: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    recreate_database()