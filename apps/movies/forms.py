"""
Forms for the movies app.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Comment


class CommentForm(forms.ModelForm):
    """Form for creating and editing comments."""

    class Meta:
        model = Comment
        fields = ['content', 'is_spoiler']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full bg-gray-800/50 text-white px-4 py-3 rounded-lg border border-gray-700/50 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20 resize-none',
                'placeholder': _('Share your thoughts about this movie...'),
                'rows': 4,
                'maxlength': 2000,
            }),
        }
        labels = {
            'content': '',
            'is_spoiler': _('This comment contains spoilers'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_spoiler'].widget.attrs.update({
            'class': 'mr-2 text-purple-500 focus:ring-purple-500/20'
        })


class ReplyForm(forms.ModelForm):
    """Form for replying to comments."""

    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full bg-gray-800/30 text-white px-3 py-2 rounded-lg border border-gray-700/30 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20 resize-none text-sm',
                'placeholder': _('Write a reply...'),
                'rows': 2,
                'maxlength': 1000,
            }),
        }
        labels = {
            'content': '',
        }