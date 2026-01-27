"""
Webhook 日志模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, JSON
from datetime import datetime
import enum

from database import Base


class WebhookStatus(str, enum.Enum):
    """Webhook 状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class Webhook(Base):
    """Webhook 日志模型"""

    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # 'push', 'merge_request', etc.
    payload = Column(JSON, nullable=True)
    status = Column(Enum(WebhookStatus), default=WebhookStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Webhook(id={self.id}, event_type='{self.event_type}', status='{self.status}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "repository_id": self.repository_id,
            "event_type": self.event_type,
            "status": self.status.value if isinstance(self.status, enum.Enum) else self.status,
            "error_message": self.error_message,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            # 不返回完整的 payload，太大
            "has_payload": bool(self.payload)
        }
