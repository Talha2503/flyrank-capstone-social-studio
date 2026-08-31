import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from app.database import Base

def gen_id():
    return str(uuid.uuid4())

class Post(Base):
    __tablename__ = "posts"
    id = Column(String, primary_key=True, default=gen_id)
    source_type = Column(String, nullable=False)   # url | markdown
    source_content = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Variant(Base):
    __tablename__ = "variants"
    id = Column(String, primary_key=True, default=gen_id)
    post_id = Column(String, ForeignKey("posts.id"), nullable=False)
    platform = Column(String, nullable=False)       # discord | mock_x | mock_linkedin
    content = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="draft")  # draft|approved|rejected|published
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Slot(Base):
    __tablename__ = "slots"
    id = Column(String, primary_key=True, default=gen_id)
    variant_id = Column(String, ForeignKey("variants.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    idempotency_key = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class PublishAttempt(Base):
    __tablename__ = "publish_attempts"
    id = Column(String, primary_key=True, default=gen_id)
    slot_id = Column(String, ForeignKey("slots.id"), nullable=False)
    status = Column(String, nullable=False)          # success | failed
    platform_message_id = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    attempted_at = Column(DateTime, default=datetime.utcnow)