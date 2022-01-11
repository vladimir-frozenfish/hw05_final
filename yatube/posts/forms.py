from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):

    class Meta:
        """форма для добавления или редактирования поста
        выводит два соответствующих поля"""
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(ModelForm):

    class Meta:
        """форма для добавления комментария"""
        model = Comment
        fields = ('text',)
