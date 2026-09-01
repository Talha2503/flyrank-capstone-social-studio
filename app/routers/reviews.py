import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.adapters.factory import get_publisher

from app.database import get_db
from app import models, schemas

router = APIRouter()


def get_variant_or_404(variant_id: str, db: Session) -> models.Variant:
    variant = db.query(models.Variant).filter(models.Variant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="variant not found")
    return variant


@router.post("/variants/{variant_id}/approve", response_model=schemas.VariantOut)
def approve_variant(variant_id: str, db: Session = Depends(get_db)):
    variant = get_variant_or_404(variant_id, db)
    if variant.status not in ("draft", "rejected"):
        raise HTTPException(status_code=400, detail=f"cannot approve a variant with status '{variant.status}'")
    variant.status = "approved"
    db.commit()
    db.refresh(variant)
    return variant


@router.post("/variants/{variant_id}/reject", response_model=schemas.VariantOut)
def reject_variant(variant_id: str, db: Session = Depends(get_db)):
    variant = get_variant_or_404(variant_id, db)
    if variant.status == "published":
        raise HTTPException(status_code=400, detail="cannot reject a published variant")
    variant.status = "rejected"
    db.commit()
    db.refresh(variant)
    return variant


@router.get("/variants/{variant_id}", response_model=schemas.VariantOut)
def get_variant(variant_id: str, db: Session = Depends(get_db)):
    return get_variant_or_404(variant_id, db)


@router.post("/variants/{variant_id}/schedule", response_model=schemas.SlotOut)
def schedule_variant(variant_id: str, payload: schemas.ScheduleRequest, db: Session = Depends(get_db)):
    variant = get_variant_or_404(variant_id, db)

    if variant.status != "approved":
        raise HTTPException(
            status_code=422,
            detail=f"cannot schedule a variant with status '{variant.status}'; only 'approved' variants can be scheduled",
        )

    # deterministic idempotency key from variant_id + scheduled_at
    raw_key = f"{variant.id}|{payload.scheduled_at.isoformat()}"
    idempotency_key = hashlib.sha256(raw_key.encode()).hexdigest()

    existing = db.query(models.Slot).filter(models.Slot.idempotency_key == idempotency_key).first()
    if existing:
        return existing

    slot = models.Slot(
        variant_id=variant.id,
        scheduled_at=payload.scheduled_at,
        idempotency_key=idempotency_key,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot

@router.post("/slots/{slot_id}/publish")
def publish_slot(slot_id: str, db: Session = Depends(get_db)):
    slot = db.query(models.Slot).filter(models.Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="slot not found")

    variant = db.query(models.Variant).filter(models.Variant.id == slot.variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="variant not found")

    # durable idempotency check: has this slot already been successfully published?
    existing_success = (
        db.query(models.PublishAttempt)
        .filter(models.PublishAttempt.slot_id == slot.id, models.PublishAttempt.status == "success")
        .first()
    )
    if existing_success:
        return {
            "status": "already_published",
            "platform_message_id": existing_success.platform_message_id,
            "publish_attempt_id": existing_success.id,
        }

    publisher = get_publisher(variant.platform)

    try:
        result = publisher.publish(content=variant.content, idempotency_key=slot.idempotency_key)
    except Exception as e:
        attempt = models.PublishAttempt(slot_id=slot.id, status="failed", error_message=str(e))
        db.add(attempt)
        db.commit()
        raise HTTPException(status_code=502, detail=f"publish failed: {e}")

    attempt = models.PublishAttempt(
        slot_id=slot.id,
        status="success",
        platform_message_id=result["platform_message_id"],
    )
    db.add(attempt)
    variant.status = "published"
    db.commit()
    db.refresh(attempt)

    return {
        "status": "published",
        "platform_message_id": attempt.platform_message_id,
        "publish_attempt_id": attempt.id,
    }

@router.get("/publish-history")
def publish_history(db: Session = Depends(get_db)):
    attempts = db.query(models.PublishAttempt).order_by(models.PublishAttempt.attempted_at.desc()).all()
    result = []
    for a in attempts:
        slot = db.query(models.Slot).filter(models.Slot.id == a.slot_id).first()
        variant = db.query(models.Variant).filter(models.Variant.id == slot.variant_id).first() if slot else None
        result.append({
            "publish_attempt_id": a.id,
            "slot_id": a.slot_id,
            "variant_id": slot.variant_id if slot else None,
            "platform": variant.platform if variant else None,
            "status": a.status,
            "platform_message_id": a.platform_message_id,
            "error_message": a.error_message,
            "attempted_at": a.attempted_at.isoformat() if a.attempted_at else None,
        })
    return result