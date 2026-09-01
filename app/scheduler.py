import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from app.database import SessionLocal
from app import models
from app.adapters.factory import get_publisher

logger = logging.getLogger("scheduler")


def process_due_slots():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        due_slots = (
            db.query(models.Slot)
            .filter(models.Slot.scheduled_at <= now)
            .all()
        )

        for slot in due_slots:
            # durable idempotency check — survives restarts, this is the source of truth
            existing_success = (
                db.query(models.PublishAttempt)
                .filter(models.PublishAttempt.slot_id == slot.id, models.PublishAttempt.status == "success")
                .first()
            )
            if existing_success:
                continue  # already published, skip silently

            variant = db.query(models.Variant).filter(models.Variant.id == slot.variant_id).first()
            if not variant or variant.status not in ("approved", "published"):
                continue  # not eligible

            try:
                publisher = get_publisher(variant.platform)
                result = publisher.publish(content=variant.content, idempotency_key=slot.idempotency_key)
                attempt = models.PublishAttempt(
                    slot_id=slot.id,
                    status="success",
                    platform_message_id=result["platform_message_id"],
                )
                db.add(attempt)
                variant.status = "published"
                db.commit()
                logger.info(f"published slot {slot.id} on {variant.platform}")
            except Exception as e:
                attempt = models.PublishAttempt(slot_id=slot.id, status="failed", error_message=str(e))
                db.add(attempt)
                db.commit()
                logger.error(f"failed to publish slot {slot.id}: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(process_due_slots, "interval", seconds=10, id="process_due_slots")
    scheduler.start()
    return scheduler