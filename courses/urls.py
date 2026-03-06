from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('archiv/', views.course_archive, name='course_archive'),
    path('register/<int:course_id>/', views.register, name='course_register'),
    path('ical/<int:course_id>/', views.course_ical, name='course_ical'),
    path('confirmation/<uuid:token>/', views.course_confirmation, name='course_confirmation'),
    path('cancel/<uuid:token>/', views.course_cancel, name='course_cancel'),
    path('datenschutz/', views.privacy, name='privacy'),
    path('impressum/', views.impressum, name='impressum'),
]
