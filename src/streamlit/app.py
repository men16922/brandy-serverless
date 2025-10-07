# Streamlit Frontend Application
# 5-step workflow UI for AI branding chatbot

import streamlit as st
import requests
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from PIL import Image
import io

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:3000')

# Workflow steps configuration
WORKFLOW_STEPS = [
    {"id": 1, "name": "비즈니스 분석", "agent": "product_insight", "description": "업종/지역/규모 분석"},
    {"id": 2, "name": "상호명 제안", "agent": "reporter", "description": "3개 상호명 후보 생성"},
    {"id": 3, "name": "간판 디자인", "agent": "signboard", "description": "AI 간판 이미지 생성"},
    {"id": 4, "name": "인테리어 추천", "agent": "interior", "description": "맞춤형 인테리어 디자인"},
    {"id": 5, "name": "보고서 생성", "agent": "report_generator", "description": "종합 브랜딩 보고서"}
]

# Industry and region options
INDUSTRIES = [
    "restaurant", "retail", "service", "healthcare", "education",
    "technology", "manufacturing", "construction", "finance", "other"
]

REGIONS = [
    "seoul", "busan", "daegu", "incheon", "gwangju", "daejeon",
    "ulsan", "gyeonggi", "gangwon", "chungbuk", "chungnam",
    "jeonbuk", "jeonnam", "gyeongbuk", "gyeongnam", "jeju"
]

SIZES = ["small", "medium", "large"]

