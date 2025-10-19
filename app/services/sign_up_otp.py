import redis
import random
import time

r = redis.Redis(host='localhost', port=6379, db=0)

def generate_otp(email):
    otp = str(random.randint(100000, 999999))
    r.setex(f"otp:{email}", 60, otp)  # TTL = 60 giây
    return otp

def verify_otp(email, input_code):
    stored = r.get(f"otp:{email}")
    if stored and stored.decode() == input_code:
        return True
    return False
# sử dụng redis để giữ mã otp cho từng mail yêu cầu đăng ký trong 1p