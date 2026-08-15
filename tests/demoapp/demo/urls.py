"""URL configuration for the bitcaster-django demo project."""

from django.contrib import admin
from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("admin/", admin.site.urls),
    # user lifecycle: automatic Bitcaster register/unregister via signal handlers
    path("users/", views.users, name="users"),
    path("users/add/<str:username>/", views.user_add, name="user-add"),
    path("users/<str:username>/update/", views.user_update, name="user-update"),
    path("users/<str:username>/activate/", views.user_set_active, {"active": True}, name="user-activate"),
    path("users/<str:username>/deactivate/", views.user_set_active, {"active": False}, name="user-deactivate"),
    path("users/<str:username>/delete/", views.user_delete, name="user-delete"),
    path("users/<str:username>/groups/<str:group>/add/", views.user_group, {"add": True}, name="user-group-add"),
    path("users/<str:username>/groups/<str:group>/remove/", views.user_group, {"add": False}, name="user-group-remove"),
    # event triggering: Client facade and advanced client django namespace
    path("trigger/<str:event>/", views.trigger, name="trigger"),
    path("trigger/<str:event>/users/", views.trigger_users, name="trigger-users"),
    path("trigger/<str:event>/groups/", views.trigger_groups, name="trigger-groups"),
]
