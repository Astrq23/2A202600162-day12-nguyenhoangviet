#  Code Lab: Deploy Your AI Agent to Production

> **AICB-P1 · VinUniversity 2026**  
> Thời gian: 3-4 giờ | Độ khó: Intermediate

##  Mục Tiêu

Sau khi hoàn thành lab này, bạn sẽ:
- Hiểu sự khác biệt giữa development và production
- Containerize một AI agent với Docker
- Deploy agent lên cloud platform
- Bảo mật API với authentication và rate limiting
- Thiết kế hệ thống có khả năng scale và reliable

---

##  Yêu Cầu

```bash
 Python 3.11+
 Docker & Docker Compose
 Git
 Text editor (VS Code khuyến nghị)
 Terminal/Command line
```

**Không cần:**
-  OpenAI API key (dùng mock LLM)
-  Credit card
-  Kinh nghiệm DevOps trước đó

---

##  Lộ Trình Lab

| Phần | Thời gian | Nội dung |
|------|-----------|----------|
| **Part 1** | 30 phút | Localhost vs Production |
| **Part 2** | 45 phút | Docker Containerization |
| **Part 3** | 45 phút | Cloud Deployment |
| **Part 4** | 40 phút | API Security |
| **Part 5** | 40 phút | Scaling & Reliability |
| **Part 6** | 60 phút | Final Project |

---

## Part 1: Localhost vs Production (30 phút)

###  Concepts

**Vấn đề:** "It works on my machine" — code chạy tốt trên laptop nhưng fail khi deploy.

**Nguyên nhân:**
- Hardcoded secrets
- Khác biệt về environment (Python version, OS, dependencies)
- Không có health checks
- Config không linh hoạt

**Giải pháp:** 12-Factor App principles

###  Exercise 1.1: Phát hiện anti-patterns

```bash
cd 01-localhost-vs-production/develop
```

**Nhiệm vụ:** Đọc `app.py` và tìm ít nhất 5 vấn đề.

**Đáp án tham khảo (tìm được 8 vấn đề):**
- Hardcode secrets trong code (`OPENAI_API_KEY`, `DATABASE_URL`)
- `DEBUG=True` trong code
- Dùng `print()` thay vì structured logging
- Log lộ secret (`print` API key)
- Không có endpoint `/health` hoặc `/ready`
- Port hardcode `8000`, không đọc từ `PORT`
- Bind `host="localhost"` nên không phù hợp container/cloud
- `reload=True` (dev mode) bật trong runtime chính

<details>
<summary> Gợi ý</summary>

Tìm:
- API key hardcode
- Port cố định
- Debug mode
- Không có health check
- Không xử lý shutdown

</details>

###  Exercise 1.2: Chạy basic version

```bash
pip install -r requirements.txt
python app.py
```

Test:
```bash
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

**Quan sát:** Nó chạy! Nhưng có production-ready không?

###  Exercise 1.3: So sánh với advanced version

```bash
cd ../production
cp .env.example .env
pip install -r requirements.txt
python app.py
```

**Nhiệm vụ:** So sánh 2 files `app.py`. Điền vào bảng:

| Feature | Basic | Advanced | Tại sao quan trọng? |
|---------|-------|----------|---------------------|
| Config | Hardcode | Env vars | Dễ dàng thay đổi mà không cần rebuild |
| Health check | Không có `/health`, `/ready` | Có `/health` (liveness) + `/ready` (readiness) | Theo dõi trạng thái của ứng dụng |
| Logging | print() | JSON | Dễ dàng phân tích và theo dõi |
| Shutdown | Đột ngột | Graceful | Tránh mất dữ liệu và đảm bảo tài nguyên được giải phóng đúng cách |

###  Checkpoint 1

- [v] Hiểu tại sao hardcode secrets là nguy hiểm
- [v] Biết cách dùng environment variables
- [v] Hiểu vai trò của health check endpoint
- [v] Biết graceful shutdown là gì

---

## Part 2: Docker Containerization (45 phút)

###  Concepts

**Vấn đề:** "Works on my machine" part 2 — Python version khác, dependencies conflict.

**Giải pháp:** Docker — đóng gói app + dependencies vào container.

**Benefits:**
- Consistent environment
- Dễ deploy
- Isolation
- Reproducible builds

###  Exercise 2.1: Dockerfile cơ bản

```bash
cd ../../02-docker/develop
```

**Nhiệm vụ:** Đọc `Dockerfile` và trả lời:

1. Base image là gì? Base image là một image đã có sẵn, chứa OS và runtime. Nó giúp tiết kiệm thời gian vì không phải cài đặt Python từ đầu.
2. Working directory là gì? Working directory là thư mục trong container nơi các lệnh tiếp theo sẽ được thực thi. Nó giúp tổ chức file trong container.
3. Tại sao COPY requirements.txt trước? COPY requirements.txt trước giúp tận dụng cache của Docker. Nếu chỉ thay đổi code mà không thay đổi dependencies, Docker sẽ không phải cài lại dependencies, tiết kiệm thời gian build.
4. CMD vs ENTRYPOINT khác nhau thế nào? CMD cung cấp command/args mặc định và dễ override khi `docker run`. ENTRYPOINT đặt executable chính của container; khi run, args sẽ nối thêm vào ENTRYPOINT (và vẫn có thể thay bằng `--entrypoint` nếu cần).

###  Exercise 2.2: Build và run

```bash
# Build image
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .

