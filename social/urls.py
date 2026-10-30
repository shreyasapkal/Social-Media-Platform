
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('explore/', views.explore_view, name='explore'),
    path('notifications/', views.notifications_view, name='notifications'),

    path('api/posts/create/', views.create_post, name='create_post'),
    path('api/posts/<int:post_id>/like/', views.like_post, name='like_post'),
    path('api/posts/<int:post_id>/comment/', views.comment_post, name='comment_post'),
    path('api/posts/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('api/comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('api/follow/<str:username>/', views.follow_user, name='follow_user'),
]
