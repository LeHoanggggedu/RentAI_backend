# db/connections.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv


# 1️⃣ Tải biến môi trường từ file .env
load_dotenv()

# 2️⃣ Đọc thông tin từ .env
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# 3️⃣ Tạo URL kết nối theo định dạng PostgreSQL
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 4️⃣ Tạo engine (máy kết nối)
# echo=True sẽ in log SQL ra terminal khi chạy (rất hữu ích khi debug)
engine = create_engine(DATABASE_URL, echo=True)

# 5️⃣ Tạo session factory (nhà máy tạo phiên làm việc với DB)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 6️⃣ Tạo Base cho các models (class ORM)
Base = declarative_base()


# 7️⃣ Hàm tiện ích để tạo session cho từng request
def get_db():
    db = SessionLocal()
    try:
        yield db  # dùng yield để FastAPI quản lý vòng đời session
    finally:
        db.close()  # đảm bảo đóng session khi xong việc
