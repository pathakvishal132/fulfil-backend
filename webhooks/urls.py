from django.urls import path
from . import views

urlpatterns = [
    # Test webhook endpoint used by frontend: /webhooks/<id>/test/
    path("<int:id>/test/", views.TestWebhookView.as_view(), name="webhook-test"),
]
