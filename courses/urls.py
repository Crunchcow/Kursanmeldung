from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('register/<int:course_id>/', views.register, name='course_register'),
    path('ical/<int:course_id>/', views.course_ical, name='course_ical'),
    path('confirmation/<uuid:token>/', views.course_confirmation, name='course_confirmation'),
    path('cancel/<uuid:token>/', views.course_cancel, name='course_cancel'),
    path('datenschutz/', views.privacy, name='privacy'),
    path('impressum/', views.impressum, name='impressum'),
    path('auth/login/', views.oidc_login, name='oidc_login'),
    path('auth/callback/', views.oidc_callback, name='oidc_callback'),
    path('api/sync-user/', views.clubauth_sync_user, name='clubauth_sync_user'),
]
