from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.utils.db import Base

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = {'extend_existing': True}  # ✅ Add this line

    id = Column(Integer, primary_key=True, index=True)
    from_user = Column(Integer, ForeignKey("users.id"))
    to_user = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)

    from_user_rel = relationship("User", foreign_keys=[from_user])
    to_user_rel = relationship("User", foreign_keys=[to_user])
