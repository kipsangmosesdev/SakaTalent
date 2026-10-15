from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html' ),name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    path('profile/', views.my_profile, name='my_profile'),
    path('add-performance/', views.add_performance, name='add_performance'),
    path('my-performances/', views.my_performances, name='my_performances'),
    path('dashboard/', views.dashboard,name='dashboard'),
    path('rankings/<int:event_id>/', views.rankings, name='rankings'),
    path('talent/', views.talent_discovery, name='talent_discovery'),
    path('athlete/<int:athlete_id>/', views.athlete_detail, name='athlete_detail'),
]