from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('register/<int:course_id>/', views.register, name='course_register'),
    path('datenschutz/', views.privacy, name='privacy'),
    path('impressum/', views.impressum, name='impressum'),
]
