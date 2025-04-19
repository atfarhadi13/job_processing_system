# Django Job Processing API

This project implements a REST API for managing asynchronous job processing with user authentication and email verification using OTP, built with Django, Django REST Framework, and Celery.

## Features

- **User Registration & Authentication:** Register users via email with OTP verification.
- **Job Management:** Create, schedule, cancel, and retrieve jobs.
- **Asynchronous Processing:** Jobs are processed asynchronously using Celery.
- **Results Reporting:** Retrieve job results after completion.

## API Endpoints

### Authentication
- `POST /api/register/` - Register new user (sends OTP)
- `POST /api/verify-email/` - Verify user's email with OTP
- `POST /api/login/` - User login to obtain authentication token

### Job Management
- `GET /api/jobs/` - List all user's jobs
- `POST /api/jobs/` - Create a new job
- `GET /api/jobs/<id>/` - Retrieve specific job details
- `DELETE /api/jobs/<id>/` - Cancel a job

### Job Results
- `GET /api/jobs/<id>/result/` - Retrieve result of completed job

## Setup Instructions

### Prerequisites
- Python 3.8+
- Redis

### Installation
```bash
git clone <repository-url>
cd job_processing_system

# Create virtual environment
python -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Database Setup
```bash
python manage.py migrate
```

### Running the Server
```bash
python manage.py runserver
```

### Running Celery

Make sure Redis is running, then:

```bash
celery -A job_processing_system worker --beat --scheduler django --loglevel=info
```

## Testing
Run tests with:

```bash
python manage.py test
```

## Technologies Used
- Django
- Django REST Framework
- Celery
- Redis
- Django Celery Beat (optional for scheduling)

## Author
Your Name Here

## License
[MIT License](LICENSE.md)

