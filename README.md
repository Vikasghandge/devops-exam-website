# devops-exam-website
# DevOps Exam Portal

A full-stack web application for DevOps certification practice exams.
Built with Python Flask + MySQL, fully containerised with Docker and Docker Compose.

## Project Architecture

```
devops-exam-app/
├── app/
│   ├── app.py              ← Flask application
│   ├── requirements.txt    ← Python dependencies
│   ├── Dockerfile          ← Multi-stage Docker build
│   └── templates/
│       ├── login.html      ← Login page
│       ├── register.html   ← Registration page
│       ├── dashboard.html  ← User dashboard
│       ├── exam.html       ← Exam with countdown timer
│       └── result.html     ← Result + answer review
├── mysql/
│   └── init.sql            ← DB schema + 20 DevOps questions
├── docker-compose.yml      ← Two-container setup (app + db)
└── README.md
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11 + Flask 3.0 |
| Database | MySQL 8.0 |
| Frontend | HTML5 + CSS3 + Vanilla JS |
| Container | Docker (multi-stage build) |
| Orchestration | Docker Compose |

## Features

- User registration and login
- 20-minute countdown timer with auto-submit
- 15 random MCQ questions per attempt (from pool of 20+)
- Live progress tracker showing answered/unanswered
- Detailed result page with answer review and explanations
- Attempt history on dashboard
- All data persisted in MySQL container

## Quick Start

### Prerequisites
- Docker Desktop installed
- Docker Compose installed

### Run the project

```bash
# 1. Clone the repo
git clone https://github.com/Vikasghandge/devops-exam-app.git
cd devops-exam-app

# 2. Start all containers
docker-compose up --build

# 3. Open browser
http://localhost:5000
```

### Default test credentials
```
Email:    vikas@example.com
Password: vikas123
```

### Useful commands

```bash
# Start in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# View app logs only
docker-compose logs -f app

# Stop everything
docker-compose down

# Stop and delete data
docker-compose down -v

# Rebuild app only
docker-compose up -d --build app

# Connect to MySQL
docker exec -it exam-db mysql -u examuser -pexampass examdb
```

## Docker Details

### Multi-stage Dockerfile
- Stage 1 (builder): installs Python dependencies
- Stage 2 (production): lean image, only runtime files
- Result: ~60% smaller image than single-stage
- Non-root user for security

### Docker Compose services
- `db` — MySQL 8.0 with persistent volume
- `app` — Flask app, waits for DB healthcheck before starting
- Both on shared `exam-network` bridge

## Database Schema

```sql
users     — id, username, email, password, created_at
questions — id, question, options (JSON), correct_answer, explanation, category
results   — id, user_id, score, total, percentage, time_taken, taken_at
```

## Interview Talking Points

- "I built this as a portfolio project using Python Flask and MySQL"
- "Both services run in Docker containers via Docker Compose"
- "Multi-stage Dockerfile reduces image size by ~60%"
- "MySQL credentials are passed as environment variables — not hardcoded"
- "The DB container uses a healthcheck so the app only starts when MySQL is ready"
- "Data persists across restarts using a named Docker volume"
- "Questions are randomised on each attempt using MySQL ORDER BY RAND()"

## Author

Vikas Ghandge — DevOps Engineer
GitHub: github.com/Vikasghandge
