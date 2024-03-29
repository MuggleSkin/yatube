from django.db import models
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from sorl.thumbnail import delete

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField(
        "date published", auto_now_add=True, db_index=True
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="posts",
    )
    image = models.ImageField(upload_to="posts/", blank=True, null=True)

    def __str__(self):
        return self.text


class Comment(models.Model):
    text = models.TextField()
    created = models.DateTimeField("date created", auto_now_add=True)
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="follower"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following"
    )

    class Meta:
        unique_together = ("user", "author")

    def __str__(self):
        return self.user.username


@receiver(models.signals.post_delete, sender=Post)
def auto_delete_image_on_delete(**kwargs):
    """
    Deletes image from filesystem
    when corresponding `Post` object is deleted.
    """
    instance = kwargs["instance"]
    if instance.image:
        delete(instance.image)


@receiver(models.signals.pre_save, sender=Post)
def auto_delete_image_on_change(**kwargs):
    """
    Deletes old image from filesystem
    when corresponding `Post` object is updated
    with new image.
    """
    instance = kwargs["instance"]
    try:
        old_image = Post.objects.get(pk=instance.pk).image
        new_image = instance.image
    except Post.DoesNotExist:
        return

    if old_image and (not old_image == new_image):
        delete(old_image)
