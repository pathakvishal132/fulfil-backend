import csv
from celery import shared_task
from .models import Product


@shared_task(bind=True)
def process_csv_task(self, file_path, job_id):
    total_rows = sum(1 for _ in open(file_path, encoding="utf-8")) - 1
    processed = 0

    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            sku = row.get("sku", "").strip().lower()
            name = row.get("name", "").strip()
            description = row.get("description", "").strip() or None
            Product.objects.update_or_create(
                sku=sku,
                defaults={"name": name, "description": description, "is_active": True},
            )

            processed += 1
            self.update_state(
                state="PROGRESS", meta={"current": processed, "total": total_rows}
            )

    return {"current": total_rows, "total": total_rows, "status": "Task completed!"}
