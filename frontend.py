"""
简历优化 Agent - Streamlit 前端测试页面
"""
import streamlit as st
import requests
import json
from typing import Optional

# 页面配置
st.set_page_config(
    page_title="简历优化 Agent",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API 配置
API_BASE_URL = "http://localhost:8000/api/v1"

# 自定义样式
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: bold;
        color: #333;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
        padding-bottom: 0.3rem;
        border-bottom: 2px solid #1f77b4;
    }
    .score-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
    }
    .skill-tag {
        display: inline-block;
        background-color: #ff6b6b;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        margin: 0.2rem;
        font-size: 0.9rem;
    }
    .strength-tag {
        display: inline-block;
        background-color: #51cf66;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        margin: 0.2rem;
        font-size: 0.9rem;
    }
    .comparison-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


def parse_resume_file(file) -> Optional[dict]:
    """调用后端解析简历文件"""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        response = requests.post(f"{API_BASE_URL}/parse-resume", files=files, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"解析失败: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ 无法连接到后端服务，请确保服务已启动 (python -m app.main)")
        return None
    except Exception as e:
        st.error(f"解析出错: {str(e)}")
        return None


def analyze_resume(resume_text: str, job_desc: dict) -> Optional[dict]:
    """调用后端分析简历"""
    try:
        payload = {
            "resume_text": resume_text,
            "job_description": job_desc
        }
        response = requests.post(f"{API_BASE_URL}/analyze", json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"分析失败: {response.text}")
            return None
    except Exception as e:
        st.error(f"分析出错: {str(e)}")
        return None


def rewrite_section(section_text: str, job_desc: dict) -> Optional[dict]:
    """调用后端重写段落"""
    try:
        payload = {
            "section_text": section_text,
            "job_description": job_desc
        }
        response = requests.post(f"{API_BASE_URL}/rewrite-section", json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"重写失败: {response.text}")
            return None
    except Exception as e:
        st.error(f"重写出错: {str(e)}")
        return None


def render_analysis_result(feedback: dict):
    """渲染分析结果"""
    if not feedback:
        return

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown('<div class="section-header">📊 匹配度评分</div>', unsafe_allow_html=True)
        score = feedback.get("match_score", 0)
        color = "#51cf66" if score >= 70 else "#ffd93d" if score >= 50 else "#ff6b6b"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
                    color: white; padding: 2rem; border-radius: 15px; text-align: center;">
            <div style="font-size: 3rem; font-weight: bold;">{score}</div>
            <div style="font-size: 1rem; opacity: 0.9;">分 / 100</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-header">⚠️ 缺失技能</div>', unsafe_allow_html=True)
        missing_skills = feedback.get("missing_skills", [])
        if missing_skills:
            skills_html = " ".join([f'<span class="skill-tag">{skill}</span>' for skill in missing_skills])
            st.markdown(skills_html, unsafe_allow_html=True)
        else:
            st.success("✅ 技能匹配度很高，没有明显缺失！")

    st.markdown('<div class="section-header">💪 简历优势</div>', unsafe_allow_html=True)
    strengths = feedback.get("strengths", [])
    if strengths:
        strengths_html = " ".join([f'<span class="strength-tag">{s}</span>' for s in strengths])
        st.markdown(strengths_html, unsafe_allow_html=True)
    else:
        st.info("暂无识别出的优势")

    st.markdown('<div class="section-header">📝 优化建议</div>', unsafe_allow_html=True)
    advice = feedback.get("general_advice", "")
    if advice:
        st.info(advice)


