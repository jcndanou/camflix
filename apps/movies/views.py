"""
Views for movies app.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Movie, Genre, MovieList, MovieListItem, Comment, CommentLike
from .forms import CommentForm, ReplyForm


class MovieListView(ListView):
    """List all movies with filtering and sorting."""

    model = Movie
    template_name = 'movies/list.html'
    context_object_name = 'movies'
    paginate_by = 24

    def get_queryset(self):
        queryset = super().get_queryset()

        # Search
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(title_fr__icontains=query) |
                Q(overview__icontains=query)
            )

        # Genre filter
        genre_id = self.request.GET.get('genre')
        if genre_id:
            queryset = queryset.filter(genres__id=genre_id)

        # Year filter
        year = self.request.GET.get('year')
        if year:
            queryset = queryset.filter(release_date__year=year)

        # Sorting
        sort = self.request.GET.get('sort', '-popularity')
        if sort in ['popularity', '-popularity', 'release_date', '-release_date',
                    'vote_average', '-vote_average', 'title', '-title']:
            queryset = queryset.order_by(sort)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['genres'] = Genre.objects.all()
        context['current_genre'] = self.request.GET.get('genre')
        context['current_sort'] = self.request.GET.get('sort', '-popularity')
        context['current_query'] = self.request.GET.get('q', '')
        return context


class MovieDetailView(DetailView):
    """Movie detail page."""

    model = Movie
    template_name = 'movies/detail.html'
    context_object_name = 'movie'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movie = self.object

        # Get user rating if authenticated
        if self.request.user.is_authenticated:
            try:
                context['user_rating'] = movie.ratings.get(user=self.request.user)
            except:
                context['user_rating'] = None

            # Check if in watchlist
            context['in_watchlist'] = MovieList.objects.filter(
                user=self.request.user,
                list_type='watchlist',
                movies=movie
            ).exists()

        # Get similar movies
        similar_movies = Movie.objects.filter(
            genres__in=movie.genres.all()
        ).exclude(id=movie.id).distinct()[:12]
        context['similar_movies'] = similar_movies

        # Get cast
        context['cast'] = movie.cast.select_related('actor')[:10]

        # Get comments
        comments = movie.comments.filter(parent=None, is_deleted=False).select_related('user').prefetch_related('replies')
        context['comments'] = comments
        context['comment_form'] = CommentForm()
        context['reply_form'] = ReplyForm()

        # Get user reactions for comments if authenticated
        if self.request.user.is_authenticated:
            user_reactions = {}
            for comment in comments:
                reaction = comment.get_user_reaction(self.request.user)
                if reaction:
                    user_reactions[comment.id] = reaction
                # Also check replies
                for reply in comment.replies.filter(is_deleted=False):
                    reaction = reply.get_user_reaction(self.request.user)
                    if reaction:
                        user_reactions[reply.id] = reaction
            context['user_reactions'] = user_reactions

        return context


def home_view(request):
    """Home page view."""
    context = {}

    # Get trending movies
    trending_movies = Movie.objects.order_by('-popularity')[:18]
    context['trending_movies'] = trending_movies

    return render(request, 'home.html', context)


def trending_view(request):
    """Trending movies page."""
    movies = Movie.objects.order_by('-popularity')[:48]

    context = {
        'movies': movies,
        'page_title': _('Films tendances'),
    }
    return render(request, 'movies/grid.html', context)


def top_rated_view(request):
    """Top rated movies page."""
    movies = Movie.objects.filter(
        vote_count__gte=100
    ).order_by('-vote_average')[:48]

    context = {
        'movies': movies,
        'page_title': _('Films les mieux notés'),
    }
    return render(request, 'movies/grid.html', context)


def genres_view(request):
    """Browse movies by genre."""
    genres = Genre.objects.annotate(
        movie_count=Count('movies')
    ).filter(movie_count__gt=0).order_by('name')

    context = {
        'genres': genres,
    }
    return render(request, 'movies/genres.html', context)


def search_view(request):
    """Search movies."""
    query = request.GET.get('q', '')
    movies = []

    if query:
        movies = Movie.objects.filter(
            Q(title__icontains=query) |
            Q(title_fr__icontains=query) |
            Q(original_title__icontains=query) |
            Q(overview__icontains=query) |
            Q(overview_fr__icontains=query)
        ).distinct()[:48]

    context = {
        'movies': movies,
        'query': query,
        'page_title': _('Résultats de recherche'),
    }
    return render(request, 'movies/grid.html', context)


@login_required
def watchlist_view(request):
    """User's watchlist."""
    watchlist, created = MovieList.objects.get_or_create(
        user=request.user,
        list_type='watchlist',
        defaults={'name': _("Ma liste à voir")}
    )

    movies = watchlist.movies.all()

    context = {
        'movies': movies,
        'page_title': _('Ma liste'),
        'watchlist': watchlist,
    }
    return render(request, 'movies/watchlist.html', context)


