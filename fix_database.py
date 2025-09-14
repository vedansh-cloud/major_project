from app import get_db_connection

def fix_database():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Check if description column exists
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'transactions' 
                AND column_name = 'description'
            """)
            result = cursor.fetchone()
            
            if result[0] == 0:
                # Add the missing description column
                cursor.execute("""
                    ALTER TABLE transactions 
                    ADD COLUMN description TEXT AFTER amount
                """)
                print("Added description column to transactions table")
            else:
                print("Description column already exists")
                
            connection.commit()
            print("Database fix completed successfully")
            
        except Exception as e:
            print(f"Error fixing database: {e}")
        finally:
            cursor.close()
            connection.close()
    else:
        print("Could not connect to database")

if __name__ == "__main__":
    fix_database()