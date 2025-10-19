# 🔴 Hướng dẫn cài đặt Redis cho Production

## 📋 Mục lục
1. [Tại sao cần Redis thật?](#tại-sao-cần-redis-thật)
2. [Mock Redis hiện tại](#mock-redis-hiện-tại)
3. [Cài đặt Redis trên Windows](#cài-đặt-redis-trên-windows)
4. [Cài đặt Redis trên Linux/Production](#cài-đặt-redis-trên-linuxproduction)
5. [Chuyển từ Mock sang Redis thật](#chuyển-từ-mock-sang-redis-thật)

---

## ⚠️ Tại sao cần Redis thật?

### **Mock Redis hiện tại:**
- ✅ OTP được lưu trong memory (RAM)
- ✅ API hoạt động bình thường
- ❌ OTP **KHÔNG tự động hết hạn** sau 60 giây
- ❌ OTP **MẤT HẾT** khi restart server
- ❌ Không thể dùng trong production với nhiều server

### **Redis thật:**
- ✅ OTP **TỰ ĐỘNG hết hạn** sau 60 giây (TTL)
- ✅ OTP được lưu persistent (không mất khi restart)
- ✅ Hỗ trợ multiple servers (clustering)
- ✅ Hiệu suất cao (millions ops/second)
- ✅ Chuẩn production

---

## 🔧 Mock Redis hiện tại

**File:** `app/api/users_api.py`

```python
# Mock Redis class for development
class MockRedis:
    """
    CẢNH BÁO: Chỉ dùng cho development/testing
    - OTP không tự động hết hạn
    - Data mất khi restart server
    - Không thể scale multiple servers
    """
    def __init__(self):
        self.store = {}
        print("⚠️ Using Mock Redis - FOR DEVELOPMENT ONLY")
    
    def setex(self, key, seconds, value):
        self.store[key] = value
        print(f"\n{'='*60}")
        print(f"📧 OTP Code: {value}")
        print(f"📬 For: {key.replace('otp:', '')}")
        print(f"⏱️ Should expire in: {seconds}s (NOT IMPLEMENTED)")
        print(f"{'='*60}\n")
        return True
    
    def get(self, key):
        return self.store.get(key)
    
    def delete(self, key):
        if key in self.store:
            del self.store[key]
        return True

# Kết nối Redis với fallback
try:
    redis_client = redis.Redis(
        host=REDIS_HOST, 
        port=REDIS_PORT, 
        db=REDIS_DB, 
        decode_responses=True,
        socket_connect_timeout=2
    )
    redis_client.ping()
    print("✅ Connected to Redis server")
except Exception as e:
    print(f"⚠️ Redis not available: {e}")
    print("⚠️ Using Mock Redis (Development mode)")
    redis_client = MockRedis()
```

**Khi nào cần chuyển sang Redis thật:**
- 🚀 Khi deploy production
- 👥 Khi có nhiều users đồng thời
- 🔒 Khi cần bảo mật OTP tốt hơn
- ⚖️ Khi cần load balancing với nhiều servers

---

## 🪟 Cài đặt Redis trên Windows

### **Phương án 1: WSL (Khuyên dùng)**

#### **Bước 1: Bật WSL trong Windows**
```powershell
# PowerShell với quyền Administrator
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

#### **Bước 2: Restart máy**

#### **Bước 3: Cài WSL kernel update**
Download: https://aka.ms/wsl2kernel

#### **Bước 4: Đặt WSL 2 làm mặc định**
```powershell
wsl --set-default-version 2
```

#### **Bước 5: Cài Ubuntu**
```powershell
# Cài Ubuntu từ Microsoft Store
wsl --install -d Ubuntu

# Hoặc nếu muốn cài vào ổ D:
# 1. Tải Ubuntu
Invoke-WebRequest -Uri "https://cloud-images.ubuntu.com/wsl/jammy/current/ubuntu-jammy-wsl-amd64-wsl.rootfs.tar.gz" -OutFile "D:\ubuntu.tar.gz"

# 2. Import vào ổ D
wsl --import Ubuntu D:\WSL\Ubuntu D:\ubuntu.tar.gz --version 2

# 3. Tạo user
wsl -d Ubuntu
useradd -m -s /bin/bash yourname
passwd yourname
# Nhập password

# 4. Đặt default user
exit
ubuntu config --default-user yourname
```

#### **Bước 6: Cài Redis trong WSL**
```bash
# Mở WSL
wsl

# Update package
sudo apt update

# Cài Redis
sudo apt install redis-server -y

# Cấu hình Redis
sudo nano /etc/redis/redis.conf
# Tìm dòng: supervised no
# Đổi thành: supervised systemd
# Lưu: Ctrl+X, Y, Enter

# Khởi động Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Kiểm tra
redis-cli ping
# Kết quả: PONG ✅
```

#### **Bước 7: Tự động khởi động Redis**
```bash
# Thêm vào ~/.bashrc
echo "sudo service redis-server start" >> ~/.bashrc
```

#### **Bước 8: Test từ Windows**
```powershell
# PowerShell
Test-NetConnection localhost -Port 6379
# TcpTestSucceeded : True ✅

# Test bằng Python
python -c "import redis; r = redis.Redis(); print('Redis:', r.ping())"
# Redis: True ✅
```

---

### **Phương án 2: Docker (Dễ nhất)**

#### **Bước 1: Cài Docker Desktop**
Download: https://www.docker.com/products/docker-desktop

#### **Bước 2: Chạy Redis container**
```bash
# Chạy Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  --restart unless-stopped \
  redis:latest

# Kiểm tra
docker ps | findstr redis

# Test
docker exec -it redis redis-cli ping
# PONG ✅
```

#### **Bước 3: Redis với persistent data**
```bash
# Tạo volume để lưu data
docker volume create redis-data

# Chạy Redis với volume
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v redis-data:/data \
  --restart unless-stopped \
  redis:latest redis-server --appendonly yes
```

---

### **Phương án 3: Memurai (Native Windows)**

#### **Bước 1: Download Memurai**
https://www.memurai.com/get-memurai
Chọn **Memurai Developer** (Free)

#### **Bước 2: Cài đặt**
- Chạy file `.msi`
- ☑️ Check "Install as Windows Service"
- Finish

#### **Bước 3: Khởi động service**
```powershell
# Kiểm tra
Get-Service Memurai

# Khởi động nếu stopped
Start-Service Memurai

# Test
Test-NetConnection localhost -Port 6379
```

---

## 🐧 Cài đặt Redis trên Linux/Production

### **Ubuntu/Debian:**
```bash
# Update
sudo apt update

# Cài Redis
sudo apt install redis-server -y

# Cấu hình cho production
sudo nano /etc/redis/redis.conf

# Các setting quan trọng:
# bind 127.0.0.1                    # Chỉ cho phép localhost
# requirepass your_strong_password  # Đặt password
# maxmemory 256mb                   # Giới hạn RAM
# maxmemory-policy allkeys-lru      # Policy khi hết RAM

# Khởi động
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Kiểm tra
sudo systemctl status redis-server
redis-cli ping
```

### **CentOS/RHEL:**
```bash
# Thêm repo
sudo yum install epel-release -y

# Cài Redis
sudo yum install redis -y

# Khởi động
sudo systemctl start redis
sudo systemctl enable redis

# Kiểm tra
redis-cli ping
```

### **Cấu hình Security (Production):**
```bash
# File: /etc/redis/redis.conf

# 1. Đặt password
requirepass YourStrongPassword123!

# 2. Chỉ bind localhost (nếu app cùng server)
bind 127.0.0.1

# 3. Giới hạn RAM
maxmemory 512mb
maxmemory-policy allkeys-lru

# 4. Persistence (lưu data vào disk)
save 900 1
save 300 10
save 60 10000

# 5. Log
loglevel notice
logfile /var/log/redis/redis-server.log

# Restart sau khi sửa
sudo systemctl restart redis-server
```

---

## 🔄 Chuyển từ Mock sang Redis thật

### **Bước 1: Kiểm tra Redis đã chạy**
```bash
# Test connection
redis-cli ping
# PONG ✅

# Hoặc từ Python
python -c "import redis; r = redis.Redis(); print(r.ping())"
# True ✅
```

### **Bước 2: Cập nhật file .env**
```env
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=         # Nếu có password
```

### **Bước 3: Cập nhật code (nếu có password)**

**File:** `app/api/users_api.py`

```python
# Đọc password từ .env
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Kết nối Redis
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD if REDIS_PASSWORD else None,
        decode_responses=True,
        socket_connect_timeout=2
    )
    redis_client.ping()
    print("✅ Connected to Redis server successfully")
except Exception as e:
    print(f"⚠️ Redis connection failed: {e}")
    print("⚠️ Falling back to Mock Redis")
    redis_client = MockRedis()
```

### **Bước 4: Test**
```bash
# Restart server
python main.py

# Nên thấy:
# ✅ Connected to Redis server successfully

# Test API
POST http://localhost:8000/api/register/step1
{
  "name": "Test User",
  "phone": "0123456789",
  "email": "test@example.com",
  "password": "123123",
  "role": "nguoi_mua"
}

# Kiểm tra Redis
redis-cli
> KEYS otp:*
> GET otp:test@example.com
> TTL otp:test@example.com    # Thấy thời gian còn lại
```

### **Bước 5: Xóa Mock Redis (Optional)**

Khi Redis đã chạy ổn định, có thể xóa class MockRedis:

```python
# Xóa toàn bộ class MockRedis

# Kết nối Redis bình thường
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD if REDIS_PASSWORD else None,
    decode_responses=True
)

# Không cần try-except nữa vì Redis bắt buộc phải có
```

---

## 📊 So sánh các phương án

| Phương án | Ưu điểm | Nhược điểm | Khuyên dùng |
|-----------|---------|------------|-------------|
| **Mock Redis** | ✅ Không cần cài gì<br>✅ Setup nhanh | ❌ Không có TTL<br>❌ Mất data khi restart | Development only |
| **WSL** | ✅ Redis chính thống<br>✅ Miễn phí<br>✅ Đầy đủ tính năng | ❌ Cần bật WSL<br>❌ Chỉ cho Windows 10+ | ⭐ Development |
| **Docker** | ✅ Dễ setup<br>✅ Portable<br>✅ Chuẩn production | ❌ Cần cài Docker | ⭐ Development & Production |
| **Memurai** | ✅ Native Windows<br>✅ Có GUI | ❌ Phí cho commercial<br>❌ Fork của Redis | Development |
| **Linux Native** | ✅ Performance cao nhất<br>✅ Ổn định | ❌ Chỉ cho Linux | ⭐ Production |

---

## 🎯 Khuyến nghị

### **Development (Local):**
- **Hiện tại:** Mock Redis ✅
- **Sau này:** WSL hoặc Docker

### **Production (Server):**
- **Ubuntu/Debian:** Redis native
- **Docker:** Redis container với volume
- **Cloud:** Redis managed service (AWS ElastiCache, Azure Redis, etc.)

---

## 🔒 Security Checklist cho Production

- [ ] Đặt password mạnh cho Redis
- [ ] Bind Redis chỉ với localhost hoặc private network
- [ ] Không expose port 6379 ra internet
- [ ] Enable persistence (save to disk)
- [ ] Set maxmemory để tránh tràn RAM
- [ ] Enable log để monitor
- [ ] Backup định kỳ file RDB/AOF
- [ ] Update Redis lên version mới nhất
- [ ] Sử dụng firewall rule
- [ ] Monitor Redis metrics (memory, connections, ops/s)

---

## 📚 Tài liệu tham khảo

- Redis Official: https://redis.io/docs/
- WSL Installation: https://docs.microsoft.com/en-us/windows/wsl/install
- Docker Redis: https://hub.docker.com/_/redis
- Redis Security: https://redis.io/docs/management/security/

---

## ❓ Troubleshooting

### **Lỗi: Connection refused**
```bash
# Kiểm tra Redis có chạy không
redis-cli ping

# Kiểm tra port
netstat -ano | findstr :6379

# Khởi động lại Redis
sudo systemctl restart redis-server
```

### **Lỗi: Authentication failed**
```bash
# Kiểm tra password trong .env
# Hoặc connect với password
redis-cli -a YourPassword ping
```

### **Lỗi: Out of memory**
```bash
# Kiểm tra memory usage
redis-cli INFO memory

# Tăng maxmemory trong config
sudo nano /etc/redis/redis.conf
# maxmemory 512mb
```

---

## 📝 TODO - Khi chuyển sang Redis thật

- [ ] Cài đặt Redis (chọn 1 phương án trên)
- [ ] Test connection: `redis-cli ping`
- [ ] Update file `.env` với Redis config
- [ ] Restart API server
- [ ] Test API đăng ký và xác thực OTP
- [ ] Kiểm tra OTP tự động hết hạn sau 60s
- [ ] Monitor Redis performance
- [ ] Backup Redis data (nếu production)
- [ ] (Optional) Xóa MockRedis class khỏi code

---

**Ngày tạo:** 2025-10-19  
**Trạng thái:** Mock Redis đang được sử dụng  
**Next step:** Cài Redis khi deploy production hoặc khi cần test TTL thực sự