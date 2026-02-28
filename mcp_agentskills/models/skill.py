from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mcp_agentskills.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Skill(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_skill_user_name"),)

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500), default="")
    skill_dir: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("User", back_populates="skills")
