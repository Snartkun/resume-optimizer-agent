"""
LLM 服务层 - 与 OpenAI API 交互，使用 Structured Outputs 强制 JSON 输出
"""
import asyncio
from typing import Optional
from openai import AsyncOpenAI, RateLimitError, APIError, Timeout
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.models import Feedback, RewrittenBulletPoint, JobDescription
from app.config import get_settings


class LLMService:
    """
    LLM 服务类 - 封装所有 LLM 调用逻辑

    使用 OpenAI Structured Outputs 功能确保返回格式严格符合 Pydantic 模型
    """

    # 系统提示词 - 定义 Agent 角色 (优化版)
    SYSTEM_PROMPT = """你是一位拥有10年世界500强企业招聘经验的资深 HR 兼职业规划师。

你的核心信念：
- 优秀的简历不是"格式正确"，而是让读者快速理解"这个人为什么牛逼"
- 每一段经历都应该回答三个问题：你解决了什么问题？你怎么解决的？结果有多牛？
- 数据和结果是信任的基础，但上下文和逻辑是说服的关键
- 针对不同岗位类型（技术/产品/运营/管理），侧重点完全不同

重写经历时，你不只是套用 STAR 法则，而是：
1. 先诊断原描述为什么缺乏说服力（是空洞形容词？缺乏量化？逻辑不清？与岗位无关？）
2. 重构叙事逻辑，突出与目标岗位最相关的价值点
3. 用自然、专业的语言呈现，避免生硬的"为了 STAR 而 STAR"""

    def __init__(self):
        settings = get_settings()
        self.provider = settings.LLM_PROVIDER.lower()
        self.temperature = settings.LLM_TEMPERATURE
        self.max_retries = settings.LLM_MAX_RETRIES

        # 根据 provider 选择配置
        if self.provider == "deepseek":
            self.client = AsyncOpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
                timeout=settings.LLM_TIMEOUT,
            )
            self.model = settings.DEEPSEEK_MODEL
        else:  # 默认使用 OpenAI
            self.client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL if settings.OPENAI_BASE_URL else None,
                timeout=settings.LLM_TIMEOUT,
            )
            self.model = settings.OPENAI_MODEL

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APIError, Timeout)),
        reraise=True
    )
    async def _call_llm_with_structured_output(
        self,
        messages: list[dict],
        response_format: type,
    ) -> dict:
        """
        调用 LLM API 并强制返回结构化输出

        支持 OpenAI 和 DeepSeek (兼容 OpenAI 格式)

        Args:
            messages: 对话消息列表
            response_format: Pydantic 模型类，定义输出结构

        Returns:
            解析后的 Pydantic 模型实例
        """
        # OpenAI 支持 beta.parse 方法直接使用 Pydantic 模型
        if self.provider == "openai":
            completion = await self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                response_format=response_format,
                temperature=self.temperature,
            )
            return completion.choices[0].message.parsed

        # DeepSeek 使用 JSON mode + 提示词中的 schema 约束
        else:
            import json

            # 在系统提示词后添加 JSON schema 约束
            schema = response_format.model_json_schema()
            schema_instruction = f"\n\n你必须严格按照以下 JSON Schema 格式输出，不要输出任何其他内容：\n{json.dumps(schema, ensure_ascii=False, indent=2)}"

            modified_messages = messages.copy()
            modified_messages[0]["content"] += schema_instruction

            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=modified_messages,
                response_format={"type": "json_object"},
                temperature=self.temperature,
            )

            # 解析 JSON 并验证
            content = completion.choices[0].message.content
            parsed_data = json.loads(content)
            return response_format(**parsed_data)

    async def analyze_resume_with_jd(
        self,
        resume_text: str,
        job_description: JobDescription
    ) -> Feedback:
        """
        Task Prompt 1: 简历诊断 (有 JD)
        """
        task_prompt = f"""请对以下简历进行专业诊断分析。

## 目标职位信息
- 职位名称: {job_description.title}
- 所需技能: {', '.join(job_description.required_skills)}
- 核心职责: {', '.join(job_description.core_responsibilities)}

## 简历全文
{resume_text}

## 诊断任务
1. 评估简历与 JD 的匹配度（0-100分）
2. 提取出 JD 中要求但简历中缺失的硬技能和软技能
3. 给出3条宏观的修改建议（写入 general_advice）
4. 总结简历的优势（写入 strengths）

请严格按照 Feedback 数据模型输出结果。"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": task_prompt}
        ]

        for attempt in range(self.max_retries):
            try:
                result = await self._call_llm_with_structured_output(
                    messages=messages,
                    response_format=Feedback
                )
                return result
            except Exception:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError("Unexpected error in analyze_resume_with_jd")

    async def analyze_resume_without_jd(
        self,
        resume_text: str
    ) -> Feedback:
        """
        Task Prompt 1 (退化模式): 通用简历诊断
        """
        task_prompt = f"""请对以下简历进行专业诊断分析。

## 简历全文
{resume_text}

