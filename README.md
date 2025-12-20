# Job Application Tracking System (ATS) – Backend

## 📌 Overview
A robust backend system for managing job applications with real-world hiring workflows, role-based access control, and asynchronous processing.

## 🏗️ Architecture Overview

## 🔄 Application Workflow & State Machine

## 🔐 Role-Based Access Control (RBAC)

## 🗄️ Database Design (ERD)

## 📡 API Endpoints Overview

## ⚙️ Asynchronous Email Notifications

## 🧪 Testing the APIs

## 🚀 Setup & Installation

## 📹 Demo Video

## ✅ Key Features Summary


## 📌 Overview

This project is a backend Job Application Tracking System (ATS) designed to model real-world hiring workflows. 
It goes beyond basic CRUD operations by implementing a strict application state machine, role-based access control (RBAC), and asynchronous background processing for email notifications.

The system supports multiple user roles such as candidates and recruiters, enforces valid application stage transitions, and maintains a complete audit history of application changes. 
To ensure responsiveness and scalability, time-consuming operations like sending emails are handled asynchronously using a message queue and background worker.

## 🏗️ Architecture Overview

The system follows a layered backend architecture to ensure separation of concerns, scalability, and maintainability.

### Components

- **Django REST Framework (API Layer)**
  - Handles authentication, authorization, and HTTP request/response logic.
  - Exposes RESTful endpoints for jobs, applications, and users.

- **Service Layer**
  - Encapsulates business logic such as application state transitions.
  - Acts as the single source of truth for workflow rules.

- **PostgreSQL / SQLite (Database Layer)**
  - Stores users, companies, jobs, applications, and application history.
  - Enforces relational integrity using foreign keys.

- **Celery (Background Worker)**
  - Executes long-running or non-blocking tasks such as sending emails.
  - Ensures API responses remain fast and responsive.

- **Redis (Message Broker)**
  - Acts as a queue between Django and Celery.
  - Stores tasks until workers process them.

### Asynchronous Flow

1. An API request triggers an event (e.g., application submission).
2. Django enqueues an email task using Celery.
3. Redis stores the task.
4. A Celery worker consumes the task and processes it asynchronously.

This design mirrors real-world production systems used in large-scale applications.

## 🔄 Application Workflow & State Machine

Each job application follows a strict, predefined workflow:

Applied → Screening → Interview → Offer → Hired

An application can transition to **Rejected** from any non-terminal stage.

### Key Rules
- Invalid transitions (e.g., Applied → Offer) are blocked.
- Terminal states (Hired, Rejected) cannot transition further.
- Every valid transition is recorded in an audit log.

This ensures consistency, traceability, and reliability of the hiring process.
## ⚙️ Asynchronous Email Notifications

The system sends email notifications for key events:

### Candidate Notifications
- Upon successful application submission
- On every application stage change

### Recruiter Notifications
- When a new candidate applies to a job

Emails are dispatched asynchronously using Celery and Redis, ensuring:
- Fast API responses
- No blocking operations
- Improved scalability

Email tasks are processed independently by a background worker.
## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- Redis (or Memurai on Windows)
- Virtualenv

### Steps

```bash
git clone  https://github.com/Satyanagapraveen/ats-backend-23A91A12A5
cd ats-backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

python -m celery -A config worker -l info --pool=solo

SECRET_KEY=your-secret-key
DEBUG=True
REDIS_URL=redis://localhost:6379/0

```
 
## ✅ Key Features Summary

- JWT-based authentication
- Role-based access control (RBAC)
- Multi-tenant job management
- Application workflow state machine
- Complete audit trail for application changes
- Asynchronous email notifications
- Clean layered architecture
- Production-inspired backend design

