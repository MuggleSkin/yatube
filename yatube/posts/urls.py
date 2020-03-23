from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("group/<slug:slug>/", views.group_posts, name="group_page"),
    path("new/", views.new_post, name='new_post'),
    path("user/<username>/", views.profile, name="profile"),
    path("user/<username>/<int:post_id>/", views.post_view, name="post"),
    path("user/<username>/<int:post_id>/edit", views.post_edit, name="post_edit"),
]
