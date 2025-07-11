import psycopg2
import os
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

load_dotenv()

conn_params = {
    "dbname": os.getenv("PG_DB_NAME"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
    "host": os.getenv("PG_HOST"),
    "port": os.getenv("PG_PORT"),
}

def get_insurance_data_for_pdf():
    """Retrieve all data from the database for PDF export."""
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()

        cur.execute("SELECT * FROM customer_insurance")

        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    except Exception as error:
        print(f"Error retrieving data: {error}")
        return []
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def export_data_to_string_pdf(data, output_filename="insurance_data_strings.pdf"):
    """Exports each row of data as plain text strings to a PDF."""
    doc = SimpleDocTemplate(output_filename, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']

    if not data:
        p = Paragraph("No data to export.", normal_style)
        elements.append(p)
    else:
        for row_dict in data:
            row_string = ""
            for key, value in row_dict.items():
                row_string += f"{key}: {value}\n"
            p = Paragraph(row_string, normal_style)
            elements.append(p)
            elements.append(Spacer(1, 0.1*inch)) # Add a little space between rows

    doc.build(elements)
    print(f"Data exported as plain text strings to {output_filename}")

if __name__ == "__main__":
    insurance_data = get_insurance_data_for_pdf()
    export_data_to_string_pdf(insurance_data)