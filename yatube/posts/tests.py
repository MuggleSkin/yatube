from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Post, Group


User = get_user_model()


@override_settings(CACHES=settings.TEST_CACHES)
class PostsManagementTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_username",
            email="test_mail@yandex.ru",
            password="test_password",
        )
        self.group = Group.objects.create(
            title="group title",
            slug="group-slug",
            description="group description",
        )
        self.post = Post.objects.create(
            text="It is a text of a test post",
            author=self.user,
            group=self.group,
        )

        self.client = Client()
        self.client.force_login(self.user)

    def test_profile_page(self):
        response = self.client.get(
            reverse("profile", kwargs={"username": self.user.username})
        )
        self.assertNotEqual(
            response.status_code,
            404,
            "<user's profile> page doesn't exist or mapped incorrectly",
        )

    def test_new_post_page(self):
        new_post_url = reverse("new_post")

        # Authorised user
        response = self.client.get(new_post_url)
        self.assertEqual(
            response.status_code,
            200,
            "Authorized user has no access to <new post> page",
        )

        # Unauthorised user
        self.client.logout()

        response = self.client.get(new_post_url)
        self.assertRedirects(
            response=response,
            expected_url=f"{reverse('login')}?next={new_post_url}",
            msg_prefix="<new post> page should redirect unauthorized user to <login> page",
        )

    def test_post_creation(self):
        text = "This post was created using a form"
        self.client.post(reverse("new_post"), {"text": text})
        new_post = Post.objects.last()
        self.assertEqual(new_post.text, text, "Post wasn't added to database")

        check_urls = {
            "index": reverse("index"),
            "profile": reverse(
                "profile", kwargs={"username": self.user.username}
            ),
            "post": reverse(
                "post",
                kwargs={
                    "username": self.user.username,
                    "post_id": new_post.id,
                },
            ),
        }

        for url in check_urls:
            response = self.client.get(check_urls[url])
            self.assertContains(
                response,
                new_post.text,
                msg_prefix=f"Created post doesn't appear in <{url}> page",
            )

    def test_post_edition(self):
        post_edit_url = reverse(
            "post_edit",
            kwargs={"username": self.user.username, "post_id": self.post.id},
        )

        # Authorized user editing his own post:
        text = "This post was edited using a form"
        self.client.post(post_edit_url, {"text": text})
        edited_post = Post.objects.get(text=text)

        check_urls = {
            "index": reverse("index"),
            "profile": reverse(
                "profile", kwargs={"username": self.user.username}
            ),
            "post": reverse(
                "post",
                kwargs={
                    "username": self.user.username,
                    "post_id": edited_post.id,
                },
            ),
        }

        for url in check_urls:
            response = self.client.get(check_urls[url])
            self.assertContains(
                response,
                edited_post.text,
                msg_prefix=f"Edited post doesn't appear in <{url}> page",
            )

        # Authorized user tries to edit another user's post:
        another_user = User.objects.create_user(
            username="another_username",
            email="another_mail@yandex.ru",
            password="another_password",
        )
        another_post = Post.objects.create(
            text="Another text of a test post", author=another_user
        )

        another_post_url = reverse(
            "post",
            kwargs={
                "username": another_user.username,
                "post_id": another_post.id,
            },
        )
        another_post_edit_url = reverse(
            "post_edit",
            kwargs={
                "username": another_user.username,
                "post_id": another_post.id,
            },
        )

        response = self.client.get(another_post_edit_url)
        self.assertRedirects(
            response=response,
            expected_url=another_post_url,
            msg_prefix="Only author can edit his own post. Other users should be redirected to <post> page",
        )

        # Unauthorized user tries to edit someone's post:
        self.client.logout()

        response = self.client.get(post_edit_url)
        self.assertRedirects(
            response=response,
            expected_url=f"{reverse('login')}?next={post_edit_url}",
            msg_prefix="<post edition> page should redirect unauthorized user to <login> page",
        )

    def test_comment(self):
        # Authorized user comments a post
        comment_url = reverse(
            "add_comment",
            kwargs={"username": self.user.username, "post_id": self.post.id},
        )
        text = "test comment"
        self.client.post(comment_url, {"text": text})

        post_url = reverse(
            "post",
            kwargs={"username": self.user.username, "post_id": self.post.id},
        )
        response = self.client.get(post_url)
        self.assertContains(
            response, text, msg_prefix="Comment doesn't appear in <post> page"
        )

        # Unauthorized user tries to comment a post
        self.client.logout()
        response = self.client.post(comment_url, {"text": text})
        self.assertRedirects(
            response=response,
            expected_url=f"{reverse('login')}?next={comment_url}",
            msg_prefix="Unauthorized user should be redirected to <login> page after attempt of commenting post",
        )

    def test_follow(self):
        second_user = User.objects.create_user(
            username="second_username",
            email="second_mail@yandex.ru",
            password="second_password",
        )
        second_post = Post.objects.create(
            text="The second text of a test post", author=second_user
        )

        follow_url = reverse(
            "profile_follow", kwargs={"username": second_user.username}
        )
        unfollow_url = reverse(
            "profile_unfollow", kwargs={"username": second_user.username}
        )
        follow_index_url = reverse("follow_index")

        # Authorized user follows another user
        self.client.get(follow_url)
        response = self.client.get(follow_index_url)
        self.assertContains(
            response,
            second_post.text,
            msg_prefix="Author's post should appear in his follower's <follow_index> page",
        )

        # Authorized user unfollows previously followed user
        self.client.get(unfollow_url)
        response = self.client.get(follow_index_url)
        self.assertNotContains(
            response,
            second_post.text,
            msg_prefix="Author's post should only appear in his follower's <follow_index> page",
        )


