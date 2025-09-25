# CamFlix - Système de Fonctionnement et Déploiement

## Vue d'Ensemble du Système

CamFlix est une plateforme de recommandation de films inspirée de Criticker, développée avec Django 5.2.6. Le système utilise une architecture basée sur des microservices avec des tâches asynchrones pour gérer les données de films et les recommandations personnalisées.

### Caractéristiques Principales

- **Framework**: Django 5.2.6 avec Python 3.12+
- **Base de données**: PostgreSQL (production) / SQLite (développement)
- **Cache & File d'attente**: Redis avec Celery
- **API externe**: TMDB (The Movie Database)
- **Interface utilisateur**: HTMX + Django Templates
- **Authentification**: Django-Allauth avec modèle utilisateur personnalisé

## Architecture du Système

### Structure des Applications Django

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

### Flux de Données

1. **Synchronisation TMDB** : Celery récupère les données de films depuis l'API TMDB
2. **Évaluations Utilisateurs** : Les utilisateurs notent les films via l'interface web
3. **Calcul de Recommandations** : Celery calcule les similarités entre utilisateurs
4. **Cache Redis** : Les recommandations sont mises en cache pour des performances optimales

## Configuration des Environnements

### Variables d'Environnement (.env)

```bash
# Configuration générale
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
LANGUAGE_CODE=fr
TIME_ZONE=Europe/Paris

# Base de données
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/camflix_db

# Redis & Cache
CACHE_URL=redis://127.0.0.1:6380/1
CELERY_BROKER_URL=redis://localhost:6380/2
CELERY_RESULT_BACKEND=redis://localhost:6380/3

# TMDB API
TMDB_API_KEY=your-tmdb-api-key

# Email (production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@camflix.com

# Sentry (monitoring)
SENTRY_DSN=your-sentry-dsn

# CORS (pour API)
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.com

# Admin
ADMIN_EMAIL=admin@camflix.com
```

### Configuration des Services

#### PostgreSQL
```yaml
# docker-compose.yml
postgres:
  image: postgres:16-alpine
  environment:
    POSTGRES_DB: camflix_db
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
  ports:
    - "5432:5432"
```

#### Redis
```yaml
# docker-compose.yml
redis:
  image: redis:7-alpine
  ports:
    - "6380:6379"
```

## Tâches Celery Planifiées

### Synchronisation des Données
- **sync-trending-movies** : Synchronise les films tendances (quotidien, 2h00)
- **sync-popular-movies** : Synchronise les films populaires (quotidien, 3h00)
- **update-movie-details** : Met à jour les détails des films récents (toutes les 6h)

### Recommandations
- **calculate-user-similarities** : Calcule les similarités entre utilisateurs (toutes les 4h)
- **cleanup-recommendations-cache** : Nettoie le cache des recommandations (quotidien, 4h00)
- **send-recommendation-emails** : Envoie les recommandations hebdomadaires (lundi, 9h00)

## Système de Recommandations

### Algorithme de Similarité
Le système utilise un algorithme de filtrage collaboratif basé sur :
- Corrélation de Pearson entre les évaluations des utilisateurs
- Calcul de la similarité pondérée par le nombre d'évaluations communes
- Cache des résultats pour optimiser les performances

### Modèles de Données Principaux

#### Utilisateur (accounts.User)
```python
class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### Film (movies.Movie)
```python
class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    release_date = models.DateField()
    poster_path = models.CharField(max_length=255, blank=True)
    overview = models.TextField()
    genres = models.ManyToManyField(Genre)
```

#### Évaluation (ratings.Rating)
```python
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    created_at = models.DateTimeField(auto_now_add=True)
```

## API REST

### Endpoints Principaux
- `GET /api/movies/` : Liste des films avec pagination
- `GET /api/movies/{id}/` : Détails d'un film
- `POST /api/ratings/` : Créer une évaluation
- `GET /api/recommendations/` : Recommandations personnalisées
- `GET /api/users/profile/` : Profil utilisateur

### Authentification
- Session Django pour l'interface web
- Token-based pour les API externes (optionnel)

## Sécurité

### Mesures de Sécurité Implémentées
- **CSRF Protection** : Protection contre les attaques CSRF
- **XSS Protection** : Filtres de sécurité du navigateur
- **HTTPS Enforcement** : Redirection automatique HTTPS en production
- **Rate Limiting** : Limitation du taux de requêtes
- **Content Security Policy** : Headers de sécurité stricts
- **Database Connection Pooling** : Connexions sécurisées à la base de données

### Configuration de Production
```python
# core/settings/production.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

## Monitoring et Logging

### Logs Application
- **Django Logs** : `/var/log/camflix/django.log`
- **Celery Logs** : Console + fichiers de logs
- **Rotation** : Fichiers de 15MB, 10 sauvegardes

### Monitoring avec Sentry
- Intégration Django, Celery, et Redis
- Taux d'échantillonnage : 10%
- Environnement de production configuré

## Performance

### Optimisations Implémentées
- **Cache Redis** : Sessions, données d'application, résultats Celery
- **Database Connection Pooling** : Connexions réutilisées (60s max age)
- **Static Files Compression** : WhiteNoise avec compression
- **Query Optimization** : Select related, prefetch related
- **Template Caching** : Cache des templates fréquemment utilisés

### Métriques de Performance
- **Page Load Time** : < 2s pour les pages principales
- **API Response Time** : < 500ms pour les endpoints simples
- **Recommendation Calculation** : Traitement asynchrone via Celery

## Développement et Tests

### Commandes de Développement
```bash
# Démarrer l'environnement de développement
python manage.py runserver

# Lancer Redis
docker-compose up -d redis

# Worker Celery
celery -A core worker --loglevel=info

# Celery Beat (scheduler)
celery -A core beat --loglevel=info

# Tests
python manage.py test

# Migrations
python manage.py makemigrations
python manage.py migrate
```

### Structure des Tests
- Tests unitaires pour chaque application
- Tests d'intégration pour l'API
- Tests de performance pour les recommandations
- Coverage > 80% pour le code critique

## Internationalisation

### Langues Supportées
- Français (par défaut)
- Anglais

### Configuration i18n
```python
LANGUAGE_CODE = 'fr'
LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
]
USE_I18N = True
USE_L10N = True
```

## Évolutivité

### Architecture Préparée Pour
- **Microservices** : Applications Django modulaires
- **API Gateway** : Django REST Framework
- **Cache Distribué** : Redis Cluster
- **Base de Données** : PostgreSQL avec réplication
- **CDN** : Intégration prête pour les fichiers statiques

### Points d'Extension
- Nouvelles sources de données de films
- Algorithmes de recommandations avancés (ML)
- Intégration de réseaux sociaux
- API mobile native
- Streaming de contenu

Cette architecture modulaire et évolutive permet à CamFlix de croître tout en maintenant la performance et la fiabilité du système.