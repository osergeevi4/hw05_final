import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post, User


class ProfileTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='golum', password='123456'
        )
        self.post = Post.objects.create(
            text='Что-то тут не так',
            author=self.user,
            image='file.jpg'
        )
        self.group = Group.objects.create(title='testgroup', slug='testslug')
        self.client.force_login(self.user)

    def test_profile(self):
        response = self.client.get(reverse('profile', kwargs={'username': 'golum'}))
        self.assertEqual(response.status_code, 200)

    def test_user_have_post(self):
        login = self.client.login(username='golum', password='123456')
        response = self.client.post('/new/', text='111', group='222')
        self.assertEqual(response.status_code, 200)

    def test_page_post(self):
        response = self.client.get('')
        self.assertContains(response, self.post.text, status_code=200)
        response_pr = self.client.get(reverse('profile', kwargs={'username': 'golum'}))
        self.assertContains(response_pr, self.post.text, status_code=200)
        response_ps = self.client.get(reverse('post', args=[self.user.username, self.post.id]))
        self.assertContains(response_ps, self.post.text, status_code=200)

    def test_post_edit(self):
        resp = self.client.get(reverse('post_edit',
                               args=[self.user.username, self.post.id]))
        self.assertEqual(resp.status_code, 200)
        self.client.post(reverse('post_edit',
                         args=[self.user.username, self.post.id]),
                         {'text': 'новый текст'})
        response_index = self.client.get('')
        self.assertContains(response_index, 'новый текст')
        response_profile = self.client.get(reverse('profile',
                                           kwargs={'username': 'golum'}))
        self.assertContains(response_profile, 'новый текст')
        response_post = self.client.get(reverse('post',
                                        args=[self.user.username, self.post.id]))
        self.assertContains(response_post, 'новый текст')

    def test_404(self):
        response = self.client.get('/404/')
        self.assertEqual(response.status_code, 404)


class TestUnauthorized(TestCase):
    def setUp(self):
        self.unauthorized_client = Client()

    def test_redirect(self):
        response = self.client.get('/new/')
        self.assertRedirects(response, '/auth/login/?next=/new/', status_code=302, target_status_code=200)
        self.assertEqual(Post.objects.all().count(), 0)


class TestImage(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="123456")
        self.client.force_login(self.user)
        self.group = Group.objects.create(title='testgroup', slug='testgroup')
        self.post = Post.objects.create(
            text='Test text',
            author=self.user,
            group=self.group,
            image=SimpleUploadedFile(name='test.png',
                                     content=open('test.png', 'rb').read(),
                                     content_type='image/png')
        )

    def get_test_image_file():
        from PIL import Image
        img = Image.new('RGB', (60, 30), color=(73, 109, 137))
        img.save('test.png')

    get_test_image_file()

    def test_tag_post(self):
        with open('test.png', 'rb') as img:
            response_post = self.client.post(reverse('post', args=[self.user.username, self.post.id]),
                                       {'text': 'Test post with image', 'author': self.user, 'group': self.group,
                                        'image': img})
            self.assertEqual(response_post.status_code, 200)
        request_post = self.client.get(reverse('post', args=[self.user.username, self.post.id]))
        self.assertIn('img', request_post.content.decode())

    def test_tag_pages(self):
        with open('test.png', 'rb') as img:
            request_pr = self.client.post(reverse('profile', kwargs={'username': 'testuser'}),
                                          {'text': 'Text with img', 'image': img})
            self.assertEqual(request_pr.status_code, 200)
            response_pr = self.client.get(reverse('profile', args=[self.user.username]))
            self.assertIn('img', response_pr.content.decode())
            response_ind = self.client.get(reverse('index'))
            self.assertIn('img', response_ind.content.decode())
            response_grp = self.client.get(reverse('group', args=[self.group.slug]))
            self.assertIn('img', response_grp.content.decode())

    def test_not_upload(self):
        file = tempfile.NamedTemporaryFile(mode='w+t',
                                           suffix=".txt",
                                           delete=False)
        file.writelines(['Text\n'])
        file.seek(0)
        with file as img:
            request = self.client.post(reverse('post_edit', args=[self.user.username, self.post.id]),
                                       {'text': 'Test post with img', 'image': img}, follow=True)
            self.assertFormError(request, 'form', 'image', errors=('Загрузите правильное изображение. '
                                                                   'Файл, который вы загрузили, '
                                                                   'поврежден или не является изображением.'))


class FollowTest(TestCase):
    def setUp(self):
        self.auth_client = Client()
        self.user1 = User.objects.create_user(
            username='golum', password='123456'
        )
        self.auth_client.force_login(self.user1)
        self.unauth_client = Client()
        self.user2 = User.objects.create_user(
            username='golumni', password='123456'
        )
        self.post = Post.objects.create(text='Test post', author=self.user2)
        self.user3 = User.objects.create_user(
            username='golumnini', password='123456'
        )
        self.post3 = Post.objects.create(text='Test post3', author=self.user3)

    def test_auth_follow(self):
        response = self.auth_client.get(reverse('profile', args=[self.user2]))
        self.assertContains(response, text='Подписаться')
        self.follow = Follow.objects.create(user=self.user1, author=self.user2)
        response_unfollow = self.auth_client.get(reverse('profile', args=[self.user2]))
        self.assertContains(response_unfollow, text='Отписаться')

    def test_follow_index(self):
        self.follow = Follow.objects.create(user=self.user1, author=self.user2)
        resp_follow_index = self.auth_client.get(reverse('follow_index'))
        self.assertContains(resp_follow_index, 'Test post')
        self.assertNotContains(resp_follow_index, self.post3)

    def test_auth_unauth_comment(self):
        self.new_comment = 'It is new comment'
        response = self.auth_client.get(reverse('add_comment', args=[self.user2, self.post.id]))
        self.assertEqual(response.status_code, 200)
        response_comment = self.auth_client.post(reverse('add_comment',
                           kwargs={'username': self.user2.username, 'post_id': self.post.id}),
                           data={'text': self.new_comment, 'post_id':  self.post.id}, follow=True)
        self.assertContains(response_comment, self.new_comment)
        response = self.unauth_client.get(reverse('add_comment', args=[self.user3, self.post.id]))
        self.assertEqual(response.status_code, 200, msg='Авторизуйтесь для возможности комментирования')


class CacheTest(TestCase):
    def setUp(self):
        self.first_client = Client()
        self.second_client = Client()
        self.user = User.objects.create_user(username='golum', )
        self.first_client.force_login(self.user)

    def test_cache(self):
        self.second_client.get(reverse('index'))
        self.first_client.post(reverse('new_post'), {'text': 'Тест кэша'})
        response = self.second_client.get(reverse('index'))
        self.assertNotContains(response, 'Тест кэша')