# Run container
docker run -p 8000:8000 my-agent:develop

# Test
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```

**Quan sát:** Image size là bao nhiêu? 1.66GB
```bash
docker images my-agent:develop
```

###  Exercise 2.3: Multi-stage build

```bash
cd ../production
```

**Nhiệm vụ:** Đọc `Dockerfile` và tìm:
- Stage 1 làm gì? Stage 1 là builder stage, nơi cài đặt tất cả dependencies và build ứng dụng. Nó có thể sử dụng base image nặng hơn vì chỉ dùng để build.
- Stage 2 làm gì? Stage 2 là runtime stage, nơi tạo container cuối cùng với các dependency cần thiết để chạy ứng dụng.
- Tại sao image nhỏ hơn? Image nhỏ hơn vì chỉ chứa các file cần thiết để chạy ứng dụng, không chứa các file build và dependencies không cần thiết.

Build và so sánh:
```bash
docker build -t my-agent:advanced .
docker images | grep my-agent
```

###  Exercise 2.4: Docker Compose stack

**Nhiệm vụ:** Đọc `docker-compose.yml` và vẽ architecture diagram.


```bash
docker compose up
```

Services nào được start? Chúng communicate thế nào?

**Trả lời:**
- Services được start: `agent`, `redis`, `qdrant`, `nginx`
- Luồng giao tiếp:
  - Client -> `nginx` (port 80)
  - `nginx` proxy vào `agent`
  - `agent` gọi `redis` (cache/session/rate-limit) qua `REDIS_URL`
  - `agent` gọi `qdrant` qua `QDRANT_URL`
  - Tất cả dịch vụ trao đổi qua network nội bộ `internal`


Test:
```bash
# Health check
curl http://localhost/health

# Agent endpoint
curl http://localhost/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain microservices"}'
```

###  Checkpoint 2

- [v] Hiểu cấu trúc Dockerfile
- [v] Biết lợi ích của multi-stage builds
- [v] Hiểu Docker Compose orchestration
- [v] Biết cách debug container (`docker logs`, `docker exec`)

---

## Part 3: Cloud Deployment (45 phút)

###  Concepts

**Vấn đề:** Laptop không thể chạy 24/7, không có public IP.

**Giải pháp:** Cloud platforms — Railway, Render, GCP Cloud Run.

**So sánh:**

| Platform | Độ khó | Free tier | Best for |
|----------|--------|-----------|----------|
| Railway | ⭐ | $5 credit | Prototypes |
| Render | ⭐⭐ | 750h/month | Side projects |
| Cloud Run | ⭐⭐⭐ | 2M requests | Production |

###  Exercise 3.1: Deploy Railway (15 phút)

```bash
cd ../../03-cloud-deployment/railway
```

**Steps:**

1. Install Railway CLI:
```bash
npm i -g @railway/cli
```

2. Login:
```bash
railway login
```

3. Initialize project:
```bash
railway init
```

4. Set environment variables:
```bash
railway variables set PORT=8000
railway variables set AGENT_API_KEY=my-secret-key
```

5. Deploy:
```bash
railway up
```

6. Get public URL:
```bash
railway domain
```

**Nhiệm vụ:** Test public URL với curl hoặc Postman.

**Kết quả mong đợi khi test public URL:**
- `GET /health` trả về `200` và JSON có `status: "ok"`
- `POST /ask` trả về `200` và có trường `answer`
- Nếu endpoint có auth thì gọi thiếu key/token phải nhận `401` hoặc `403`

Test:
```bash
# Health check
curl http://student-agent-domain/health

