"""
试炼生成器模块

提供智能出题功能，包括：
- 根据心得生成试炼
- 根据薄弱点生成针对性试炼
- 将生成结果持久化到数据库
"""

import re
from typing import List, Dict, Any, Optional
import random
from .chat_client import ChatClient
from algomate.models import Question
from ...data.database import Database
import json


LEETCODE_FALLBACK_MAP = {
    "数组与双指针": [
        {"title": "两数之和", "url": "https://leetcode.cn/problems/two-sum/", "difficulty": "easy", "description": "给定一个整数数组和一个目标值，找出数组中和为目标值的两个数"},
        {"title": "盛最多水的容器", "url": "https://leetcode.cn/problems/container-with-most-water/", "difficulty": "medium", "description": "使用双指针找到能盛最多水的容器"},
        {"title": "三数之和", "url": "https://leetcode.cn/problems/3sum/", "difficulty": "medium", "description": "找出数组中所有和为零的三元组"},
    ],
    "链表": [
        {"title": "反转链表", "url": "https://leetcode.cn/problems/reverse-linked-list/", "difficulty": "easy", "description": "反转一个单链表"},
        {"title": "合并两个有序链表", "url": "https://leetcode.cn/problems/merge-two-sorted-lists/", "difficulty": "easy", "description": "将两个升序链表合并为一个新的升序链表"},
        {"title": "两数相加", "url": "https://leetcode.cn/problems/add-two-numbers/", "difficulty": "medium", "description": "两个非空链表表示的数相加，返回表示和的链表"},
    ],
    "哈希表": [
        {"title": "两数之和", "url": "https://leetcode.cn/problems/two-sum/", "difficulty": "easy", "description": "使用哈希表高效查找目标值"},
        {"title": "有效的字母异位词", "url": "https://leetcode.cn/problems/valid-anagram/", "difficulty": "easy", "description": "判断两个字符串是否为字母异位词"},
        {"title": "字母异位词分组", "url": "https://leetcode.cn/problems/group-anagrams/", "difficulty": "medium", "description": "将字母异位词分组在一起"},
    ],
    "栈与队列": [
        {"title": "有效的括号", "url": "https://leetcode.cn/problems/valid-parentheses/", "difficulty": "easy", "description": "判断字符串中的括号是否有效匹配"},
        {"title": "用栈实现队列", "url": "https://leetcode.cn/problems/implement-queue-using-stacks/", "difficulty": "easy", "description": "使用栈实现队列的基本操作"},
        {"title": "最小栈", "url": "https://leetcode.cn/problems/min-stack/", "difficulty": "medium", "description": "设计一个支持在常数时间内获取最小元素的栈"},
    ],
    "二分查找": [
        {"title": "二分查找", "url": "https://leetcode.cn/problems/binary-search/", "difficulty": "easy", "description": "在有序数组中使用二分查找定位目标值"},
        {"title": "搜索插入位置", "url": "https://leetcode.cn/problems/search-insert-position/", "difficulty": "easy", "description": "在排序数组中查找目标值，若不存在则返回插入位置"},
        {"title": "在排序数组中查找元素的第一个和最后一个位置", "url": "https://leetcode.cn/problems/find-first-and-last-position-of-element-in-sorted-array/", "difficulty": "medium", "description": "在排序数组中查找目标值的起始和结束位置"},
    ],
    "前缀和": [
        {"title": "区域和检索-数组不可变", "url": "https://leetcode.cn/problems/range-sum-query-immutable/", "difficulty": "easy", "description": "使用前缀和高效计算数组区间和"},
        {"title": "二维区域和检索-矩阵不可变", "url": "https://leetcode.cn/problems/range-sum-query-2d-immutable/", "difficulty": "medium", "description": "使用二维前缀和高效计算矩阵区域和"},
        {"title": "和为K的子数组", "url": "https://leetcode.cn/problems/subarray-sum-equals-k/", "difficulty": "medium", "description": "使用前缀和与哈希表统计和为K的子数组个数"},
    ],
    "滑动窗口": [
        {"title": "无重复字符的最长子串", "url": "https://leetcode.cn/problems/longest-substring-without-repeating-characters/", "difficulty": "medium", "description": "使用滑动窗口找到不含重复字符的最长子串"},
        {"title": "长度最小的子数组", "url": "https://leetcode.cn/problems/minimum-size-subarray-sum/", "difficulty": "medium", "description": "使用滑动窗口找到和大于等于目标值的最短子数组"},
        {"title": "找到字符串中所有字母异位词", "url": "https://leetcode.cn/problems/find-all-anagrams-in-a-string/", "difficulty": "easy", "description": "使用滑动窗口找到字符串中所有字母异位词的起始索引"},
    ],
    "DFS": [
        {"title": "路径总和", "url": "https://leetcode.cn/problems/path-sum/", "difficulty": "easy", "description": "使用深度优先搜索判断二叉树中是否存在路径和等于目标值"},
        {"title": "岛屿数量", "url": "https://leetcode.cn/problems/number-of-islands/", "difficulty": "medium", "description": "使用深度优先搜索计算网格中岛屿的数量"},
        {"title": "全排列", "url": "https://leetcode.cn/problems/permutations/", "difficulty": "medium", "description": "使用深度优先搜索生成不含重复数字数组的全排列"},
    ],
    "BFS": [
        {"title": "二叉树的层序遍历", "url": "https://leetcode.cn/problems/binary-tree-level-order-traversal/", "difficulty": "medium", "description": "使用广度优先搜索逐层遍历二叉树"},
        {"title": "岛屿数量", "url": "https://leetcode.cn/problems/number-of-islands/", "difficulty": "medium", "description": "使用广度优先搜索计算网格中岛屿的数量"},
        {"title": "打开转盘锁", "url": "https://leetcode.cn/problems/open-the-lock/", "difficulty": "hard", "description": "使用广度优先搜索找到打开转盘锁的最少步数"},
    ],
    "拓扑排序": [
        {"title": "课程表", "url": "https://leetcode.cn/problems/course-schedule/", "difficulty": "medium", "description": "使用拓扑排序判断能否完成所有课程的学习"},
        {"title": "课程表II", "url": "https://leetcode.cn/problems/course-schedule-ii/", "difficulty": "medium", "description": "使用拓扑排序返回完成所有课程的学习顺序"},
        {"title": "单词接龙II", "url": "https://leetcode.cn/problems/word-ladder-ii/", "difficulty": "hard", "description": "找到所有从起始词到目标词的最短转换序列"},
    ],
    "二叉树遍历": [
        {"title": "二叉树的中序遍历", "url": "https://leetcode.cn/problems/binary-tree-inorder-traversal/", "difficulty": "easy", "description": "返回二叉树的中序遍历结果"},
        {"title": "二叉树的前序遍历", "url": "https://leetcode.cn/problems/binary-tree-preorder-traversal/", "difficulty": "easy", "description": "返回二叉树的前序遍历结果"},
        {"title": "二叉树的右视图", "url": "https://leetcode.cn/problems/binary-tree-right-side-view/", "difficulty": "medium", "description": "返回二叉树从右侧看去的节点值序列"},
    ],
    "二叉搜索树": [
        {"title": "二叉搜索树中的搜索", "url": "https://leetcode.cn/problems/search-in-a-binary-search-tree/", "difficulty": "easy", "description": "在二叉搜索树中查找指定值的节点"},
        {"title": "将有序数组转换为二叉搜索树", "url": "https://leetcode.cn/problems/convert-sorted-array-to-binary-search-tree/", "difficulty": "easy", "description": "将升序数组转换为高度平衡的二叉搜索树"},
        {"title": "验证二叉搜索树", "url": "https://leetcode.cn/problems/validate-binary-search-tree/", "difficulty": "medium", "description": "判断一个二叉树是否为有效的二叉搜索树"},
    ],
    "堆与优先队列": [
        {"title": "数组中的第K个最大元素", "url": "https://leetcode.cn/problems/kth-largest-element-in-an-array/", "difficulty": "medium", "description": "使用堆找到数组中第K大的元素"},
        {"title": "前K个高频元素", "url": "https://leetcode.cn/problems/top-k-frequent-elements/", "difficulty": "medium", "description": "使用优先队列找出数组中出现频率前K高的元素"},
        {"title": "数据流的中位数", "url": "https://leetcode.cn/problems/find-median-from-data-stream/", "difficulty": "hard", "description": "使用双堆高效获取数据流的中位数"},
    ],
    "图的遍历": [
        {"title": "克隆图", "url": "https://leetcode.cn/problems/clone-graph/", "difficulty": "medium", "description": "深度拷贝一个无向图"},
        {"title": "岛屿数量", "url": "https://leetcode.cn/problems/number-of-islands/", "difficulty": "medium", "description": "使用图的遍历计算网格中岛屿的数量"},
        {"title": "太平洋大西洋水流问题", "url": "https://leetcode.cn/problems/pacific-atlantic-water-flow/", "difficulty": "hard", "description": "找到水流既能流向太平洋又能流向大西洋的坐标"},
    ],
    "最短路径": [
        {"title": "网络延迟时间", "url": "https://leetcode.cn/problems/network-delay-time/", "difficulty": "medium", "description": "使用最短路径算法计算信号到达所有节点的最短时间"},
        {"title": "K站中转内最便宜的航班", "url": "https://leetcode.cn/problems/cheapest-flights-within-k-stops/", "difficulty": "medium", "description": "找到最多经过K站中转的最便宜航班价格"},
        {"title": "单词接龙", "url": "https://leetcode.cn/problems/word-ladder/", "difficulty": "hard", "description": "使用最短路径算法找到单词转换的最短路径"},
    ],
    "并查集": [
        {"title": "省份数量", "url": "https://leetcode.cn/problems/number-of-provinces/", "difficulty": "medium", "description": "使用并查集计算连通分量的数量"},
        {"title": "冗余连接", "url": "https://leetcode.cn/problems/redundant-connection/", "difficulty": "medium", "description": "使用并查集找到图中导致环路的冗余边"},
        {"title": "被围绕的区域", "url": "https://leetcode.cn/problems/surrounded-regions/", "difficulty": "hard", "description": "使用并查集标记不被围绕的区域"},
    ],
    "递归": [
        {"title": "爬楼梯", "url": "https://leetcode.cn/problems/climbing-stairs/", "difficulty": "easy", "description": "使用递归或动态规划计算爬楼梯的方法数"},
        {"title": "斐波那契数", "url": "https://leetcode.cn/problems/fibonacci-number/", "difficulty": "easy", "description": "使用递归计算斐波那契数列的第N项"},
        {"title": "杨辉三角", "url": "https://leetcode.cn/problems/pascals-triangle/", "difficulty": "medium", "description": "使用递归生成杨辉三角的前N行"},
    ],
    "回溯": [
        {"title": "全排列", "url": "https://leetcode.cn/problems/permutations/", "difficulty": "medium", "description": "使用回溯法生成不含重复数字数组的全排列"},
        {"title": "子集", "url": "https://leetcode.cn/problems/subsets/", "difficulty": "medium", "description": "使用回溯法生成数组所有可能的子集"},
        {"title": "N皇后", "url": "https://leetcode.cn/problems/n-queens/", "difficulty": "hard", "description": "使用回溯法求解N皇后问题"},
    ],
    "剪枝技巧": [
        {"title": "子集II", "url": "https://leetcode.cn/problems/subsets-ii/", "difficulty": "medium", "description": "使用剪枝技巧生成含重复元素数组的所有子集"},
        {"title": "组合总和II", "url": "https://leetcode.cn/problems/combination-sum-ii/", "difficulty": "medium", "description": "使用剪枝技巧找出数组中所有和为目标值的组合"},
        {"title": "括号生成", "url": "https://leetcode.cn/problems/generate-parentheses/", "difficulty": "hard", "description": "使用剪枝技巧生成所有有效的括号组合"},
    ],
    "组合与排列": [
        {"title": "组合总和", "url": "https://leetcode.cn/problems/combination-sum/", "difficulty": "medium", "description": "找出候选数组中所有和为目标值的组合"},
        {"title": "全排列", "url": "https://leetcode.cn/problems/permutations/", "difficulty": "medium", "description": "生成不含重复数字数组的全排列"},
        {"title": "全排列II", "url": "https://leetcode.cn/problems/permutations-ii/", "difficulty": "hard", "description": "生成含重复数字数组的全排列"},
    ],
    "贪心选择": [
        {"title": "分发饼干", "url": "https://leetcode.cn/problems/assign-cookies/", "difficulty": "easy", "description": "使用贪心策略满足尽可能多的孩子"},
        {"title": "跳跃游戏", "url": "https://leetcode.cn/problems/jump-game/", "difficulty": "medium", "description": "使用贪心策略判断能否到达数组末尾"},
        {"title": "加油站", "url": "https://leetcode.cn/problems/gas-station/", "difficulty": "medium", "description": "使用贪心策略找到可以绕环路行驶一周的起始加油站"},
    ],
    "区间问题": [
        {"title": "合并区间", "url": "https://leetcode.cn/problems/merge-intervals/", "difficulty": "medium", "description": "合并所有重叠的区间"},
        {"title": "插入区间", "url": "https://leetcode.cn/problems/insert-interval/", "difficulty": "medium", "description": "将新区间插入到有序区间列表中并合并重叠区间"},
        {"title": "用最少数量的箭引爆气球", "url": "https://leetcode.cn/problems/minimum-number-of-arrows-to-burst-balloons/", "difficulty": "hard", "description": "使用贪心策略计算引爆所有气球所需的最少箭数"},
    ],
    "构造策略": [
        {"title": "旋转图像", "url": "https://leetcode.cn/problems/rotate-image/", "difficulty": "easy", "description": "将N×N矩阵顺时针旋转90度"},
        {"title": "螺旋矩阵", "url": "https://leetcode.cn/problems/spiral-matrix/", "difficulty": "medium", "description": "按螺旋顺序返回矩阵的所有元素"},
        {"title": "生命游戏", "url": "https://leetcode.cn/problems/game-of-life/", "difficulty": "medium", "description": "根据规则在原地更新生命游戏的下一状态"},
    ],
    "线性DP": [
        {"title": "爬楼梯", "url": "https://leetcode.cn/problems/climbing-stairs/", "difficulty": "easy", "description": "使用动态规划计算爬楼梯的方法数"},
        {"title": "最长递增子序列", "url": "https://leetcode.cn/problems/longest-increasing-subsequence/", "difficulty": "medium", "description": "使用动态规划找到数组中最长递增子序列的长度"},
        {"title": "打家劫舍", "url": "https://leetcode.cn/problems/house-robber/", "difficulty": "medium", "description": "使用动态规划计算一夜内能偷窃的最高金额"},
    ],
    "背包问题": [
        {"title": "分割等和子集", "url": "https://leetcode.cn/problems/partition-equal-subset-sum/", "difficulty": "medium", "description": "使用0-1背包判断数组能否分割成两个和相等的子集"},
        {"title": "目标和", "url": "https://leetcode.cn/problems/target-sum/", "difficulty": "medium", "description": "使用背包思想计算通过加减运算得到目标值的方法数"},
        {"title": "零钱兑换", "url": "https://leetcode.cn/problems/coin-change/", "difficulty": "hard", "description": "使用完全背包计算凑成总金额所需的最少硬币数"},
    ],
    "子序列DP": [
        {"title": "最长递增子序列", "url": "https://leetcode.cn/problems/longest-increasing-subsequence/", "difficulty": "medium", "description": "使用动态规划找到数组中最长递增子序列的长度"},
        {"title": "最长公共子序列", "url": "https://leetcode.cn/problems/longest-common-subsequence/", "difficulty": "medium", "description": "使用动态规划找到两个字符串的最长公共子序列长度"},
        {"title": "编辑距离", "url": "https://leetcode.cn/problems/edit-distance/", "difficulty": "hard", "description": "使用动态规划计算将一个字符串转换为另一个的最少操作数"},
    ],
    "分治思想": [
        {"title": "多数元素", "url": "https://leetcode.cn/problems/majority-element/", "difficulty": "easy", "description": "使用分治法或投票算法找到数组中的多数元素"},
        {"title": "排序数组", "url": "https://leetcode.cn/problems/sort-an-array/", "difficulty": "medium", "description": "使用分治法（归并排序）对数组排序"},
        {"title": "搜索二维矩阵II", "url": "https://leetcode.cn/problems/search-a-2d-matrix-ii/", "difficulty": "medium", "description": "使用分治策略在有序矩阵中高效搜索目标值"},
    ],
    "排序算法": [
        {"title": "颜色分类", "url": "https://leetcode.cn/problems/sort-colors/", "difficulty": "easy", "description": "使用排序算法对包含0、1、2的数组进行原地排序"},
        {"title": "排序数组", "url": "https://leetcode.cn/problems/sort-an-array/", "difficulty": "medium", "description": "实现一个排序算法对数组排序"},
        {"title": "数组中的第K个最大元素", "url": "https://leetcode.cn/problems/kth-largest-element-in-an-array/", "difficulty": "medium", "description": "使用快速排序的划分思想找到第K大的元素"},
    ],
    "单调栈": [
        {"title": "下一个更大元素I", "url": "https://leetcode.cn/problems/next-greater-element-i/", "difficulty": "easy", "description": "使用单调栈找到每个元素的下一个更大元素"},
        {"title": "每日温度", "url": "https://leetcode.cn/problems/daily-temperatures/", "difficulty": "medium", "description": "使用单调栈计算需要等待多少天才能迎来更暖和的温度"},
        {"title": "柱状图中最大的矩形", "url": "https://leetcode.cn/problems/largest-rectangle-in-histogram/", "difficulty": "hard", "description": "使用单调栈找到柱状图中能勾勒出的最大矩形面积"},
    ],
    "单调队列": [
        {"title": "绝对差不超过限制的最长连续子数组", "url": "https://leetcode.cn/problems/longest-continuous-subarray-with-absolute-diff-less-than-or-equal-to-limit/", "difficulty": "medium", "description": "使用单调队列找到满足绝对差限制的最长子数组"},
        {"title": "滑动窗口最大值", "url": "https://leetcode.cn/problems/sliding-window-maximum/", "difficulty": "hard", "description": "使用单调队列高效获取滑动窗口中的最大值"},
        {"title": "滑动窗口中位数", "url": "https://leetcode.cn/problems/sliding-window-median/", "difficulty": "hard", "description": "使用双优先队列高效获取滑动窗口中的中位数"},
    ],
    "位运算": [
        {"title": "只出现一次的数字", "url": "https://leetcode.cn/problems/single-number/", "difficulty": "easy", "description": "使用异或运算找到数组中只出现一次的数字"},
        {"title": "汉明距离", "url": "https://leetcode.cn/problems/hamming-distance/", "difficulty": "easy", "description": "使用位运算计算两个整数的汉明距离"},
        {"title": "两个整数之和", "url": "https://leetcode.cn/problems/sum-of-two-integers/", "difficulty": "medium", "description": "使用位运算实现两数相加而不使用加号"},
    ],
    "数学技巧": [
        {"title": "回文数", "url": "https://leetcode.cn/problems/palindrome-number/", "difficulty": "easy", "description": "判断一个整数是否为回文数"},
        {"title": "整数反转", "url": "https://leetcode.cn/problems/reverse-integer/", "difficulty": "easy", "description": "将一个32位有符号整数反转"},
        {"title": "快乐数", "url": "https://leetcode.cn/problems/happy-number/", "difficulty": "medium", "description": "判断一个数是否为快乐数"},
    ],
    "字符串算法": [
        {"title": "实现 strStr()", "url": "https://leetcode.cn/problems/implement-strstr/", "difficulty": "easy", "description": "在字符串中查找子串的首次出现位置"},
        {"title": "最长回文子串", "url": "https://leetcode.cn/problems/longest-palindromic-substring/", "difficulty": "medium", "description": "使用中心扩展或Manacher算法找到最长回文子串"},
        {"title": "无重复字符的最长子串", "url": "https://leetcode.cn/problems/longest-substring-without-repeating-characters/", "difficulty": "medium", "description": "使用滑动窗口找到不含重复字符的最长子串"},
    ],
}


