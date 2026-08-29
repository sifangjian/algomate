"""UI 整改综合 E2E: 验证 #A/#B/#C/#D 前端改动。
流程:
 1. 首页 / 显示「今日修炼概览」面板 + 三数卡片, 无 9项指标
 2. 点击「进入今日修炼」跳 /review
 3. /review 显示筛选 Tab(待复习/濒危/已完成) 与题卡任务卡(重做原题/去 LeetCode/变体练习)
 4. 题卡详情页 /card/problem/1 显示「管理」变体题按钮 -> 打开 Modal 可编辑 variants
 5. 控制台 0 错误
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

    # === 1. 首页 ===
    page.goto(f"{BASE}/", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2500)
    body = page.inner_text("body")
    step("首页含'今日修炼概览'", "今日修炼概览" in body)
    step("首页无'9 项指标'", "9 项指标" not in body)
    step("首页无'今日任务列表'", "今日任务列表" not in body)
    # 进入今日修炼按钮
    try:
        page.get_by_text("进入今日修炼", exact=False).first.click(timeout=5000)
        page.wait_for_timeout(1500)
    except Exception as e:
        print("点击进入今日修炼失败:", e)

    # === 2. /review 筛选 + 题卡卡 ===
    cur = page.url
    step("跳转到 /review", "/review" in cur)
    body = page.inner_text("body")
    step("/review 含筛选Tab'待复习'", "待复习" in body)
    step("/review 含'重做原题'标签", "重做原题" in body)
    step("/review 含'去 LeetCode 重做'", "去 LeetCode 重做" in body)
    step("/review 含'变体练习'", "变体练习" in body)

    # 点变体练习打开 Modal
    try:
        page.get_by_text("变体练习", exact=False).first.click(timeout=5000)
        page.wait_for_timeout(1000)
        body2 = page.inner_text("body")
        step("变体练习 Modal 打开(显示'完成练习'或'变体题练习')",
              ("变体题练习" in body2) or ("完成练习" in body2))
    except Exception as e:
        print("点击变体练习失败:", e)
        step("变体练习 Modal 打开", False)

    # === 3. 题卡详情页变体管理 ===
    page.goto(f"{BASE}/card/problem/1", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)
    body = page.inner_text("body")
    step("题卡详情含'同考点变体题'", "同考点变体题" in body)
    step("题卡详情含'管理'变体按钮", "管理" in body)
    try:
        page.get_by_text("管理", exact=False).first.click(timeout=5000)
        page.wait_for_timeout(800)
        body3 = page.inner_text("body")
        step("变体管理 Modal 打开(显示'管理变体题')", "管理变体题" in body3)
    except Exception as e:
        print("点击管理变体失败:", e)
        step("变体管理 Modal 打开", False)

    browser.close()

print("\n=== 控制台错误 ===")
print("错误数:", len(errors))
for e in errors[:8]:
    print("  -", e[:140])

all_ok = all(results.values()) and len(errors) == 0
print("\n综合前端验收:", "PASS" if all_ok else "FAIL")
sys.exit(0 if all_ok else 1)
