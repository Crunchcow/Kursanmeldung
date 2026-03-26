"""
URL configuration for kursanmeldung project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Damit Django-Admin auf der Login-Seite automatisch einen
    # "Passwort vergessen?"-Link anzeigt, leiten wir auf allauths
    # eigene (bereits gestaltete) Passwort-Reset-Seite weiter.
    path('admin/password_reset/', RedirectView.as_view(url='/accounts/password/reset/'), name='admin_password_reset'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('courses.urls')),
]
