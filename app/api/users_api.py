from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import redis
import random
import string
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

from app.models.users import Users
from app.db.connections import get_db

# Tải biến môi trường
load_dotenv()

# Cấu hình
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Cấu hình Email
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "hbhcycece@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "loao ifuz vlwg idlp")

# Cấu hình Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Khởi tạo Router
router = APIRouter()


# Mock Redis class for development (when Redis is not available)
class MockRedis:
    """
    ⚠️ FOR DEVELOPMENT ONLY
    - OTP will NOT expire automatically
    - Data is lost when server restarts
    """

    def __init__(self):
        self.store = {}

    def setex(self, key, seconds, value):
        self.store[key] = value
        print(f"\n{'=' * 60}")
        print(f"📧 OTP Code: {value}")
        print(f"📬 For: {key.replace('otp:', '')}")
        print(f"⏱️ Should expire in: {seconds}s (NOT IMPLEMENTED)")
        print(f"{'=' * 60}\n")
        return True

    def get(self, key):
        return self.store.get(key)

    def delete(self, key):
        if key in self.store:
            del self.store[key]
        return True


# Initialize Redis client with fallback to Mock
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=2
    )
    redis_client.ping()
    print("✅ Connected to Redis server successfully")
except Exception as e:
    print(f"⚠️ Redis connection failed: {e}")
    print("⚠️ Using Mock Redis (Development mode)")
    redis_client = MockRedis()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()


# ============= SCHEMAS =============
class UserRegisterStep1(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)  # Bcrypt giới hạn 72 bytes
    role: str = Field(default="nguoi_mua")

    @validator('role')
    def validate_role(cls, v):
        allowed_roles = ['admin', 'chu_nha', 'moi_gioi', 'nha_dau_tu', 'nguoi_thue', 'nguoi_mua']
        if v not in allowed_roles:
            raise ValueError(f'Role phải là một trong: {", ".join(allowed_roles)}')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        if not v.replace('+', '').replace('-', '').isdigit():
            raise ValueError('Số điện thoại không hợp lệ')
        return v


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_info: dict


class MessageResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


# ============= HELPER FUNCTIONS =============
def hash_password(password: str) -> str:
    # Bcrypt chỉ hỗ trợ tối đa 72 bytes
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))


def generate_referral_code() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


def send_otp_email(email: str, otp: str):
    """Gửi mã OTP qua email"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = email
        msg['Subject'] = "Mã xác thực OTP - Đăng ký tài khoản"

        body = f"""
        <html>
            <body>
                <h2>Xác thực tài khoản</h2>
                <p>Mã OTP của bạn là: <strong style="font-size: 24px; color: #2563eb;">{otp}</strong></p>
                <p>Mã có hiệu lực trong 60 giây.</p>
                <p>Nếu bạn không yêu cầu mã này, vui lòng bỏ qua email này.</p>
            </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, email, text)
        server.quit()

        return True
    except Exception as e:
        print(f"Lỗi gửi email: {str(e)}")
        return False


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token không hợp lệ")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")


# ============= API ENDPOINTS =============

@router.post("/register/step1", response_model=MessageResponse)
async def register_step1_and_step2(user_data: UserRegisterStep1, db: Session = Depends(get_db)):
    """
    Bước 1 & 2: Nhập thông tin và lưu vào database
    Sau đó tự động gửi OTP
    """

    # Kiểm tra email đã tồn tại
    existing_email = db.query(Users).filter(Users.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được sử dụng"
        )

    # Kiểm tra số điện thoại đã tồn tại
    existing_phone = db.query(Users).filter(Users.phone == user_data.phone).first()
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Số điện thoại đã được sử dụng"
        )

    # Tạo referral code duy nhất
    referral_code = generate_referral_code()
    while db.query(Users).filter(Users.referral_code == referral_code).first():
        referral_code = generate_referral_code()

    # Hash mật khẩu
    hashed_password = hash_password(user_data.password)

    # Tạo user mới với activate = 0
    new_user = Users(
        name=user_data.name,
        phone=user_data.phone,
        email=user_data.email,
        password=hashed_password,
        role=user_data.role,
        referral_code=referral_code,
        activate=0
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Tạo OTP và lưu vào Redis
        otp = generate_otp()
        redis_key = f"otp:{user_data.email}"
        redis_client.setex(redis_key, 60, otp)

        # Gửi OTP qua email
        email_sent = send_otp_email(user_data.email, otp)

        if not email_sent:
            return MessageResponse(
                success=True,
                message="Đăng ký thành công! Tuy nhiên có lỗi khi gửi OTP.",
                data={
                    "user_id": new_user.id,
                    "email": new_user.email,
                    "otp_for_testing": otp
                }
            )

        return MessageResponse(
            success=True,
            message="Đăng ký thành công! Mã OTP đã được gửi đến email của bạn.",
            data={
                "user_id": new_user.id,
                "email": new_user.email,
                "otp_expires_in": "60 giây"
            }
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi đăng ký: {str(e)}"
        )


@router.post("/register/verify-otp", response_model=MessageResponse)
async def verify_otp_step3(otp_data: OTPVerify, db: Session = Depends(get_db)):
    """Bước 3: Xác thực OTP và kích hoạt tài khoản"""

    redis_key = f"otp:{otp_data.email}"
    stored_otp = redis_client.get(redis_key)

    if not stored_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã OTP đã hết hạn hoặc không tồn tại"
        )

    if stored_otp != otp_data.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã OTP không chính xác"
        )

    user = db.query(Users).filter(Users.email == otp_data.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Người dùng không tồn tại"
        )

    if user.activate == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản đã được kích hoạt trước đó"
        )

    user.activate = 1

    try:
        db.commit()
        redis_client.delete(redis_key)

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role},
            expires_delta=access_token_expires
        )

        return MessageResponse(
            success=True,
            message="Xác thực thành công! Tài khoản đã được kích hoạt.",
            data={
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "access_token": access_token,
                "token_type": "bearer"
            }
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi kích hoạt tài khoản: {str(e)}"
        )


@router.post("/register/resend-otp", response_model=MessageResponse)
async def resend_otp(email: EmailStr, db: Session = Depends(get_db)):
    """Gửi lại mã OTP"""

    user = db.query(Users).filter(Users.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email không tồn tại trong hệ thống"
        )

    if user.activate == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản đã được kích hoạt"
        )

    otp = generate_otp()
    redis_key = f"otp:{email}"
    redis_client.setex(redis_key, 60, otp)

    email_sent = send_otp_email(email, otp)

    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể gửi email. Vui lòng thử lại."
        )

    return MessageResponse(
        success=True,
        message="Mã OTP mới đã được gửi đến email của bạn.",
        data={
            "email": email,
            "otp_expires_in": "60 giây"
        }
    )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """API Đăng nhập"""

    user = db.query(Users).filter(Users.email == login_data.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác"
        )

    if not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác"
        )

    if user.activate == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản chưa được kích hoạt. Vui lòng xác thực OTP."
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_info={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "referral_code": user.referral_code,
            "activate": user.activate
        }
    )


@router.get("/me")
async def get_current_user(email: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Lấy thông tin user hiện tại"""
    user = db.query(Users).filter(Users.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    return {
        "success": True,
        "data": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "referral_code": user.referral_code,
            "activate": user.activate
        }
    }