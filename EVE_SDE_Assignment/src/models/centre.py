from sqlalchemy import Column, Integer, String

from src.utils.db import Base

class Centre(Base):
    __tablename__ = "centres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    location = Column(String(255), nullable=False)