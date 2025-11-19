# product/views.py
import uuid
import json
import os
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.conf import settings
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from celery.result import AsyncResult

from backend.celery import app
from .models import Product
from .serializers import ProductSerializer
from .tasks import process_csv_task


# ----------------- CSV Upload (Async) -----------------
class ProductUploadView(APIView):
    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "CSV file required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Save CSV temporarily
        file_path = default_storage.save(f"uploads/{file.name}", file)

        # Generate job ID
        job_id = str(uuid.uuid4())

        # Trigger Celery task asynchronously
        process_csv_task.apply_async(args=[file_path, job_id], task_id=job_id)

        return Response(
            {"message": "Upload started", "job_id": job_id},
            status=status.HTTP_202_ACCEPTED,
        )


# ----------------- Task Status -----------------
class ProductUploadStatusView(APIView):
    """Return Celery task progress/result for a given job_id."""

    def get(self, request, job_id):
        task_result = AsyncResult(job_id, app=app)

        state = task_result.state

        def _safe_serialize(obj):
            # Try to JSON-serialize the object; fall back to str(obj)
            try:
                return json.loads(json.dumps(obj, default=str))
            except Exception:
                return str(obj)

        if state == "PENDING":
            return Response({"status": "PENDING"}, status=status.HTTP_202_ACCEPTED)
        elif state == "PROGRESS":
            # task_result.info expected to contain {'current': x, 'total': y}
            return Response(
                {"status": "PROGRESS", "meta": _safe_serialize(task_result.info)}
            )
        elif state == "SUCCESS":
            return Response(
                {"status": "SUCCESS", "result": _safe_serialize(task_result.result)}
            )
        else:
            # For FAILURE or other states, return state and any info available
            info = None
            try:
                info = _safe_serialize(task_result.info)
            except Exception:
                info = None
            return Response({"status": state, "info": info})


# ----------------- Pagination -----------------
class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "pageSize"  # frontend uses pageSize
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({"rows": data, "total": self.page.paginator.count})


# ----------------- CRUD Endpoints -----------------
class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    pagination_class = ProductPagination

    def get_queryset(self):
        qs = Product.objects.all().order_by("id")
        sku = self.request.query_params.get("sku")
        name = self.request.query_params.get("name")
        active = self.request.query_params.get("active")

        if sku:
            qs = qs.filter(sku__icontains=sku)
        if name:
            qs = qs.filter(name__icontains=name)
        if active is not None and active != "":
            # Accept 'true'/'false' strings
            if str(active).lower() in ["true", "1", "yes"]:
                qs = qs.filter(active=True)
            else:
                qs = qs.filter(active=False)
        return qs

    def create(self, request, *args, **kwargs):
        """Create a single product. If a product with the same SKU exists,
        return a clear message and the existing product instead of failing.
        """
        sku = request.data.get("sku")
        if sku:
            # case-insensitive match to be forgiving about input
            existing = Product.objects.filter(sku__iexact=sku).first()
            if existing is not None:
                serializer = self.get_serializer(existing)
                return Response(
                    {
                        "message": "Product with this SKU already exists",
                        "product": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )

        return super().create(request, *args, **kwargs)


class ProductRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = "id"


# ----------------- Bulk Delete -----------------
class ProductBulkDeleteView(APIView):
    def delete(self, request):
        Product.objects.all().delete()
        return Response({"message": "All products deleted successfully"})


# ----------------- Chunked Upload -----------------
CHUNK_DIR = getattr(settings, "UPLOAD_CHUNKS_DIR", "upload_chunks")


class UploadChunkView(APIView):
    def post(self, request):
        upload_id = request.POST.get("uploadId")
        index = request.POST.get("index")
        filename = request.POST.get("filename")
        chunk = request.FILES.get("chunk")

        if not upload_id or index is None or chunk is None:
            return Response({"error": "uploadId, index and chunk required"}, status=400)

        # Ensure directory exists
        dir_path = os.path.join(CHUNK_DIR, upload_id)
        os.makedirs(dir_path, exist_ok=True)

        # Save chunk
        chunk_path = os.path.join(dir_path, f"chunk_{index}")
        with open(chunk_path, "wb") as f:
            for data in chunk.chunks():
                f.write(data)

        return JsonResponse({"status": "ok"})


class UploadFinalizeView(APIView):
    def post(self, request):
        upload_id = request.POST.get("uploadId")
        filename = request.POST.get("filename")
        overwrite = request.POST.get("overwrite", "").lower() in ["true", "1"]

        if not upload_id or not filename:
            return Response({"error": "uploadId and filename required"}, status=400)

        # Reassemble chunks
        dir_path = os.path.join(CHUNK_DIR, upload_id)
        assembled_path = default_storage.path(f"uploads/{filename}")

        with open(assembled_path, "wb") as out:
            i = 0
            while True:
                chunk_path = os.path.join(dir_path, f"chunk_{i}")
                if not os.path.exists(chunk_path):
                    break
                with open(chunk_path, "rb") as c:
                    out.write(c.read())
                i += 1

        # Trigger celery task
        job_id = str(uuid.uuid4())
        process_csv_task.apply_async(args=[assembled_path, job_id], task_id=job_id)

        return Response({"message": "finalized", "job_id": job_id}, status=202)