# Agent endpoint
curl http://studen-agent-domain/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": ""}'
```

###  Exercise 3.2: Deploy Render (15 phút)

```bash
cd ../render
```

**Steps:**

1. Push code lên GitHub (nếu chưa có)
2. Vào [render.com](https://render.com) → Sign up
3. New → Blueprint
4. Connect GitHub repo
5. Render tự động đọc `render.yaml`
6. Set environment variables trong dashboard
7. Deploy!

**Nhiệm vụ:** So sánh `render.yaml` với `railway.toml`. Khác nhau gì?

**Trả lời:**
- `render.yaml` là Blueprint IaC đầy đủ: định nghĩa nhiều service (web + redis), region, plan, env vars, autoDeploy.
- `railway.toml` gọn hơn: tập trung build/deploy command, healthcheck path, restart policy.
- Render thường gắn flow GitHub-first (Blueprint), Railway thường linh hoạt qua CLI (`railway init`, `railway up`).
- Cả hai đều không nên hardcode secret, cần set secret trên dashboard/CLI.

###  Exercise 3.3: (Optional) GCP Cloud Run (15 phút)

```bash
cd ../production-cloud-run
```

**Yêu cầu:** GCP account (có free tier).

**Nhiệm vụ:** Đọc `cloudbuild.yaml` và `service.yaml`. Hiểu CI/CD pipeline.

**Tóm tắt CI/CD pipeline Cloud Run:**
1. `cloudbuild.yaml` chạy test (`pytest`)
2. Build Docker image và gắn tag theo commit SHA
3. Push image lên Container Registry
4. Deploy lên Cloud Run với giới hạn min/max instances, CPU/RAM, timeout, env vars và Secret Manager
5. `service.yaml` mô tả hạ tầng ở mức service: autoscaling, concurrency, probes (`/health`, `/ready`), resources

###  Checkpoint 3

- [v] Deploy thành công lên ít nhất 1 platform
- [v] Có public URL hoạt động
- [v] Hiểu cách set environment variables trên cloud
- [v] Biết cách xem logs

---

## Part 4: API Security (40 phút)

###  Concepts

**Vấn đề:** Public URL = ai cũng gọi được = hết tiền OpenAI.

**Giải pháp:**
1. **Authentication** — Chỉ user hợp lệ mới gọi được
2. **Rate Limiting** — Giới hạn số request/phút
3. **Cost Guard** — Dừng khi vượt budget

###  Exercise 4.1: API Key authentication

```bash
cd ../../04-api-gateway/develop
```

**Nhiệm vụ:** Đọc `app.py` và tìm:
- API key được check ở đâu?
- Điều gì xảy ra nếu sai key?
- Làm sao rotate key?

**Trả lời:**
- API key được check trong dependency `verify_api_key()`, dùng `APIKeyHeader(name="X-API-Key")`, sau đó inject vào endpoint `/ask` qua `Depends`.
- Thiếu key -> `401` (Missing API key). Sai key -> `403` (Invalid API key).
- Rotate key bằng cách đổi biến môi trường `AGENT_API_KEY` trên server/cloud, rồi restart hoặc redeploy service (có thể cho overlap 2 key trong giai đoạn chuyển đổi nếu cần zero-downtime).

Test:
```bash
python app.py

#  Không có key
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'

#  Có key
curl http://localhost:8000/ask -X POST \
  -H "X-API-Key: secret-key-123" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

###  Exercise 4.2: JWT authentication (Advanced)

```bash
cd ../production
```

**Nhiệm vụ:** 
1. Đọc `auth.py` — hiểu JWT flow
2. Lấy token:
```bash
python app.py

curl http://localhost:8000/auth/token -X POST \
  -H "Content-Type: application/json" \
  -d '{"username": "student", "password": "demo123"}'
```

3. Dùng token để gọi API:
```bash
TOKEN="<token_từ_bước_2>"
curl http://localhost:8000/ask -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain JWT"}'
```

**JWT flow ngắn gọn:**
- User gửi username/password vào `/auth/token`
- Server xác thực và trả JWT có `sub`, `role`, `exp`
- Client gửi `Authorization: Bearer <token>`
- Dependency `verify_token()` decode + verify chữ ký + kiểm tra hết hạn
- Nếu hợp lệ thì inject user info cho endpoint

###  Exercise 4.3: Rate limiting

**Nhiệm vụ:** Đọc `rate_limiter.py` và trả lời:
- Algorithm nào được dùng? (Token bucket? Sliding window?)
- Limit là bao nhiêu requests/minute?
- Làm sao bypass limit cho admin?

