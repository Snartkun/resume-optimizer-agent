"""
FastAPI 主应用入口
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.routers import resume
from app.models import ErrorResponse

app = FastAPI(
    title="简历优化 Agent API",
    description="基于 LLM 的简历修改与优化服务",
    version="0.1.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(resume.router, prefix="/api/v1", tags=["resume"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="INTERNAL_ERROR",
            message="服务器内部错误",
            details={"detail": str(exc)}
        ).model_dump()
    )


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用简历优化 Agent API",
        "docs": "/docs",
        "version": "0.1.0"
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
