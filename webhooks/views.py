from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class TestWebhookView(APIView):
    """
    Minimal endpoint to simulate/test a webhook target.
    Frontend calls: POST /webhooks/<id>/test/
    """

    def post(self, request, id: int):
        # In a real implementation, you'd retrieve the webhook config by id
        # and attempt a delivery. Here we just return a successful response.
        return Response(
            {"message": f"Webhook {id} test successful"}, status=status.HTTP_200_OK
        )

    def get(self, request, id: int):
        return Response(
            {"message": f"Webhook {id} test (GET)"}, status=status.HTTP_200_OK
        )