**Trả lời:**
- Algorithm: **Sliding Window Counter** (dùng `deque` timestamps per user).
- Limit mặc định:
  - User: `10 req/min`
  - Admin: `100 req/min`
- Bypass/relax cho admin: chọn limiter theo role (`rate_limiter_admin` thay vì `rate_limiter_user`).

Test:
```bash
# Gọi liên tục 20 lần
for i in {1..20}; do
  curl http://localhost:8000/ask -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"question": "Test '$i'"}'
  echo ""
done
```

Quan sát response khi hit limit.

###  Exercise 4.4: Cost guard

**Nhiệm vụ:** Đọc `cost_guard.py` và implement logic:

```python
def check_budget(user_id: str, estimated_cost: float) -> bool:
    """
    Return True nếu còn budget, False nếu vượt.
    
    Logic:
    - Mỗi user có budget $10/tháng
    - Track spending trong Redis
    - Reset đầu tháng
    """
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"

    current = float(r.get(key) or 0)
    if current + estimated_cost > 10:
      return False

    r.incrbyfloat(key, estimated_cost)
    # hết hạn sau hơn 1 tháng để tự dọn key cũ
    r.expire(key, 32 * 24 * 3600)
    return True
```

<details>
<summary> Solution</summary>

```python
import redis
from datetime import datetime

r = redis.Redis()

def check_budget(user_id: str, estimated_cost: float) -> bool:
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    
    current = float(r.get(key) or 0)
    if current + estimated_cost > 10:
        return False
    
    r.incrbyfloat(key, estimated_cost)
    r.expire(key, 32 * 24 * 3600)  # 32 days
    return True
```

</details>

###  Checkpoint 4

- [v] Implement API key authentication
- [v] Hiểu JWT flow
- [v] Implement rate limiting
- [v] Implement cost guard với Redis

---

## Part 5: Scaling & Reliability (40 phút)

###  Concepts

**Vấn đề:** 1 instance không đủ khi có nhiều users.

**Giải pháp:**
1. **Stateless design** — Không lưu state trong memory
2. **Health checks** — Platform biết khi nào restart
3. **Graceful shutdown** — Hoàn thành requests trước khi tắt
4. **Load balancing** — Phân tán traffic

###  Exercise 5.1: Health checks

```bash
cd ../../05-scaling-reliability/develop
```

**Nhiệm vụ:** Implement 2 endpoints:

```python
@app.get("/health")
def health():
    """Liveness probe — container còn sống không?"""
  return {"status": "ok"}

@app.get("/ready")
def ready():
    """Readiness probe — sẵn sàng nhận traffic không?"""
  try:
    # Check Redis
    r.ping()
    # Check database
    db.execute("SELECT 1")
    return {"status": "ready"}
  except Exception:
    return JSONResponse(
      status_code=503,
      content={"status": "not ready"}
    )
```

<details>
<summary> Solution</summary>

```python
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    try:
        # Check Redis
        r.ping()
        # Check database
        db.execute("SELECT 1")
        return {"status": "ready"}
    except:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready"}
        )
```

</details>

###  Exercise 5.2: Graceful shutdown

**Nhiệm vụ:** Implement signal handler:

```python
import signal
import sys

def shutdown_handler(signum, frame):
    """Handle SIGTERM from container orchestrator"""
    global is_ready
    print(f"Received signal {signum}, start graceful shutdown...")

    # 1) Stop accepting new requests
    is_ready = False

    # 2) Finish current requests (wait tối đa 30s)
    timeout = 30
    waited = 0
    while in_flight_requests > 0 and waited < timeout:
        time.sleep(1)
        waited += 1

    # 3) Close connections
    if redis_client:
        redis_client.close()
    if db_conn:
        db_conn.close()

    # 4) Exit
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)
```

Test:
```bash
python app.py &
PID=$!

# Gửi request
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Long task"}' &

# Ngay lập tức kill
kill -TERM $PID

# Quan sát: Request có hoàn thành không?
```

###  Exercise 5.3: Stateless design

```bash
cd ../production
```

**Nhiệm vụ:** Refactor code để stateless.

**Anti-pattern:**
```python
#  State trong memory
conversation_history = {}

@app.post("/ask")
def ask(user_id: str, question: str):
    history = conversation_history.get(user_id, [])
    # ...
```

**Correct:**
```python
#  State trong Redis
@app.post("/ask")
def ask(user_id: str, question: str):
    history = r.lrange(f"history:{user_id}", 0, -1)
    # ...
```

