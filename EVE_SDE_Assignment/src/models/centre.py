from sqlalchemy import Column, Integer, String, UniqueConstraint

from src.utils.db import Base


class Centre(Base):
    __tablename__ = "centres"

    __table_args__ = (
        UniqueConstraint(
            "name",
            "location",
            name="uq_centres_name_location",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    location = Column(String(255), nullable=False)