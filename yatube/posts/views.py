from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

# from django.http import HttpResponse

from .models import Post, Group, Comment, Follow
from .forms import PostForm, CommentForm

User = get_user_model()


def index(request):
    post_list = (
        Post.objects.select_related("author")
        .select_related("group")
        .order_by("-pub_date")
        .all()
    )
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request, "index.html", {"page": page, "paginator": paginator}
    )


def group_posts(request, slug):
    # функция get_object_or_404 позволяет получить объект из базы данных
    # по заданным критериям или вернуть сообщение об ошибке если объект не найден
    group = get_object_or_404(Group, slug=slug)

    post_list = (
        Post.objects.select_related("author")
        .select_related("group")
        .filter(group=group)
        .order_by("-pub_date")
        .all()
    )
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "group.html",
        {"group": group, "page": page, "paginator": paginator},
    )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_followers = author.following.all()
    followers_as_users = []
    for follower in author_followers:
        followers_as_users.append(follower.user)

    post_list = (
        Post.objects.select_related("author")
        .select_related("group")
        .filter(author=author)
        .order_by("-pub_date")
        .all()
    )
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "profile.html",
        {
            "author": author,
            "page": page,
            "paginator": paginator,
            "followers": followers_as_users,
        },
    )


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, author=author, id=post_id)
    comments = (
        Comment.objects.select_related("author")
        .select_related("post")
        .filter(post=post)
        .order_by("-created")
        .all()
    )

    author_followers = author.following.all()
    followers_as_users = []
    for follower in author_followers:
        followers_as_users.append(follower.user)

    form = CommentForm()
    return render(
        request,
        "post.html",
        {
            "author": author,
            "post": post,
            "followers": followers_as_users,
            "form": form,
            "comments": comments,
        },
    )


@login_required
def post_edit(request, username, post_id):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        return redirect("post", username=username, post_id=post_id)
    post = get_object_or_404(Post, author=author, id=post_id)

    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("post", username=username, post_id=post_id)

    return render(request, "new_post.html", {"form": form, "post": post})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)

    if request.method == "POST":
        if form.is_valid():
            unsaved_post = form.save(commit=False)
            unsaved_post.author = request.user
            unsaved_post.save()
            return redirect("index")

    return render(request, "new_post.html", {"form": form})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            unsaved_comment = form.save(commit=False)
            unsaved_comment.post = post
            unsaved_comment.author = request.user
            unsaved_comment.save()

    return redirect("post", username=username, post_id=post_id)


@login_required
def follow_index(request):
    following = request.user.follower.all()
    following_users = []
    for follow in following:
        following_users.append(follow.author)

    post_list = (
        Post.objects.select_related("author")
        .select_related("group")
        .filter(author__in=following_users)
        .order_by("-pub_date")
        .all()
    )
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(
        request, "follow.html", {"page": page, "paginator": paginator}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user == author:
        return redirect("profile", username=username)

    Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user == author:
        return redirect("profile", username=username)
    follow = get_object_or_404(Follow, user=request.user, author=author)
    follow.delete()
    return redirect("profile", username=username)


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)