Tại sao? Vì khi scale ra nhiều instances, mỗi instance có memory riêng.

###  Exercise 5.4: Load balancing

**Nhiệm vụ:** Chạy stack với Nginx load balancer:

```bash
docker compose up --scale agent=3
```

Quan sát:
- 3 agent instances được start
- Nginx phân tán requests
- Nếu 1 instance die, traffic chuyển sang instances khác

Test:
```bash
# Gọi 10 requests
for i in {1..10}; do
  curl http://localhost/ask -X POST \
    -H "Content-Type: application/json" \
    -d '{"question": "Request '$i'"}'
done

# Check logs — requests được phân tán
docker compose logs agent
```

###  Exercise 5.5: Test stateless

```bash
python test_stateless.py
```

Script này:
1. Gọi API để tạo conversation
2. Kill random instance
3. Gọi tiếp — conversation vẫn còn không?

###  Checkpoint 5

- [v] Implement health và readiness checks
- [v] Implement graceful shutdown
- [v] Refactor code thành stateless
- [v] Hiểu load balancing với Nginx
- [v] Test stateless design

---

## Part 6: Final Project (60 phút)

###  Objective

Build một production-ready AI agent từ đầu, kết hợp TẤT CẢ concepts đã học.

###  Requirements

**Functional:**
- [ ] Agent trả lời câu hỏi qua REST API
- [ ] Support conversation history
- [ ] Streaming responses (optional)

**Non-functional:**
- [ ] Dockerized với multi-stage build
- [ ] Config từ environment variables
- [ ] API key authentication
- [ ] Rate limiting (10 req/min per user)
- [ ] Cost guard ($10/month per user)
- [ ] Health check endpoint
- [ ] Readiness check endpoint
- [ ] Graceful shutdown
- [ ] Stateless design (state trong Redis)
- [ ] Structured JSON logging
- [ ] Deploy lên Railway hoặc Render
- [ ] Public URL hoạt động

### 🏗 Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Nginx (LB)     │
└──────┬──────────┘
       │
       ├─────────┬─────────┐
       ▼         ▼         ▼
   ┌──────┐  ┌──────┐  ┌──────┐
   │Agent1│  │Agent2│  │Agent3│
   └───┬──┘  └───┬──┘  └───┬──┘
       │         │         │
       └─────────┴─────────┘
                 │
                 ▼
           ┌──────────┐
           │  Redis   │
           └──────────┘
```

###  Step-by-step

#### Step 1: Project setup (5 phút)

```bash
mkdir my-production-agent
cd my-production-agent

# Tạo structure
mkdir -p app
touch app/__init__.py
touch app/main.py
touch app/config.py
touch app/auth.py
touch app/rate_limiter.py
touch app/cost_guard.py
touch Dockerfile
touch docker-compose.yml
touch requirements.txt
touch .env.example
touch .dockerignore
```

#### Step 2: Config management (10 phút)

**File:** `app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PORT: int = 8000
    REDIS_URL: str = "redis://localhost:6379/0"
    AGENT_API_KEY: str
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_PER_MINUTE: int = 10
    MONTHLY_BUDGET_USD: float = 10.0

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

#### Step 3: Main application (15 phút)

**File:** `app/main.py`

```python
import redis
from fastapi import FastAPI, Depends, HTTPException
from .config import settings
from .auth import verify_api_key
from .rate_limiter import check_rate_limit
from .cost_guard import check_budget
from .llm import ask_llm

app = FastAPI()
r = redis.from_url(settings.REDIS_URL, decode_responses=True)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    try:
        r.ping()
        return {"ready": True}
    except Exception:
        raise HTTPException(status_code=503, detail="Dependencies not ready")

@app.post("/ask")
def ask(
    question: str,
    user_id: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit),
    _budget: None = Depends(check_budget)
):
    # 1) Get conversation history from Redis
    history_key = f"history:{user_id}"
    history = r.lrange(history_key, 0, -1)

    # 2) Call LLM
    answer = ask_llm(question=question, history=history)

    # 3) Save to Redis
    r.rpush(history_key, f"user:{question}")
    r.rpush(history_key, f"assistant:{answer}")
    r.expire(history_key, 30 * 24 * 3600)

    # 4) Return response
    return {"user_id": user_id, "answer": answer}
```

#### Step 4: Authentication (5 phút)

**File:** `app/auth.py`

```python
from fastapi import Header, HTTPException
from .config import settings

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.AGENT_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    # Demo: map key -> user_id
    return "user_from_api_key"
```

