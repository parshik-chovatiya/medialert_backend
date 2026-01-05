# Medicine Reminder Backend API

Django REST API for Medicine Reminder Application with automated notifications.

## Project Structure

```
medicine_reminder_backend/
├── medicine_reminder/          # Main project folder
│   ├── __init__.py
│   ├── settings.py            # Django settings
│   ├── urls.py                # Main URL configuration
│   ├── celery.py              # Celery configuration
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── users/                 # User management
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── reminders/             # Reminder & DoseSchedule
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tasks.py           # Celery tasks
│   ├── inventory/             # Inventory management
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   └── notifications/         # Notification system
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       └── services.py        # Notification services
├── requirements.txt
├── .env
├── .env.example
├── manage.py
└── README.md
```

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 6+

## Setup Instructions

### 1. Clone and Create Virtual Environment

```bash
# Create project directory
mkdir medicine_reminder_backend
cd medicine_reminder_backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup (PostgreSQL)

```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE medicine_reminder_db;

# Create user (optional)
CREATE USER medicine_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE medicine_reminder_db TO medicine_user;

# Exit
\q
```

### 4. Environment Configuration

```bash
# Copy example env file
cp .env.example .env

# Edit .env file with your configurations
nano .env  # or use any text editor
```

### 5. Redis Setup

```bash
# Install Redis (Ubuntu/Debian)
sudo apt-get install redis-server

# Start Redis
redis-server

# Or on macOS with Homebrew
brew install redis
brew services start redis
```

### 6. Django Project Setup

```bash
# Create Django project
django-admin startproject medicine_reminder .

# Create apps
python manage.py startapp users
python manage.py startapp reminders
python manage.py startapp inventory
python manage.py startapp notifications

# Move apps to apps/ folder
mkdir apps
mv users reminders inventory notifications apps/
```

### 7. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 8. Create Superuser

```bash
python manage.py createsuperuser
```

### 9. Run Development Server

```bash
python manage.py runserver
```

Server will run at: `http://127.0.0.1:8000/`

### 10. Run Celery Worker (Separate Terminal)

```bash
# Activate virtual environment first
# On Windows:
celery -A medicine_reminder worker --pool=solo -l info

# On macOS/Linux:
celery -A medicine_reminder worker -l info
```

### 11. Run Celery Beat (Separate Terminal)

```bash
# Activate virtual environment first
celery -A medicine_reminder beat -l info
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/token/refresh/` - Refresh JWT token
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/me/` - Get current user

### Onboarding
- `POST /api/onboarding/` - Complete onboarding
- `GET /api/onboarding/status/` - Check onboarding status

### Reminders
- `GET /api/reminders/` - List all reminders
- `POST /api/reminders/` - Create reminder
- `GET /api/reminders/{id}/` - Get reminder details
- `PUT /api/reminders/{id}/` - Update reminder
- `PATCH /api/reminders/{id}/` - Partial update
- `DELETE /api/reminders/{id}/` - Delete reminder

### Inventory
- `GET /api/inventory/` - List inventory
- `GET /api/inventory/{id}/` - Get inventory details
- `POST /api/inventory/{id}/adjust/` - Manually adjust quantity

### Notifications
- `GET /api/notifications/logs/` - Get notification logs

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=apps
```

## Environment Variables Reference

See `.env.example` for all required environment variables.

## Firebase Setup for Push Notifications

1. Go to Firebase Console: https://console.firebase.google.com/
2. Create a new project
3. Go to Project Settings > Service Accounts
4. Generate new private key
5. Download JSON file
6. Set path in `.env`: `FIREBASE_CREDENTIALS_PATH=path/to/file.json`

## Twilio Setup for SMS

1. Sign up at: https://www.twilio.com/
2. Get Account SID and Auth Token
3. Get a Twilio phone number
4. Add credentials to `.env`

## Production Deployment

- Use `DEBUG=False`
- Set proper `ALLOWED_HOSTS`
- Use environment-specific database
- Use proper email backend
- Configure Redis for production
- Use process manager (Gunicorn + Nginx)

## License

Proprietary