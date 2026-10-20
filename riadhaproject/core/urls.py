from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('scout-agent/', views.scout_agent, name='scout_agent'),
    path('scout-agent/ask/', views.scout_agent_ask, name='scout_agent_ask'),
    path('signup/', views.signup, name='signup'),
    path('signup/google/', views.google_signup, name='google_signup'),
    path('signup/google/callback/', views.google_signup_callback, name='google_signup_callback'),
    path('login/', auth_views.LoginView.as_view(
        template_name='core/login.html',
        extra_context={
            'google_signup_enabled': bool(
                settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET
            ),
        },
    ), name='login'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='core/password_reset_form.html',
        email_template_name='core/password_reset_email.html',
        subject_template_name='core/password_reset_subject.txt',
        success_url='/password-reset/done/',
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='core/password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='core/password_reset_confirm.html',
        success_url='/reset/complete/',
    ), name='password_reset_confirm'),
    path('reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='core/password_reset_complete.html',
    ), name='password_reset_complete'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    path('profile/', views.my_profile, name='my_profile'),
    path('add-performance/', views.add_performance, name='add_performance'),
    path('my-performances/', views.my_performances, name='my_performances'),
    path('dashboard/', views.dashboard,name='dashboard'),
    path('training/', views.training_dashboard, name='training_dashboard'),
    path('rankings/<int:event_id>/', views.rankings, name='rankings'),
    path('talent/', views.talent_discovery, name='talent_discovery'),
    path('athlete/<int:athlete_id>/', views.athlete_detail, name='athlete_detail'),
]
