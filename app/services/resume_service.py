"""
简历业务服务层
"""
from typing import Optional
from app.models import Feedback, RewrittenBulletPoint, JobDescription
from app.services.llm_service import LLMService


class ResumeService:
    """
    简历服务类 - 处理简历相关的核心业务逻辑
    """

    def __init__(self):
        self.llm_service = LLMService()

    async def analyze_with_jd(
        self,
        resume_text: str,
        job_description: JobDescription
    ) -> Feedback:
        """
        分析简历与职位描述的匹配度

        Args:
            resume_text: 解析后的简历全文
            job_description: 目标职位描述

        Returns:
            Feedback: 包含匹配度评分、缺失技能、优势和总体建议
        """
        return await self.llm_service.analyze_resume_with_jd(
            resume_text=resume_text,
            job_description=job_description
        )

    async def analyze_without_jd(
        self,
        resume_text: str
    ) -> Feedback:
        """
        通用简历分析（无 JD 时的退化处理）

        Args:
            resume_text: 解析后的简历全文

        Returns:
            Feedback: 基于简历方向的通用优化建议
        """
        return await self.llm_service.analyze_resume_without_jd(
            resume_text=resume_text
        )

    async def rewrite_section(
        self,
        section_text: str,
        job_description: JobDescription,
        keywords: Optional[list] = None
    ) -> RewrittenBulletPoint:
        """
        使用 STAR 法则重写简历段落

        Args:
            section_text: 需要重写的简历段落
            job_description: 目标职位描述
            keywords: 需要融入的额外关键词

        Returns:
            RewrittenBulletPoint: 包含原始文本、重写后文本和修改说明
        """
        # 如果没有提供额外关键词，从 JD 中提取
        if keywords is None:
            keywords = job_description.required_skills

        return await self.llm_service.rewrite_experience(
            section_text=section_text,
            job_description=job_description,
            keywords=keywords
        )
