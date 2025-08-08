
# 🏥 AI Health Report Manager

An intelligent healthcare management system that generates personalized health reports using AI technology, manages patient data, and automates report distribution via email.

## 🌟 Features

### Core Functionality
- **📊 Excel Data Upload** - Bulk patient data import with validation
- **🤖 AI-Powered Reports** - Intelligent health analysis using Google Gemini 2.0 Flash
- **📧 Bulk Email Distribution** - Automated PDF report sending with SMTP
- **🔍 Patient Search & Management** - Comprehensive patient database operations
- **📈 Dashboard Analytics** - Visual insights and patient statistics
- **🗑️ Secure Data Management** - GDPR-compliant data deletion capabilities

### Technical Features
- **SQLite Database** - Local patient data storage
- **PDF Generation** - Professional health reports using ReportLab
- **Responsive UI** - Enhanced CSS styling for medical professionals
- **Progress Tracking** - Real-time operation status updates
- **Bulk Operations** - Efficient mass report generation and sending
- **Security-First Design** - Environment variables for sensitive data

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (Python 3.13 not recommended due to compatibility issues)
- Gmail account with app password (for email functionality)
- Google Gemini API key

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/12-jagat/myproject1.git
cd myproject1
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
Create a `.env` file or configure secrets:
```env
GEMINI_API_KEY=your_gemini_api_key_here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_gmail_app_password
```

4. **Run the application:**
```bash
streamlit run proj.py
```

## 📋 Requirements

```txt
streamlit==1.28.0
pandas==2.0.3
numpy==1.24.4
google-generativeai==0.3.2
reportlab==4.0.4
python-dotenv==1.0.0
openpyxl==3.1.2
```

## 🏗️ Project Structure

```
myproject1/
├── proj.py                 # Main Streamlit application
├── requirements.txt        # Python dependencies
├── runtime.txt            # Python version specification
├── logo.png               # Application logo
├── .gitignore            # Git ignore rules
├── health_reports.db     # SQLite database (auto-generated)
└── .streamlit/
    └── secrets.toml      # Streamlit secrets (for deployment)
```

## 🔧 Configuration

### Environment Variables Setup

For secure deployment, configure these environment variables:

```env
GEMINI_API_KEY=your_actual_gemini_api_key
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_gmail_app_password
```

