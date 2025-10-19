

from sqlalchemy import Column, Integer, String, CheckConstraint,SmallInteger
import enum
from db.connections import Base
from sqlalchemy import Enum



class UserRole(enum.Enum):
    admin='admin'
    chu_nha='chu_nha'
    moi_gioi='moi_gioi'
    nha_dau_tu='nha_dau_tu'
    nguoi_thue='nguoi_thue'
    nguoi_mua= 'nguoi_mua'
class User(Base):
    __tablename__ ='users'
    # sqlacodegen --schema=public postgresql://postgres:123456@localhost:5432/postgres > app/models/users.py
    # xuất model tự động trong schema được chọn bằng sqlacodegen
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.nguoi_mua, nullable=False)
    referral_code = Column(String(20), unique=True)
    activate = Column(SmallInteger,default='0')

    __table_args__= (
        CheckConstraint(
            "role IN('admin','chu_nha','moi_gioi','nha_dau_tu','nguoi_thue','nguoi_mua')",
            name = 'role_check'
        ),
        CheckConstraint('activate = ANY (ARRAY[0, 1])',name='account_check' )
    )

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, email={self.email}, role={self.role.value})>"