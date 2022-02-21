from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Прикрепить картинку для этого поста',
        }
        labels = {
            'text': 'Текст поста',
            'group': 'Выберите группу (не обязательно)',
            'image': 'Загрузите фото (не обязательно)',
        }


class CommentForm(ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': 'Введите текст комментария',
        }
        labels = {
            'text': 'Текст комментария',
        }