def init_session_state():
    """Initialize Streamlit session state"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    if 'session_data' not in st.session_state:
        st.session_state.session_data = None
    if 'business_info' not in st.session_state:
        st.session_state.business_info = None
    if 'polling_active' not in st.session_state:
        st.session_state.polling_active = False
    if 'agent_status' not in st.session_state:
        st.session_state.agent_status = {}

def display_progress_bar():
    """Display workflow progress bar with step indicators"""
    st.markdown("### 워크플로 진행 상황")
    
    # Create progress columns
    cols = st.columns(len(WORKFLOW_STEPS))
    
    for i, step in enumerate(WORKFLOW_STEPS):
        with cols[i]:
            # Determine step status
            if st.session_state.current_step > step["id"]:
                status = "✅"  # Completed
                color = "green"
            elif st.session_state.current_step == step["id"]:
                status = "🔄"  # In progress
                color = "blue"
            else:
                status = "⏳"  # Pending
                color = "gray"
            
            # Display step
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; border: 2px solid {color}; border-radius: 10px; margin: 5px;">
                <div style="font-size: 24px;">{status}</div>
                <div style="font-weight: bold;">{step["name"]}</div>
                <div style="font-size: 12px; color: gray;">{step["description"]}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Overall progress bar
    progress = st.session_state.current_step / len(WORKFLOW_STEPS)
    st.progress(progress)
    st.write(f"진행률: {int(progress * 100)}% ({st.session_state.current_step}/{len(WORKFLOW_STEPS)} 단계)")

def display_agent_status():
    """Display real-time agent execution status"""
    if st.session_state.agent_status:
        st.markdown("### 에이전트 실행 상태")
        
        # Create columns for agent status
        agent_cols = st.columns(3)
        
        for i, (agent_name, status) in enumerate(st.session_state.agent_status.items()):
            with agent_cols[i % 3]:
                status_icon = {
                    "running": "🔄",
                    "completed": "✅", 
                    "failed": "❌",
                    "pending": "⏳"
                }.get(status.get("status", "pending"), "⏳")
                
                latency = status.get("latency_ms", 0)
                latency_text = f"{latency}ms" if latency > 0 else "대기중"
                
                st.markdown(f"""
                <div style="padding: 8px; border: 1px solid #ddd; border-radius: 5px; margin: 2px;">
                    <div>{status_icon} <strong>{agent_name}</strong></div>
                    <div style="font-size: 12px;">응답시간: {latency_text}</div>
                </div>
                """, unsafe_allow_html=True)

def create_session(session_request: Dict[str, Any]) -> Optional[str]:
    """Create a new workflow session"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/sessions",
            json=session_request,
            timeout=30  # Increased timeout for session creation
        )
        
        if response.status_code in [200, 201]:  # Accept both 200 and 201
            data = response.json()
            return data.get("sessionId") or data.get("session_id")  # Try both field names
        else:
            st.error(f"세션 생성 실패: HTTP {response.status_code}")
            try:
                error_data = response.json()
                st.error(f"오류 상세: {error_data}")
            except:
                st.error(f"응답 내용: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("❌ API 서버에 연결할 수 없습니다")
        st.info("API 서버를 시작하세요: `./scripts/dev.sh api`")
        return None
    except requests.exceptions.Timeout:
        st.error("⏰ API 응답 시간 초과 (30초)")
        st.info("서버가 시작 중이거나 과부하 상태일 수 있습니다. 잠시 후 다시 시도하세요.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"API 호출 오류: {str(e)}")
        return None

def get_session_status(session_id: str) -> Optional[Dict[str, Any]]:
    """Get current session status from Supervisor Agent"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/status/{session_id}",
            timeout=10  # Increased timeout for status check
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except requests.exceptions.RequestException:
        return None

def poll_session_status():
    """Poll session status and update UI"""
    if st.session_state.session_id and st.session_state.polling_active:
        status_data = get_session_status(st.session_state.session_id)
        
        if status_data:
            st.session_state.session_data = status_data
            st.session_state.current_step = status_data.get("currentStep", 1)
            
            # Update agent status from agentStatuses
            agent_statuses = status_data.get("agentStatuses", {})
            for agent_name, agent_info in agent_statuses.items():
                st.session_state.agent_status[agent_name] = {
                    "status": agent_info.get("status", "pending"),
                    "latency_ms": agent_info.get("latency_ms", 0),
                    "tool": agent_info.get("tool", ""),
                    "timestamp": agent_info.get("timestamp", "")
                }
            
            # Check if workflow is completed
            if status_data.get("status") == "completed":
                st.session_state.polling_active = False
                st.success("워크플로가 완료되었습니다!")
            elif status_data.get("status") == "failed":
                st.session_state.polling_active = False
                st.error("워크플로 실행 중 오류가 발생했습니다.")

def step1_business_analysis():
    """Step 1: Business Information Input and Analysis"""
    st.markdown("## 1단계: 비즈니스 정보 입력")
    
    with st.form("business_info_form"):
        st.markdown("### 기본 정보")
        
        col1, col2 = st.columns(2)
        
        with col1:
            industry = st.selectbox(
                "업종 선택",
                options=INDUSTRIES,
                format_func=lambda x: {
                    "restaurant": "음식점/카페",
                    "retail": "소매업",
                    "service": "서비스업",
                    "healthcare": "의료/건강",
                    "education": "교육",
                    "technology": "기술/IT",
                    "manufacturing": "제조업",
                    "construction": "건설업",
                    "finance": "금융업",
                    "other": "기타"
                }.get(x, x)
            )
            
            region = st.selectbox(
                "지역 선택",
                options=REGIONS,
                format_func=lambda x: {
                    "seoul": "서울",
                    "busan": "부산",
                    "daegu": "대구",
                    "incheon": "인천",
                    "gwangju": "광주",
                    "daejeon": "대전",
                    "ulsan": "울산",
                    "gyeonggi": "경기도",
                    "gangwon": "강원도",
                    "chungbuk": "충청북도",
                    "chungnam": "충청남도",
                    "jeonbuk": "전라북도",
                    "jeonnam": "전라남도",
                    "gyeongbuk": "경상북도",
                    "gyeongnam": "경상남도",
                    "jeju": "제주도"
                }.get(x, x)
            )
        
        with col2:
            size = st.selectbox(
                "사업 규모",
                options=SIZES,
                format_func=lambda x: {
                    "small": "소규모 (직원 1-10명)",
                    "medium": "중규모 (직원 11-50명)",
                    "large": "대규모 (직원 50명 이상)"
                }.get(x, x)
            )
        
        description = st.text_area(
            "사업 설명 (선택사항)",
            placeholder="사업에 대한 추가 설명을 입력하세요...",
            height=100
        )
        
        # Image upload
        uploaded_file = st.file_uploader(
            "참고 이미지 업로드 (선택사항)",
            type=['png', 'jpg', 'jpeg'],
            help="브랜딩에 참고할 이미지를 업로드하세요"
        )
        
        submitted = st.form_submit_button("분석 시작", type="primary")
        
        if submitted:
            # Prepare business info
            business_info = {
                "industry": industry,
                "region": region,
                "size": size,
                "description": description if description else None,
                "uploaded_image_url": None  # Will be handled later for image upload
            }
            
            # Handle image upload if provided
            if uploaded_file:
                # For now, we'll store the image info in session state
                # In production, this would be uploaded to S3
                st.session_state.uploaded_image = uploaded_file
                st.info("이미지가 업로드되었습니다. (실제 S3 업로드는 백엔드에서 처리됩니다)")
            
            # Create session
            with st.spinner("세션을 생성하고 분석을 시작하는 중..."):
                # Add sessionId to business_info for API compatibility
                session_request = {
                    "businessInfo": business_info
                }
                session_id = create_session(session_request)
                
                if session_id:
                    st.session_state.session_id = session_id
                    st.session_state.business_info = business_info
                    st.session_state.current_step = 1
                    st.session_state.polling_active = True
                    st.success(f"세션이 생성되었습니다: {session_id}")
                    st.rerun()
                else:
                    st.error("세션 생성에 실패했습니다.")
                    st.info("**문제 해결:**")
                    st.markdown("1. API 서버가 실행 중인지 확인하세요")
                    st.code("./scripts/dev.sh api")
                    st.markdown("2. 환경이 올바르게 설정되었는지 확인하세요")
                    st.code("./scripts/dev.sh validate")
                    st.markdown("3. 잠시 후 다시 시도해보세요")

def display_analysis_results():
    """Display business analysis results"""
    results = st.session_state.session_data.get("results", {}) if st.session_state.session_data else {}
    analysis = results.get("analysis")
    
    if analysis:
        
        st.markdown("### 📊 비즈니스 분석 결과")
        
        # Score display
        score = analysis.get("score", 0)
        st.metric("종합 점수", f"{score:.1f}/100")
        
        # Summary
        if analysis.get("summary"):
            st.markdown("**분석 요약**")
            st.info(analysis["summary"])
        
        # Insights
        insights = analysis.get("insights", [])
        if insights:
            st.markdown("**핵심 인사이트**")
            for i, insight in enumerate(insights, 1):
                st.markdown(f"{i}. {insight}")
        
        # Market trends
        trends = analysis.get("market_trends", [])
        if trends:
            st.markdown("**시장 트렌드**")
            for trend in trends:
                st.markdown(f"• {trend}")
        
        # Recommendations
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            st.markdown("**추천사항**")
            for rec in recommendations:
                st.markdown(f"• {rec}")

def display_business_names():
    """Display business name suggestions with selection interface"""
    results = st.session_state.session_data.get("results", {}) if st.session_state.session_data else {}
    names_data = results.get("names")
    
    if names_data:
        suggestions = names_data.get("suggestions", [])
        selected_name = names_data.get("selected_name")
        regen_count = names_data.get("regeneration_count", 0)
        max_regens = names_data.get("max_regenerations", 3)
        
        st.markdown("### 🏷️ 상호명 후보")
        
        if suggestions:
            # Display name cards
            cols = st.columns(len(suggestions))
            
            for i, suggestion in enumerate(suggestions):
                with cols[i]:
                    # Card styling
                    is_selected = selected_name == suggestion.get("name")
                    border_color = "#4CAF50" if is_selected else "#ddd"
                    
                    st.markdown(f"""
                    <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 15px; margin: 5px; height: 200px;">
                        <h4 style="margin-top: 0;">{suggestion.get("name", "")}</h4>
                        <p style="font-size: 12px; color: #666;">{suggestion.get("description", "")}</p>
                        <div style="margin-top: 10px;">
                            <div>발음: {suggestion.get("pronunciation_score", 0):.1f}/100</div>
                            <div>검색: {suggestion.get("search_score", 0):.1f}/100</div>
                            <div><strong>종합: {suggestion.get("overall_score", 0):.1f}/100</strong></div>
                        </div>
                        {"<div style='color: green; font-weight: bold; margin-top: 10px;'>✓ 선택됨</div>" if is_selected else ""}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Selection button
                    if not is_selected:
                        if st.button(f"선택", key=f"select_name_{i}"):
                            select_business_name(suggestion.get("name"))
            
            # Regeneration option
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"재생성 횟수: {regen_count}/{max_regens}")
                if regen_count < max_regens:
                    st.info("마음에 드는 상호명이 없다면 다시 생성할 수 있습니다.")
                else:
                    st.warning("재생성 횟수를 모두 사용했습니다.")
            
            with col2:
                if regen_count < max_regens:
                    if st.button("다시 생성", type="secondary"):
                        regenerate_business_names()

def display_signboard_gallery():
    """Display signboard image gallery with selection interface"""
    results = st.session_state.session_data.get("results", {}) if st.session_state.session_data else {}
    signboard_data = results.get("signboards")
    
    if signboard_data:
        images = signboard_data.get("images", [])
        selected_url = signboard_data.get("selected_image_url")
        
        st.markdown("### 🪧 간판 디자인")
        
        if images:
            # Display image gallery
            cols = st.columns(len(images))
            
            for i, image in enumerate(images):
                with cols[i]:
                    # Image card
                    is_selected = selected_url == image.get("url")
                    border_color = "#4CAF50" if is_selected else "#ddd"
                    
                    st.markdown(f"""
                    <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 10px; margin: 5px;">
                        <div style="text-align: center;">
                            <strong>{image.get("provider", "").upper()}</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display image (placeholder for now)
                    if image.get("url"):
                        try:
                            # In production, this would load the actual image from S3
                            st.image(
                                "https://via.placeholder.com/300x200?text=" + image.get("provider", "Image"),
                                caption=f"{image.get('style', '')} 스타일",
                                use_column_width=True
                            )
                        except:
                            st.error("이미지 로드 실패")
                    
                    # Image details
                    st.write(f"**스타일:** {image.get('style', 'N/A')}")
                    st.write(f"**생성시간:** {image.get('generated_at', 'N/A')[:16]}")
                    
                    if image.get("is_fallback"):
                        st.warning("⚠️ 폴백 이미지")
                    
                    # Selection button
                    if not is_selected:
                        if st.button(f"선택", key=f"select_signboard_{i}"):
                            select_signboard_image(image.get("url"))
                    else:
                        st.success("✓ 선택됨")

def display_interior_options():
    """Display interior design options with selection interface"""
    results = st.session_state.session_data.get("results", {}) if st.session_state.session_data else {}
    interior_data = results.get("interiors")
    
    if interior_data:
        images = interior_data.get("images", [])
        selected_url = interior_data.get("selected_image_url")
        budget_range = interior_data.get("budget_range")
        color_palette = interior_data.get("color_palette", [])
        
        st.markdown("### 🏠 인테리어 추천")
        
        # Budget and color palette info
        if budget_range or color_palette:
            col1, col2 = st.columns(2)
            
            with col1:
                if budget_range:
                    st.info(f"**예상 예산:** {budget_range}")
            
            with col2:
                if color_palette:
                    st.markdown("**색상 팔레트:**")
                    palette_html = ""
                    for color in color_palette[:5]:  # Show max 5 colors
                        palette_html += f'<div style="display: inline-block; width: 30px; height: 30px; background-color: {color}; border: 1px solid #ccc; margin: 2px;"></div>'
                    st.markdown(palette_html, unsafe_allow_html=True)
        
        if images:
            # Display interior options
            cols = st.columns(len(images))
            
            for i, image in enumerate(images):
                with cols[i]:
                    # Interior card
                    is_selected = selected_url == image.get("url")
                    border_color = "#4CAF50" if is_selected else "#ddd"
                    
                    st.markdown(f"""
                    <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 10px; margin: 5px;">
                        <div style="text-align: center;">
                            <strong>옵션 {i+1}</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display image (placeholder for now)
                    if image.get("url"):
                        try:
                            st.image(
                                "https://via.placeholder.com/300x200?text=Interior+" + str(i+1),
                                caption=f"{image.get('style', '')} 인테리어",
                                use_column_width=True
                            )
                        except:
                            st.error("이미지 로드 실패")
                    
                    # Interior details
                    st.write(f"**스타일:** {image.get('style', 'N/A')}")
                    metadata = image.get("metadata", {})
                    if metadata.get("budget_estimate"):
                        st.write(f"**예산:** {metadata['budget_estimate']}")
                    
                    # Selection button
                    if not is_selected:
                        if st.button(f"선택", key=f"select_interior_{i}"):
                            select_interior_option(image.get("url"))
                    else:
                        st.success("✓ 선택됨")

def display_report_download():
    """Display PDF report download interface"""
    results = st.session_state.session_data.get("results", {}) if st.session_state.session_data else {}
    report_data = results.get("report")
    
    if report_data:
        
        st.markdown("### 📄 브랜딩 보고서")
        
        st.success("브랜딩 보고서가 생성되었습니다!")
        
        # Report info
        st.info("""
        **포함 내용:**
        - 비즈니스 분석 결과
        - 선택된 상호명 및 후보들
        - 간판 디자인 (선택된 것 + 전체 옵션)
        - 인테리어 추천 (선택된 것 + 전체 옵션)
        - 색상 팔레트 및 예산 가이드
        - 맞춤형 브랜딩 권장사항
        """)
        
        # Download button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📥 보고서 다운로드", type="primary", use_container_width=True):
                download_report()
        
        # Additional options
        st.markdown("---")
        st.markdown("**추가 옵션:**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 새로운 워크플로 시작"):
                start_new_workflow()
        
        with col2:
            if st.button("📧 이메일로 전송"):
                st.info("이메일 전송 기능은 추후 구현 예정입니다.")

def select_business_name(name: str):
    """Select a business name"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/names/select",
            json={"session_id": st.session_state.session_id, "selected_name": name},
            timeout=10
        )
        
        if response.status_code == 200:
            st.success(f"'{name}' 상호명이 선택되었습니다!")
            poll_session_status()
            st.rerun()
        else:
            st.error("상호명 선택에 실패했습니다.")
            
    except requests.exceptions.RequestException as e:
        st.error(f"API 호출 오류: {str(e)}")

def regenerate_business_names():
    """Regenerate business name suggestions"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/names/regenerate",
            json={"session_id": st.session_state.session_id},
            timeout=15
        )
        
        if response.status_code == 200:
            st.success("새로운 상호명을 생성하고 있습니다...")
            st.session_state.polling_active = True
            poll_session_status()
            st.rerun()
        else:
            st.error("상호명 재생성에 실패했습니다.")
            
    except requests.exceptions.RequestException as e:
        st.error(f"API 호출 오류: {str(e)}")

def select_signboard_image(image_url: str):
    """Select a signboard image"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/signboards/select",
            json={"session_id": st.session_state.session_id, "selected_image_url": image_url},
            timeout=10
        )
        
        if response.status_code == 200:
            st.success("간판 디자인이 선택되었습니다!")
            poll_session_status()
            st.rerun()
        else:
            st.error("간판 선택에 실패했습니다.")
            
    except requests.exceptions.RequestException as e:
        st.error(f"API 호출 오류: {str(e)}")

def select_interior_option(image_url: str):
    """Select an interior option"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/interiors/select",
            json={"session_id": st.session_state.session_id, "selected_image_url": image_url},
            timeout=10
        )
        
        if response.status_code == 200:
            st.success("인테리어 옵션이 선택되었습니다!")
            poll_session_status()
            st.rerun()
        else:
            st.error("인테리어 선택에 실패했습니다.")
            
    except requests.exceptions.RequestException as e:
        st.error(f"API 호출 오류: {str(e)}")

