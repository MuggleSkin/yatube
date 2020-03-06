from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
#from django.http import HttpResponse

from .models import Post, Group

def index(request):
    latest = Post.objects.order_by('-pub_date')[:10]
    return render(request, "index.html", {"posts": latest})

@login_required
def group_posts(request, slug):
    # функция get_object_or_404 позволяет получить объект из базы данных
    # по заданным критериям или вернуть сообщение об ошибке если объект не найден
    group = get_object_or_404(Group, slug=slug)

    posts = Post.objects.filter(group=group).order_by("-pub_date")[:12]
    return render(request, "group.html", {"group": group, "posts": posts})