@login_required
def add_to_watchlist(request, movie_id):
    """Add movie to watchlist."""
    movie = get_object_or_404(Movie, id=movie_id)

    watchlist, created = MovieList.objects.get_or_create(
        user=request.user,
        list_type='watchlist',
        defaults={'name': _("Ma liste à voir")}
    )

    if not watchlist.movies.filter(id=movie.id).exists():
        MovieListItem.objects.create(
            movie_list=watchlist,
            movie=movie
        )
        messages.success(request, _('Film ajouté à votre liste'))
    else:
        messages.info(request, _('Ce film est déjà dans votre liste'))

    return redirect('movies:detail', pk=movie.id)


@login_required
def remove_from_watchlist(request, movie_id):
    """Remove movie from watchlist."""
    movie = get_object_or_404(Movie, id=movie_id)

    try:
        watchlist = MovieList.objects.get(
            user=request.user,
            list_type='watchlist'
        )
        MovieListItem.objects.filter(
            movie_list=watchlist,
            movie=movie
        ).delete()
        messages.success(request, _('Film retiré de votre liste'))
    except MovieList.DoesNotExist:
        pass

    return redirect('movies:detail', pk=movie.id)


# Comment views
@login_required
@require_POST
def add_comment(request, movie_id):
    """Add a comment to a movie."""
    movie = get_object_or_404(Movie, id=movie_id)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.movie = movie
        comment.user = request.user

        # Check if it's a reply
        parent_id = request.POST.get('parent_id')
        if parent_id:
            parent = get_object_or_404(Comment, id=parent_id)
            comment.parent = parent

        comment.save()
        messages.success(request, _('Your comment has been posted'))
    else:
        messages.error(request, _('Error posting comment'))

    return redirect('movies:detail', pk=movie.id)


@login_required
@require_POST
def edit_comment(request, comment_id):
    """Edit a comment."""
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)

    if request.POST.get('content'):
        comment.content = request.POST['content']
        comment.is_spoiler = request.POST.get('is_spoiler') == 'on'
        comment.is_edited = True
        comment.edited_at = timezone.now()
        comment.save()
        messages.success(request, _('Comment updated'))

    return redirect('movies:detail', pk=comment.movie.id)


@login_required
@require_POST
def delete_comment(request, comment_id):
    """Soft delete a comment."""
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    comment.is_deleted = True
    comment.deleted_at = timezone.now()
    comment.save()
    messages.success(request, _('Comment deleted'))

    return redirect('movies:detail', pk=comment.movie.id)


@login_required
@require_POST
def toggle_comment_like(request, comment_id):
    """Toggle like/dislike on a comment."""
    comment = get_object_or_404(Comment, id=comment_id)
    is_like = request.POST.get('is_like') == 'true'

    like, created = CommentLike.objects.get_or_create(
        comment=comment,
        user=request.user,
        defaults={'is_like': is_like}
    )

    if not created:
        if like.is_like == is_like:
            # Remove the reaction if clicking the same button
            like.delete()
            reaction = None
        else:
            # Switch the reaction
            like.is_like = is_like
            like.save()
            reaction = 'like' if is_like else 'dislike'
    else:
        reaction = 'like' if is_like else 'dislike'

    # Return JSON response for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'like_count': comment.like_count,
            'dislike_count': comment.dislike_count,
            'user_reaction': reaction,
        })

    return redirect('movies:detail', pk=comment.movie.id)