def download_report():
    """Download the generated report"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/report/url",
            params={"session_id": st.session_state.session_id},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            download_url = data.get("download_url")
            
            if download_url:
                st.markdown(f"[📥 보고서 다운로드 링크]({download_url})")
                st.info("링크는 10분간 유효합니다.")
            else:
                st.error("다운로드 링크를 생성할 수 없습니다.")
        else:
            st.error("보고서 다운로드 링크 생성에 실패했습니다.")
            
    except requests.exceptions.RequestException as e:
        st.error(f"API 호출 오류: {str(e)}")

def start_new_workflow():
    """Start a new workflow"""
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("새로운 워크플로를 시작합니다!")
    st.rerun()

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="AI 브랜딩 챗봇",
        page_icon="🎨",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # Header
    st.title("🎨 AI 브랜딩 챗봇")
    st.markdown("**5단계 자동 워크플로로 완전한 브랜딩 패키지를 생성하세요**")
    
    # Sidebar with session info
    with st.sidebar:
        st.markdown("### 세션 정보")
        if st.session_state.session_id:
            st.success(f"세션 ID: {st.session_state.session_id[:8]}...")
            
            # Auto-refresh toggle
            auto_refresh = st.checkbox("자동 새로고침", value=st.session_state.polling_active)
            st.session_state.polling_active = auto_refresh
            
            # Manual refresh button
            if st.button("상태 새로고침"):
                poll_session_status()
                st.rerun()
            
            # Reset session button
            if st.button("새 세션 시작"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        else:
            st.info("세션이 없습니다. 새로운 워크플로를 시작하세요.")
        
        # API connection status
        st.markdown("### API 연결 상태")
        try:
            # Try to connect to the API Gateway (test with a simple request)
            response = requests.get(f"{API_BASE_URL}/", timeout=5)
            if response.status_code in [200, 404]:  # 404 is OK for API Gateway root
                st.success("✅ API Gateway 연결됨")
            else:
                st.warning(f"⚠️ API 응답 이상 ({response.status_code})")
        except requests.exceptions.ConnectionError:
            st.error("❌ API 서버에 연결할 수 없습니다")
            st.info("**해결 방법:**")
            st.code("./scripts/dev.sh api")
            st.info("또는 직접 실행:")
            st.code("sam build && sam local start-api --port 3000")
        except requests.exceptions.Timeout:
            st.warning("⚠️ API 응답 시간 초과")
            st.info("API 서버가 시작 중일 수 있습니다. 잠시 후 다시 시도하세요.")
        except Exception as e:
            st.error(f"❌ API 연결 오류: {str(e)}")
        
        # Development info
        st.markdown("### 개발 정보")
        st.code(f"API URL: {API_BASE_URL}")
        
        # Show session info
        if st.session_state.session_id:
            st.code(f"Session ID: {st.session_state.session_id}")
            st.code(f"Current Step: {st.session_state.current_step}")
            st.code(f"Polling Active: {st.session_state.polling_active}")
        
        # Show raw session data
        if st.session_state.session_data:
            with st.expander("세션 데이터 (JSON)", expanded=False):
                st.json(st.session_state.session_data)
        
        # Show business info
        if st.session_state.business_info:
            with st.expander("비즈니스 정보", expanded=False):
                st.json(st.session_state.business_info)
        
        # Show agent status
        if st.session_state.agent_status:
            with st.expander("에이전트 상태", expanded=False):
                st.json(st.session_state.agent_status)
    
    # Main content area
    if st.session_state.session_id:
        # Display progress bar
        display_progress_bar()
        
        # Display agent status
        display_agent_status()
        
        # Poll status if active
        if st.session_state.polling_active:
            poll_session_status()
            time.sleep(2)  # Wait 2 seconds before next poll
            st.rerun()
        
        # Display current step content
        if st.session_state.current_step == 1:
            display_analysis_results()
            if not st.session_state.session_data or not st.session_state.session_data.get("results", {}).get("analysis"):
                st.info("🔄 비즈니스 분석이 진행 중입니다...")
        elif st.session_state.current_step == 2:
            display_analysis_results()  # Keep showing analysis
            st.markdown("---")
            display_business_names()
            if not st.session_state.session_data or not st.session_state.session_data.get("results", {}).get("names"):
                st.info("🔄 상호명 생성이 진행 중입니다...")
        elif st.session_state.current_step == 3:
            display_analysis_results()  # Keep showing analysis
            st.markdown("---")
            display_business_names()    # Keep showing selected name
            st.markdown("---")
            display_signboard_gallery()
            if not st.session_state.session_data or not st.session_state.session_data.get("results", {}).get("signboards"):
                st.info("🔄 간판 디자인 생성이 진행 중입니다...")
        elif st.session_state.current_step == 4:
            display_analysis_results()
            st.markdown("---")
            display_business_names()
            st.markdown("---")
            display_signboard_gallery()
            st.markdown("---")
            display_interior_options()
            if not st.session_state.session_data or not st.session_state.session_data.get("results", {}).get("interiors"):
                st.info("🔄 인테리어 추천이 진행 중입니다...")
        elif st.session_state.current_step == 5:
            display_analysis_results()
            st.markdown("---")
            display_business_names()
            st.markdown("---")
            display_signboard_gallery()
            st.markdown("---")
            display_interior_options()
            st.markdown("---")
            display_report_download()
            if not st.session_state.session_data or not st.session_state.session_data.get("results", {}).get("report"):
                st.info("🔄 보고서 생성이 진행 중입니다...")
        else:
            st.info(f"단계 {st.session_state.current_step}는 아직 구현되지 않았습니다.")
    else:
        # Step 1: Business information input
        step1_business_analysis()

if __name__ == "__main__":
    main()