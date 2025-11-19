"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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

urlpatterns = [
    # expose API endpoints at project root so frontend can call e.g. /upload/,
    # /products/, /products/bulk-delete/, /upload/status/<job_id>/, etc.
    path("", include("api.urls")),
    # webhooks test endpoint (frontend calls `/webhooks/<id>/test/`)
    path("webhooks/", include("webhooks.urls")),
    path("admin/", admin.site.urls),
]
