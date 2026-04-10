"""
Stock Price Tracker — fetch prices and send email alert
Run with: python scripts/fetch_and_alert.py --session open|close
"""

import os
import json
import argparse
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import yfinance as yf

# ── 관심 종목 설정 ──────────────────────────────────────────────────────────
# 한국 주식: 종목코드 + ".KS" (코스피) or ".KQ" (코스닥)
# 미국 주식: 그냥 티커 심볼
WATCHLIST = [
    {"ticker": "259960.KS", "name": "크래프톤"},
    {"ticker": "005930.KS", "name": "삼성전자"},
    {"ticker": "TSLA",      "name": "테슬라"},
    {"ticker": "NFLX",      "name": "넷플릭스"},
    {"ticker": "KO",        "name": "코카콜라"},
    {"ticker": "SPY",       "name": "S&P 500 ETF"},
]

DATA_FILE = Path(__file__).parent.parent / "docs" / "data.json"
# ───────────────────────────────────────────────────────────────────────────


def fetch_price(ticker: str) -> dict | None:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="35d")  # 1달치 여유있게
        if hist.empty:
            return None

        # 오늘 (또는 가장 최근 거래일) 종가
        current = float(hist["Close"].iloc[-1])

        # 전일
        prev_1d = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else None

        # 1주일 전 (5거래일)
        prev_1w = float(hist["Close"].iloc[-6]) if len(hist) >= 6 else None

        # 1개월 전 (약 21거래일)
        prev_1m = float(hist["Close"].iloc[-22]) if len(hist) >= 22 else None

        info = stock.info
        currency = info.get("currency", "USD")

        return {
            "ticker": ticker,
            "currency": currency,
            "current": current,
            "prev_1d": prev_1d,
            "prev_1w": prev_1w,
            "prev_1m": prev_1m,
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }
    except Exception as e:
        print(f"[ERROR] {ticker}: {e}")
        return None


def pct_change(current: float, prev: float | None) -> float | None:
    if prev is None or prev == 0:
        return None
    return (current - prev) / prev * 100


def fmt_price(price: float, currency: str) -> str:
    if currency == "KRW":
        return f"₩{price:,.0f}"
    return f"${price:,.2f}"


def fmt_pct(pct: float | None) -> tuple[str, str]:
    """Returns (text, color_hex)"""
    if pct is None:
        return "N/A", "#888888"
    sign = "+" if pct >= 0 else ""
    # 한국 관례: 오른 건 빨강, 내린 건 파랑
    color = "#E53935" if pct >= 0 else "#1565C0"
    return f"{sign}{pct:.2f}%", color


