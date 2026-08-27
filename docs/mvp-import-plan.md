# MVP 改造计划：LeetCode 一键导入

> 目标：消灭「LeetCode 做完 → 回系统手工建卡」的复制粘贴。
> 分工：系统自动抓题面/难度/标签/代码建卡；用户只补心得体会、技巧总结。
> 节奏：分阶段、逐项验证，避免一次性大改难以定位问题。

## 设计要点

- 抓取发生在**浏览器扩展**（运行在已登录的 LeetCode 会话里），后端无需 LeetCode token。
- 后端只新增一个 `POST /api/v1/import` 接口，复用现有 `problem_cards` / `solution_cards` / `technique_cards` 模型与 `solution_techniques` 关联。
- 去重键：题卡用 LeetCode `slug`；重复导入 = 追加一条新解法。
- 技巧卡：按 LeetCode topic tags 自动建空壳草稿并关联解法，内容由用户后补。

## 改造清单

### 阶段 0：数据模型与溯源字段（地基）
- [0.1] 核对现有模型字段 ✅（结论见下）
- [0.2] 给模型加溯源/去重字段
  - `ProblemCard.leetcode_slug`：去重键（唯一索引）
  - `SolutionCard.language`：编程语言
  - `leetcode_link` 已存在，复用为深链；不加 `source`

### 阶段 1：后端导入接口（curl 可验证，不依赖扩展）
- [1.1] 新增 `api/v1/import.py` 路由 + `ImportRequest` schema
- [1.2] 按 slug 去重建题卡（已存在 → 追加解法分支）
- [1.3] 建 `SolutionCard` 并关联题卡（写代码/语言，复杂度/思路留空）
- [1.4] 按 LeetCode tags 建 `TechniqueCard` 草稿（空壳）并关联解法
- [1.5] 返回建好的卡片 id 集合（curl 验证全链路）

### 阶段 2：浏览器扩展（抓取，挂 LeetCode）
- [2.1] 扩展骨架 + 注入浮窗按钮
- [2.2] 读题面/难度/标签（优先 GraphQL，DOM 兜底）
- [2.3] 读最新 AC 提交代码
- [2.4] 组装 payload POST 到 import 接口
- [2.5] 后端 CORS 放开扩展 origin
- [2.6] 导入结果反馈

### 阶段 3：用户体验收尾（MVP 闭环）
- [3.1] 导入后引导补写感受
- [3.2] 去重提示
- [3.3] 本地全链路联调

## 字段核对结论（[0.1]）

| 模型 | 已有相关字段 | 缺口 |
|------|------|------|
| `ProblemCard` | `title`, `difficulty`, `leetcode_link`, `tags`(JSON), `my_status` | 缺 `leetcode_slug` 去重键 |
| `SolutionCard` | `code`, `name`, `algorithm_type`, `time_complexity`, `approach`... | 缺 `language` 字段 |
| `TechniqueCard` | `name`, `category`, `review_interval`, `proficiency`... | 够用 |

## 验收标准（每阶段）

- 阶段 0：`docker compose` 重启后端后，新字段在 DB 生效（自动迁移），可新建带 slug 的题卡。
- 阶段 1：用 curl 发手写 JSON，完整走通「建题卡+解法+技巧草稿」，返回 id；同一 slug 第二次不重复建题卡。
- 阶段 2/3：扩展点击 → 后端建卡 → 用户只补心得。