## 诊断任务（通用优化模式）
由于未提供目标职位描述，请基于简历内容推断求职方向，并给出：
1. 评估简历整体质量分数（0-100分，基于专业性、完整性、数据支撑等）
2. 基于推断的职位方向，列出可能缺失的关键技能
3. 给出3条通用的简历优化建议（写入 general_advice）
4. 总结简历的优势（写入 strengths）

请严格按照 Feedback 数据模型输出结果。"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": task_prompt}
        ]

        for attempt in range(self.max_retries):
            try:
                result = await self._call_llm_with_structured_output(
                    messages=messages,
                    response_format=Feedback
                )
                return result
            except Exception:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError("Unexpected error in analyze_resume_without_jd")

    async def rewrite_experience(
        self,
        section_text: str,
        job_description: JobDescription,
        keywords: Optional[list] = None
    ) -> RewrittenBulletPoint:
        """
        Task Prompt 2: 经历重写 (优化版)
        """
        keywords_to_use = keywords if keywords else job_description.required_skills
        keywords_str = ', '.join(keywords_to_use)

        task_prompt = f"""请对以下工作经历进行深度优化重写。

## 目标职位信息
- 职位名称: {job_description.title}
- 所需技能: {', '.join(job_description.required_skills)}
- 核心职责: {', '.join(job_description.core_responsibilities)}

## 需要自然融入的关键词
{keywords_str}

## 原始经历描述
{section_text}

---

## 重写任务

### 第一步：诊断原描述的问题
分析这段描述为什么缺乏说服力。常见问题包括：
- **空洞形容词**："负责"、"参与"、"协助"——没说清楚具体做什么
- **缺乏量化**：没有数字，无法判断贡献大小
- **逻辑断层**：做了什么→怎么做的→结果如何，链条断裂
- **与岗位无关**：描述的内容和目标职位需求不匹配
- **罗列职责**：像 JD 一样列举任务，而非展示成就

### 第二步：重构叙事逻辑
基于目标职位的核心需求，重新组织这段经历：
- **识别价值锚点**：这段经历中，最能让目标岗位眼前一亮的点是什么？
- **构建因果链**：因为遇到了什么挑战（或机会），所以我采取了什么行动，最终产生了什么可量化的影响
- **突出差异化**：如果换成别人写同样的经历，会有什么不同？我的独特贡献在哪里？

### 第三步：撰写优化版本
撰写要求：
1. **开头抓人**：用具体的业务场景或技术挑战开头，而非泛泛的"负责"
2. **过程有料**：描述具体的方法、技术选型或决策逻辑，展示专业深度
3. **结果量化**：用数字说话（性能提升 X%、成本降低 Y 万、效率提高 Z 倍、服务 N 万用户）
4. **语言自然**：像资深工程师/产品经理向 CTO 汇报工作，而非学生背课文
5. **融入关键词**：将 JD 中的关键词自然嵌入，不要为了堆砌而生硬插入

### 第四步：解释修改逻辑
在 explanation 中说明：
- 原描述的核心问题是什么
- 重写后如何更好地回答了"这个人为什么牛逼"
- 针对目标岗位，这个版本的优势在哪里

---

## 输出格式要求
严格按照 RewrittenBulletPoint 数据模型输出：
- original_bullet: 原始描述原文
- rewritten_bullet: 优化后的描述（1-3句话，聚焦最有价值的亮点）
- explanation: 修改思路和理由（具体、专业，避免套话）

---

## 优秀 vs 平庸的对比示例

【技术岗 - 后端开发】

❌ 平庸版本：
"负责公司电商平台的开发工作，使用 Java 和 Spring Boot 框架，参与数据库设计。"

✅ 优秀版本：
"主导电商平台核心交易链路重构，针对高并发场景设计多级缓存策略（Redis + 本地缓存），将下单接口 P99 延迟从 800ms 降至 120ms；通过异步消息队列（Kafka）解耦库存扣减逻辑，支撑日订单量从 10 万增长至 100 万，系统稳定性保持 99.99%。"

区别：平庸版罗列技术栈，优秀版讲清业务场景→技术方案→量化结果。

---

【产品岗 - 数据产品】

❌ 平庸版本：
"负责数据分析平台的产品设计，与研发团队沟通需求，推进项目上线。"

✅ 优秀版本：
"从 0 到 1 搭建企业级数据分析平台，深入访谈 20+ 业务团队，识别出"数据获取周期长"的核心痛点；设计自助式查询工具替代传统提数流程，将数据获取时间从平均 3 天缩短至 10 分钟，上线 3 个月内 MAU 达到 500+，用户满意度 4.8/5。"

区别：平庸版强调"做了什么"，优秀版强调"解决了什么问题、问题有多痛、解决方案多有效"。"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": task_prompt}
        ]

        for attempt in range(self.max_retries):
            try:
                result = await self._call_llm_with_structured_output(
                    messages=messages,
                    response_format=RewrittenBulletPoint
                )
                return result
            except Exception:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError("Unexpected error in rewrite_experience")
