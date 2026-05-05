# BamBooChatBot — Hệ thống Chat AI (FastAPI + Frontend tĩnh + Firebase)

## Mô tả
- BamBooChatBot là ứng dụng mẫu tích hợp frontend tĩnh (HTML/JS) với backend FastAPI sử dụng mô hình sinh văn bản.
- Hỗ trợ xác thực người dùng bằng Firebase Auth và lưu lịch sử phiên chat vào Firestore.
- Backend có các endpoint chính: `/generate`, `/chat`, `/sessions` (CRUD), `/health`.

## Tính năng chính
- Xác thực bằng Firebase (client + admin)
- Sinh văn bản bởi mô hình (transformers)
- Lọc/loại bỏ các khối nội bộ như `<think>` trước khi trả về cho người dùng
- Quản lý session người dùng (tạo / liệt kê / đổi tên / xóa)
- Frontend tĩnh (HTML + JS) giao tiếp REST với backend

## Yêu cầu
- Python 3.10+
- Các package: xem `requirements.txt` (ví dụ: `fastapi`, `uvicorn`, `transformers`, `torch`, `firebase-admin`, `python-dotenv`, `psutil`)
- Kết nối Internet để tải model HuggingFace (hoặc cấu hình `HF_TOKEN` để tăng rate limit)
- Tài khoản Firebase và Service Account JSON để dùng Admin SDK

## Cấu trúc dự án
- `backend/` — mã FastAPI (`main.py`, `firebase_client.py`, ...)
- `frontend/` — file HTML/JS tĩnh (`homepage.html`, `app.js`, `login.html`, `signup.html`)
- `requirements.txt` — phụ thuộc Python
- `config/serviceAccountKey.json` hoặc biến môi trường `.env` chứa `FIREBASE_CREDENTIALS_PATH`/`FIREBASE_CREDENTIALS_JSON`

## Cấu hình Firebase
1. Tạo project Firebase, bật Authentication (Email/Password) và Firestore.
2. Tải Service Account JSON. Không commit file này vào git. Có hai cách an toàn để cung cấp thông tin xác thực cho backend:

- A) Lưu file cục bộ trên máy chủ (không trong repo) và đặt `FIREBASE_CREDENTIALS_PATH` trỏ tới file đó.
- B) (Khuyến nghị khi triển khai) Đặt nội dung JSON của service account vào biến môi trường `FIREBASE_CREDENTIALS_JSON` (ví dụ trên CI/CD / secret manager).
3. Tạo file `.env` ở gốc dự án với ví dụ sau:
```env
# Nếu dùng file cục bộ (dev), trỏ tới đường dẫn an toàn ngoài repo:
FIREBASE_CREDENTIALS_PATH=/path/to/your/secure/serviceAccountKey.json
# Hoặc (khuyến nghị) cung cấp JSON trực tiếp từ secret manager / CI:
# FIREBASE_CREDENTIALS_JSON={...}
# (tùy chọn) HF_TOKEN=your_huggingface_token
```

### Di chuyển key ra khỏi repo (quick steps)

1. Nếu bạn đang giữ `config/serviceAccountKey.json` trong repo, di chuyển nó ra chỗ an toàn (ví dụ: `C:\secrets\serviceAccountKey.json`) và commit thay đổi để xóa file khỏi git:

```powershell
# di chuyển file ra ngoài repo
Move-Item .\config\serviceAccountKey.json C:\secrets\serviceAccountKey.json

# xóa file khỏi git history trong index (nếu đã commit trước đó)
git rm --cached config/serviceAccountKey.json
git commit -m "Remove service account key from repo"
git push
```

2. Trên máy chủ/CI, export biến môi trường trỏ tới file hoặc JSON:

```powershell
# sử dụng đường dẫn an toàn
$env:FIREBASE_CREDENTIALS_PATH = 'C:\secrets\serviceAccountKey.json'

# hoặc (trong CI) đặt nội dung JSON trực tiếp
# $env:FIREBASE_CREDENTIALS_JSON = Get-Content 'C:\secrets\serviceAccountKey.json' -Raw
```

