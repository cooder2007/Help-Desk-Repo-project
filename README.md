Christ University Help Desk — Setup Guide
🚀 Quick Start (2 steps only)
⚙️ Step 0 — PostgreSQL Setup (One-time)
1. Install PostgreSQL

Download and install from:
👉 https://www.postgresql.org/download/

During installation:

Remember your username (default: postgres)
Set a password
Default port: 5432
2. Create Database

Open pgAdmin or terminal and run:

CREATE DATABASE helpdesk_db;
3. Update Backend Config

Inside your backend project, update your DB connection (usually in app.py or config.py):

DB_CONFIG = {
    "host": "localhost",
    "database": "helpdesk_db",
    "user": "postgres",
    "password": "your_password",
    "port": "5432"
}

If you're using a connection string:

DATABASE_URL = "postgresql://

postgres:your_password@localhost:5432/helpdesk_db"

4. Install PostgreSQL Driver

pip install psycopg2-binary

🧠 Step 1 — Run the Backend
### How to run the code in backend

Step 1: ctrl+~ (open terminal in VS Code)

Step 2: cd backend

Step 3: py -3.10 -m venv venv

Step 4: venv\Scripts\activate

Step 5: python --version

Step 6: pip install --upgrade pip setuptools wheel

Step 7: pip install -r requirements.txt

Step 8: python app.py

✅ You should see:

A warning (normal)

Database initialised (PostgreSQL connected)

Chatbot loaded X Q&A pairs

Server running at http://localhost:5000

🌐 Step 2 — Open the Frontend

Open frontend/index.html with VS Code Live Server
(Right-click → Open with Live Server)

👀 What You Will See

Landing Page

Stylus typing animation:

"Welcome To Our Site"

Deletes → "Got a Doubt? Ask Us."

Auth form slides in

Register

Choose role: Student / Teacher / Admin / HOD

Fill role-specific details

Login

Email + Password

Dashboard

Role-based sidebar with features

👥 Roles

Student

Post doubts (tokens)

Upvote visible tokens

Teacher

View and reply to visible tokens

Admin

View ALL tokens

Reply to ALL

Update status

HOD

View department + university tokens

Reply to department only

🎯 Token Levels

University → Everyone

Inter-Dept → Everyone

Intra-Dept → Same department only

Semester → Same dept + same semester

Class → Same class section only

🛠️ Troubleshooting

🔴 Backend Issues

PostgreSQL not connecting:

Check username/password

Ensure PostgreSQL service is running

Verify port 5432

psycopg2 error:

pip install psycopg2-binary

🔴 Frontend Issues

Page stuck/blank:

Use Live Server ❌ NOT double-click

CORS error:

Backend must run at http://localhost:5000

Chatbot unavailable:

Run backend first → python app.py

🔴 pip Issues

pip install flask flask-cors flask-jwt-extended bcrypt pandas 

scikit-learn numpy psycopg2-binary

💡 Pro Tip

If database tables are not auto-created:

Add a manual init script OR

Use ORM like SQLAlchemy (recommended for scaling 🚀)
