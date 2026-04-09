# 简历优化 Agent (Resume-Optimizer-Agent) 架构与需求规范

## 1. 项目概述 (Project Overview)
本项目旨在开发一个基于 LLM 的“简历修改与优化 Agent”。该 Agent 将扮演资深 HR 和职业规划师的角色，通过分析用户的原始简历和目标岗位的职位描述（Job Description, JD），提供打分、诊断反馈，并按需重写简历内容（例如使用 STAR 法则优化工作经历）。

## 2. 技术栈建议 (Tech Stack)
* **后端:** Python (FastAPI)
* **Agent 框架:** LangChain 或直接调用 OpenAI / Gemini API (搭配 Pydantic 进行结构化输出)
* **文档解析:** `pdfplumber` 或 `PyMuPDF` (处理 PDF), `python-docx` (处理 Word)
* **前端:** 简单的 Streamlit 或 React (非核心部分，视具体实现定)

## 3. 核心业务流程 (User Flow)
1.  **输入阶段:** 用户上传原始简历文件（PDF/Word）并粘贴目标岗位的 JD。
2.  **解析阶段:** 系统提取简历纯文本，并将其结构化（基本信息、教育背景、工作经历、项目经验、技能）。
3.  **匹配与分析阶段 (Agent 工作):** Agent 对比简历与 JD，找出技能差距 (Skill Gap)，评估匹配度。
4.  **修改建议阶段 (Agent 工作):** Agent 针对每一条工作经历提出具体的修改建议。
5.  **内容重写阶段 (Agent 工作):** Agent 使用 STAR 法则（情境、任务、行动、结果）对不够充实的经历进行深度润色和重写。
6.  **输出阶段:** 将优化前后的对比结果和修改建议返回给用户。

## 4. 数据模型设计 (Data Models - Pydantic)
在生成代码时，请严格按照以下结构化数据进行 LLM 的输出约束 (Structured Output)：

```python
from pydantic import BaseModel
from typing import List

class JobDescription(BaseModel):
    title: str
    required_skills: List[str]
    core_responsibilities: List[str]

class ResumeSection(BaseModel):
    section_name: str # e.g., "Work Experience", "Education"
    original_text: str
    
class Feedback(BaseModel):
    match_score: int # 0-100
    missing_skills: List[str]
    strengths: List[str]
    general_advice: str

class RewrittenBulletPoint(BaseModel):
    original_bullet: str
    rewritten_bullet: str
    explanation: str # 为什么这么改
```

## 5. Agent Prompts (核心提示词设计)

### 5.1 System Prompt (系统角色设定)
> "你是一位拥有10年世界500强企业招聘经验的资深 HR 兼职业规划师。你的任务是帮助求职者将他们的简历与目标岗位 JD 进行完美匹配。你非常注重细节，强调使用数据和结果来证明能力。在重写经历时，你始终遵循 STAR 法则（Situation, Task, Action, Result）。"

### 5.2 Task Prompt 1: 简历诊断 (Resume Diagnosis)
> **输入:** {简历全文} + {目标岗位 JD}
> **任务:** > 1. 评估简历与 JD 的匹配度（0-100分）。
> 2. 提取出 JD 中要求但简历中缺失的硬技能和软技能。
> 3. 给出3条宏观的修改建议。
> **输出格式:** 请严格按照 `Feedback` 数据模型输出 JSON。

### 5.3 Task Prompt 2: 经历重写 (Experience Rewriting)
> **输入:** {单条工作/项目经历} + {目标岗位 JD 关键词}
> **任务:** > 1. 指出当前这段经历描述的不足之处。
> 2. 使用 STAR 法则重写这段经历，确保将其转化为具有业务影响力和数据支撑的“成就句”。
> 3. 尽可能自然地融入 JD 中的关键词，以便通过 ATS（简历解析系统）。
> **输出格式:** 请严格按照 `RewrittenBulletPoint` 数据模型输出 JSON。

## 6. API 接口定义 (API Endpoints)
如果使用 FastAPI 开发，需实现以下核心接口：

* `POST /api/v1/parse-resume`: 接收文件上传，返回提取的文本。
* `POST /api/v1/analyze`: 接收解析后的简历文本和 JD，调用 Task Prompt 1，返回 `Feedback` JSON。
* `POST /api/v1/rewrite-section`: 接收特定的简历段落文本和 JD，调用 Task Prompt 2，返回 `RewrittenBulletPoint` JSON。

## 7. 错误处理与边界条件 (Edge Cases)
* 如果解析出的简历文本为空或乱码，系统应抛出明确的错误提示要求用户重新上传规范格式。
* 如果用户未提供 JD，Agent 应基于简历原本的职位方向给出通用型的优化建议（退化处理）。
* LLM API 超时或并发超限时，需实现重试机制 (Retry Logic)。