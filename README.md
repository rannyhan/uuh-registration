# 울산대학교병원 교수임상연수과정 사전신청 시스템

## 배포 방법 (Render — 영구 무료)

---

### 1단계 — GitHub 계정 만들기 & 코드 올리기

1. [github.com](https://github.com) 접속 → **Sign up** (무료 가입)
2. 로그인 후 우측 상단 **`+`** → **`New repository`** 클릭
3. Repository name: `uhh-registration` 입력
4. **`Create repository`** 클릭

5. 생성된 페이지에서 **`uploading an existing file`** 링크 클릭
6. 이 폴더 안의 파일들을 **모두 드래그&드롭** (하위 폴더 templates 포함)
7. 하단 **`Commit changes`** 클릭 → GitHub 업로드 완료 ✅

> 💡 터미널을 쓸 수 있다면 아래 명령어로도 가능해요:
> ```bash
> cd uhh-registration
> git init
> git add .
> git commit -m "first commit"
> git branch -M main
> git remote add origin https://github.com/[내GitHub아이디]/uhh-registration.git
> git push -u origin main
> ```

---

### 2단계 — Render에 배포하기

1. [render.com](https://render.com) 접속 → **`Get Started for Free`**
2. **`GitHub으로 로그인`** 선택 (방금 만든 GitHub 계정으로)
3. 로그인 후 대시보드에서 **`New +`** → **`Web Service`** 클릭
4. **`Connect a repository`** → `uhh-registration` 저장소 선택 → **`Connect`**

5. 아래 설정 입력:

   | 항목 | 입력값 |
   |------|--------|
   | Name | uhh-registration |
   | Region | Singapore (Asia와 가장 가까움) |
   | Branch | main |
   | Runtime | Python 3 |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `gunicorn app:app` |
   | Instance Type | **Free** 선택 |

6. **`Create Web Service`** 클릭 → 자동 배포 시작 (2~3분 소요)
7. 배포 완료 후 상단에 표시되는 URL이 신청 페이지 주소입니다 ✅
   - 예시: `https://uhh-registration.onrender.com`

---

### 3단계 — 페이지 공유하기

위 URL을 카카오톡, 이메일, 문자로 공유하면 됩니다.

---

### 수정이 필요할 때 (날짜, 문구 변경 등)

1. GitHub 저장소 접속 → 수정할 파일 클릭
2. 우측 연필 아이콘(✏️) 클릭 → 내용 수정
3. **`Commit changes`** 클릭
4. Render가 자동으로 변경사항을 감지해 재배포해요 (1~2분)

---

### 알아두면 좋은 점

| 항목 | 내용 |
|------|------|
| 비용 | 완전 무료 (기간 제한 없음) |
| 슬립 모드 | 15분 이상 접속 없으면 슬립 진입 → 첫 접속 시 10~20초 로딩 |
| 슬립 해결책 | 신청 기간 중 주기적으로 접속하면 슬립 안 됨 |
| 데이터 보관 | 서버 재배포 후에도 신청 기록 유지됨 |
| 관리자 비밀번호 | 기본값 `6574` (변경 방법은 아래 참고) |

---

### 관리자 비밀번호 변경 방법 (선택사항)

Render 대시보드 → 해당 서비스 선택 → **`Environment`** 탭 → **`Add Environment Variable`**

| Key | Value |
|-----|-------|
| `ADMIN_PW` | 원하는 비밀번호 |

저장 후 자동 재배포됩니다.

---

### 파일 구조

```
uhh-registration/
├── app.py              ← Flask 서버 (API + DB 처리)
├── requirements.txt    ← Python 패키지 목록
├── README.md           ← 이 파일
└── templates/
    └── index.html      ← 신청 페이지 (화면)
```
