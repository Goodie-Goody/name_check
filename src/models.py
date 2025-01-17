'''models.py'''

from sqlalchemy import Column, Integer, String
from base import Base

class ServiceType(Base):
    """
    ServiceType table definition.
    """
    __tablename__ = "services_servicetype"
    __table_args__ = {'extend_existing': True}  # Allow redefining the table if it exists

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    def __repr__(self):
        return f"<ServiceType(id={self.id}, name='{self.name}')>"
