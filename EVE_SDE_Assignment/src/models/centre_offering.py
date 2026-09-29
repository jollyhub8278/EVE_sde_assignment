from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
)

from src.utils.db import Base


class CentreTest(Base):
    __tablename__ = "centre_tests"

    __table_args__ = (
        UniqueConstraint(
            "centre_id",
            "test_id",
            name="uq_centre_tests_centre_test",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    centre_id = Column(
        Integer,
        ForeignKey("centres.id"),
        nullable=False,
        index=True,
    )

    test_id = Column(
        Integer,
        ForeignKey("diagnostic_tests.id"),
        nullable=False,
        index=True,
    )

    price = Column(Numeric(10, 2), nullable=False)