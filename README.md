# 📈 주식 트래커

장타 투자자를 위한 자동 주식 가격 알림 + 모바일 대시보드

## 기능
- 📧 장 시작 / 장 마감 시 이메일 자동 발송
- 📊 모바일 최적화 웹 대시보드 (GitHub Pages)
- 비교 기준: **전일 / 1주일 전 / 1개월 전**
- 오른 건 🔴 빨강, 내린 건 🔵 파랑

## 알림 타이밍 (KST 기준)
| 이벤트 | 시간 |
|--------|------|
| 🇰🇷 한국 장 시작 | 09:00 |
| 🇰🇷 한국 장 마감 | 15:30 |
| 🇺🇸 미국 장 시작 | 22:30 (전날 밤) |
| 🇺🇸 미국 장 마감 | 06:00 (다음날 새벽) |

---

## 세팅 방법 (10분)

### 1. 레포지토리 생성
```
GitHub에서 새 public 레포 생성 → 이 파일들 업로드
```

### 2. 관심 종목 수정
`scripts/fetch_and_alert.py` 상단의 `WATCHLIST` 수정:
```python
WATCHLIST = [
    {"ticker": "005930.KS", "name": "삼성전자"},   # 코스피: 종목코드.KS
    {"ticker": "035720.KQ", "name": "카카오"},       # 코스닥: 종목코드.KQ
    {"ticker": "AAPL",      "name": "Apple"},        # 미국: 티커 그대로
]
```

### 3. GitHub Secrets 설정
레포 → Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 값 | 설명 |
|-------------|-----|------|
| `EMAIL_SENDER` | your@gmail.com | 발신 Gmail 주소 |
| `EMAIL_PASSWORD` | xxxx xxxx xxxx xxxx | Gmail 앱 비밀번호 ([발급 방법](https://myaccount.google.com/apppasswords)) |
| `EMAIL_RECEIVER` | your@gmail.com | 수신 이메일 |
| `DASHBOARD_URL` | https://your-id.github.io/repo-name | 대시보드 URL |

> ⚠️ Gmail 앱 비밀번호: Google 계정 → 보안 → 2단계 인증 활성화 → 앱 비밀번호 발급

### 4. GitHub Pages 활성화
레포 → Settings → Pages → Source: `Deploy from branch` → Branch: `main` / folder: `/docs`

### 5. GitHub Actions 권한 설정
레포 → Settings → Actions → General → Workflow permissions → **Read and write permissions** 체크

### 6. 테스트 실행
Actions 탭 → "Stock Price Alert" → Run workflow → session: `open`

---

## 파일 구조
```
stock-tracker/
├── .github/workflows/
│   └── stock-alert.yml      # 자동화 스케줄 (GitHub Actions)
├── scripts/
│   └── fetch_and_alert.py   # 주가 수집 + 이메일 발송
└── docs/
    ├── index.html           # 모바일 대시보드
    └── data.json            # 최신 주가 데이터 (자동 업데이트)
```

---

## 나중에 카카오 봇으로 업그레이드할 때
`scripts/fetch_and_alert.py`의 `send_email()` 함수를 카카오 API 호출로 교체하면 됩니다.
카카오 채널 개설 후 `KAKAO_ACCESS_TOKEN` secret 추가하는 방식으로 확장 가능해요.
