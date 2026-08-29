"""验证: ① 今日聚焦无统计数字(无'连续学习'/'本周复习'/'进入今日修炼'按钮) ② 点聚焦区跳/review
③ 今日修炼用 PanelSection 风格(today.review 标题) ④ 控制台 0 错误"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:3000"
fails = []

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append(str(e)))

    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_timeout(1200)

    # ① 今日聚焦区(focusCard)不应出现统计标记
    try:
        focus_txt = pg.inner_text("css=[class*='focusCard']")
    except Exception:
        focus_txt = ""
        fails.append("未找到 .focusCard 今日聚焦区")
    bad_markers = ["连续学习", "本周复习", "进入今日修炼", "天连续", "周复习进度"]
    for m in bad_markers:
        if m in focus_txt:
            fails.append(f"今日聚焦区仍含统计标记: {m}")
    if "今日" not in focus_txt and "复习" not in focus_txt:
        fails.append("今日聚焦区无建议文案")

    # ② 点聚焦区跳 /review
    try:
        pg.click("css=[class*='focusCard']", timeout=3000)
        pg.wait_for_timeout(1000)
        if "/review" not in pg.url:
            fails.append(f"点击聚焦区未跳转到 /review, 当前 url={pg.url}")
    except Exception as e:
        fails.append(f"点击聚焦区失败: {e}")

    # ③ 今日修炼页面渲染 PanelSection 风格
    rev = pg.inner_text("body")
    if "today.review" not in rev and "今日修炼" not in rev:
        fails.append("今日修炼页面未渲染 PanelSection 标题")

    b.close()

if errs:
    fails.append(f"控制台错误 {len(errs)} 条: {errs[:3]}")
if fails:
    print("FAIL:")
    for f in fails: print(" -", f)
    sys.exit(1)
print("PASS: 今日聚焦无统计+可跳转 / 今日修炼 PanelSection 风格 / 0 控制台错误")
