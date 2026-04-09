"""
Pydantic 数据模型定义
根据 spec.md 定义所有结构化数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class JobDescription(BaseModel):
    """职位描述数据模型"""
    title: str = Field(description="职位名称")
    required_skills: List[str] = Field(description="所需技能列表")
    core_responsibilities: List[str] = Field(description="核心职责列表")


class ResumeSection(BaseModel):
    """简历段落数据模型"""
    section_name: str = Field(description="段落名称，如：工作经历、教育背景、项目经验等")
    original_text: str = Field(description="原始文本内容")


class Feedback(BaseModel):
    """简历诊断反馈数据模型"""
    match_score: int = Field(ge=0, le=100, description="匹配度评分 (0-100)")
    missing_skills: List[str] = Field(description="缺失的技能列表")
    strengths: List[str] = Field(description="简历优势列表")
    general_advice: str = Field(description="总体修改建议")


class RewrittenBulletPoint(BaseModel):
    """重写后的经历数据模型"""
    original_bullet: str = Field(description="原始经历描述")
    rewritten_bullet: str = Field(description="使用 STAR 法则重写后的经历")
    explanation: str = Field(description="修改原因说明")


# ==================== API 请求/响应模型 ====================

class ResumeParseRequest(BaseModel):
    """简历解析请求（文件上传使用 FormData，这里仅作参考）"""
    pass


class ResumeParseResponse(BaseModel):
    """简历解析响应"""
    success: bool
    message: str
    sections: Optional[List[ResumeSection]] = None
    full_text: Optional[str] = None


class ResumeAnalyzeRequest(BaseModel):
    """简历分析请求"""
    resume_text: str = Field(description="解析后的简历全文")
    job_description: JobDescription = Field(description="目标职位描述")


class ResumeAnalyzeResponse(BaseModel):
    """简历分析响应"""
    success: bool
    message: str
    feedback: Optional[Feedback] = None


class ResumeRewriteRequest(BaseModel):
    """简历段落重写请求"""
    section_text: str = Field(description="需要重写的简历段落")
    job_description: JobDescription = Field(description="目标职位描述")
    keywords: Optional[List[str]] = Field(default=None, description="需要融入的关键词")


class ResumeRewriteResponse(BaseModel):
    """简历段落重写响应"""
    success: bool
    message: str
    rewritten: Optional[RewrittenBulletPoint] = None


# ==================== 内部数据模型 ====================

class ParsedResume(BaseModel):
    """解析后的完整简历数据模型"""
    full_text: str
    sections: List[ResumeSection]
    contact_info: Optional[dict] = None


class STARAnalysis(BaseModel):
    """STAR 法则分析结果"""
    situation: Optional[str] = Field(description="情境")
    task: Optional[str] = Field(description="任务")
    action: Optional[str] = Field(description="行动")
    result: Optional[str] = Field(description="结果")
    has_data_metrics: bool = Field(description="是否包含数据指标")


class ErrorResponse(BaseModel):
    """统一错误响应模型"""
    error_code: str
    message: str
    details: Optional[dict] = None
