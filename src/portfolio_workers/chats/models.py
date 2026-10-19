from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from portfolio_workers.database import Base
from datetime import datetime, timezone

class MessageHistories(Base):
    __tablename__ = "message_histories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(25), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    messages = relationship("Messages", back_populates="message_history")

class Messages(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    message_text = Column(String(512), index=True, nullable=False)
    message_history_id = Column(Integer, ForeignKey(column="message_histories.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    message_history = relationship("MessageHistories", back_populates="messages")
