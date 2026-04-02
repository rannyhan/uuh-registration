# uuh-registration

## Render 환경 변수 설정 (필수!)

Render 대시보드 → 서비스 선택 → **Environment** 탭 → **Add Environment Variable**

| Key | Value |
|-----|-------|
| `SHEET_ID` | Google Sheets URL 중간의 ID (예: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms`) |
| `GOOGLE_CREDENTIALS` | JSON 키 파일 내용 전체를 한 줄로 붙여넣기 |
| `ADMIN_PW` | 관리자 비밀번호 (기본값: 6574) |

### GOOGLE_CREDENTIALS 입력 방법
1. JSON 키 파일을 메모장/텍스트편집기로 열기
2. 내용 전체 복사 (Ctrl+A → Ctrl+C)
3. Render 환경 변수 Value 칸에 붙여넣기

### SHEET_ID 찾는 방법
Google Sheets URL에서 /d/ 와 /edit 사이의 값
예: `https://docs.google.com/spreadsheets/d/[여기가SHEET_ID]/edit`

## 파일 구조
```
uuh-registration/
├── app.py
├── requirements.txt
├── README.md
└── templates/
    └── index.html
```

## Start Command (Render 설정)
```
gunicorn app:app
```
