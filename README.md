# 简历优化 Agent (Resume-Optimizer-Agent)

基于 LLM 的简历修改与优化服务，使用 FastAPI + Pydantic 构建。

## 项目结构

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 应用配置
│   ├── models.py               # Pydantic 数据模型
│   ├── routers/
│   │   ├── __init__.py
│   │   └── resume.py           # 简历相关 API 路由
│   ├── services/
│   │   ├── __init__.py
│   │   ├── resume_service.py   # 简历业务逻辑
│   │   └── llm_service.py      # LLM 调用服务
│   └── utils/
│       ├── __init__.py
│       └── document_parser.py  # 文档解析工具
├── .env.example                # 环境变量示例
├── .gitignore
├── requirements.txt            # Python 依赖
└── README.md
```

## API 接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/parse-resume` | 解析上传的简历文件 |
| POST | `/api/v1/analyze` | 分析简历与 JD 匹配度 |
| POST | `/api/v1/rewrite-section` | 使用 STAR 法则重写段落 |

## 快速开始

1. 安装依赖:
```bash
pip install -r requirements.txt
```

2. 配置环境变量:
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Keys
```

3. 启动服务:
```bash
python -m app.main
```

4. 访问 API 文档:
```
http://localhost:8000/docs
```

## 数据模型

详见 [app/models.py](app/models.py)，包含以下核心模型:

- `JobDescription` - 职位描述
- `ResumeSection` - 简历段落
- `Feedback` - 诊断反馈
- `RewrittenBulletPoint` - 重写后的经历
