"""
简历相关 API 路由
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

from app.models import (
    ResumeParseResponse,
    ResumeAnalyzeRequest,
    ResumeAnalyzeResponse,
    ResumeRewriteRequest,
    ResumeRewriteResponse,
    JobDescription,
)
from app.services.resume_service import ResumeService
from app.utils.document_parser import DocumentParser

router = APIRouter()
resume_service = ResumeService()


@router.post("/parse-resume", response_model=ResumeParseResponse)
async def parse_resume(
    file: UploadFile = File(..., description="简历文件 (PDF 或 Word)"),
):
    """
    解析上传的简历文件，提取文本内容

    支持的格式：PDF (.pdf), Word (.doc, .docx)
    """
    try:
        # 读取文件内容
        content = await file.read()

        # 根据文件类型解析
        if file.filename.endswith('.pdf'):
            parsed = await DocumentParser.parse_pdf(content)
        elif file.filename.endswith(('.doc', '.docx')):
            parsed = await DocumentParser.parse_word(content)
        else:
            raise HTTPException(
                status_code=400,
                detail="不支持的文件格式，请上传 PDF 或 Word 文件"
            )

        # 检查解析结果
        if not parsed or not parsed.full_text.strip():
            return ResumeParseResponse(
                success=False,
                message="简历解析失败：无法提取有效文本，请检查文件格式是否正确"
            )

        return ResumeParseResponse(
            success=True,
            message="解析成功",
            sections=parsed.sections,
            full_text=parsed.full_text
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")


@router.post("/analyze", response_model=ResumeAnalyzeResponse)
async def analyze_resume(request: ResumeAnalyzeRequest):
    """
    分析简历与职位描述的匹配度

    - 评估匹配度评分 (0-100)
    - 识别缺失的技能
    - 提供宏观修改建议
    """
    try:
        # 退化处理：如果没有提供 JD，使用通用优化模式
        if not request.job_description:
            feedback = await resume_service.analyze_without_jd(request.resume_text)
        else:
            feedback = await resume_service.analyze_with_jd(
                request.resume_text,
                request.job_description
            )

        return ResumeAnalyzeResponse(
            success=True,
            message="分析完成",
            feedback=feedback
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/rewrite-section", response_model=ResumeRewriteResponse)
async def rewrite_section(request: ResumeRewriteRequest):
    """
    使用 STAR 法则重写简历段落

    针对单条工作经历或项目经验，使用 STAR 法则优化，
    并自然融入 JD 关键词以提高 ATS 通过率。
    """
    try:
        result = await resume_service.rewrite_section(
            section_text=request.section_text,
            job_description=request.job_description,
            keywords=request.keywords
        )

        return ResumeRewriteResponse(
            success=True,
            message="重写完成",
            rewritten=result
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重写失败: {str(e)}")
