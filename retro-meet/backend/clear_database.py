import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL not found in .env file.")
else:
    print(f"Connecting to database...")
    engine = create_engine(DATABASE_URL)

    # List of tables to clear, in order to respect foreign key constraints
    # (e.g., clear tables with foreign keys first)
    tables_to_clear = [
        "responses",
        "project_participants",
        "participants",
        "projects"
    ]

    try:
        with engine.connect() as connection:
            print("Connection successful.")
            # Begin a transaction
            with connection.begin() as transaction:
                try:
                    # Temporarily disable foreign key checks to avoid order issues (MySQL specific)
                    # For PostgreSQL, you might use: connection.execute(text("SET CONSTRAINTS ALL DEFERRED;"))
                    # For SQLite, foreign key checks are often off by default or handled differently.
                    # Assuming MySQL for now based on typical setups.
                    # If using PostgreSQL or SQLite, this part might need adjustment.
                    is_mysql = 'mysql' in engine.url.drivername
                    is_postgresql = 'postgresql' in engine.url.drivername

                    if is_mysql:
                        connection.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                        print("MySQL: Foreign key checks disabled.")
                    elif is_postgresql:
                        # For PostgreSQL, it's more common to handle this by deleting in the correct order
                        # or by using CASCADE, but to be safe for a generic script:
                        print("PostgreSQL: Deferring constraints or deleting in order is preferred. This script will attempt direct deletes.")

                    for table in tables_to_clear:
                        print(f"Clearing table: {table}...")
                        # Use DELETE FROM to clear all rows
                        connection.execute(text(f"DELETE FROM {table}"))
                        
                        # Optional: Reset auto-incrementing primary key
                        # MySQL syntax:
                        if is_mysql:
                            connection.execute(text(f"ALTER TABLE {table} AUTO_INCREMENT = 1"))
                            print(f"MySQL: Table {table} auto-increment reset.")
                        # PostgreSQL syntax (for sequences typically named table_id_seq):
                        elif is_postgresql:
                            try:
                                connection.execute(text(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1"))
                                print(f"PostgreSQL: Sequence for table {table} reset.")
                            except Exception as seq_e:
                                print(f"PostgreSQL: Could not reset sequence for {table} (may not exist or naming differs): {seq_e}")
                        # SQLite does not typically need this; AUTOINCREMENT handles it.
                        print(f"Table {table} cleared.")

                    if is_mysql:
                        connection.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                        print("MySQL: Foreign key checks re-enabled.")
                    
                    # Commit the transaction
                    transaction.commit()
                    print("\nDatabase has been successfully cleared!")

                except Exception as e:
                    print(f"An error occurred during transaction: {e}")
                    # Rollback the transaction in case of error
                    transaction.rollback()
                    print("Transaction rolled back.")

    except Exception as e:
        print(f"Failed to connect to the database: {e}")
