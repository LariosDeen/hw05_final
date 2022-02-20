from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        labels = {
            'text': 'Текст поста'
        }


class CommentForm(ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': 'Текст комментария',
        }
        labels = {
            'text': 'Введите текст комментария',
        }