#### Step 5: Rate limiting (10 phút)

**File:** `app/rate_limiter.py`

```python
import time
import redis
from fastapi import HTTPException
from .config import settings

r = redis.from_url(settings.REDIS_URL)

def check_rate_limit(user_id: str):
    now = time.time()
    key = f"rate:{user_id}"

    # sliding window 60s bằng sorted set
    r.zremrangebyscore(key, 0, now - 60)
    current = r.zcard(key)

    if current >= settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    member = str(now)
    r.zadd(key, {member: now})
    r.expire(key, 120)
```

#### Step 6: Cost guard (10 phút)

**File:** `app/cost_guard.py`

```python
from datetime import datetime
import redis
from fastapi import HTTPException
from .config import settings

r = redis.from_url(settings.REDIS_URL)

def check_budget(user_id: str):
    month = datetime.utcnow().strftime("%Y-%m")
    key = f"budget:{user_id}:{month}"

    current = float(r.get(key) or 0)
    if current >= settings.MONTHLY_BUDGET_USD:
        raise HTTPException(status_code=402, detail="Monthly budget exceeded")
```

#### Step 7: Dockerfile (5 phút)

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runtime
RUN useradd -m appuser
WORKDIR /app
COPY --from=builder /root/.local /home/appuser/.local
COPY app/ ./app/
COPY utils/ ./utils/
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Step 8: Docker Compose (5 phút)

```yaml
version: "3.9"
services:
  agent:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  redis:
    image: redis:7-alpine

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - agent
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
```

#### Step 9: Test locally (5 phút)

```bash
docker compose up --scale agent=3

# Test all endpoints
curl http://localhost/health
curl http://localhost/ready
curl -H "X-API-Key: secret" http://localhost/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello", "user_id": "user1"}'
```

#### Step 10: Deploy (10 phút)

```bash
# Railway
railway init
railway variables set REDIS_URL=...
railway variables set AGENT_API_KEY=...
railway up

# Hoặc Render
# Push lên GitHub → Connect Render → Deploy
```

###  Validation

Chạy script kiểm tra:

```bash
cd 06-lab-complete
python check_production_ready.py
```

Script sẽ kiểm tra:
-  Dockerfile exists và valid
-  Multi-stage build
-  .dockerignore exists
-  Health endpoint returns 200
-  Readiness endpoint returns 200
-  Auth required (401 without key)
-  Rate limiting works (429 after limit)
-  Cost guard works (402 when exceeded)
-  Graceful shutdown (SIGTERM handled)
-  Stateless (state trong Redis, không trong memory)
-  Structured logging (JSON format)

###  Grading Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Functionality** | 20 | Agent hoạt động đúng |
| **Docker** | 15 | Multi-stage, optimized |
| **Security** | 20 | Auth + rate limit + cost guard |
| **Reliability** | 20 | Health checks + graceful shutdown |
| **Scalability** | 15 | Stateless + load balanced |
| **Deployment** | 10 | Public URL hoạt động |
| **Total** | 100 | |

---

##  Hoàn Thành!

Bạn đã:
-  Hiểu sự khác biệt dev vs production
-  Containerize app với Docker
-  Deploy lên cloud platform
-  Bảo mật API
-  Thiết kế hệ thống scalable và reliable

###  Next Steps

1. **Monitoring:** Thêm Prometheus + Grafana
2. **CI/CD:** GitHub Actions auto-deploy
3. **Advanced scaling:** Kubernetes
4. **Observability:** Distributed tracing với OpenTelemetry
5. **Cost optimization:** Spot instances, auto-scaling

###  Resources

- [12-Factor App](https://12factor.net/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)

---

##  Q&A

**Q: Tôi không có credit card, có thể deploy không?**  
A: Có! Railway cho $5 credit, Render có 750h free tier.

**Q: Mock LLM khác gì với OpenAI thật?**  
A: Mock trả về canned responses, không gọi API. Để dùng OpenAI thật, set `OPENAI_API_KEY` trong env.

**Q: Làm sao debug khi container fail?**  
A: `docker logs <container_id>` hoặc `docker exec -it <container_id> /bin/sh`

**Q: Redis data mất khi restart?**  
A: Dùng volume: `volumes: - redis-data:/data` trong docker-compose.

**Q: Làm sao scale trên Railway/Render?**  
A: Railway: `railway scale <replicas>`. Render: Dashboard → Settings → Instances.

---

**Happy Deploying! **