def build_email_html(stocks: list[dict], session: str, kst_now: str) -> str:
    session_label = "🔔 장 시작" if session == "open" else "🔕 장 마감"

    rows = ""
    for s in stocks:
        name = s["name"]
        data = s["data"]
        if data is None:
            rows += f"""
            <tr>
              <td style="padding:12px 8px;border-bottom:1px solid #f0f0f0;">
                <b>{name}</b><br><span style="color:#aaa;font-size:12px;">{s['ticker']}</span>
              </td>
              <td colspan="3" style="padding:12px 8px;color:#aaa;text-align:center;">데이터 없음</td>
            </tr>"""
            continue

        price_str = fmt_price(data["current"], data["currency"])
        d1t, d1c = fmt_pct(pct_change(data["current"], data["prev_1d"]))
        d7t, d7c = fmt_pct(pct_change(data["current"], data["prev_1w"]))
        d30t, d30c = fmt_pct(pct_change(data["current"], data["prev_1m"]))

        rows += f"""
        <tr>
          <td style="padding:14px 8px;border-bottom:1px solid #f0f0f0;vertical-align:top;">
            <div style="font-weight:600;font-size:15px;">{name}</div>
            <div style="color:#aaa;font-size:11px;margin-top:2px;">{s['ticker']}</div>
          </td>
          <td style="padding:14px 8px;border-bottom:1px solid #f0f0f0;text-align:right;vertical-align:top;">
            <div style="font-weight:700;font-size:16px;">{price_str}</div>
          </td>
          <td style="padding:14px 8px;border-bottom:1px solid #f0f0f0;text-align:center;vertical-align:top;">
            <div style="font-size:12px;color:#888;margin-bottom:4px;">전일</div>
            <div style="color:{d1c};font-weight:600;">{d1t}</div>
          </td>
          <td style="padding:14px 8px;border-bottom:1px solid #f0f0f0;text-align:center;vertical-align:top;">
            <div style="font-size:12px;color:#888;margin-bottom:4px;">1주일</div>
            <div style="color:{d7c};font-weight:600;">{d7t}</div>
          </td>
          <td style="padding:14px 8px;border-bottom:1px solid #f0f0f0;text-align:center;vertical-align:top;">
            <div style="font-size:12px;color:#888;margin-bottom:4px;">1개월</div>
            <div style="color:{d30c};font-weight:600;">{d30t}</div>
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:520px;margin:20px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    
    <div style="background:#111;padding:20px 24px;">
      <div style="color:#888;font-size:12px;letter-spacing:0.05em;text-transform:uppercase;">주식 트래커</div>
      <div style="color:#fff;font-size:20px;font-weight:700;margin-top:4px;">{session_label} 알림</div>
      <div style="color:#666;font-size:12px;margin-top:6px;">{kst_now} KST</div>
    </div>

    <div style="padding:8px 16px;">
      <table style="width:100%;border-collapse:collapse;">
        <thead>
          <tr style="background:#fafafa;">
            <th style="padding:8px;text-align:left;font-size:11px;color:#aaa;font-weight:500;border-bottom:2px solid #eee;">종목</th>
            <th style="padding:8px;text-align:right;font-size:11px;color:#aaa;font-weight:500;border-bottom:2px solid #eee;">현재가</th>
            <th style="padding:8px;text-align:center;font-size:11px;color:#aaa;font-weight:500;border-bottom:2px solid #eee;">전일比</th>
            <th style="padding:8px;text-align:center;font-size:11px;color:#aaa;font-weight:500;border-bottom:2px solid #eee;">1주일</th>
            <th style="padding:8px;text-align:center;font-size:11px;color:#aaa;font-weight:500;border-bottom:2px solid #eee;">1개월</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <div style="padding:16px 24px;border-top:1px solid #f0f0f0;text-align:center;">
      <a href="{os.environ.get('DASHBOARD_URL', '#')}" 
         style="display:inline-block;background:#111;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;font-size:13px;font-weight:600;">
        📊 대시보드 열기
      </a>
    </div>

    <div style="padding:12px 24px;background:#fafafa;text-align:center;color:#bbb;font-size:11px;">
      오른 건 빨강 🔴 · 내린 건 파랑 🔵
    </div>
  </div>
</body>
</html>"""


def send_email(subject: str, html_body: str):
    sender = os.environ["EMAIL_SENDER"]
    receiver = os.environ["EMAIL_RECEIVER"]
    password = os.environ["EMAIL_PASSWORD"]
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
    print(f"[OK] Email sent to {receiver}")


def save_data(stocks_data: list[dict]):
    """Save latest prices to docs/data.json for dashboard"""
    DATA_FILE.parent.mkdir(exist_ok=True)
    existing = {}
    if DATA_FILE.exists():
        try:
            existing = json.loads(DATA_FILE.read_text())
        except Exception:
            pass

    for s in stocks_data:
        if s["data"]:
            existing[s["ticker"]] = {
                "name": s["name"],
                **s["data"],
            }

    DATA_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
    print(f"[OK] data.json saved ({len(existing)} tickers)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", choices=["open", "close"], required=True)
    args = parser.parse_args()

    kst_now = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime("%Y-%m-%d %H:%M")

    print(f"[INFO] Fetching prices — session={args.session}, time={kst_now} KST")

    stocks_data = []
    for item in WATCHLIST:
        print(f"  → {item['ticker']} ({item['name']})")
        data = fetch_price(item["ticker"])
        stocks_data.append({"ticker": item["ticker"], "name": item["name"], "data": data})

    save_data(stocks_data)

    html = build_email_html(stocks_data, args.session, kst_now)
    session_label = "장 시작" if args.session == "open" else "장 마감"
    subject = f"[주식] {session_label} 알림 — {kst_now}"

    send_email(subject, html)


if __name__ == "__main__":
    main()
