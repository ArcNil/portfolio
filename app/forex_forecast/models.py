"""SQLAlchemy models for the forex forecast feature.

Ported from ArcNil/forex_forecast (src/app/models/forex_pair_model.py),
converted from Flask-SQLAlchemy to plain SQLAlchemy 2.0 style.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Numeric, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all forex forecast ORM models."""


class ForexPair(Base):
    """A currency pair (e.g. USD→PHP) with its latest known rate."""

    __tablename__ = "forex_pair"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_currency: Mapped[str] = mapped_column(String(5), nullable=False)
    to_currency: Mapped[str] = mapped_column(String(5), nullable=False)
    current_rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    daily_rates: Mapped[list["DailyRate"]] = relationship(
        back_populates="forex_pair",
        cascade="all, delete-orphan",
    )


class DailyRate(Base):
    """One day's rate for a pair — actual history and forecast values alike."""

    __tablename__ = "daily_rate"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    forex_pair_id: Mapped[int] = mapped_column(
        ForeignKey("forex_pair.id"), nullable=False
    )

    forex_pair: Mapped[ForexPair] = relationship(back_populates="daily_rates")

    def to_dict(self) -> dict:
        """Serialize for API responses, matching the original app's shape."""
        return {"date": self.date.isoformat(), "rate": float(self.rate)}


def make_engine(database_url: str):
    """Create a SQLAlchemy engine from a resolved database URL."""
    return create_engine(database_url)