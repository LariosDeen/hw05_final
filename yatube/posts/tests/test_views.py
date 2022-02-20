import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse

from django import forms

from ..forms import PostForm
from ..models import Group, Post, User, Comment, Follow


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='MikeyMouse')
        cls.user_2 = User.objects.create_user(username='JohnKennedy')
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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post_1 = Post.objects.create(
            author=cls.user_1,
            text='Тестовый пост 1',
            pub_date='01.02.2022',
            group_id=cls.group_mouses.id,
            image=cls.uploaded,
        )
        cls.post_2 = Post.objects.create(
            author=cls.user_2,
            text='Тестовый пост 2',
            pub_date='02.02.2022',
            group_id=cls.group_presidents.id,
        )
        cls.form_data = {
            'text': 'Новый пост',
            'group': cls.group_mouses.id,
            'author': cls.post_1.author,
        }
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        cls.name_page_list = [
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': cls.group_mouses.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': cls.post_1.author}
            ),
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user_1)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        name_page_template = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts',
                    kwargs={'slug': self.group_mouses.slug}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.post_1.author}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post_1.id}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post_1.id}
                    ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in name_page_template.items():
            with self.subTest(template=template):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        """Шаблон index формируется со всеми постами из БД."""
        response = self.author_client.get(reverse('posts:index'))
        object_post_list = response.context['page_obj'].object_list
        self.assertTrue(self.post_1 in object_post_list)
        self.assertTrue(self.post_2 in object_post_list)

    def test_group_posts_correct_context(self):
        """Шаблон group_posts формируется с постами
        отфильтрованными по группе.
        """
        response = self.author_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': self.group_mouses.slug}
                    )
        )
        object_page_obj = response.context['page_obj']
        self.assertEqual(
            object_page_obj.object_list[0].group,
            self.group_mouses)
        self.assertEqual(len(object_page_obj.object_list), 1)

    def test_profile_correct_context(self):
        """Шаблон profile формируется с постами одного автора."""
        response = self.author_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.post_2.author}
                    )
        )
        object_page_obj = response.context['page_obj']
        self.assertEqual(
            object_page_obj.object_list[0].author,
            self.post_2.author)
        self.assertEqual(
            object_page_obj.object_list[0].text,
            self.post_2.text)
        self.assertEqual(
            object_page_obj.object_list[0].group,
            self.post_2.group)
        self.assertEqual(len(object_page_obj.object_list), 1)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail формируется с одним постом,
        отфильтрованным по id.
        """
        response = self.author_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post_1.id}
                    )
        )
        object_post_id = response.context['post_id']
        object_one_post = response.context['one_post']
        self.assertEqual(object_post_id, self.post_1.id)
        self.assertNotIsInstance(object_one_post, list)

    def test_paginator_correct_context(self):
        """Шаблоны index, group_posts и profile формируются с
        правильным контекстом для пажинатора.
        """
        Post.objects.bulk_create(
            [Post(author=self.user_1, text='T', group_id=1)] * 15
        )
        for name_page in self.name_page_list:
            with self.subTest(reverse_name=name_page):
                response = self.guest_client.get(name_page)
                posts_in_page = len(response.context['page_obj'].object_list)
                self.assertEqual(posts_in_page, 10)

    def test_post_create_correct_context(self):
        """Шаблон post_create формируется с полями
        формы для создания поста.
        """
        response = self.author_client.get(
            reverse('posts:post_create')
        )
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertIsNone(response.context['widget']['value'])
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIsNone(response.context.get('is_edit', None))

    def test_post_edit_correct_context(self):
        """Шаблон post_edit формируется с полями
        формы для редактирования поста.
        """
        response = self.author_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post_1.id}
                    )
        )
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertEqual(
            response.context['widget']['value'], self.post_1.text
        )
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertTrue(response.context['is_edit'])
        self.assertIsInstance(response.context['is_edit'], bool)

    def test_new_post_in_pages(self):
        """Проверка появления вновь созданного поста c указанием
        группы на страницах index, group_posts и profile.
        """
        self.author_client.post(
            reverse('posts:post_create'),
            data=self.form_data
        )
        for name_page in self.name_page_list:
            with self.subTest(name_page=name_page):
                response = self.author_client.get(name_page)
                self.assertEqual(
                    str(response.context['page_obj'].object_list[0]),
                    self.form_data['text'][:15]
                )

    def test_no_new_post_in_other_group(self):
        """Проверка отсутствия вновь созданного поста c указанием
        группы на странице group_posts другой группы.
        """
        self.author_client.post(
            reverse('posts:post_create'),
            data=self.form_data
        )
        response = self.guest_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': self.group_presidents.slug}
                    )
        )
        context_posts_list = response.context['page_obj'].object_list
        new_post = Post.objects.get(text=self.form_data['text'])
        self.assertFalse(new_post in context_posts_list)

    def test_image_in_context(self):
        """При выводе поста с картинкой изображение передаётся в словаре
        context на страницы index, group_posts, profile и post_detail.
        """
        for name_page in self.name_page_list:
            with self.subTest(name_page=name_page):
                response = self.author_client.get(name_page)
                self.assertTrue(response.context['page_obj'][-1].image)
                self.assertEqual(
                    response.context['page_obj'][-1].image,
                    self.post_1.image
                )
        response = self.author_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post_1.id}
            )
        )
        self.assertTrue(response.context['one_post'].image)
        self.assertEqual(
            response.context['one_post'].image, self.post_1.image
        )

    def test_comment_send_author_client(self):
        """Авторизованный пользователь может комментировать посты."""
        comments_before = Comment.objects.count()
        self.author_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post_2.id}
            ),
            data={'text': 'Comment for post 2'}
        )
        comments_after = Comment.objects.count()
        comment_text = Comment.objects.all()[0].text
        self.assertEqual(comments_before + 1, comments_after)
        self.assertEqual('Comment for post 2', comment_text)

    def test_comment_send_guest_client(self):
        """Неавторизованный пользователь не может комментировать посты."""
        comments_before = Comment.objects.count()
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post_2.id}
            ),
            data={'text': 'Comment for post 1'}
        )
        comments_after = Comment.objects.count()
        self.assertNotEqual(comments_before + 1, comments_after)

    def test_comment_in_page_detail(self):
        """Комментарий появляется на странице поста после успешной отправки."""
        self.author_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post_2.id}
            ),
            data={'text': 'Comment for post 2'}
        )
        response = self.author_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post_2.id}
            )
        )
        comment_text = response.context['comments'][0].text
        self.assertEqual('Comment for post 2', comment_text)

    def test_cache_home_page(self):
        """Проверка работы кеша главной страницы."""
        one_time_post = Post.objects.create(
            text='One time post text',
            author=self.user_1,
        )

        def response():
            return self.guest_client.get(reverse('posts:index'))

        resp_cont_init = response().content
        one_time_post.delete()
        resp_cont_post_del = response().content
        self.assertEqual(resp_cont_init, resp_cont_post_del)
        cache.clear()
        resp_cont_cache_clear = response().content
        self.assertNotEqual(resp_cont_post_del, resp_cont_cache_clear)

    def test_author_user_follow(self):
        """Авторизованный пользователь может подписаться
        на других пользователей.
        """
        follow_obj = Follow.objects.filter(
            user=self.user_1,
            author=self.user_2
        )
        self.assertFalse(follow_obj)
        self.author_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_2.username}
        ))
        follow_obj = Follow.objects.filter(
            user=self.user_1,
            author=self.user_2
        )
        self.assertTrue(follow_obj)

    def test_author_user_unfollow(self):
        """Авторизованный пользователь может отписаться
        от подписок на других пользователей.
        """
        follow_obj = Follow.objects.create(
            user=self.user_1,
            author=self.user_2
        )
        self.assertTrue(follow_obj)
        self.author_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user_2.username}
        ))
        follow_obj = Follow.objects.filter(
            user=self.user_1,
            author=self.user_2
        )
        self.assertFalse(follow_obj)

    def test_follower_has_post_unfollower_no_post(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан на него.
        """
        user_3 = User.objects.create_user(username='ElonMusk')
        Follow.objects.create(user=self.user_1, author=user_3)
        new_post = Post.objects.create(author=user_3, text='New post')
        response_1 = self.author_client.get(reverse('posts:follow_index'))
        self.author_client.get(reverse('users:logout'))
        user_2_auth = Client()
        user_2_auth.force_login(self.user_2)
        response_2 = user_2_auth.get(reverse('posts:follow_index'))
        new_post_follow_1 = response_1.context['page_obj'].object_list[0]
        self.assertEqual(new_post, new_post_follow_1)
        new_post_follow_2 = response_2.context['page_obj'].object_list
        self.assertFalse(new_post_follow_2)
