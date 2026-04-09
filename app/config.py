"""
应用配置
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""

    # 应用信息
    APP_NAME: str = "简历优化 Agent"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # API 配置
    API_PREFIX: str = "/api/v1"

    # LLM Provider 选择: "openai" | "deepseek"
    LLM_PROVIDER: str = "deepseek"

    # OpenAI API 配置
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o"

    # DeepSeek API 配置
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"  # 或 deepseek-reasoner

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-pro"

    # LLM 调用配置
    LLM_TIMEOUT: int = 30  # 秒
    LLM_MAX_RETRIES: int = 3
    LLM_TEMPERATURE: float = 0.7

    # 文件上传配置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = [".pdf", ".doc", ".docx"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