3. Nếu key bị lộ: thu hồi (rotate) key trong Firebase Console → IAM & Admin → Service Accounts → chọn key → Revoke/Delete, rồi tạo key mới.

## Cài đặt backend
```powershell
# tạo venv (khuyến nghị)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Chạy backend (phát triển)
```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Ghi chú: tải model lần đầu có thể chậm. Đặt biến `HF_TOKEN` nếu bạn muốn tăng tốc tải từ Hugging Face.

## Chạy frontend (phát triển, tĩnh)
```powershell
cd frontend
# phục vụ tệp tĩnh bằng http.server
python -m http.server 8001
# mở http://127.0.0.1:8001/homepage.html trong trình duyệt
```

Nếu muốn, bạn có thể cấu hình FastAPI để phục vụ tệp tĩnh hoặc dùng nginx.

## Biến môi trường quan trọng
- `FIREBASE_CREDENTIALS_PATH` hoặc `FIREBASE_CREDENTIALS_JSON` — cho Firebase Admin SDK
- `HF_TOKEN` (tùy chọn) — token Hugging Face để tăng rate limit khi tải model

## API — ví dụ và mô tả

- POST `/generate`
  - Body JSON: `{ "prompt": "Your prompt", "max_length": 400, "temperature": 0.7 }`
  - Trả về: `{ "status": "success", "data": "<assistant reply>" }`

- POST `/chat`
  - Body JSON: `{ "prompt": "...", "userId": "<uid>", "sessionId": "<session-id>", "idToken": "<Firebase idToken>", "max_length": 800 }`
  - Trả về: `{ "status": "success", "data": "<assistant reply>", "sessionId": "...", "timestamp": "..." }`
  - Lưu ý: `idToken` phải lấy từ client Firebase (see example dưới).

- Sessions endpoints (Firestore-backed):
  - `POST /sessions` — body `{ "idToken": "...", "name": "Optional name" }` → tạo session
  - `GET /sessions?idToken=<idToken>` → liệt kê session
  - `GET /sessions/{sessionId}?userId=<uid>&idToken=<idToken>` → lấy lịch sử messages
  - `PATCH /sessions/{sessionId}` — body `{ "idToken": "...", "name": "New name" }` → đổi tên
  - `DELETE /sessions/{sessionId}?idToken=<idToken>` → xóa session

## Ví dụ curl (backend chạy ở http://127.0.0.1:8000)

1) `/generate` (no auth):
```bash
curl -sS -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain the main differences between REST and GraphQL, with examples.", "max_length":400, "temperature":0.7}'
```

2) `/chat` (cần `idToken` từ Firebase client):
```bash
curl -sS -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Summarize OAuth2 in simple terms.", "userId":"<uid>", "sessionId":"session-20260505", "idToken":"<FIREBASE_ID_TOKEN>", "max_length":800}'
```

## Lấy `idToken` từ client (ví dụ JavaScript Firebase Web SDK)
Trong `frontend/app.js` sau khi login thành công:
```javascript
const user = firebase.auth().currentUser;
const idToken = await user.getIdToken(/* forceRefresh= */ true);
// gửi idToken trong body khi gọi /chat hoặc các API cần auth
```

## Cách README giải quyết các vấn đề chính
- Loại bỏ `<think>`: backend tự động strip các block này.
- Trả lời tiếng Anh: backend chèn instruction buộc English-only và retry nếu phát hiện ký tự CJK.
- Đầu ra quá ngắn: backend retry với prompt yêu cầu trả về multi-paragraph và tăng `max_new_tokens`.

## Tối ưu hoá và thay đổi model
- Để đổi nhanh model thử nghiệm, sửa `MODEL_ID` trong `backend/main.py` và restart server.
- Nếu muốn inference nhanh trên CPU, cân nhắc chuyển sang model dạng ggml/gguf và dùng `llama.cpp` hoặc dùng quantization (`bitsandbytes`) nếu có GPU.

