"""验证: 导入一个题目后待复习应=1且仅含题卡(不含技巧卡); 删题后 by-slug 返回 None。
依赖后端 8000 活跃、当前库为空。"""
import sys, json, urllib.request

BASE = "http://localhost:8000/api/v1"
fails = []

def post(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def get(path):
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return json.loads(r.read())

# 导入一个题目(带1条技巧卡)
imp = {"slug": "two-sum", "title": "两数之和", "leetcode_link": "https://leetcode.cn/problems/two-sum/",
       "difficulty": "简单", "tags": ["数组"], "code": "def twoSum(self, n, t): pass", "language": "python3",
       "solutions": [{"name": "哈希表", "complexity_time": "O(n)", "complexity_space": "O(n)",
                      "breakthrough": "x", "pitfalls": "y", "is_optimal": True, "language": "python3", "variants": []}],
       "techniques": [{"name": "哈希表O(1)找元素", "summary": "用哈希表", "code_template": ""}]}
post("/import", imp)

# /reviews/today 应只含题卡, due=1
today = get("/reviews/today")["data"]
if today["due_count"] != 1:
    fails.append(f"导入后 due_count 应为1, 实际 {today['due_count']}")
types = [t["card_type"] for t in today["tasks"]]
if types != ["problem"]:
    fails.append(f"今日任务应仅含 problem 题卡, 实际 {types}")
if "tip" in types:
    fails.append("今日任务错误地包含技巧卡(tip)")

# by-slug 应找到该题
bs = get("/cards/by-slug/two-sum")
if not bs.get("data") or not bs["data"].get("card_id"):
    fails.append("导入后 by-slug 未找到题卡")

# 删除题卡 → by-slug 应返回 None
req = urllib.request.Request(BASE + "/problems/1", method="DELETE")
urllib.request.urlopen(req, timeout=10).read()
bs2 = get("/cards/by-slug/two-sum")
if bs2.get("data") is not None:
    fails.append("删除题卡后 by-slug 仍返回数据(应 None)")

# 删后待复习归零
today2 = get("/reviews/today")["data"]
if today2["due_count"] != 0:
    fails.append(f"删除题卡后 due_count 应为0, 实际 {today2['due_count']}")

if fails:
    print("FAIL:")
    for f in fails: print(" -", f)
    sys.exit(1)
print("PASS: 导入一题→待复习=1(仅题卡) / 删题→by-slug=None且待复习归零")
