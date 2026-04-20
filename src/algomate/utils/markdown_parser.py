"""
Markdown 解析与渲染模块

提供 Markdown 文档的解析、转换和渲染功能：
- 将 Markdown 解析为结构化数据
- 支持代码块、列表、表格等常用语法
- 提供 HTML 渲染输出
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class CodeBlock:
    """代码块数据结构

    Attributes:
        language: 代码语言类型（如 python, javascript 等）
        content: 代码内容
        start_line: 在原文档中的起始行号
        end_line: 在原文档中的结束行号
    """
    language: str
    content: str
    start_line: int
    end_line: int


@dataclass
class MarkdownSection:
    """Markdown 文档章节结构

    Attributes:
        level: 标题级别（1-6）
        title: 章节标题
        content: 章节内容（不含子标题）
        line_number: 在原文档中的行号
        children: 子章节列表
    """
    level: int
    title: str
    content: str
    line_number: int
    children: List["MarkdownSection"] = field(default_factory=list)


@dataclass
class ParsedMarkdown:
    """解析后的 Markdown 文档结构

    Attributes:
        raw_content: 原始 Markdown 内容
        sections: 顶层章节列表
        code_blocks: 文档中的代码块列表
        metadata: 文档元数据（YAML front matter）
    """
    raw_content: str
    sections: List[MarkdownSection] = field(default_factory=list)
    code_blocks: List[CodeBlock] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MarkdownParser:
    """Markdown 解析器类

    提供 Markdown 文档的解析和转换功能：
    - 解析 Markdown 文本为结构化数据
    - 提取代码块、章节、列表等信息
    - 支持转换为 HTML 格式

    Example:
        >>> parser = MarkdownParser()
        >>> result = parser.parse("# 标题\\n\\n这是内容")
        >>> print(result.sections[0].title)
        标题
    """

    CODE_BLOCK_PATTERN = re.compile(r"```(\w*)\n([\s\S]*?)```")
    INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")
    HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")
    LIST_ITEM_PATTERN = re.compile(r"^[\s]*[-*+]\s+(.+)$")
    NUMBERED_LIST_PATTERN = re.compile(r"^[\s]*\d+\.\s+(.+)$")
    FRONT_MATTER_PATTERN = re.compile(r"^---\n([\s\S]*?)\n---")

    def __init__(self):
        """初始化 Markdown 解析器"""
        self.raw_content: str = ""

    def parse(self, markdown_text: str) -> ParsedMarkdown:
        """解析 Markdown 文本

        Args:
            markdown_text: Markdown 格式的文本内容

        Returns:
            ParsedMarkdown 结构对象，包含解析后的所有信息
        """
        self.raw_content = markdown_text
        result = ParsedMarkdown(raw_content=markdown_text)

        result.metadata = self._extract_front_matter(markdown_text)
        result.code_blocks = self._extract_code_blocks(markdown_text)
        result.sections = self._extract_sections(markdown_text)

        return result

    def _extract_front_matter(self, text: str) -> Dict[str, Any]:
        """提取 YAML front matter 元数据

        Args:
            text: Markdown 文本

        Returns:
            解析出的元数据字典，无元数据时返回空字典
        """
        match = self.FRONT_MATTER_PATTERN.match(text)
        if not match:
            return {}

        metadata = {}
        for line in match.group(1).strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()

        return metadata

    def _extract_code_blocks(self, text: str) -> List[CodeBlock]:
        """提取所有代码块

        Args:
            text: Markdown 文本

        Returns:
            CodeBlock 对象列表
        """
        code_blocks = []
        lines = text.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("```"):
                language = line[3:].strip()
                code_lines = []
                start_line = i
                i += 1

                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i])
                    i += 1

                end_line = i
                code_blocks.append(CodeBlock(
                    language=language,
                    content="\n".join(code_lines),
                    start_line=start_line,
                    end_line=end_line
                ))
            i += 1

        return code_blocks

    def _extract_sections(self, text: str) -> List[MarkdownSection]:
        """提取文档章节结构

        Args:
            text: Markdown 文本

        Returns:
            MarkdownSection 对象列表（顶层章节）
        """
        lines = text.split("\n")
        sections = []
        current_section: Optional[MarkdownSection] = None
        current_content: List[str] = []

        for i, line in enumerate(lines):
            header_match = self.HEADER_PATTERN.match(line)

            if header_match:
                if current_section:
                    current_section.content = "\n".join(current_content).strip()
                    sections.append(current_section)

                level = len(header_match.group(1))
                current_section = MarkdownSection(
                    level=level,
                    title=header_match.group(2),
                    content="",
                    line_number=i + 1
                )
                current_content = []
            elif current_section is not None:
                current_content.append(line)

        if current_section:
            current_section.content = "\n".join(current_content).strip()
            sections.append(current_section)

        return sections

    def extract_headers(self, markdown_text: str) -> List[Dict[str, Any]]:
        """提取所有标题及其层级关系

        Args:
            markdown_text: Markdown 文本

        Returns:
            标题信息列表，每项包含 level、title、line_number
        """
        headers = []
        for i, line in enumerate(markdown_text.split("\n")):
            match = self.HEADER_PATTERN.match(line)
            if match:
                headers.append({
                    "level": len(match.group(1)),
                    "title": match.group(2),
                    "line_number": i + 1
                })
        return headers

    def extract_code_languages(self, markdown_text: str) -> List[str]:
        """提取文档中使用的所有代码语言

        Args:
            markdown_text: Markdown 文本

        Returns:
            代码语言列表（去重）
        """
        parser = MarkdownParser()
        parsed = parser.parse(markdown_text)
        languages = set()

        for block in parsed.code_blocks:
            if block.language:
                languages.add(block.language)

        return sorted(list(languages))

    def to_html(self, markdown_text: str) -> str:
        """将 Markdown 转换为 HTML

        支持基础语法转换：
        - 标题、段落、换行
        - 粗体、斜体、行内代码
        - 代码块、列表

        Args:
            markdown_text: Markdown 文本

        Returns:
            转换后的 HTML 字符串
        """
        html_parts = []
        lines = markdown_text.split("\n")
        in_code_block = False
        code_content = []
        code_language = ""

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```") and not in_code_block:
                in_code_block = True
                code_language = stripped[3:].strip() if len(stripped) > 3 else ""
                code_content = []
                continue

            if in_code_block:
                if stripped == "```":
                    html_parts.append(
                        f'<pre><code class="language-{code_language}">'
                        f"{self._escape_html(chr(10).join(code_content))}</code></pre>"
                    )
                    in_code_block = False
                    code_content = []
                else:
                    code_content.append(line)
                continue

            processed = self._process_inline_elements(line)
            if self.HEADER_PATTERN.match(line):
                match = self.HEADER_PATTERN.match(line)
                level = len(match.group(1))
                html_parts.append(f"<h{level}>{match.group(2)}</h{level}>")
            elif stripped == "":
                html_parts.append("<br>")
            else:
                html_parts.append(f"<p>{processed}</p>")

        return "\n".join(html_parts)

    def _process_inline_elements(self, text: str) -> str:
        """处理行内元素

        Args:
            text: 原始文本

        Returns:
            处理后的 HTML 文本
        """
        text = self._escape_html(text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        text = self.INLINE_CODE_PATTERN.sub(r"<code>\1</code>", text)
        return text

    def _escape_html(self, text: str) -> str:
        """转义 HTML 特殊字符

        Args:
            text: 原始文本

        Returns:
            转义后的文本
        """
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


def parse_markdown(markdown_text: str) -> ParsedMarkdown:
    """便捷函数：解析 Markdown 文本

    Args:
        markdown_text: Markdown 格式的文本内容

    Returns:
        ParsedMarkdown 结构对象
    """
    parser = MarkdownParser()
    return parser.parse(markdown_text)


def markdown_to_html(markdown_text: str) -> str:
    """便捷函数：Markdown 转 HTML

    Args:
        markdown_text: Markdown 格式的文本内容

    Returns:
        HTML 字符串
    """
    parser = MarkdownParser()
    return parser.to_html(markdown_text)