@override_settings(CACHES=settings.TEST_CACHES)
class TestImageUpload(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_username",
            email="test_mail@yandex.ru",
            password="test_password",
        )
        self.group = Group.objects.create(
            title="group title",
            slug="group-slug",
            description="group description",
        )
        self.post = Post.objects.create(
            text="It is a text of a test post",
            author=self.user,
            group=self.group,
        )

        self.client = Client()
        self.client.force_login(self.user)

    def test_image_upload(self):
        path = "test_data/test_img.jpg"
        post_edit_url = reverse(
            "post_edit",
            kwargs={"username": self.user.username, "post_id": self.post.id},
        )
        with open(path, "rb") as test_img:
            self.client.post(
                post_edit_url,
                {
                    "group": self.group.id,
                    "text": "new text",
                    "image": test_img,
                },
            )

        check_urls = {
            "index": reverse("index"),
            "group": reverse("group_page", kwargs={"slug": self.group.slug}),
            "profile": reverse(
                "profile", kwargs={"username": self.user.username}
            ),
            "post": reverse(
                "post",
                kwargs={
                    "username": self.user.username,
                    "post_id": self.post.id,
                },
            ),
        }
        for url in check_urls:
            response = self.client.get(check_urls[url])
            self.assertContains(
                response,
                "<img",
                msg_prefix=f"Image doesn't appear in <{url}> page",
            )

    def test_non_image_upload(self):
        post_edit_url = reverse(
            "post_edit",
            kwargs={"username": self.user.username, "post_id": self.post.id},
        )
        with open("manage.py", "rb") as test_file:
            self.client.post(
                post_edit_url, {"text": "new text", "image": test_file}
            )
        post = Post.objects.last()
        with self.assertRaises(
            ValueError,
            msg="Post should not contain non-graphic files in its <image> field",
        ):
            post.image.open()

    def tearDown(self):
        posts = Post.objects.all()
        for post in posts:
            post.delete()


class TestCachedPages(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_username",
            email="test_mail@yandex.ru",
            password="test_password",
        )
        self.group = Group.objects.create(
            title="group title",
            slug="group-slug",
            description="group description",
        )
        self.post = Post.objects.create(
            text="It is a text of a test post",
            author=self.user,
            group=self.group,
        )

        self.client = Client()
        self.client.force_login(self.user)

    def test_cached_page(self):
        index_url = reverse("index")
        post_edit_url = reverse(
            "post_edit",
            kwargs={"username": self.user.username, "post_id": self.post.id},
        )
        response = self.client.get(index_url)
        self.assertContains(
            response,
            self.post.text,
            msg_prefix="Initial post doesn't appear in <index> page",
        )

        text = "This post was edited using a form"
        self.client.post(post_edit_url, {"text": text})
        response = self.client.get(index_url)
        self.assertNotContains(
            response,
            text,
            msg_prefix="Cached <index> page shoudn't render new post instantly",
        )
