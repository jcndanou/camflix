"""
Admin configuration for movies app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Movie, Genre, Person, MovieCast, MovieList, MovieListItem


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_fr', 'tmdb_id', 'movie_count']
    search_fields = ['name', 'name_fr']
    ordering = ['name']

    def movie_count(self, obj):
        return obj.movies.count()
    movie_count.short_description = 'Nombre de films'


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['name', 'person_type', 'birthday', 'popularity', 'tmdb_id']
    list_filter = ['person_type']
    search_fields = ['name']
    ordering = ['-popularity']
    readonly_fields = ['profile_image']

    def profile_image(self, obj):
        if obj.profile_url:
            return format_html('<img src="{}" width="100" />', obj.profile_url)
        return "Pas d'image"
    profile_image.short_description = 'Photo'


class MovieCastInline(admin.TabularInline):
    model = MovieCast
    extra = 1
    autocomplete_fields = ['actor']


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'release_year', 'vote_average', 'popularity', 'tmdb_id', 'poster_thumbnail']
    list_filter = ['status', 'adult', 'genres', 'release_date']
    search_fields = ['title', 'title_fr', 'original_title', 'tmdb_id', 'imdb_id']
    filter_horizontal = ['genres', 'directors']
    ordering = ['-popularity']
    date_hierarchy = 'release_date'
    readonly_fields = ['poster_image', 'backdrop_image', 'tmdb_id', 'imdb_id', 'created_at', 'updated_at']
    inlines = [MovieCastInline]

    fieldsets = (
        ('Informations principales', {
            'fields': ('tmdb_id', 'imdb_id', 'title', 'original_title', 'title_fr')
        }),
        ('Contenu', {
            'fields': ('overview', 'overview_fr', 'tagline')
        }),
        ('Détails', {
            'fields': ('release_date', 'runtime', 'status', 'adult', 'original_language')
        }),
        ('Médias', {
            'fields': ('poster_path', 'poster_image', 'backdrop_path', 'backdrop_image')
        }),
        ('Métriques', {
            'fields': ('popularity', 'vote_average', 'vote_count', 'budget', 'revenue')
        }),
        ('Relations', {
            'fields': ('genres', 'directors')
        }),
        ('Métadonnées', {
            'fields': ('last_tmdb_sync', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def release_year(self, obj):
        return obj.year
    release_year.short_description = 'Année'
    release_year.admin_order_field = 'release_date'

    def poster_thumbnail(self, obj):
        if obj.poster_url:
            return format_html('<img src="{}" width="50" />', obj.poster_url)
        return "-"
    poster_thumbnail.short_description = 'Affiche'

    def poster_image(self, obj):
        if obj.poster_url:
            return format_html('<img src="{}" width="200" />', obj.poster_url)
        return "Pas d'affiche"
    poster_image.short_description = 'Affiche'

    def backdrop_image(self, obj):
        if obj.backdrop_url:
            return format_html('<img src="{}" width="400" />', obj.backdrop_url)
        return "Pas d'image de fond"
    backdrop_image.short_description = 'Image de fond'


@admin.register(MovieList)
class MovieListAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'list_type', 'is_public', 'movie_count', 'created_at']
    list_filter = ['list_type', 'is_public', 'created_at']
    search_fields = ['name', 'user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def movie_count(self, obj):
        return obj.movie_count
    movie_count.short_description = 'Nombre de films'


@admin.register(MovieListItem)
class MovieListItemAdmin(admin.ModelAdmin):
    list_display = ['movie_list', 'movie', 'order', 'added_at']
    list_filter = ['added_at']
    search_fields = ['movie_list__name', 'movie__title']
    autocomplete_fields = ['movie_list', 'movie']
    ordering = ['movie_list', 'order']
