from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx

from app.database import get_db
from app import models, schemas
from app.services.generator import generate_variant
from app.services.constraints import validate_variant

router = APIRouter()

VALID_PLATFORMS = ("discord", "mock_x", "mock_linkedin")


def resolve_body(source_type: str, source_content: str) -> str:
    if source_type == "markdown":
        return source_content
    if source_type == "url":
        resp = httpx.get(source_content, timeout=10)
        resp.raise_for_status()
        return resp.text
    raise HTTPException(status_code=400, detail="source_type must be 'url' or 'markdown'")


@router.post("/posts", response_model=schemas.PostOut)
def create_post(payload: schemas.PostCreate, db: Session = Depends(get_db)):
    body = resolve_body(payload.source_type, payload.source_content)
    post = models.Post(
        source_type=payload.source_type,
        source_content=payload.source_content,
        body=body,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.post("/posts/{post_id}/variants", response_model=list[schemas.VariantOut])
def create_variants(post_id: str, payload: schemas.VariantGenerateRequest, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="post not found")

    created = []
    errors = []

    for platform in payload.platforms:
        if platform not in VALID_PLATFORMS:
            errors.append({"platform": platform, "violations": [f"unknown platform: {platform}"]})
            continue

        content = generate_variant(platform, post.body)
        violations = validate_variant(platform, content)
        if violations:
            errors.append({"platform": platform, "violations": violations})
            continue

        variant = models.Variant(post_id=post.id, platform=platform, content=content, status="draft")
        db.add(variant)
        db.commit()
        db.refresh(variant)
        created.append(variant)

    if errors and not created:
        raise HTTPException(status_code=422, detail=errors)

    return created