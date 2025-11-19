from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products"

    def ready(self):
        # Ensure tasks are imported so Celery autodiscovery registers them.
        # This avoids "KeyError: 'products.tasks.process_csv_task'" when
        # worker/process producers use the task name before the module
        # has been imported by the worker.
        try:
            import products.tasks  # noqa: F401
        except Exception:
            # Avoid crashing Django startup if tasks import fails; Celery
            # will log import errors separately. We intentionally swallow
            # the exception here to keep the app import resilient.
            pass
