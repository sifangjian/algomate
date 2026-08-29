"""模块 C E2E: 修炼页题卡任务卡渲染验证。
检查今日修炼中题卡任务是否显示「重做原题」标签 + 「去 LeetCode 重做」+「变体练习」按钮。
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:3000"


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"PAGEERR: {e}"))

        page.goto(f"{BASE}/review", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2500)

        body = page.inner_text("body")
        print("=== 页面可见文本(前600) ===")
        print(body[:600])

        # 题卡任务特征
        has_redo_tag = "重做原题" in body
        has_redo_btn = "去 LeetCode 重做" in body
        has_variant_btn = "变体练习" in body
        has_start_redo = "开始重做" in body
        print("\n=== 检查结果 ===")
        print("重做原题标签:", has_redo_tag)
        print("去 LeetCode 重做按钮:", has_redo_btn)
        print("变体练习按钮:", has_variant_btn)
        print("开始重做按钮:", has_start_redo)

        # 点击「开始重做」看是否出现 AC/卡住 自评
        if has_start_redo:
            try:
                page.get_by_text("开始重做", exact=True).first.click(timeout=5000)
                page.wait_for_timeout(800)
                body2 = page.inner_text("body")
                print("已 AC 按钮:", "已 AC" in body2)
                print("卡住了 按钮:", "卡住了" in body2)
            except Exception as e:
                print("点击开始重做失败:", e)

        browser.close()

    ok = has_redo_tag and has_redo_btn and has_variant_btn and has_start_redo
    print("\n模块C 前端渲染验收:", "PASS" if ok else "FAIL")
    if errors:
        print("控制台错误数:", len(errors))
        for e in errors[:5]:
            print("  -", e[:120])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
