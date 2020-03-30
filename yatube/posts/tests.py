from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Post

User = get_user_model()

'''
Напишите тесты для проверки сценариев:

1)После регистрации пользователя создается его персональная страница (profile)
2)Авторизованный пользователь может опубликовать пост (new)
3)Неавторизованный посетитель не может опубликовать пост (его редиректит на страницу входа)
4)После публикации поста новая запись появляется на главной странице сайта (index),
    на персональной странице пользователя (profile), и на отдельной странице поста (post)
5)Авторизованный пользователь может отредактировать свой пост и его содержимое изменится на всех связанных страницах
'''

class PostsManagementTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test_username", email="test_mail@yandex.ru", password="test_password")
        self.post = Post.objects.create(text="It is a text of a test post", author=self.user)

        self.client = Client()
        self.client.force_login(self.user)

    def test_profile_page(self):
        response = self.client.get(reverse('profile', kwargs={'username': self.user.username}))
        self.assertNotEqual(response.status_code, 404, "<user's profile> page doesn't exist or mapped incorrectly")

    def test_new_post_page(self):
        new_post_url = reverse('new_post')

        #Authorised user
        response = self.client.get(new_post_url)
        self.assertEqual(response.status_code, 200, "Authorized user has no access to <new post> page")

        #Unauthorised user
        self.client.logout()

        response = self.client.get(new_post_url, follow=True)
        self.assertRedirects(
            response=response,
            expected_url=f"{reverse('login')}?next={new_post_url}",
            msg_prefix="<new post> page should redirect unauthorized user to <login> page"
        )
    
    def test_post_creation(self):
        text = 'This post was created using a form'
        self.client.post(reverse('new_post'), {'text' : text}, follow=True)
        new_post = Post.objects.last()
        self.assertEqual(new_post.text, text, "Post wasn't added to database")

        check_urls = {
            'index' : reverse('index'),
            'profile' : reverse('profile', kwargs={'username': self.user.username}),
            'post' : reverse('post', kwargs={'username': self.user.username, 'post_id' : new_post.id}),
        }

        for url in check_urls:
            response = self.client.get(check_urls[url])
            self.assertContains(response, new_post.text, msg_prefix=f"Created post doesn't appear in <{url}> page")
    
    def test_post_edition(self):
        post_edit_url = reverse('post_edit', kwargs={'username': self.user.username, 'post_id' : self.post.id})

        #Authorized user editing his own post:
        text = 'This post was edited using a form'
        self.client.post(post_edit_url, {'text' : text}, follow=True)
        edited_post = Post.objects.get(text=text)

        check_urls = {
            'index' : reverse('index'),
            'profile' : reverse('profile', kwargs={'username': self.user.username}),
            'post' : reverse('post', kwargs={'username': self.user.username, 'post_id' : edited_post.id}),
        }

        for url in check_urls:
            response = self.client.get(check_urls[url])
            self.assertContains(response, edited_post.text, msg_prefix=f"Edited post doesn't appear in <{url}> page")
        
        #Authorized user tries to edit another user's post:
        another_user = User.objects.create_user(username="another_username", email="another_mail@yandex.ru", password="another_password")
        another_post = Post.objects.create(text="Another text of a test post", author=another_user)

        another_post_url = reverse('post', kwargs={'username': another_user.username, 'post_id' : another_post.id})
        another_post_edit_url = reverse('post_edit', kwargs={'username': another_user.username, 'post_id' : another_post.id})

        response = self.client.get(another_post_edit_url)
        self.assertRedirects(
            response=response,
            expected_url=another_post_url,
            msg_prefix="Only author can edit his own post. Other users should be redirected to <post> page"
        )

        #Unauthorized user tries to edit someone's post:
        self.client.logout()

        response = self.client.get(post_edit_url)
        self.assertRedirects(
            response=response,
            expected_url=f"{reverse('login')}?next={post_edit_url}",
            msg_prefix="<post edition> page should redirect unauthorized user to <login> page"
        )