def render_rewrite_result(result: dict):
    """渲染重写结果"""
    if not result:
        return

    st.markdown('<div class="section-header">✨ STAR 法则优化</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📝 原始描述**")
        st.markdown(f"""
        <div style="background-color: #fff3cd; padding: 1rem; border-radius: 8px;
                    border-left: 4px solid #ffc107; color: #856404;">
            {result.get('original_bullet', '')}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("**✅ 优化后描述**")
        st.markdown(f"""
        <div style="background-color: #d4edda; padding: 1rem; border-radius: 8px;
                    border-left: 4px solid #28a745; color: #155724;">
            {result.get('rewritten_bullet', '')}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("**💡 修改说明**")
    st.success(result.get('explanation', ''))


def main():
    # 页面标题
    st.markdown('<div class="main-title">📄 简历优化 Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">基于 DeepSeek LLM 的智能简历诊断与优化工具</div>', unsafe_allow_html=True)

    # 侧边栏 - 职位描述输入
    with st.sidebar:
        st.header("🎯 目标职位信息")

        job_title = st.text_input("职位名称", placeholder="例如：高级后端工程师")

        st.subheader("所需技能")
        skills_input = st.text_area(
            "输入技能（每行一个）",
            placeholder="Python\nFastAPI\nRedis\nKubernetes",
            height=100
        )

        st.subheader("核心职责")
        responsibilities_input = st.text_area(
            "输入职责（每行一个）",
            placeholder="设计高并发系统\n性能优化\n技术方案评审",
            height=100
        )

        # 构建 JD 对象
        job_description = None
        if job_title and skills_input:
            job_description = {
                "title": job_title,
                "required_skills": [s.strip() for s in skills_input.split('\n') if s.strip()],
                "core_responsibilities": [r.strip() for r in responsibilities_input.split('\n') if r.strip()]
            }

        if not job_description:
            st.warning("⚠️ 请填写职位信息以进行分析")

    # 主区域
    tab1, tab2, tab3 = st.tabs(["📤 上传简历", "📊 分析报告", "✨ 智能重写"])

    # Tab 1: 上传简历
    with tab1:
        st.markdown('<div class="section-header">上传简历文件</div>', unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "选择简历文件（PDF 或 Word）",
            type=['pdf', 'doc', 'docx'],
            help="支持 PDF、DOC、DOCX 格式"
        )

        if uploaded_file:
            col1, col2 = st.columns([1, 2])

            with col1:
                st.success(f"✅ 已上传: {uploaded_file.name}")
                st.info(f"文件大小: {uploaded_file.size / 1024:.1f} KB")

                if st.button("🔍 开始解析", type="primary"):
                    with st.spinner("正在解析简历..."):
                        result = parse_resume_file(uploaded_file)
                        if result and result.get("success"):
                            st.session_state['parsed_resume'] = result
                            st.success("✅ 解析成功！")
                        else:
                            st.error("❌ 解析失败")

            with col2:
                if 'parsed_resume' in st.session_state:
                    with st.expander("📄 查看解析结果", expanded=True):
                        resume_data = st.session_state['parsed_resume']
                        st.text_area("简历全文", resume_data.get('full_text', ''), height=300)

                        if resume_data.get('sections'):
                            st.subheader("识别出的段落")
                            for section in resume_data['sections']:
                                with st.expander(f"📑 {section.get('section_name', '未知段落')}"):
                                    st.text(section.get('original_text', ''))

    # Tab 2: 分析报告
    with tab2:
        st.markdown('<div class="section-header">简历诊断分析</div>', unsafe_allow_html=True)

        if 'parsed_resume' not in st.session_state:
            st.info("👈 请先在上传标签页解析简历")
        elif not job_description:
            st.info("👈 请在侧边栏填写职位信息")
        else:
            resume_text = st.session_state['parsed_resume'].get('full_text', '')

            if st.button("🔍 开始分析", type="primary"):
                with st.spinner("DeepSeek 正在分析简历与职位匹配度..."):
                    result = analyze_resume(resume_text, job_description)
                    if result and result.get("success"):
                        st.session_state['analysis_result'] = result.get("feedback")
                        st.success("✅ 分析完成！")

            if 'analysis_result' in st.session_state:
                render_analysis_result(st.session_state['analysis_result'])

    # Tab 3: 智能重写
    with tab3:
        st.markdown('<div class="section-header">STAR 法则智能重写</div>', unsafe_allow_html=True)

        if 'parsed_resume' not in st.session_state:
            st.info("👈 请先在上传标签页解析简历")
        elif not job_description:
            st.info("👈 请在侧边栏填写职位信息")
        else:
            # 选择要重写的段落
            sections = st.session_state['parsed_resume'].get('sections', [])

            if sections:
                section_options = {f"{s.get('section_name', f'段落{i}')}": s.get('original_text', '')
                                   for i, s in enumerate(sections)}

                selected_section = st.selectbox(
                    "选择要优化的段落",
                    options=list(section_options.keys())
                )

                section_text = section_options.get(selected_section, '')

                with st.expander("查看选中段落内容"):
                    st.text(section_text)

                if st.button("✨ 使用 STAR 法则重写", type="primary"):
                    with st.spinner("DeepSeek 正在优化..."):
                        result = rewrite_section(section_text, job_description)
                        if result and result.get("success"):
                            st.session_state['rewrite_result'] = result.get("rewritten")
                            st.success("✅ 重写完成！")

                if 'rewrite_result' in st.session_state:
                    render_rewrite_result(st.session_state['rewrite_result'])
            else:
                # 手动输入段落
                section_text = st.text_area("输入要重写的经历描述", height=150,
                                           placeholder="例如：负责公司官网的开发工作，使用 Python 和 Django 框架...")

                if section_text and st.button("✨ 使用 STAR 法则重写", type="primary"):
                    with st.spinner("DeepSeek 正在优化..."):
                        result = rewrite_section(section_text, job_description)
                        if result and result.get("success"):
                            st.session_state['rewrite_result'] = result.get("rewritten")
                            st.success("✅ 重写完成！")

                if 'rewrite_result' in st.session_state:
                    render_rewrite_result(st.session_state['rewrite_result'])


if __name__ == "__main__":
    main()
