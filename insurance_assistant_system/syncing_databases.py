import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import openai
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
import json
import time
from threading import Timer, Event, Thread, Lock
import os
from dotenv import load_dotenv

load_dotenv()

# Validate environment variables
required_vars = ["PG_DB_NAME", "PG_USER", "PG_PASSWORD", "PG_HOST", "PG_PORT", "OPENAI_API_KEY"]
for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")

conn_params = {
    "dbname": os.getenv("PG_DB_NAME"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
    "host": os.getenv("PG_HOST"),
    "port": os.getenv("PG_PORT"),
}

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

try:
    # Connect to PostgreSQL database
    conn = psycopg2.connect(**conn_params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Verify table exists
    cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'insurance_policies')")
    if not cur.fetchone()[0]:
        raise Exception("Table 'insurance_policies' does not exist")

    # Create trigger function
    cur.execute("""
        CREATE OR REPLACE FUNCTION notify_insurance_policy_change() RETURNS TRIGGER AS $$
        BEGIN
            PERFORM pg_notify('insurance_policy_change', row_to_json(NEW)::text);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger
    cur.execute("""
        CREATE OR REPLACE TRIGGER insurance_policy_change_trigger
        AFTER INSERT OR UPDATE ON insurance_policies
        FOR EACH ROW EXECUTE FUNCTION notify_insurance_policy_change();
    """)
    conn.commit()

    # Listen for notifications
    cur.execute("LISTEN insurance_policy_change;")

    # Connect to Milvus
    connections.connect("default", host="localhost", port="19530")
    collection = Collection("insurance_policy_embeddings")  # Should verify collection exists

    # Thread-safe notifications list
    notifications = []
    notifications_lock = Lock()
    stop_event = Event()

    def get_openai_embedding(text):
        try:
            response = openai.Embedding.create(
                input=text,
                model="text-embedding-3-large"
            )
            return response['data'][0]['embedding']
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return None

    def process_notifications():
        global notifications
        with notifications_lock:
            if notifications:
                current_batch = notifications.copy()
                notifications = []

        if current_batch:
            print(f"Processing {len(current_batch)} notifications")
            processed_ids = set()
            
            for notify in current_batch:
                try:
                    data = json.loads(notify.payload)
                    record_id = data['id']
                    
                    if record_id in processed_ids:
                        continue
                        
                    processed_ids.add(record_id)
                    
                    text = f"{data['customer_name']} {data['policy_type']} " \
                           f"{data.get('life_insurance_details','')} " \
                           f"{data.get('home_insurance_details','')} " \
                           f"{data.get('auto_insurance_details','')}"

                    embedding = get_openai_embedding(text)
                    if embedding:
                        collection.delete(f"id == {record_id}")
                        collection.insert([{"id": record_id, "embedding": embedding}])
                        collection.flush()
                        print(f"Updated embedding for record ID {record_id}")
                except Exception as e:
                    print(f"Error processing notification: {e}")

        if not stop_event.is_set():
            Timer(5, process_notifications).start()

    def listen_for_stop_command():
        while not stop_event.is_set():
            command = input()
            if command.lower() == "stop":
                stop_event.set()
                break

    # Start processing thread
    process_notifications()

    # Start stop command thread
    stop_thread = Thread(target=listen_for_stop_command)
    stop_thread.daemon = True
    stop_thread.start()

    print("Waiting for notifications on channel 'insurance_policy_change'...")

    while not stop_event.is_set():
        conn.poll()
        while conn.notifies:
            notify = conn.notifies.pop(0)
            with notifications_lock:
                notifications.append(notify)

except Exception as e:
    print(f"Error: {e}")
finally:
    stop_event.set()
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
    connections.disconnect("default")
    print("Program stopped")