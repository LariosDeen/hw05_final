import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import Client, TestCase, override_settings

from ..models import Post, Group, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='MikeyMouse')
        cls.group_mouses = Group.objects.create(
            title='Тестовая группа mouses',
            slug='mouses',
            description='Описание тестовой группы mouses',
        )
        cls.group_presidents = Group.objects.create(
            title='Тестовая группа presidents',
            slug='presidents',
            description='Описание тестовой группы presidents',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст тестового поста',
            pub_date='01.02.2022',
            group_id=cls.group_mouses.id
        )
        cls.form_data = {
            'text': 'Текст изменённого поста',
            'group': cls.group_mouses.id,
            'author': cls.user
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_create_post_saved(self):
        """При отправке валидной формы со страницы create
        создаётся новая запись в базе данных.
        """
        posts_count = Post.objects.count()
        self.author_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True)
        last_post = Post.objects.first()
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(last_post.text, self.form_data['text'])
        self.assertEqual(last_post.group.id, self.form_data['group'])
        self.assertEqual(last_post.author, self.form_data['author'])

    def test_edit_post_changed(self):
        """При отправке валидной формы со страницы post_edit
        происходит изменение поста с отправленным id в базе данных.
        """
        self.author_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ),
            data=self.form_data,
            follow=True,
        )
        changed_post = Post.objects.get(id=self.post.id)
        response = self.guest_client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group_presidents.slug}
            )
        )
        another_group_posts = response.context['page_obj'].object_list
        self.assertEqual(changed_post.text, self.form_data['text'])
        self.assertEqual(changed_post.group.id, self.form_data['group'])
        self.assertEqual(changed_post.author, self.form_data['author'])
        self.assertNotIn(changed_post, another_group_posts)

    def test_guest_can_not_create_new_post(self):
        """При попытке создать новую запись неавторизованный клиент
        перенаправляется на страницу авторизации a запись не производится.
        """
        posts_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(posts_count, Post.objects.count())

    def test_create_post_with_image(self):
        """При отправке поста с картинкой через форму PostForm
        создаётся запись в базе данных.
        """
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Пост с фото',
            'group': self.group_mouses.id,
            'author': self.user,
            'image': uploaded,
        }
        posts_count = Post.objects.count()
        self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)
        post_with_image = Post.objects.get(text='Пост с фото')
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post_with_image.text, form_data['text'])
        self.assertEqual(post_with_image.group.id, form_data['group'])
        self.assertEqual(post_with_image.author, form_data['author'])
        self.assertEqual(post_with_image.image, 'posts/small.gif')
