from sqlalchemy import Column, Integer, String, SmallInteger
from app.db.connections import Base


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), default='nguoi_mua')
    referral_code = Column(String(20), unique=True)
    activate = Column(SmallInteger, default=0)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
