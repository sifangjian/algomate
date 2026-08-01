---
card_type: problem
---

## 题目名

LeetCode 3. 无重复字符的最长子串

## 一句话题干

给定字符串，求不含重复字符的最长连续子串长度

## 核心考点

`[[滑动窗口]]`、`[[哈希表]]`

## 解法思路

- ① 用哈希集维护窗口内字符
- ② 右指针移动时检查字符是否已在集中
- ③ 重复则移动左指针逐个移除，直到无重复
- ④ 每次更新 maxLen = max(maxLen, right - left + 1)

## 核心代码片段

```
while (right < n) {
    while (set.contains(s.charAt(right)))
        set.remove(s.charAt(left++));
    set.add(s.charAt(right));
    maxLen = Math.max(maxLen, right - left + 1);
    right++;
}
```

（仅保留核心逻辑，完整代码见 LeetCode）

## 复杂度

时间：O(n)  空间：O(min(n, m))，m 为字符集大小

## 关联技巧

`[[滑动窗口]]`

## 个人复盘

（非必填）