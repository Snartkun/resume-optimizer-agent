"""
文档解析工具 - 处理 PDF 和 Word 文档
"""
import io
import re
from typing import Optional
import fitz  # PyMuPDF

from app.models import ParsedResume, ResumeSection


class DocumentParser:
    """
    文档解析器 - 提取 PDF 和 Word 文档的文本内容

    依赖:
    - PyMuPDF (fitz) - 处理 PDF
    - python-docx - 处理 Word (后续实现)
    """

    # 简历常见段落标题的正则表达式模式（支持中英文）
    SECTION_PATTERNS = [
        # 基本信息
        r'(?:^|\n)\s*(?:基本信息|个人信息|Profile|Personal\s*Info|联系方式|Contact)\s*(?:[:：]|\n)',
        # 教育背景
        r'(?:^|\n)\s*(?:教育背景|教育经历|学历|Education|Academic)\s*(?:[:：]|\n)',
        # 工作经历
        r'(?:^|\n)\s*(?:工作经历|工作经验|工作背景|Work\s*Experience|Employment|职业经历|实习经历)\s*(?:[:：]|\n)',
        # 项目经验
        r'(?:^|\n)\s*(?:项目经验|项目经历|项目|Projects|Project\s*Experience)\s*(?:[:：]|\n)',
        # 技能
        r'(?:^|\n)\s*(?:技能|专业技能|职业技能|Skills|Technical\s*Skills|技能专长|擅长技能)\s*(?:[:：]|\n)',
        # 自我评价/总结
        r'(?:^|\n)\s*(?:自我评价|个人总结|Summary|About\s*Me|个人简介|自我介绍)\s*(?:[:：]|\n)',
        # 获奖/证书
        r'(?:^|\n)\s*(?:获奖情况|荣誉证书|证书|Awards|Certifications|资质证书)\s*(?:[:：]|\n)',
    ]

    @classmethod
    async def parse_pdf(cls, file_content: bytes) -> ParsedResume:
        """
        解析 PDF 文件

        Args:
            file_content: PDF 文件的二进制内容

        Returns:
            ParsedResume: 解析后的简历数据

        Raises:
            ValueError: PDF 加密或无法解析
            Exception: 其他解析错误
        """
        try:
            # 从内存打开 PDF
            doc = fitz.open(stream=file_content, filetype="pdf")

            # 检查是否加密
            if doc.is_encrypted:
                raise ValueError("PDF 文件已加密，请先解除密码保护后重新上传")

            # 提取所有页面的文本
            full_text_parts = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                full_text_parts.append(text)

            doc.close()

            # 合并所有页面文本
            raw_text = "\n".join(full_text_parts)

            # 清理文本
            cleaned_text = cls._clean_text(raw_text)

            # 检查是否为空（可能是扫描版 PDF）
            if not cleaned_text.strip():
                raise ValueError("无法从 PDF 中提取文本，可能是扫描版图片 PDF，请尝试使用 OCR 工具转换后上传")

            # 提取段落
            sections = cls._extract_sections(cleaned_text)

            return ParsedResume(
                full_text=cleaned_text,
                sections=sections
            )

        except fitz.FileDataError as e:
            raise ValueError(f"PDF 文件格式错误或已损坏: {str(e)}")
        except Exception as e:
            if "加密" in str(e) or "扫描版" in str(e):
                raise
            raise Exception(f"PDF 解析失败: {str(e)}")

    @classmethod
    async def parse_word(cls, file_content: bytes) -> ParsedResume:
        """
        解析 Word 文档 (.doc, .docx)

        TODO: 后续使用 python-docx 实现
        """
        raise NotImplementedError("Word 文档解析待实现，请暂时使用 PDF 格式")

    @classmethod
    def _clean_text(cls, text: str) -> str:
        """
        清理提取的文本

        - 统一换行符
        - 去除多余空格和空行
        - 去除页眉页脚中的页码
        - 修复断行问题
        """
        if not text:
            return ""

        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 去除页码（常见的页码模式：单独一行的数字、"Page X of Y" 等）
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)  # 单独的数字
        text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)

        # 去除多余空格（保留中文字符间的空格，去除英文单词间多余空格）
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # 去除行首尾空格
            line = line.strip()
            # 将多个连续空格替换为单个
            line = re.sub(r' +', ' ', line)
            if line:  # 保留非空行
                cleaned_lines.append(line)

        # 合并行：如果一行以标点结尾或下一行以大写字母/中文开头，保留换行
        # 否则可能是段落内换行，需要合并
        merged_lines = []
        for i, line in enumerate(cleaned_lines):
            if i == 0:
                merged_lines.append(line)
            else:
                prev_line = merged_lines[-1]
                # 如果前一行以标点结束，或当前行是标题模式，保留换行
                if (prev_line[-1] in '。！？.!?:：') or \
                   (len(line) <= 20 and re.match(r'^[\u4e00-\u9fa5]+[:：]', line)):  # 可能是标题
                    merged_lines.append(line)
                # 如果当前行以大写字母开头且前一行没有结束标点，可能是新段落
                elif line[0].isupper() and prev_line[-1] not in '。！？.!?；;':
                    merged_lines.append(line)
                else:
                    # 合并到前一行（段落内换行）
                    merged_lines[-1] = prev_line + line

        return '\n'.join(merged_lines)

    @classmethod
    def _extract_sections(cls, text: str) -> list[ResumeSection]:
        """
        从完整文本中提取简历段落

        使用正则表达式匹配常见简历段落标题，然后根据标题位置切分文本
        """
        sections = []

        # 找到所有标题的位置
        title_positions = []
        for pattern in cls.SECTION_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # 获取标题文本（去除冒号和空白）
                title_text = match.group().strip().strip(':：').strip()
                title_positions.append((match.start(), match.end(), title_text))

        # 按位置排序并去重（重叠的标题取最长的）
        title_positions.sort(key=lambda x: x[0])

        # 合并重叠的标题
        unique_positions = []
        for pos in title_positions:
            if not unique_positions:
                unique_positions.append(pos)
            else:
                last = unique_positions[-1]
                # 如果当前标题在上一个标题范围内，跳过
                if pos[0] < last[1]:
                    # 如果当前标题更长，替换上一个
                    if pos[1] - pos[0] > last[1] - last[0]:
                        unique_positions[-1] = pos
                else:
                    unique_positions.append(pos)

        # 如果没有识别出标题，返回整个文本作为一个段落
        if not unique_positions:
            sections.append(ResumeSection(
                section_name="全文",
                original_text=text.strip()
            ))
            return sections

        # 提取各段落内容
        for i, (start, end, title) in enumerate(unique_positions):
            # 确定段落结束位置
            if i < len(unique_positions) - 1:
                section_end = unique_positions[i + 1][0]
            else:
                section_end = len(text)

            # 提取段落内容（去除标题本身）
            content = text[end:section_end].strip()

            # 清理标题
            clean_title = cls._clean_section_title(title)

            if content:  # 只添加有内容的段落
                sections.append(ResumeSection(
                    section_name=clean_title,
                    original_text=content
                ))

        # 如果第一个标题之前有内容，作为"其他信息"段落
        if unique_positions and unique_positions[0][0] > 0:
            header_content = text[:unique_positions[0][0]].strip()
            if header_content:
                sections.insert(0, ResumeSection(
                    section_name="其他信息",
                    original_text=header_content
                ))

        return sections

    @classmethod
    def _clean_section_title(cls, title: str) -> str:
        """
        清理段落标题，统一命名
        """
        title_lower = title.lower()

        # 基本信息
        if any(kw in title_lower for kw in ['基本信息', '个人信息', 'profile', 'personal', 'contact', '联系方式']):
            return "基本信息"

        # 教育背景
        if any(kw in title_lower for kw in ['教育', '学历', 'education', 'academic']):
            return "教育背景"

        # 工作经历
        if any(kw in title_lower for kw in ['工作', '经验', 'employment', 'experience']) and 'project' not in title_lower:
            return "工作经历"

        # 项目经验
        if any(kw in title_lower for kw in ['项目', 'project']):
            return "项目经验"

        # 技能
        if any(kw in title_lower for kw in ['技能', 'skill', '擅长']):
            return "专业技能"

        # 自我评价
        if any(kw in title_lower for kw in ['自我评价', '总结', 'summary', 'about', '简介', '介绍']):
            return "自我评价"

        # 获奖/证书
        if any(kw in title_lower for kw in ['获奖', '证书', 'award', 'certification', '资质']):
            return "获奖证书"

        return title
