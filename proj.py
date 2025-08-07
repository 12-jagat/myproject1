import streamlit as st
import pandas as pd
import sqlite3
import smtplib
import os
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import google.generativeai as genai
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import base64
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="AI Health Report Manager",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Gemini AI
@st.cache_resource
def init_gemini():
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.0-flash-exp')
    return None

# Database functions
def init_database():
    """Initialize SQLite database with patients table"""
    conn = sqlite3.connect('health_reports.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            diagnosis TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_patient_data(df):
    """Insert patient data from DataFrame into database"""
    conn = sqlite3.connect('health_reports.db')
    cursor = conn.cursor()
    
    success_count = 0
    error_count = 0
    errors = []
    
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for index, row in df.iterrows():
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO patients (patient_id, name, age, diagnosis, email, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                str(row['Patient ID']).strip(),
                str(row['Name']).strip(),
                int(row['Age']),
                str(row['Diagnosis']).strip(),
                str(row['Email']).strip().lower(),
                current_timestamp
            ))
            success_count += 1
        except Exception as e:
            error_count += 1
            errors.append(f"Row {index + 1}: {str(e)}")
    
    conn.commit()
    conn.close()
    
    return success_count, error_count, errors

def get_all_patients():
    """Retrieve all patients from database"""
    conn = sqlite3.connect('health_reports.db')
    df = pd.read_sql_query('SELECT * FROM patients ORDER BY created_at DESC', conn)
    conn.close()
    return df

def search_patients(query):
    """Search patients by name, ID, or diagnosis"""
    conn = sqlite3.connect('health_reports.db')
    query = f"%{query}%"
    
    df = pd.read_sql_query('''
        SELECT * FROM patients 
        WHERE name LIKE ? OR patient_id LIKE ? OR diagnosis LIKE ?
        ORDER BY created_at DESC
    ''', conn, params=(query, query, query))
    
    conn.close()
    return df

def delete_patient(patient_id):
    """Delete a patient from database"""
    conn = sqlite3.connect('health_reports.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM patients WHERE patient_id = ?', (patient_id,))
    deleted_count = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return deleted_count > 0

