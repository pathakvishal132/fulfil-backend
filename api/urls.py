# from django.contrib import admin
# from django.urls import path

# from products.views import (
#     ProductUploadView,
#     ProductUploadStatusView,
#     ProductListCreateView,
#     ProductRetrieveUpdateDeleteView,
#     ProductBulkDeleteView,
# )

# urlpatterns = [
#     path("upload/", ProductUploadView.as_view(), name="product-upload"),
#     path(
#         "upload/status/<str:job_id>/",
#         ProductUploadStatusView.as_view(),
#         name="product-upload-status",
#     ),
#     path("products/", ProductListCreateView.as_view(), name="product-list-create"),
#     path(
#         "products/<int:id>/",
#         ProductRetrieveUpdateDeleteView.as_view(),
#         name="product-detail",
#     ),
#     path(
#         "products/bulk-delete/",
#         ProductBulkDeleteView.as_view(),
#         name="product-bulk-delete",
#     ),
# ]
from django.urls import path
from products.views import (
    ProductUploadView,
    ProductUploadStatusView,
    ProductListCreateView,
    ProductRetrieveUpdateDeleteView,
    ProductBulkDeleteView,
    UploadChunkView,
    UploadFinalizeView,
)

urlpatterns = [
    # Upload CSV (async)
    path("upload/", ProductUploadView.as_view(), name="product-upload"),
    # Upload status - frontend will append job id: `${API.uploadStatus}/${jobId}/`
    path(
        "upload/status/<str:job_id>/",
        ProductUploadStatusView.as_view(),
        name="product-upload-status",
    ),
    # Products CRUD
    path("products/", ProductListCreateView.as_view(), name="product-list-create"),
    path(
        "products/<int:id>/",
        ProductRetrieveUpdateDeleteView.as_view(),
        name="product-detail",
    ),
    path(
        "products/bulk-delete/",
        ProductBulkDeleteView.as_view(),
        name="product-bulk-delete",
    ),
    # Chunked upload endpoints (optional)
    path("products/upload-chunk/", UploadChunkView.as_view(), name="upload-chunk"),
    path(
        "products/upload-finalize/",
        UploadFinalizeView.as_view(),
        name="upload-finalize",
    ),
]
