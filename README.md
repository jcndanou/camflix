# CamFlix - Movie Recommendation Platform

## Overview

CamFlix is a movie recommendation platform inspired by Criticker, built with Django 5.2.6. The system uses a microservices architecture with asynchronous tasks to handle movie data and personalized recommendations.

## Key Features

- **Personalized Recommendations**: Collaborative filtering algorithm based on user ratings
- **Movie Database**: Integration with The Movie Database (TMDB) API
- **Modern UI**: HTMX with Django templates for dynamic user experience
- **User Authentication**: Custom user model with Django-Allauth
- **Asynchronous Processing**: Celery with Redis for background tasks
- **REST API**: Complete API for external integrations
- **Multi-language Support**: French and English

## System Architecture

### Technology Stack

- **Backend**: Django 5.2.6 with Python 3.12+
- **Database**: PostgreSQL (production) / SQLite (development)
- **Cache & Queue**: Redis with Celery
- **External API**: TMDB (The Movie Database)
- **Frontend**: HTMX + Django Templates
- **Authentication**: Django-Allauth

### Project Structure
```
camflix/
├── core/                    # Configuration principale Django
│   ├── settings/           # Configuration par environnement
│   │   ├── base.py        # Configuration de base
│   │   ├── local.py       # Développement
│   │   └── production.py  # Production
│   ├── celery.py          # Configuration Celery
│   ├── urls.py            # URLs principales
│   ├── wsgi.py            # Interface WSGI
│   └── asgi.py            # Interface ASGI
├── apps/                   # Applications métier
│   ├── accounts/          # Gestion des utilisateurs
│   ├── movies/            # Gestion des films
│   ├── ratings/           # Système de notation
│   ├── recommendations/   # Moteur de recommandations
│   ├── api/              # API REST
│   └── common/           # Utilitaires partagés
├── templates/            # Templates Django
├── static/              # Fichiers statiques
├── media/               # Fichiers médias
└── logs/                # Journaux d'application
```
## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL
- Redis
- TMDB API key

### Installation

1. **Clone the repository**
   ```bash
    git clone <repository-url>
    cd camflix
   ```
2. **Create virtual environment**
   ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**
   ```bash
    pip install -r requirements.txt
   ```
4. **Install dependencies**
    Create a .env file:
   ```bash
    # Core settings
    DEBUG=True
    SECRET_KEY=your-secret-key-here
    ALLOWED_HOSTS=localhost,127.0.0.1
    
    # Database
    DATABASE_URL=postgresql://user:password@localhost:5432/camflix_db
    
    # Redis
    CACHE_URL=redis://127.0.0.1:6380/1
    CELERY_BROKER_URL=redis://localhost:6380/2
    
    # TMDB API
    TMDB_API_KEY=your-tmdb-api-key
   ```
5. **Database Setup**
    ```bash
    python manage.py migrate
    python manage.py createsuperuser
   ```
6. **Start Services**
    ```bash
    # Start Redis (using Docker)
    docker-compose up -d redis
    
    # Start Django development server
    python manage.py runserver
    
    # Start Celery worker (in separate terminal)
    celery -A core worker --loglevel=info
    
    # Start Celery beat scheduler (in separate terminal)
    celery -A core beat --loglevel=info
   ```

## API Endpoints

- `GET /api/movies/` - List movies with pagination
- `GET /api/movies/{id}/` - Movie details
- `POST /api/ratings/` - Create a rating
- `GET /api/recommendations/` - Personalized recommendations
- `GET /api/users/profile/` - User profile

## Scheduled Tasks

### Data Synchronization
- **sync-trending-movies**: Daily at 2:00 AM
- **sync-popular-movies**: Daily at 3:00 AM  
- **update-movie-details**: Every 6 hours

### Recommendations
- **calculate-user-similarities**: Every 4 hours
- **cleanup-recommendations-cache**: Daily at 4:00 AM
- **send-recommendation-emails**: Mondays at 9:00 AM

## Development

### Running Tests
1. **Run Tests**
   ```bash
   python manage.py test
   ```

### Database Migrations
1. **Run Tests**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

## Deployment

### Production Checklist

1. **Environment Configuration**
   - Set `DEBUG=False`
   - Configure production database
   - Set up SSL certificates
   - Configure email backend

2. **Static Files**
   ```bash
   python manage.py collectstatic
   ```

3. **WSGI Server**
   ```bash
   Recommended: Gunicorn or uWSGI
   ```

## Docker Support
   Example `docker-compose.yml` for development:
   ```yaml
   version: '3.8'
      
      services:
        postgres:
          image: postgres:16-alpine
          environment:
            POSTGRES_DB: camflix_db
            POSTGRES_USER: postgres
            POSTGRES_PASSWORD: postgres
          ports:
            - "5432:5432"
      
        redis:
          image: redis:7-alpine
          ports:
            - "6380:6379"
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Made by Ndanou jean-claude]

---

**CamFlix** - Discover your next favorite movie!