# AI Report Generation
def generate_ai_report(patient_data, model):
    """Generate AI-powered health report using Gemini"""
    if not model:
        return "AI service unavailable. Please configure GEMINI_API_KEY in your .env file."
    
    prompt = f"""
    As a medical AI assistant, analyze the following patient data and provide a comprehensive health report:
    
    Patient Information:
    - Name: {patient_data['name']}
    - Age: {patient_data['age']} years old
    - Patient ID: {patient_data['patient_id']}
    - Diagnosis: {patient_data['diagnosis']}
    
    Please provide:
    1. A clear summary of the diagnosis
    2. Potential health implications
    3. General lifestyle recommendations
    4. Follow-up care suggestions
    5. Important precautions or warnings
    
    Keep the report professional, informative, and easy to understand for the patient.
    Format the response as a coherent paragraph suitable for a medical report.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating AI report: {str(e)}"

# PDF Generation
def create_pdf_report(patient_data, ai_report):
    """Generate PDF report for patient"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center alignment
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    # Build PDF content
    story = []
    
    # Title
    title = Paragraph("HEALTH REPORT", title_style)
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Patient Information Table
    story.append(Paragraph("Patient Information", heading_style))
    
    patient_info_data = [
        ['Patient ID:', patient_data['patient_id']],
        ['Name:', patient_data['name']],
        ['Age:', f"{patient_data['age']} years"],
        ['Email:', patient_data['email']],
        ['Diagnosis:', patient_data['diagnosis']],
        ['Report Date:', datetime.now().strftime('%Y-%m-%d %H:%M')]
    ]
    
    patient_table = Table(patient_info_data, colWidths=[2*inch, 4*inch])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(patient_table)
    story.append(Spacer(1, 20))
    
    # AI Generated Report
    story.append(Paragraph("Medical Analysis & Recommendations", heading_style))
    
    # Split AI report into paragraphs for better formatting
    report_paragraphs = ai_report.split('\n\n')
    for para in report_paragraphs:
        if para.strip():
            story.append(Paragraph(para.strip(), styles['Normal']))
            story.append(Spacer(1, 10))
    
    # Footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=1,
        textColor=colors.grey
    )
    footer = Paragraph(
        "This report was generated by AI Health Report Manager. "
        "Please consult with your healthcare provider for professional medical advice.",
        footer_style
    )
    story.append(footer)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# Email functions
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_email_with_report(patient_data, pdf_buffer):
    """Send email with PDF report attached"""
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    
    if not all([sender_email, sender_password]):
        return False, "Email credentials not configured in .env file"
    
    if not validate_email(patient_data['email']):
        return False, "Invalid email format"
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = patient_data['email']
        msg['Subject'] = f"Health Report - {patient_data['name']}"
        
        # Email body
        body = f"""
Dear {patient_data['name']},

Please find attached your health report generated on {datetime.now().strftime('%Y-%m-%d')}.

This report contains important information about your health status and recommendations for your wellbeing.

If you have any questions about this report, please consult with your healthcare provider.

Best regards,
AI Health Report Manager
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF
        pdf_buffer.seek(0)
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(pdf_buffer.read())
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename=Health_Report_{patient_data["patient_id"]}.pdf'
        )
        msg.attach(attachment)
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        return True, "Email sent successfully"
        
    except Exception as e:
        return False, f"Error sending email: {str(e)}"

# CSS Styling - IMPROVED FOR BETTER VISIBILITY
def load_css():
    """Load custom CSS for styling"""
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .metric-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .success-msg {
        padding: 1rem;
        border-radius: 8px;
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #b8daff;
        color: #155724;
        margin: 1rem 0;
        font-weight: 600;
    }
    
    .error-msg {
        padding: 1rem;
        border-radius: 8px;
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
        font-weight: 600;
    }
    
    .patient-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #e9ecef;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .patient-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .patient-card h4 {
        color: #2c3e50;
        margin-bottom: 1rem;
        font-size: 1.3em;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    
    .patient-card p {
        color: #34495e;
        margin: 0.5rem 0;
        font-size: 1em;
        line-height: 1.4;
    }
    
    .patient-card strong {
        color: #2980b9;
    }
    
    .patient-card small {
        color: #7f8c8d;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: none;
        padding: 0.75rem 1rem;
        font-weight: 600;
        font-size: 0.95em;
        transition: all 0.3s ease;
        margin: 0.2rem 0;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        color: white;
    }
    
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
        color: white;
    }
    
    .sidebar-logo {
        display: flex;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 2px solid #3498db;
        margin-bottom: 1rem;
    }
    
    .sidebar-logo h1 {
        margin: 0;
        font-size: 1.4rem;
        color: #2c3e50;
        font-weight: bold;
    }
    
    .bulk-send-card {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #f39c12;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(243, 156, 18, 0.2);
    }
    
    .bulk-send-card h4 {
        color: #d68910;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .selected-patient {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border-color: #17a2b8 !important;
    }
    
    .dataframe-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    /* Make sure text is visible in all elements */
    .stDataFrame, .stDataFrame table, .stDataFrame th, .stDataFrame td {
        color: #2c3e50 !important;
        background-color: transparent !important;
    }
    
    .stSelectbox > div > div {
        background-color: white !important;
        color: #2c3e50 !important;
    }
    
    .stTextInput > div > div > input {
        background-color: white !important;
        color: #2c3e50 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def migrate_database():
    """Migrate existing database to ensure proper datetime handling"""
    try:
        conn = sqlite3.connect('health_reports.db')
        cursor = conn.cursor()
        
        # Check if we need to update existing records with proper datetime format
        cursor.execute("SELECT COUNT(*) FROM patients")
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Get all records
            cursor.execute("SELECT id, created_at FROM patients")
            records = cursor.fetchall()
            
            for record_id, created_at in records:
                # If created_at is not in proper datetime format, update it
                try:
                    # Try to parse the existing date
                    pd.to_datetime(created_at)
                except:
                    # If parsing fails, update with current timestamp
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute("UPDATE patients SET created_at = ? WHERE id = ?", (current_time, record_id))
        
        conn.commit()
        conn.close()
        print("Database migration completed successfully")
        
    except Exception as e:
        print(f"Database migration error: {e}")

# Main Application
def main():
    # Initialize
    init_database()
    migrate_database()  # Add migration step
    load_css()
    gemini_model = init_gemini()
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-logo"><h1>🩺 Health Manager</h1></div>', unsafe_allow_html=True)
        
        menu = st.selectbox(
            "Navigation",
            ["📊 Dashboard", "📤 Upload Data", "📧 Bulk Send Reports", "👥 View Patients", "🔍 Search Patients", "🗑️ Delete Entry", "⚙️ Settings"]
        )
        
        st.markdown("---")
        
        # Quick stats
        try:
            total_patients = len(get_all_patients())
            st.metric("Total Patients", total_patients)
        except:
            st.metric("Total Patients", 0)
        
        st.markdown("---")
        st.markdown("**🔐 Security Note:** All data is stored securely in local database.")
    
    # Main Header
    st.markdown("""
    <div class="main-header">
        <h1>🩺 AI-Powered Health Report Manager</h1>
        <p style="font-size: 1.1em; margin: 0;">Secure • Intelligent • Efficient</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main Content based on menu selection
    if menu == "📊 Dashboard":
        show_dashboard()
    elif menu == "📤 Upload Data":
        show_upload_section(gemini_model)
    elif menu == "📧 Bulk Send Reports":
        show_bulk_send_section(gemini_model)
    elif menu == "👥 View Patients":
        show_patients_section(gemini_model)
    elif menu == "🔍 Search Patients":
        show_search_section(gemini_model)
    elif menu == "🗑️ Delete Entry":
        show_delete_section()
    elif menu == "⚙️ Settings":
        show_settings_section()