class QuestionGenerator:
    """试炼生成器

    负责根据心得内容和薄弱点生成试炼。

    Attributes:
        chat_client: AI 对话客户端实例
        QUESTION_TYPES: 支持的试炼类型列表
    """

    QUESTION_TYPES = ["选择题", "简答题", "LeetCode挑战"]

    def __init__(self, chat_client: Optional[ChatClient] = None):
        self._chat_client = chat_client

    @property
    def chat_client(self) -> ChatClient:
        if self._chat_client is None:
            from algomate.config.settings import AppConfig
            config = AppConfig.load()
            self._chat_client = ChatClient(api_key=config.LLM_API_KEY)
        return self._chat_client

    def generate_for_note(
        self, note_content: str, count: int = 3
    ) -> List[Dict[str, Any]]:
        """根据心得生成试炼

        随机选择试炼类型，调用 AI 生成试炼。

        Args:
            note_content: 心得内容
            count: 生成试炼数量

        Returns:
            试炼列表
        """
        selected_types = random.sample(self.QUESTION_TYPES, min(3, count))
        result = self.chat_client.generate_questions(note_content, selected_types, count)
        return self._convert_questions_to_dict(result)

    def generate_multiple_choice(
        self,
        note_content: str,
        difficulty: str = "中等",
        count: int = 1,
    ) -> List[Dict[str, Any]]:
        """生成选择题

        根据心得内容生成高质量的选择题，包含4个选项。

        Args:
            note_content: 心得内容
            difficulty: 难度等级（简单/中等/困难）
            count: 生成试炼数量

        Returns:
            选择题列表，每道题包含选项
        """
        questions = []
        for _ in range(count):
            prompt = f"""根据以下算法心得，生成一道高质量的选择题：

{note_content}

要求：
- 难度：{difficulty}
- 必须有4个选项（A、B、C、D）
- 只有一个正确答案
- 选项要有一定的干扰性

请返回JSON格式：
{{
    "question_type": "选择题",
    "content": "试炼内容（包含选项A、B、C、D）",
    "answer": "正确答案（如：A）",
    "explanation": "解析"
}}"""
            messages = [{"role": "user", "content": prompt}]
            result = self.chat_client.chat(messages)
            parsed = self._parse_json_response(result)
            if parsed and "question_type" in parsed:
                parsed["options"] = self._extract_options(parsed.get("content", ""))
                questions.append(parsed)
        return questions

    def generate_short_answer(
        self,
        note_content: str,
        difficulty: str = "中等",
        count: int = 1,
    ) -> List[Dict[str, Any]]:
        """生成简答题

        根据心得内容生成简答题，考查对概念和原理的理解。

        Args:
            note_content: 心得内容
            difficulty: 难度等级（简单/中等/困难）
            count: 生成试炼数量

        Returns:
            简答题列表
        """
        questions = []
        for _ in range(count):
            prompt = f"""根据以下算法心得，生成一道高质量的简答题：

{note_content}

要求：
- 难度：{difficulty}
- 考查对算法概念、原理的理解
- 答案应该简洁但完整

请返回JSON格式：
{{
    "question_type": "简答题",
    "content": "试炼内容",
    "answer": "参考答案要点",
    "explanation": "解析"
}}"""
            messages = [{"role": "user", "content": prompt}]
            result = self.chat_client.chat(messages)
            parsed = self._parse_json_response(result)
            if parsed and "question_type" in parsed:
                questions.append(parsed)
        return questions

    def generate_leetcode_challenge(
        self,
        note_content: str,
        difficulty: str = "medium",
        algorithm_type: str = "",
        completed_urls: list = None,
    ) -> Dict[str, Any]:
        """生成 LeetCode 挑战题

        先尝试用 AI 推荐一道 LeetCode 题目，若 AI 推荐失败或返回无效数据，
        则从 LEETCODE_FALLBACK_MAP 中查找匹配条目（先精确匹配 algorithm_type，
        再模糊匹配 note_content 中的关键词），若映射表也未找到则使用默认的"两数之和"。

        Args:
            note_content: 心得内容，用于 AI 推荐及模糊匹配回退
            difficulty: 难度等级（easy/medium/hard）
            algorithm_type: 算法类型，用于精确匹配回退
            completed_urls: 已完成的题目URL列表，用于避免重复推荐

        Returns:
            包含 LeetCode 题目信息的字典，格式为：
            {
                "question_type": "LeetCode挑战",
                "content": 描述,
                "leetcode_title": 标题,
                "leetcode_url": URL,
                "leetcode_difficulty": 难度,
                "leetcode_description": 描述,
                "answer": "self_report",
                "explanation": ""
            }
        """
        if completed_urls is None:
            completed_urls = []

        prompt = f"""根据以下算法心得，推荐一道合适的LeetCode题目。

心得内容：
{note_content}

算法类型：{algorithm_type or '自动识别'}
难度：{difficulty}

要求：
- 题目必须与心得内容紧密相关
- 提供LeetCode中文站链接

请返回JSON格式：
{{
    "title": "LeetCode题目标题",
    "url": "https://leetcode.cn/problems/xxx/",
    "difficulty": "easy/medium/hard",
    "description": "题目描述摘要"
}}"""
        messages = [{"role": "user", "content": prompt}]
        try:
            result = self.chat_client.chat(messages)
            parsed = self._parse_json_response(result)
            if parsed and parsed.get("title") and parsed.get("url"):
                if parsed["url"] not in completed_urls:
                    return {
                        "question_type": "LeetCode挑战",
                        "content": parsed.get("description", ""),
                        "leetcode_title": parsed["title"],
                        "leetcode_url": parsed["url"],
                        "leetcode_difficulty": parsed.get("difficulty", difficulty),
                        "leetcode_description": parsed.get("description", ""),
                        "answer": "self_report",
                        "explanation": "",
                    }
        except Exception:
            pass

        return self._get_leetcode_fallback(note_content, algorithm_type, completed_urls, difficulty)

    def _get_leetcode_fallback(
        self, note_content: str, algorithm_type: str = "",
        completed_urls: list = None, difficulty: str = ""
    ) -> Dict[str, Any]:
        """从回退映射表中获取 LeetCode 题目

        查找策略：
        1. 精确匹配 algorithm_type
        2. 模糊匹配 note_content 中包含的映射表关键词
        3. 若均未命中，使用默认的"数组与双指针"类型

        在匹配到的题目列表中：
        - 过滤掉 completed_urls 中的题目
        - 若指定了 difficulty，优先选择匹配难度的题目
        - 若所有题目均被过滤，则从该类型全部题目中随机选择

        Args:
            note_content: 心得内容，用于模糊匹配映射表中的算法类型关键词
            algorithm_type: 算法类型，用于精确匹配
            completed_urls: 已完成的题目URL列表
            difficulty: 优先选择的难度等级（easy/medium/hard）

        Returns:
            包含 LeetCode 题目信息的标准字典
        """
        if completed_urls is None:
            completed_urls = []

        problems = None

        if algorithm_type and algorithm_type in LEETCODE_FALLBACK_MAP:
            problems = LEETCODE_FALLBACK_MAP[algorithm_type]

        if problems is None and note_content:
            for key, val in LEETCODE_FALLBACK_MAP.items():
                if key in note_content:
                    problems = val
                    break

        if problems is None:
            problems = LEETCODE_FALLBACK_MAP.get(
                "数组与双指针",
                [
                    {
                        "title": "两数之和",
                        "url": "https://leetcode.cn/problems/two-sum/",
                        "difficulty": "easy",
                        "description": "给定一个整数数组和一个目标值，找出数组中和为目标值的两个数",
                    },
                ],
            )

        available = [p for p in problems if p["url"] not in completed_urls]

        if not available:
            available = list(problems)

        if difficulty:
            matched = [p for p in available if p["difficulty"] == difficulty]
            if matched:
                available = matched

        fb = random.choice(available)

        return {
            "question_type": "LeetCode挑战",
            "content": fb.get("description", ""),
            "leetcode_title": fb["title"],
            "leetcode_url": fb["url"],
            "leetcode_difficulty": fb["difficulty"],
            "leetcode_description": fb.get("description", ""),
            "answer": "self_report",
            "explanation": "",
        }

    def generate_weak_point_questions(
        self,
        weak_topics: List[Dict[str, Any]],
        count: int = 5,
        question_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """根据薄弱点生成试炼

        针对用户薄弱秘术生成专项试炼。

        Args:
            weak_topics: 薄弱秘术列表，每个元素包含 name（秘术名称）
            count: 生成试炼数量
            question_types: 试炼类型列表，默认包含选择题和简答题

        Returns:
            试炼列表
        """
        if question_types is None:
            question_types = ["选择题", "简答题"]

        questions = []
        types_to_generate = question_types * (count // len(question_types) + 1)

        for i, topic in enumerate(weak_topics[:count]):
            question_type = types_to_generate[i]
            prompt = self._build_weak_point_prompt(topic, question_type)
            messages = [{"role": "user", "content": prompt}]
            result = self.chat_client.chat(messages)
            parsed = self._parse_json_response(result)
            if parsed and "question_type" in parsed:
                questions.append(parsed)

        return questions

    def _build_weak_point_prompt(
        self,
        topic: Dict[str, Any],
        question_type: str,
    ) -> str:
        """构建薄弱点试炼的提示词

        Args:
            topic: 薄弱秘术字典
            question_type: 试炼类型

        Returns:
            格式化的提示词
        """
        topic_name = topic.get("name", "")
        topic_context = topic.get("context", "")
        difficulty = topic.get("difficulty", "中等")

        base_prompt = f"""针对"{topic_name}"这个薄弱秘术，生成一道高质量试炼。

知识背景：{topic_context}
难度：{difficulty}
试炼类型：{question_type}

"""

        if question_type == "选择题":
            base_prompt += """要求：
- 必须有4个选项（A、B、C、D）
- 只有一个正确答案
- 选项要有一定的干扰性

请返回JSON格式：
{
    "question_type": "选择题",
    "content": "试炼内容（包含选项）",
    "answer": "正确答案",
    "explanation": "解析"
}"""
        elif question_type == "简答题":
            base_prompt += """要求：
- 考查对概念、原理的理解
- 答案应该简洁但完整

请返回JSON格式：
{
    "question_type": "简答题",
    "content": "试炼内容",
    "answer": "参考答案要点",
    "explanation": "解析"
}"""
        elif question_type == "LeetCode挑战":
            base_prompt += """要求：
- 推荐一道LeetCode题目
- 提供LeetCode中文站链接

请返回JSON格式：
{
    "question_type": "LeetCode挑战",
    "content": "题目描述摘要",
    "answer": "解题思路要点",
    "explanation": "算法思路分析",
    "leetcode_url": "https://leetcode.cn/problems/xxx/",
    "leetcode_title": "LeetCode题目标题",
    "leetcode_difficulty": "Easy/Medium/Hard"
}"""

        return base_prompt

    def _extract_options(self, content: str) -> List[str]:
        options = {}
        option_pattern = r'([A-D])[.、]\s*([^\n]+)'
        matches = re.findall(option_pattern, content)
        for letter, text in matches:
            options[letter] = text.strip()
        return [options[k] for k in sorted(options.keys())]

    def _convert_questions_to_dict(
        self,
        questions: List[Any],
    ) -> List[Dict[str, Any]]:
        """将 Question 对象列表转换为字典列表

        Args:
            questions: Question 对象列表

        Returns:
            字典列表
        """
        result = []
        for q in questions:
            if hasattr(q, "__dict__"):
                result.append(q.__dict__)
            elif isinstance(q, dict):
                result.append(q)
        return result

    def create_questions_from_result(
        self, card_id: int, result: List[Dict[str, Any]], db: Database
    ) -> List[Question]:
        """将生成结果保存到数据库

        Args:
            card_id: 关联的卡牌 ID
            result: 生成的试炼列表
            db: 数据库实例

        Returns:
            创建的试炼对象列表
        """
        session = db.get_session()
        created_questions = []
        try:
            for item in result:
                question = Question(
                    card_id=card_id,
                    question_type=item.get("question_type", "简答题"),
                    content=item.get("content", ""),
                    answer=item.get("answer", ""),
                    explanation=item.get("explanation", ""),
                )
                session.add(question)
                created_questions.append(question)
            session.commit()
            for q in created_questions:
                session.refresh(q)
            return created_questions
        finally:
            session.close()

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析 JSON 响应

        Args:
            response: 模型返回的文本

        Returns:
            解析后的字典对象
        """
        json_match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", response)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                if isinstance(parsed, list):
                    if parsed:
                        return parsed[0]
                elif isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
        return {}
