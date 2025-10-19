
### Cấu trúc project
``` commandline
.  
├── alembic  
│   ├── versions    // thư mục chứa file migrations  
│   └── env.py  
├── app  
│   ├── api         // các file api được đặt trong này  
│   ├── core        // chứa file config load các biến env & function tạo/verify JWT access-token  
│   ├── db          // file cấu hình make DB session  
│   ├── helpers     // các function hỗ trợ như login_manager, paging  
│   ├── models      // Database model, tích hợp với alembic để auto generate migration  
│   ├── schemas     // Pydantic Schema  
│   ├── services    // Chứa logic CRUD giao tiếp với DB  
│   └── main.py     // cấu hình chính của toàn bộ project  
├── tests  
│   ├── api         // chứa các file test cho từng api  
│   ├── faker       // chứa file cấu hình faker để tái sử dụng  
│   ├── .env        // config DB test  
│   └── conftest.py // cấu hình chung của pytest  
├── .gitignore  
├── alembic.ini  
├── docker-compose.yaml  
├── Dockerfile  
├── env.example  
├── logging.ini     // cấu hình logging  
├── postgresql.conf // file cấu hình postgresql, sử dụng khi run docker-compose  
├── pytest.ini      // file setup cho pytest  
├── README.md  
└── requirements.txt
```
