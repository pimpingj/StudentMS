# High School Student Management System (HSSMS)

A Flask web application for managing students, teachers, courses, exams, grades, and attendance.

---

## Tech Stack

- **Backend**: Python 3.12, Flask 3.1
- **Database**: MySQL (via SQLAlchemy + PyMySQL)
- **Frontend**: Bootstrap 5.3, Chart.js 4.4, Bootstrap Icons
- **ML**: scikit-learn (grade predictions)

---

## Running Locally

### Prerequisites

- Python 3.10 or newer
- MySQL server running locally
- Git (optional)

### 1. Clone or download the project

```bash
git clone <repo-url>
cd StudentMS
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the MySQL database

Log in to MySQL and run:

```sql
CREATE DATABASE sms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

If your local MySQL uses a password, set the `DATABASE_URL` environment variable (see step 5).

### 5. Set environment variables (optional for local dev)

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | Full DB connection string | `mysql+pymysql://root:@localhost:3306/sms_db` |
| `SECRET_KEY` | Flask session signing key | hardcoded fallback (change for production) |
| `FLASK_DEBUG` | Set to `1` to enable debug mode | `0` (off) |

**Windows (Command Prompt):**
```cmd
set DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/sms_db
set FLASK_DEBUG=1
```

**Mac / Linux:**
```bash
export DATABASE_URL="mysql+pymysql://root:yourpassword@localhost:3306/sms_db"
export FLASK_DEBUG=1
```

### 6. Create tables and seed test data

```bash
# Create all tables
python app/run.py

# Create the admin account
python create_admin.py

# Seed sample students, teachers, courses, grades, and attendance
python seed_data.py

# (Optional) Seed ML prediction records
python seed_predictions.py

# (Optional) Seed demo notifications for stu_001
python seed_notifications.py
```

### 7. Start the development server

```bash
python app/run.py
```

Open your browser at **http://127.0.0.1:5000**

### Default accounts

| Role    | Username   | Password |
|---------|------------|----------|
| Admin   | admin      | 123456   |
| Teacher | teacher_a  | 123456   |
| Teacher | teacher_b  | 123456   |
| Student | stu_001    | 123456   |
| Student | stu_002 … stu_006 | 123456 |

---

## Deploying to PythonAnywhere

### 1. Upload the project

In the PythonAnywhere **Files** tab, upload a ZIP of the project or clone via a Bash console:

```bash
git clone <repo-url> ~/StudentMS
```

### 2. Create a virtual environment

In a PythonAnywhere Bash console:

```bash
cd ~/StudentMS
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Create a MySQL database

In the PythonAnywhere **Databases** tab:
- Create a database named `sms_db` (it will be created as `<yourusername>$sms_db`)
- Note your database username, password, and host (shown on the Databases tab)

### 4. Set up the WSGI file

In the **Web** tab, create a new web app (Manual configuration, Python 3.12).

Replace the contents of the generated WSGI file with:

```python
import sys
import os

# Add project to path
sys.path.insert(0, '/home/<yourusername>/StudentMS')

# Set environment variables before importing the app
os.environ['SECRET_KEY'] = 'replace-with-a-long-random-secret-key'
os.environ['DATABASE_URL'] = (
    'mysql+pymysql://<yourusername>:<yourpassword>'
    '@<yourusername>.mysql.pythonanywhere-services.com'
    '/<yourusername>$sms_db'
)

from app.run import app as application
```

Replace every `<yourusername>` and `<yourpassword>` with your actual values.

### 5. Set the virtualenv path

In the **Web** tab under *Virtualenv*, enter:

```
/home/<yourusername>/StudentMS/.venv
```

### 6. Initialise the database

In a PythonAnywhere Bash console:

```bash
cd ~/StudentMS
source .venv/bin/activate
python app/run.py        # creates tables, then you can Ctrl+C
python create_admin.py
python seed_data.py
```

### 7. Reload the web app

Click **Reload** in the Web tab. Your app will be live at:

```
https://<yourusername>.pythonanywhere.com
```

---

## Project Structure

```
StudentMS/
├── app/
│   ├── __init__.py          # App factory, context processors
│   ├── models.py            # SQLAlchemy models
│   ├── notifications.py     # Notification helpers
│   ├── stats.py             # Grade/attendance statistics helpers
│   ├── run.py               # WSGI entry point + local dev runner
│   ├── ml/
│   │   └── predictor.py     # scikit-learn grade prediction
│   ├── routes/
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── student.py
│   │   └── teacher.py
│   └── templates/
│       ├── base.html
│       ├── admin/
│       ├── auth/
│       ├── student/
│       └── teacher/
├── config.py                # Configuration (reads from environment)
├── requirements.txt         # Pinned dependencies
├── create_admin.py          # One-time admin account creation
├── seed_data.py             # Sample data for development
├── seed_predictions.py      # Sample ML prediction data
└── seed_notifications.py    # Sample notifications for stu_001
```
