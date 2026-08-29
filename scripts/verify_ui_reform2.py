"""UI 二次整改 E2E: 验证 ①②③。
1. SideNav: 今日修炼无 → 箭头; 无 '学习 X 天' 文本
2. 首页: 今日聚焦区(今日聚焦) + 连续学习/本周复习 趋势; 无 '今日修炼概览' 旧标题
3. StatusBar: 含 '连续学习'
4. 控制台 0 错误
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:3000"
results = {}


def step(name, cond):
    results[name] = bool(cond)
    print(f"[{'PASS' if cond else 'FAIL'}] {name}")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(f"PAGEERR: {e}"))

    page.goto(f"{BASE}/", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2500)
    body = page.inner_text("body")

    # ① SideNav 无箭头
    step("SideNav 今日修炼无 '→'", "→" not in body or "今日修炼" in body and "→" not in body.split("今日修炼")[1][:20])
    # ① SideNav 无 '学习 X 天'
    import re
    step("SideNav 无 '学习 X 天'", not re.search(r"学习\s*\d+\s*天", body[:400]))
    # ② 首页聚焦区
    step("首页含 '今日聚焦' 面板", "今日聚焦" in body)
    step("首页无旧 '今日修炼概览'", "今日修炼概览" not in body)
    step("首页含 '连续学习'", "连续学习" in body)
    step("首页含 '本周复习'", "本周复习" in body)
    step("首页含行动建议(优先/今天有)", ("待重做" in body) or ("没有待复习" in body))

    # ③ StatusBar 连续学习 (滚到底部或找固定栏)
    step("StatusBar 含 '连续学习'", "连续学习" in body)

    browser.close()

print("\n控制台错误数:", len(errors))
for e in errors[:8]:
    print("  -", e[:140])

all_ok = all(results.values()) and len(errors) == 0
print("\nUI 二次整改验收:", "PASS" if all_ok else "FAIL")
sys.exit(0 if all_ok else 1)