## Debug & Troubleshooting
- Lỗi Firebase: kiểm tra `FIREBASE_CREDENTIALS_PATH` và quyền Firestore.
- Lỗi khi tải model: kiểm tra kết nối mạng và biến `HF_TOKEN`.
- OOM / thiếu RAM: giảm `max_length`, hoặc dùng model nhỏ hơn.
- CORS: đảm bảo `frontend` gọi đúng `BACKEND_URL` (mặc định http://127.0.0.1:8000) và backend đã bật CORS (đã có trong cấu hình).

## Scripts hữu ích (ví dụ - PowerShell)
```powershell
# Start backend
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Serve frontend
cd frontend; python -m http.server 8001
```

## Các bước tiếp theo đề xuất
- Thêm unit/integration tests cho endpoints.
- Thêm CI để kiểm tra lint và chạy tests.
- Xây dựng Dockerfile cho backend và một image tĩnh cho frontend.

## Hướng dẫn cài đặt environment

Phần này hướng dẫn các cách an toàn để các developer khác chạy project cục bộ mà không cần commit `serviceAccountKey.json` vào repo.

- A — Dev tạo Firebase riêng và dùng `serviceAccountKey.json` (thông dụng)

  1. Tạo project Firebase, bật Authentication (Email/Password) và Firestore.
  2. Tải Service Account JSON từ Firebase Console (IAM → Service accounts → Create key).
  3. Lưu file an toàn trên máy dev (ví dụ `C:\secrets\serviceAccountKey.json`) — KHÔNG commit.
  4. Thiết lập biến môi trường (PowerShell):

    ```powershell
    $env:FIREBASE_CREDENTIALS_PATH = 'C:\secrets\serviceAccountKey.json'
    # Hoặc trong .env (ở gốc dự án):
    # FIREBASE_CREDENTIALS_PATH=C:\secrets\serviceAccountKey.json
    # Hoặc đặt JSON trực tiếp (không khuyến nghị trong file):
    # $env:FIREBASE_CREDENTIALS_JSON = Get-Content 'C:\secrets\serviceAccountKey.json' -Raw
    ```

  5. Chạy backend/frontend như bình thường:

    ```powershell
    uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
    # (tách terminal) cd frontend; python -m http.server 8001
    ```

  6. Trên frontend, đăng nhập bằng Firebase (email/Google). Backend sẽ verify `idToken` từ client.

- B — Dev dùng `FIREBASE_CREDENTIALS_JSON` (không cần file)

  - Thay vì lưu file, export nội dung JSON vào biến môi trường `FIREBASE_CREDENTIALS_JSON`. Ví dụ (PowerShell):

   ```powershell
   $env:FIREBASE_CREDENTIALS_JSON = Get-Content 'C:\secrets\serviceAccountKey.json' -Raw
   ```

  - Phương pháp này tiện cho CI/CD và secret manager.

- C — Dùng Firebase Emulator Suite (khuyến nghị cho dev nhóm, an toàn)

  1. Cài Firebase CLI và emulators:

    ```bash
    npm install -g firebase-tools
    firebase login
    ```

  2. Khởi tạo và khởi động emulator (Auth + Firestore):

    ```bash
    firebase init emulators
    firebase emulators:start --only auth,firestore
    ```

  3. (Tùy config) Set env để backend/người dùng biết dùng emulator (PowerShell):

    ```powershell
    $env:FIRESTORE_EMULATOR_HOST='localhost:8080'
    $env:FIREBASE_AUTH_EMULATOR_HOST='http://localhost:9099'
    ```

  4. Lợi ích: không cần service account, an toàn để chia cấu hình dev cho team, dễ reset dữ liệu.

### Lưu ý bảo mật

- Tuy dev cần credentials trên máy họ để chạy backend (phương án A), file đó là tư nhân và không nên chia qua repo.
- Nếu key từng được push lên git (đặc biệt public), hãy rotate/revoke key ngay trong Firebase Console.

---

---
Nếu bạn muốn, mình sẽ:
- Thêm mẫu `.env.example` và script `run.ps1`/`run.sh` tiện lợi.
- Bổ sung ví dụ `postman` collection hoặc `httpie` scripts.
Bạn muốn mình thêm phần nào nữa không? 