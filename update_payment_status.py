import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment or use default"""
    return os.getenv('DATABASE_URL', 'sqlite:///instance/pos_system_v01.db')

def update_database():
    """Update database with payment status column and set initial values"""
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as connection:
            with connection.begin():
                print("Starting database update...")
                
                # 1. Check if payment_status already exists
                columns_result = connection.execute(
                    text("PRAGMA table_info(orders);")
                ).fetchall()
                column_names = [col[1] for col in columns_result]
                
                if 'payment_status' in column_names:
                    print("Payment status column already exists. No changes needed.")
                    return
                
                # 2. Add the column directly to the existing table
                print("Adding payment_status column...")
                connection.execute(text("""
                    ALTER TABLE orders 
                    ADD COLUMN payment_status TEXT 
                    DEFAULT 'pending' 
                    CHECK (payment_status IN ('pending', 'paid', 'refunded', 'failed', 'partially_refunded'));
                """))
                
                # 3. Update payment status for existing orders
                print("Updating payment statuses...")
                connection.execute(text("""
                    UPDATE orders 
                    SET payment_status = 'paid' 
                    WHERE status IN ('completed', 'paid_waiting_preparation', 'preparing', 'ready_for_pickup');
                """))
                
                print("Database update completed successfully!")
                
    except Exception as e:
        print(f"Error updating database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    update_database()