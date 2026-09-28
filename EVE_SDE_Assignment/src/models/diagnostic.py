from sqlalchemy import Column, Integer, String
from src.utils.db import Base

class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, nullable=False)