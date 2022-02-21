from django.test import TestCase

from ..models import Group, Post, User, Comment, Follow


class PostModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='auth_1')
        cls.user_2 = User.objects.create_user(username='auth_2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_1,
            text='Текст тестового поста',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user_2,
            text='Текст комментария для тестового поста',
        )
        cls.follow = Follow.objects.create(
            user=cls.user_2,
            author=cls.user_1
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей Post, Group, Comment и Follow
        корректно работает __str__.
        """
        post = PostModelTests.post
        expected_post_str = post.text[:15]
        self.assertEqual(expected_post_str, str(post))

        group = PostModelTests.group
        expected_group_str = group.title
        self.assertEqual(expected_group_str, str(group))

        comment = PostModelTests.comment
        expected_comment_str = post.text[:15]
        self.assertEqual(expected_comment_str, str(comment))

        follow = PostModelTests.follow
        expected_follow_str = f'{follow.user} --> {follow.author}'
        self.assertEqual(expected_follow_str, str(follow))

    def test_post_verbose_name(self):
        """verbose_name в полях модели Post совпадает с ожидаемым."""
        post = PostModelTests.post
        field_verbose = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_group_verbose_name(self):
        """verbose_name в полях модели Group совпадает с ожидаемым."""
        group = PostModelTests.group
        field_verbose = {
            'title': 'Название',
            'slug': 'SLUG',
            'description': 'Описание',
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)

    def test_comment_verbose_name(self):
        """verbose_name в полях модели Comment совпадает с ожидаемым."""
        comment = PostModelTests.comment
        field_verbose = {
            'post': 'Запись',
            'author': 'Автор',
            'text': 'Текст комментария',
            'created': 'Дата публикации',
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_follow_verbose_name(self):
        """verbose_name в полях модели Follow совпадает с ожидаемым."""
        follow = PostModelTests.follow
        field_verbose = {
            'user': 'Подписчик',
            'author': 'Автор записей',
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    follow._meta.get_field(field).verbose_name, expected_value)

    def test_post_help_text(self):
        """help_text в полях модели Post совпадает с ожидаемым."""
        post = PostModelTests.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу (не обязательно)',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
