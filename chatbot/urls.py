from django.urls import path
from django.contrib.auth import views as auth_views
from .views import login_user, register_user, home, logout_user, clear_history, main_page, user, grades_view, about

urlpatterns = [
    path('home/', home, name='home'),
    path('login/', login_user, name='login'),
    path('register/', register_user, name='register'),
    path('logout/', logout_user, name='logout'),
    path('', main_page, name='main'),
    path('clear-history/', clear_history, name='clear-history'),
    path('user/', user, name='user'),      
    path('grades/', grades_view, name='grades'),
    path('about/', about, name='about'),
    # path('profile/change-picture/', change_picture, name='change-picture'),
    # path('upload-picture/', upload_profile_picture, name='upload-profile-picture'),
    path(
      'password-change/',
      auth_views.PasswordChangeView.as_view(
         template_name='password_change.html',
         success_url='/password-change/done/'
      ),
      name='password_change'
    ),
    path('password-change/done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='password_change_done.html'
         ), 
         name='password_change_done'),
]
