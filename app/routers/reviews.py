import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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