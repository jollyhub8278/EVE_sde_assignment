from sqlalchemy import Column, ForeignKey, Integer, Numeric

from src.utils.db import Base


class CentreTest(Base):
    __tablename__ = "centre_tests"

    id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(Integer, ForeignKey("centres.id"), nullable=False)
    test_id = Column(
        Integer,
        ForeignKey("diagnostic_tests.id"),
        nullable=False,
    )
    price = Column(Numeric(10, 2), nullable=False)