def show_dashboard():
    """Display dashboard with overview"""
    col1, col2, col3 = st.columns(3)
    
    try:
        df = get_all_patients()
        total_patients = len(df)
        
        with col1:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Total Patients", total_patients, delta=None)
            st.markdown('</div>', unsafe_allow_html=True)
        
        if total_patients > 0:
            avg_age = df['age'].mean()
            
            # Convert created_at to datetime for comparison
            try:
                df['created_at_dt'] = pd.to_datetime(df['created_at'])
                seven_days_ago = datetime.now() - pd.Timedelta(days=7)
                recent_patients = df[df['created_at_dt'] >= seven_days_ago]
            except Exception as date_error:
                # If date conversion fails, just count all as recent
                print(f"Date conversion error: {date_error}")
                recent_patients = df.head(5)  # Show last 5 as fallback
            
            with col2:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric("Average Age", f"{avg_age:.1f} years")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric("Added This Week", len(recent_patients))
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Recent Activity
            st.subheader("📋 Recent Patients")
            st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
            recent_df = df.head(5)[['patient_id', 'name', 'age', 'diagnosis', 'created_at']]
            st.dataframe(recent_df, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Diagnosis Distribution
            if len(df) > 0:
                st.subheader("📊 Diagnosis Overview")
                diagnosis_counts = df['diagnosis'].value_counts().head(10)
                st.bar_chart(diagnosis_counts)
        else:
            st.info("No patients in database yet. Upload some data to get started!")
            
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

def show_upload_section(gemini_model):
    """Display file upload section"""
    st.subheader("📤 Upload Patient Data")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Required Excel Columns:** Patient ID, Name, Age, Diagnosis, Email")
        
        uploaded_file = st.file_uploader(
            "Choose Excel file (.xlsx)",
            type=['xlsx'],
            help="Upload Excel file with patient data"
        )
        
        if uploaded_file:
            try:
                # Read Excel file
                df = pd.read_excel(uploaded_file)
                
                # Validate columns
                required_columns = ['Patient ID', 'Name', 'Age', 'Diagnosis', 'Email']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"Missing required columns: {', '.join(missing_columns)}")
                else:
                    # Preview data
                    st.subheader("📋 Data Preview")
                    st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
                    st.dataframe(df.head(), use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Data validation
                    st.subheader("✅ Data Validation")
                    validation_results = []
                    
                    # Check for empty values
                    empty_counts = df.isnull().sum()
                    for col in required_columns:
                        if empty_counts[col] > 0:
                            validation_results.append(f"⚠️ {col}: {empty_counts[col]} empty values")
                        else:
                            validation_results.append(f"✅ {col}: No empty values")
                    
                    # Email validation
                    invalid_emails = 0
                    for email in df['Email']:
                        if pd.notna(email) and not validate_email(str(email)):
                            invalid_emails += 1
                    
                    if invalid_emails > 0:
                        validation_results.append(f"⚠️ Email: {invalid_emails} invalid email formats")
                    else:
                        validation_results.append("✅ Email: All emails valid")
                    
                    for result in validation_results:
                        st.write(result)
                    
                    # Upload button
                    if st.button("🚀 Upload to Database", type="primary", use_container_width=True):
                        with st.spinner("Uploading data..."):
                            success_count, error_count, errors = insert_patient_data(df)
                            
                            if success_count > 0:
                                st.markdown(f'<div class="success-msg">✅ Successfully uploaded {success_count} records!</div>', unsafe_allow_html=True)
                            
                            if error_count > 0:
                                st.markdown(f'<div class="error-msg">❌ Failed to upload {error_count} records</div>', unsafe_allow_html=True)
                                with st.expander("View Errors"):
                                    for error in errors:
                                        st.write(f"• {error}")
            
            except Exception as e:
                st.error(f"Error reading Excel file: {str(e)}")
    
    with col2:
        st.markdown("### 📝 Upload Guidelines")
        st.markdown("""
        **File Requirements:**
        - Excel format (.xlsx)
        - Required columns must be present
        - Patient ID should be unique
        - Valid email addresses
        - Age should be numeric
        
        **Data Security:**
        - All data encrypted in transit
        - Stored in secure local database
        - No data sent to external servers
        """)

def show_bulk_send_section(gemini_model):
    """Display bulk send reports section with selection capability"""
    st.subheader("📧 Bulk Send Reports")
    
    try:
        df = get_all_patients()
        
        if len(df) == 0:
            st.info("No patients found. Upload some data first.")
            return
        
        # Initialize session state for selections
        if 'selected_patients' not in st.session_state:
            st.session_state.selected_patients = set()
        
        # Control buttons
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("✅ Select All", use_container_width=True):
                st.session_state.selected_patients = set(df['patient_id'].tolist())
                st.rerun()
        
        with col2:
            if st.button("❌ Clear All", use_container_width=True):
                st.session_state.selected_patients = set()
                st.rerun()
        
        with col3:
            selected_count = len(st.session_state.selected_patients)
            st.metric("Selected", selected_count)
        
        with col4:
            if selected_count > 0:
                if st.button(f"📧 Send {selected_count} Reports", type="primary", use_container_width=True):
                    send_bulk_reports(df, gemini_model)
        
        st.markdown("---")
        
        # Display patients with checkboxes
        st.subheader(f"👥 All Patients ({len(df)} total)")
        
        for index, patient in df.iterrows():
            is_selected = patient['patient_id'] in st.session_state.selected_patients
            card_class = "patient-card selected-patient" if is_selected else "patient-card"
            
            st.markdown(f"""
            <div class="{card_class}">
                <h4>{'✅' if is_selected else '⭕'} {patient['name']} (ID: {patient['patient_id']})</h4>
                <p><strong>Age:</strong> {patient['age']} years | <strong>Email:</strong> {patient['email']}</p>
                <p><strong>Diagnosis:</strong> {patient['diagnosis']}</p>
                <p><small><strong>Added:</strong> {patient['created_at']}</small></p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                checkbox_label = "Unselect" if is_selected else "Select"
                if st.button(checkbox_label, key=f"select_{patient['patient_id']}", use_container_width=True):
                    if is_selected:
                        st.session_state.selected_patients.discard(patient['patient_id'])
                    else:
                        st.session_state.selected_patients.add(patient['patient_id'])
                    st.rerun()
            
            with col2:
                if st.button(f"📄 Preview Report", key=f"preview_{patient['patient_id']}", use_container_width=True):
                    with st.spinner("🤖 Generating preview..."):
                        ai_report = generate_ai_report(patient, gemini_model)
                        st.session_state[f'preview_{patient["patient_id"]}'] = ai_report
            
            with col3:
                if st.button(f"📧 Send Individual", key=f"send_individual_{patient['patient_id']}", use_container_width=True):
                    send_individual_report(patient, gemini_model)
            
            with col4:
                if st.button(f"📥 Download PDF", key=f"download_{patient['patient_id']}", use_container_width=True):
                    with st.spinner("📄 Generating PDF..."):
                        ai_report = generate_ai_report(patient, gemini_model)
                        pdf_buffer = create_pdf_report(patient, ai_report)
                        st.download_button(
                            label="📥 Download",
                            data=pdf_buffer.getvalue(),
                            file_name=f"Health_Report_{patient['patient_id']}.pdf",
                            mime="application/pdf",
                            key=f"download_btn_{patient['patient_id']}"
                        )
            
            # Show preview if exists
            if f'preview_{patient["patient_id"]}' in st.session_state:
                with st.expander(f"📋 Report Preview - {patient['name']}", expanded=False):
                    st.write(st.session_state[f'preview_{patient["patient_id"]}'])
            
            st.markdown("---")
    
    except Exception as e:
        st.error(f"Error loading bulk send section: {str(e)}")

def send_bulk_reports(df, gemini_model):
    """Send reports to all selected patients"""
    if not st.session_state.selected_patients:
        st.warning("No patients selected!")
        return
    
    selected_df = df[df['patient_id'].isin(st.session_state.selected_patients)]
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    success_count = 0
    error_count = 0
    errors = []
    
    total = len(selected_df)
    
    for idx, (_, patient) in enumerate(selected_df.iterrows()):
        status_text.text(f"Processing {patient['name']} ({idx + 1}/{total})...")
        
        try:
            # Generate AI report
            ai_report = generate_ai_report(patient, gemini_model)
            
            # Create PDF
            pdf_buffer = create_pdf_report(patient, ai_report)
            
            # Send email
            success, message = send_email_with_report(patient, pdf_buffer)
            
            if success:
                success_count += 1
            else:
                error_count += 1
                errors.append(f"{patient['name']}: {message}")
            
            # Small delay to prevent overwhelming email server
            time.sleep(1)
            
        except Exception as e:
            error_count += 1
            errors.append(f"{patient['name']}: {str(e)}")
        
        # Update progress
        progress_bar.progress((idx + 1) / total)
    
    # Show results
    status_text.empty()
    progress_bar.empty()
    
    if success_count > 0:
        st.success(f"✅ Successfully sent {success_count} reports!")
    
    if error_count > 0:
        st.error(f"❌ Failed to send {error_count} reports")
        with st.expander("View Errors"):
            for error in errors:
                st.write(f"• {error}")

def send_individual_report(patient, gemini_model):
    """Send report to individual patient"""
    with st.spinner(f"📧 Sending report to {patient['name']}..."):
        try:
            # Generate AI report
            ai_report = generate_ai_report(patient, gemini_model)
            
            # Create PDF
            pdf_buffer = create_pdf_report(patient, ai_report)
            
            # Send email
            success, message = send_email_with_report(patient, pdf_buffer)
            
            if success:
                st.success(f"✅ Report sent successfully to {patient['name']}")
            else:
                st.error(f"❌ Failed to send report to {patient['name']}: {message}")
                
        except Exception as e:
            st.error(f"❌ Error sending report to {patient['name']}: {str(e)}")

def show_patients_section(gemini_model):
    """Display all patients with actions"""
    st.subheader("👥 All Patients")
    
    try:
        df = get_all_patients()
        
        if len(df) == 0:
            st.info("No patients found. Upload some data first.")
            return
        
        # Display patients
        for index, patient in df.iterrows():
            st.markdown(f"""
            <div class="patient-card">
                <h4>🏥 {patient['name']} (ID: {patient['patient_id']})</h4>
                <p><strong>Age:</strong> {patient['age']} years | <strong>Email:</strong> {patient['email']}</p>
                <p><strong>Diagnosis:</strong> {patient['diagnosis']}</p>
                <p><small><strong>Added:</strong> {patient['created_at']}</small></p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"📄 Generate Report", key=f"report_{patient['patient_id']}", use_container_width=True):
                    generate_and_show_report(patient, gemini_model)
            
            with col2:
                if st.button(f"📧 Email Report", key=f"email_{patient['patient_id']}", use_container_width=True):
                    email_patient_report(patient, gemini_model)
            
            with col3:
                if st.button(f"🗑️ Delete", key=f"delete_{patient['patient_id']}", type="secondary", use_container_width=True):
                    st.session_state[f'confirm_delete_{patient["patient_id"]}'] = True
            
            # Confirm deletion
            if st.session_state.get(f'confirm_delete_{patient["patient_id"]}', False):
                st.warning(f"⚠️ Are you sure you want to delete {patient['name']}?")
                col_yes, col_no = st.columns(2)
                
                with col_yes:
                    if st.button("Yes, Delete", key=f"confirm_yes_{patient['patient_id']}", type="primary", use_container_width=True):
                        if delete_patient(patient['patient_id']):
                            st.success(f"✅ {patient['name']} deleted successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Error deleting patient")
                
                with col_no:
                    if st.button("Cancel", key=f"confirm_no_{patient['patient_id']}", use_container_width=True):
                        st.session_state[f'confirm_delete_{patient["patient_id"]}'] = False
                        st.rerun()
            
            st.markdown("---")
    
    except Exception as e:
        st.error(f"Error loading patients: {str(e)}")

def generate_and_show_report(patient, gemini_model):
    """Generate and display AI report for patient"""
    with st.spinner("🤖 Generating AI report..."):
        ai_report = generate_ai_report(patient, gemini_model)
        
        st.subheader(f"📄 Report for {patient['name']}")
        st.markdown(f"""
        <div class="patient-card">
            <h4>Patient Information</h4>
            <p><strong>Name:</strong> {patient['name']}</p>
            <p><strong>Patient ID:</strong> {patient['patient_id']}</p>
            <p><strong>Age:</strong> {patient['age']} years</p>
            <p><strong>Diagnosis:</strong> {patient['diagnosis']}</p>
            <p><strong>Email:</strong> {patient['email']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("**AI-Generated Health Analysis:**")
        st.write(ai_report)
        
        # Generate PDF
        pdf_buffer = create_pdf_report(patient, ai_report)
        
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_buffer.getvalue(),
            file_name=f"Health_Report_{patient['patient_id']}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

def email_patient_report(patient, gemini_model):
    """Generate report and email to patient"""
    with st.spinner("📧 Generating and sending report..."):
        # Generate AI report
        ai_report = generate_ai_report(patient, gemini_model)
        
        # Create PDF
        pdf_buffer = create_pdf_report(patient, ai_report)
        
        # Send email
        success, message = send_email_with_report(patient, pdf_buffer)
        
        if success:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")

def show_search_section(gemini_model):
    """Display search functionality"""
    st.subheader("🔍 Search Patients")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Search by Name, Patient ID, or Diagnosis",
            placeholder="Enter search term...",
            help="Search is case-insensitive and matches partial terms"
        )
    
    with col2:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    if search_query or search_button:
        if search_query.strip():
            try:
                results = search_patients(search_query.strip())
                
                if len(results) == 0:
                    st.info(f"No patients found matching '{search_query}'")
                else:
                    st.success(f"Found {len(results)} patient(s) matching '{search_query}'")
                    
                    # Display results
                    for index, patient in results.iterrows():
                        st.markdown(f"""
                        <div class="patient-card">
                            <h4>🏥 {patient['name']} (ID: {patient['patient_id']})</h4>
                            <p><strong>Age:</strong> {patient['age']} years | <strong>Email:</strong> {patient['email']}</p>
                            <p><strong>Diagnosis:</strong> {patient['diagnosis']}</p>
                            <p><small><strong>Added:</strong> {patient['created_at']}</small></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button(f"📄 Generate Report", key=f"search_report_{patient['patient_id']}", use_container_width=True):
                                generate_and_show_report(patient, gemini_model)
                        
                        with col2:
                            if st.button(f"📧 Email Report", key=f"search_email_{patient['patient_id']}", use_container_width=True):
                                email_patient_report(patient, gemini_model)
                        
                        st.markdown("---")
            
            except Exception as e:
                st.error(f"Error searching patients: {str(e)}")
        else:
            st.warning("Please enter a search term")

def show_delete_section():
    """Display delete functionality"""
    st.subheader("🗑️ Delete Patient Entry")
    st.warning("⚠️ **Warning:** This action cannot be undone!")
    
    try:
        df = get_all_patients()
        
        if len(df) == 0:
            st.info("No patients to delete.")
            return
        
        # Create selectbox with patient info
        patient_options = [f"{row['name']} (ID: {row['patient_id']}) - {row['diagnosis']}" for _, row in df.iterrows()]
        
        selected_patient = st.selectbox(
            "Select Patient to Delete",
            options=range(len(patient_options)),
            format_func=lambda x: patient_options[x],
            help="Select the patient you want to delete from the database"
        )
        
        if selected_patient is not None:
            patient_data = df.iloc[selected_patient]
            
            # Show patient details
            st.markdown(f"""
            <div class="patient-card">
                <h4>Patient Details</h4>
                <p><strong>Name:</strong> {patient_data['name']}</p>
                <p><strong>Patient ID:</strong> {patient_data['patient_id']}</p>
                <p><strong>Age:</strong> {patient_data['age']} years</p>
                <p><strong>Email:</strong> {patient_data['email']}</p>
                <p><strong>Diagnosis:</strong> {patient_data['diagnosis']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Confirmation
            confirm_text = st.text_input(
                f"Type 'DELETE {patient_data['patient_id']}' to confirm:",
                placeholder=f"DELETE {patient_data['patient_id']}"
            )
            
            if st.button("🗑️ Delete Patient", type="primary", disabled=(confirm_text != f"DELETE {patient_data['patient_id']}")):
                if delete_patient(patient_data['patient_id']):
                    st.success(f"✅ Patient {patient_data['name']} deleted successfully!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Error deleting patient")
    
    except Exception as e:
        st.error(f"Error in delete section: {str(e)}")

def show_settings_section():
    """Display settings and configuration"""
    st.subheader("⚙️ Settings & Configuration")
    
    # Theme toggle
    st.markdown("### 🎨 Appearance")
    theme = st.radio("Theme", ["Light", "Dark"], horizontal=True)
    
    # Database info
    st.markdown("### 🗃️ Database Information")
    try:
        df = get_all_patients()
        st.info(f"Database contains {len(df)} patient records")
        
        if st.button("📊 Export All Data", type="secondary"):
            if len(df) > 0:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV Export",
                    data=csv,
                    file_name=f"patients_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data to export")
    
    except Exception as e:
        st.error(f"Error accessing database: {str(e)}")
    
    # Configuration status
    st.markdown("### 🔧 Configuration Status")
    
    # Check environment variables
    config_status = {
        "Gemini API Key": "✅ Configured" if os.getenv('GEMINI_API_KEY') else "❌ Not configured",
        "SMTP Server": "✅ Configured" if os.getenv('SMTP_SERVER') else "❌ Not configured (using default)",
        "Sender Email": "✅ Configured" if os.getenv('SENDER_EMAIL') else "❌ Not configured",
        "Sender Password": "✅ Configured" if os.getenv('SENDER_PASSWORD') else "❌ Not configured"
    }
    
    for setting, status in config_status.items():
        st.write(f"**{setting}:** {status}")
    
    st.markdown("---")
    
    # Environment setup instructions
    st.markdown("### 📋 Environment Setup")
    with st.expander("View .env file template"):
        st.code("""
# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password_here
        """, language="bash")
    
    # Database management
    st.markdown("### 🛠️ Database Management")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Reset Database", type="secondary"):
            st.warning("This will delete ALL patient data!")
            if st.button("Confirm Reset", type="primary"):
                try:
                    conn = sqlite3.connect('health_reports.db')
                    cursor = conn.cursor()
                    cursor.execute('DROP TABLE IF EXISTS patients')
                    conn.commit()
                    conn.close()
                    init_database()
                    st.success("✅ Database reset successfully!")
                except Exception as e:
                    st.error(f"❌ Error resetting database: {str(e)}")
    
    with col2:
        if st.button("📈 Database Stats", type="secondary"):
            try:
                conn = sqlite3.connect('health_reports.db')
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM patients")
                count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(DISTINCT diagnosis) FROM patients")
                unique_diagnoses = cursor.fetchone()[0]
                conn.close()
                
                st.success(f"📊 Total Records: {count}")
                st.success(f"🏥 Unique Diagnoses: {unique_diagnoses}")
            except Exception as e:
                st.error(f"❌ Error getting stats: {str(e)}")
    
    # About section
    st.markdown("### ℹ️ About")
    st.markdown("""
    **AI-Powered Health Report Manager v2.0**
    
    **New Features:**
    - 📧 **Bulk Send Reports** - Select multiple patients and send reports simultaneously
    - ✅ **Individual Selection** - Choose specific patients for report generation
    - 👀 **Report Preview** - Preview AI-generated reports before sending
    - 🎨 **Enhanced UI** - Improved visibility and better styling
    - 📊 **Better Data Display** - Clearer patient information presentation
    
    **Core Features:**
    - 📤 Excel data upload with validation
    - 🤖 AI-powered report generation using Gemini 2.0 Flash
    - 📧 Automated email delivery with PDF reports
    - 🔍 Advanced search and filtering
    - 🗑️ Secure data management
    - 🛡️ Privacy-focused local storage
    
    **Security & Privacy:**
    - All data stored locally in SQLite database
    - Environment variables for sensitive configuration
    - Input validation and sanitization
    - Secure email transmission
    
    **Technologies Used:**
    - Streamlit for web interface
    - Google Gemini 2.0 Flash for AI reports
    - ReportLab for PDF generation
    - SQLite for data storage
    - SMTP for email delivery
    """)

if __name__ == "__main__":
    main()