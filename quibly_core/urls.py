from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('tweet/', views.post_tweet_view, name='post_tweet'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),
    path('like/<int:tweet_id>/', views.like_tweet_view, name='like_tweet'),
    path('comment/<int:tweet_id>/', views.comment_tweet_view, name='comment_tweet'),
    path('tweet/<int:tweet_id>/', views.view_tweet_view, name='view_tweet'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
path('verify-reset-otp/', views.verify_reset_otp_view, name='verify_reset_otp'),
path('reset-password/', views.reset_password_view, name='reset_password'),
path('user/<str:username>/follow-toggle/', views.follow_toggle_view, name='follow_toggle'),
path('user/<str:username>/', views.public_profile_view, name='public_profile'),
path('notifications/', views.notifications_view, name='notifications'),
path('tweet/<int:tweet_id>/delete/', views.delete_tweet_view, name='delete_tweet'),
path('search/', views.search_users_view, name='search_users'),

    path('user/<str:username>/connections/', views.connections_view, name='connections'),








]