### Gmail App Password Setup
1. Enable 2-Step Verification on your Google Account
2. Go to [Google Account Security](https://myaccount.google.com/security)
3. Click "2-Step Verification" → "App passwords"
4. Generate an app password for "AI Health Report Manager"
5. Use the 16-character password (not your regular Gmail password)

## 📊 Usage

### 1. Upload Patient Data
- Use the **"Upload Excel File"** feature
- Ensure Excel file contains: Name, Age, Medical History, Current Symptoms
- System validates data format automatically

### 2. Generate AI Reports
- Select patients from the uploaded data
- Click **"Generate Reports"** to create AI-powered health analyses
- Reports are generated using Google Gemini AI with medical insights

### 3. Send Email Reports
- Use **"Send Bulk Emails"** to distribute reports
- PDF attachments are automatically generated
- Progress tracking shows email delivery status

### 4. Manage Patient Database
- Search patients by name or medical conditions
- View individual patient details
- Delete patient records when needed (GDPR compliance)

## 🚀 Deployment Options

### Recommended Platforms

1. **Railway.app** (Recommended ⭐)
   - Automatic Python 3.11 detection
   - Easy environment variable management
   - Free tier available
   - Best compatibility with Python packages

2. **Streamlit Community Cloud**
   - Direct GitHub integration
   - Add secrets in dashboard settings
   - May require `runtime.txt` with `python-3.11`

3. **Heroku**
   - Add `Procfile`: `web: streamlit run proj.py --server.port=$PORT --server.address=0.0.0.0`
   - Most reliable for production apps

### Deployment Configuration Files

**runtime.txt** (for Python version control):
```txt
python-3.11
```

**Procfile** (for Heroku):
```txt
web: streamlit run proj.py --server.port=$PORT --server.address=0.0.0.0
```

## ⚠️ Common Issues & Solutions

### Python 3.13 Compatibility Issues
**Problem**: `ModuleNotFoundError: No module named 'distutils'`
**Solution**: Use Python 3.11 by adding `runtime.txt` with `python-3.11`

### Email Authentication Errors
**Problem**: `(535, 'Username and Password not accepted')`
**Solution**: 
- Enable 2-Step Verification on Gmail
- Generate and use Gmail App Password (16 characters)
- Update environment variables with correct credentials

### Package Installation Failures
**Problem**: `Failed building wheel for pandas/numpy`
**Solution**: Use compatible package versions from requirements.txt

### Deployment Timeouts
**Problem**: Long deployment times on Streamlit Cloud
**Solution**: Switch to Railway.app or use minimal requirements.txt

## 🔐 Security Features

- **Environment Variables** - Sensitive data protection
- **Local Database Storage** - Patient data stays secure
- **GDPR Compliance** - Data deletion capabilities
- **Email Encryption** - Secure SMTP communication
- **Input Validation** - Prevents malicious data injection
- **App Password Usage** - Secure Gmail authentication

## 🎨 UI Features

- **Professional Medical Interface** - Healthcare-appropriate design
- **Responsive Layout** - Works on desktop and mobile devices
- **Progress Indicators** - Real-time operation feedback
- **Bulk Selection** - Efficient multi-patient operations
- **Custom CSS Styling** - Enhanced visibility and usability
- **Dashboard Analytics** - Visual patient statistics

## 📈 Performance Specifications

- **AI Report Generation** - 5-10 seconds per report
- **Bulk Operations** - Handles 100+ patients efficiently
- **Database Performance** - SQLite optimized for healthcare data
- **Memory Usage** - Optimized for cloud deployment limits
- **Email Throughput** - Bulk sending with progress tracking

## 🔧 Development

### Local Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create `.streamlit/secrets.toml` with your credentials
4. Run: `streamlit run proj.py`

### Contributing
1. Fork the repository
2. Create feature branch: `git checkout -b feature/AmazingFeature`
3. Commit changes: `git commit -m 'Add AmazingFeature'`
4. Push to branch: `git push origin feature/AmazingFeature`
5. Open Pull Request

## 📄 API Keys Required

### Google Gemini API
- **Get from**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Used for**: AI-powered health report generation
- **Quota**: Check your API limits

### Gmail App Password
- **Generate at**: Google Account → Security → App passwords
- **Used for**: Automated email report distribution
- **Security**: 16-character app-specific password

## 🏥 Medical Disclaimer

This application is designed for healthcare professionals and is for informational purposes only. It should not replace professional medical advice, diagnosis, or treatment. Always consult qualified healthcare providers for medical decisions.

## 📞 Support & Documentation

### Troubleshooting
- **Deployment Issues**: Check Python version compatibility
- **Email Problems**: Verify Gmail app password setup
- **AI Generation**: Confirm Gemini API key validity
- **Database Errors**: Ensure write permissions

### Resources
- **GitHub Issues**: [Report bugs or request features](https://github.com/12-jagat/myproject1/issues)
- **Deployment Guides**: Platform-specific documentation
- **API Documentation**: Google Gemini AI API docs

## 🎯 Live Demo

Once successfully deployed, your AI Health Report Manager will be accessible at:
- **Railway**: `https://your-app-name.up.railway.app`
- **Streamlit Cloud**: `https://myproject1-[username].streamlit.app`
- **Heroku**: `https://your-app-name.herokuapp.com`

## 🏆 Features Highlights

- ✅ **AI-Powered Health Analysis** using Google Gemini 2.0 Flash
- ✅ **Bulk Patient Data Processing** with Excel import
- ✅ **Automated PDF Report Generation** with professional formatting
- ✅ **SMTP Email Distribution** with progress tracking
- ✅ **Secure Patient Database** with search and management
- ✅ **GDPR-Compliant Data Handling** with deletion capabilities
- ✅ **Responsive Medical UI** optimized for healthcare professionals

***

**Built with ❤️ for healthcare professionals seeking efficient patient management and AI-powered health insights.**

**Version**: 2.0  
**Last Updated**: August 2025  
**Python Compatibility**: 3.11+  
**Deployment Status**: Production Ready  

