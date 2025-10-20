# Streamlit Frontend Application
# 5-step workflow UI for AI branding chatbot

import streamlit as st
import requests
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from PIL import Image
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration - AWS-only architecture
# Streamlit runs locally, all backend services use AWS
API_BASE_URL = os.getenv('API_BASE_URL', 'https://67y0voa4yd.execute-api.us-west-2.amazonaws.com/dev')

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
    if 'reasoning_chain' not in st.session_state:
        st.session_state.reasoning_chain = []
    if 'error_recovery' not in st.session_state:
        st.session_state.error_recovery = None

def display_progress_bar():
    """Display enhanced workflow progress bar with step indicators"""
    st.markdown("### 워크플로 진행 상황")
    
    # Create progress columns
    cols = st.columns(len(WORKFLOW_STEPS))
    
    for i, step in enumerate(WORKFLOW_STEPS):
        with cols[i]:
            # Determine step status
            if st.session_state.current_step > step["id"]:
                status = "✅"  # Completed
                color = "green"
                bg_color = "#e8f5e9"
            elif st.session_state.current_step == step["id"]:
                status = "🔄"  # In progress
                color = "blue"
                bg_color = "#e3f2fd"
            else:
                status = "⏳"  # Pending
                color = "gray"
                bg_color = "#f5f5f5"
            
            # Get agent status for this step
            agent_name = step["agent"]
            agent_info = st.session_state.agent_status.get(agent_name, {})
            latency = agent_info.get("latency_ms", 0)
            latency_text = f"{latency}ms" if latency > 0 else ""
            
            # Display step with enhanced information
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; border: 2px solid {color}; border-radius: 10px; margin: 5px; background-color: {bg_color};">
                <div style="font-size: 24px;">{status}</div>
                <div style="font-weight: bold; margin: 5px 0;">{step["name"]}</div>
                <div style="font-size: 11px; color: #666; margin-bottom: 5px;">{step["description"]}</div>
                {f'<div style="font-size: 10px; color: {color}; font-weight: bold;">{latency_text}</div>' if latency_text else ''}
            </div>
            """, unsafe_allow_html=True)
    
    # Overall progress bar with percentage
    progress = st.session_state.current_step / len(WORKFLOW_STEPS)
    st.progress(progress)
    
    # Enhanced progress information
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("진행률", f"{int(progress * 100)}%")
    with col2:
        st.metric("현재 단계", f"{st.session_state.current_step}/{len(WORKFLOW_STEPS)}")
    with col3:
        # Calculate estimated time remaining (rough estimate)
        if st.session_state.current_step > 1:
            # Estimate based on average time per step (assuming 1 minute per step)
            remaining_steps = len(WORKFLOW_STEPS) - st.session_state.current_step
            estimated_minutes = remaining_steps * 1
            st.metric("예상 남은 시간", f"~{estimated_minutes}분")

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

def display_reasoning_chain():
    """Display reasoning chain from Bedrock Claude (expandable section)"""
    if st.session_state.reasoning_chain and len(st.session_state.reasoning_chain) > 0:
        with st.expander("🧠 AI 의사결정 과정 (Reasoning Chain)", expanded=False):
            st.markdown("**Bedrock Claude의 Chain-of-Thought 추론 과정**")
            
            for i, step in enumerate(st.session_state.reasoning_chain):
                step_number = step.get("stepNumber", i + 1)
                agent_name = step.get("agentName", "Unknown")
                reasoning = step.get("reasoning", "")
                decision = step.get("decision", "")
                confidence = step.get("confidence", 0.0)
                timestamp = step.get("timestamp", "")
                
                # Confidence color coding
                if confidence >= 0.8:
                    confidence_color = "green"
                    confidence_label = "높음"
                elif confidence >= 0.6:
                    confidence_color = "orange"
                    confidence_label = "중간"
                else:
                    confidence_color = "red"
                    confidence_label = "낮음"
                
                st.markdown(f"""
                <div style="border-left: 4px solid #4CAF50; padding: 10px; margin: 10px 0; background-color: #f9f9f9;">
                    <div style="font-weight: bold; margin-bottom: 5px;">
                        Step {step_number}: {agent_name}
                        <span style="float: right; color: {confidence_color};">
                            신뢰도: {confidence:.2f} ({confidence_label})
                        </span>
                    </div>
                    <div style="font-size: 12px; color: #666; margin-bottom: 8px;">
                        {timestamp[:19] if timestamp else ""}
                    </div>
                    <div style="margin-bottom: 8px;">
                        <strong>추론 과정:</strong><br/>
                        {reasoning}
                    </div>
                    <div style="background-color: #e8f5e9; padding: 8px; border-radius: 4px;">
                        <strong>결정:</strong> {decision}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show alternatives if available
                alternatives = step.get("alternatives", [])
                if alternatives:
                    st.markdown("**고려된 대안:**")
                    for alt in alternatives[:3]:  # Show max 3 alternatives
                        st.markdown(f"- {alt}")
                
                st.markdown("---")

def display_error_recovery():
    """Display error recovery strategy when errors occur"""
    if st.session_state.error_recovery:
        error_info = st.session_state.error_recovery
        
        st.warning("⚠️ 오류 발생 및 자동 복구 진행 중")
        
        with st.expander("🔧 오류 복구 전략", expanded=True):
            error_type = error_info.get("error_type", "Unknown")
            error_message = error_info.get("error_message", "")
            recovery_strategy = error_info.get("recovery_strategy", "")
            retry_count = error_info.get("retry_count", 0)
            max_retries = error_info.get("max_retries", 3)
            fallback_used = error_info.get("fallback_used", False)
            
            st.markdown(f"""
            <div style="padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                <div style="font-weight: bold; margin-bottom: 10px;">
                    오류 유형: {error_type}
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>오류 메시지:</strong><br/>
                    {error_message}
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>복구 전략:</strong><br/>
                    {recovery_strategy}
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>재시도 횟수:</strong> {retry_count}/{max_retries}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if fallback_used:
                st.info("🔄 Fallback 메커니즘이 활성화되었습니다. OpenAI/Gemini를 사용하여 계속 진행합니다.")
            
            # Show recovery actions
            recovery_actions = error_info.get("recovery_actions", [])
            if recovery_actions:
                st.markdown("**수행된 복구 작업:**")
                for action in recovery_actions:
                    st.markdown(f"✓ {action}")
            
            # Show next steps
            if retry_count < max_retries:
                st.info(f"🔄 자동으로 재시도 중입니다... ({retry_count + 1}/{max_retries})")
            elif not fallback_used:
                st.warning("⚠️ 최대 재시도 횟수에 도달했습니다. Fallback 메커니즘을 시도합니다.")
            else:
                st.error("❌ 복구에 실패했습니다. 사용자 개입이 필요합니다.")

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
    """Poll session status and update UI (optimized to 2 seconds)"""
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
            
            # Store reasoning chain if available
            if "reasoningChain" in status_data:
                st.session_state.reasoning_chain = status_data["reasoningChain"]
            
            # Store error recovery info if available
            if "errorRecovery" in status_data:
                st.session_state.error_recovery = status_data["errorRecovery"]
            
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
                # Create session without autoStart (we'll trigger steps manually)
                session_request = {
                    "businessInfo": business_info
                }
                logger.info(f"Creating session with: {session_request}")
                st.write("🔍 **디버그:** 세션 생성 요청 중...")
                
                session_id = create_session(session_request)
                
                if session_id:
                    logger.info(f"Session created: {session_id}")
                    st.write(f"✅ **디버그:** 세션 생성됨 - {session_id}")
                    
                    st.session_state.session_id = session_id
                    st.session_state.business_info = business_info
                    st.session_state.current_step = 1
                    st.session_state.polling_active = True
                    st.success(f"세션이 생성되었습니다: {session_id}")
                    
                    # Start Step 1: Business Analysis
                    st.write("🔍 **디버그:** 비즈니스 분석 API 호출 중...")
                    with st.spinner("🔍 AI가 업종, 지역, 시장 트렌드를 분석하고 있습니다..."):
                        try:
                            analysis_payload = {
                                "sessionId": session_id,
                                "businessInfo": business_info
                            }
                            logger.info(f"Calling analysis API with: {analysis_payload}")
                            st.write(f"📤 **디버그:** 분석 요청 - {API_BASE_URL}/analysis")
                            
                            analysis_response = requests.post(
                                f"{API_BASE_URL}/analysis",
                                json=analysis_payload,
                                timeout=90  # Increased for Bedrock Claude processing
                            )
                            
                            logger.info(f"Analysis response status: {analysis_response.status_code}")
                            st.write(f"📥 **디버그:** 분석 응답 상태 - {analysis_response.status_code}")
                            
                            if analysis_response.status_code == 200:
                                response_data = analysis_response.json()
                                logger.info(f"Analysis response: {response_data}")
                                st.write("📊 **디버그:** 분석 응답 데이터:")
                                st.json(response_data)
                                
                                # Store analysis result in session state immediately
                                if 'analysis' in response_data:
                                    if not st.session_state.session_data:
                                        st.session_state.session_data = {'results': {}}
                                    if 'results' not in st.session_state.session_data:
                                        st.session_state.session_data['results'] = {}
                                    st.session_state.session_data['results']['analysis'] = response_data['analysis']
                                    st.write("✅ **디버그:** 분석 결과를 세션 상태에 저장했습니다!")
                                    
                                    # Disable polling since we have the result
                                    st.session_state.polling_active = False
                                    st.write("✅ **디버그:** 폴링 비활성화 - 결과를 받았습니다!")
                                
                                st.success("✅ 비즈니스 분석 완료!")
                                st.info("💡 페이지를 새로고침하면 '다음 단계: 상호명 제안' 버튼이 표시됩니다.")
                                st.info("💡 또는 아래로 스크롤하여 분석 결과를 확인하세요!")
                            else:
                                st.warning(f"⚠️ 분석 응답: {analysis_response.status_code}")
                                st.write(f"❌ **디버그:** 응답 내용: {analysis_response.text}")
                        except Exception as e:
                            logger.error(f"Analysis error: {str(e)}", exc_info=True)
                            st.error(f"분석 오류: {str(e)}")
                            st.write(f"❌ **디버그:** 예외 발생 - {type(e).__name__}: {str(e)}")
                    
                    time.sleep(2)  # Give time to read debug info
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
        
        # Next step button
        st.markdown("---")
        if st.button("➡️ 다음 단계: 상호명 제안", key="next_to_names", type="primary"):
            # 비동기 폴링 방식으로 상호명 생성
            try:
                logger.info(f"Starting async name generation for session: {st.session_state.session_id}")
                logger.info(f"API URL: {API_BASE_URL}/names/suggest")
                
                # 1. 비동기 요청 시작 (재시도 포함) - 로딩창 표시
                with st.spinner("🚀 상호명 생성 요청 중..."):
                    start_success = False
                    for start_attempt in range(3):  # 최대 3회 재시도
                        try:
                            logger.info(f"Async request attempt {start_attempt + 1}/3")
                            start_response = requests.post(
                                f"{API_BASE_URL}/names/suggest",
                                headers={'x-async-mode': 'true'},
                                json={
                                    "sessionId": st.session_state.session_id,
                                    "businessInfo": st.session_state.business_info,
                                    "analysisResult": analysis
                                },
                                timeout=90  # Increased for Bedrock processing + Lambda cold start
                            )
                            
                            if start_response.status_code == 202:
                                logger.info("Name generation started successfully")
                                start_success = True
                                st.success("✅ 상호명 생성이 시작되었습니다!")
                                break
                            else:
                                error_msg = f"상호명 생성 시작 실패: {start_response.status_code}"
                                logger.error(error_msg)
                                logger.error(f"Response: {start_response.text}")
                                if start_attempt >= 2:  # 마지막 시도
                                    st.error(error_msg)
                                    st.json(start_response.json())
                                    return
                                time.sleep(1)  # 재시도 전 대기 (2초 → 1초)
                        
                        except requests.Timeout:
                            logger.warning(f"Start request timeout (attempt {start_attempt + 1}/3)")
                            if start_attempt >= 2:  # 마지막 시도
                                st.error("⏱️ 요청 시작 타임아웃: Lambda 함수가 응답하지 않습니다.")
                                st.info("💡 잠시 후 다시 시도하거나, CloudWatch 로그를 확인하세요.")
                                return
                            time.sleep(1)  # 재시도 전 대기 (2초 → 1초)
                        
                        except Exception as e:
                            logger.error(f"Start request error: {str(e)}")
                            if start_attempt >= 2:  # 마지막 시도
                                raise
                            time.sleep(1)  # 재시도 전 대기 (2초 → 1초)
                
                if not start_success:
                    st.error("상호명 생성을 시작할 수 없습니다.")
                    return
                
                # 2. 폴링으로 결과 대기 - 진행률 표시
                st.info("💡 AI가 비즈니스에 최적화된 상호명을 생성하고 있습니다...")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                max_attempts = 90  # 90 * 2초 = 180초 (Lambda 최대 실행 시간 고려)
                for attempt in range(max_attempts):
                    time.sleep(2)  # 폴링 주기: 3초 → 2초
                    
                    try:
                        status_response = requests.get(
                            f"{API_BASE_URL}/names/status/{st.session_state.session_id}",
                            timeout=15  # Status 조회는 빠르지만 여유있게
                        )
                        
                        progress = min((attempt + 1) / max_attempts, 0.95)
                        progress_bar.progress(progress)
                        elapsed = (attempt + 1) * 2  # 2초 주기로 변경
                        status_text.text(f"🔄 상호명 생성 중... ({elapsed}초 경과 / 최대 180초)")
                        
                        # HTTP status code가 아닌 body의 statusCode 확인
                        status_data = status_response.json()
                        body_status_code = status_data.get('statusCode')
                        
                        if body_status_code == 200:
                            # 완료
                            progress_bar.progress(1.0)
                            status_text.text("✅ 완료!")
                            logger.info("Name generation completed successfully")
                            
                            # 세션 데이터 업데이트
                            suggestions = status_data.get('suggestions', [])
                            if not st.session_state.session_data:
                                st.session_state.session_data = {}
                            if 'results' not in st.session_state.session_data:
                                st.session_state.session_data['results'] = {}
                            
                            st.session_state.session_data['results']['names'] = {
                                'suggestions': suggestions,
                                'selected_name': None,
                                'regeneration_count': 0,
                                'max_regenerations': 3
                            }
                            
                            st.success("✅ 상호명 생성 완료!")
                            time.sleep(1)
                            st.session_state.current_step = 2
                            st.rerun()
                            return
                        
                        elif body_status_code == 202:
                            # 진행 중
                            logger.debug(f"Still processing... (attempt {attempt + 1}/{max_attempts})")
                            continue
                        
                        elif body_status_code == 500:
                            # 실패
                            error_msg = f"상호명 생성 실패: {status_data.get('error', 'Unknown error')}"
                            logger.error(error_msg)
                            st.error(error_msg)
                            return
                        
                        else:
                            logger.warning(f"Unexpected status: {body_status_code}")
                            continue
                    
                    except requests.Timeout:
                        logger.warning(f"Status check timeout (attempt {attempt + 1})")
                        continue
                    
                    except Exception as e:
                        logger.error(f"Status check error: {str(e)}")
                        if attempt >= max_attempts - 1:
                            raise
                        continue
                
                # 타임아웃
                error_msg = "⏱️ 요청 시간 초과: 180초를 초과했습니다."
                logger.error(error_msg)
                st.error(error_msg)
                st.info("💡 Lambda 함수가 계속 실행 중일 수 있습니다. 잠시 후 페이지를 새로고침하세요.")
                st.info("💡 CloudWatch 로그를 확인하여 Lambda 실행 상태를 확인할 수 있습니다.")
                
            except requests.exceptions.RequestException as e:
                error_msg = f"네트워크 오류: {str(e)}"
                logger.error(error_msg)
                st.error(error_msg)
            except Exception as e:
                error_msg = f"예상치 못한 오류: {str(e)}"
                logger.error(error_msg)
                logger.exception("Full traceback:")
                st.error(error_msg)

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
                            <div>발음: {suggestion.get("pronunciationScore", 0):.1f}/100</div>
                            <div>검색: {suggestion.get("searchScore", 0):.1f}/100</div>
                            <div><strong>종합: {suggestion.get("overallScore", 0):.1f}/100</strong></div>
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
    signboard_data = results.get("signboard")
    
    if signboard_data:
        # API returns 'signboards' array
        images = signboard_data.get("signboards", [])
        
        # Fallback: check for 'images' key
        if not images:
            images = signboard_data.get("images", [])
        
        # Fallback: check for single image format
        if not images and signboard_data.get("imageUrl"):
            images = [{
                "url": signboard_data.get("imageUrl"),
                "s3Key": signboard_data.get("s3Key"),
                "provider": signboard_data.get("provider", "bedrock"),
                "style": signboard_data.get("style", "modern"),
                "generatedAt": signboard_data.get("timestamp", "")
            }]
        
        selected_url = signboard_data.get("selected_image_url")
        
        st.markdown("### 🪧 간판 디자인")
        
        if images:
            # Display image gallery
            cols = st.columns(min(len(images), 3))  # Max 3 columns
            
            for i, image in enumerate(images):
                with cols[i % 3]:
                    # Image card
                    is_selected = selected_url == image.get("url")
                    border_color = "#4CAF50" if is_selected else "#ddd"
                    
                    st.markdown(f"""
                    <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 10px; margin: 5px;">
                        <div style="text-align: center;">
                            <strong>{image.get("provider", "AI").upper()}</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display image from S3 URL
                    image_url = image.get("url")
                    if image_url:
                        try:
                            st.image(
                                image_url,
                                caption=f"{image.get('style', 'Modern')} 스타일",
                                width='stretch'
                            )
                        except Exception as e:
                            logger.error(f"Image load error: {str(e)}")
                            st.error("이미지 로드 실패")
                            st.code(image_url)
                    
                    # Image details
                    st.write(f"**스타일:** {image.get('style', 'N/A')}")
                    
                    # Check both 'generatedAt' and 'generated_at'
                    generated_at = image.get('generatedAt') or image.get('generated_at')
                    if generated_at:
                        st.write(f"**생성시간:** {generated_at[:16]}")
                    
                    # Check both 'isFallback' and 'is_fallback'
                    is_fallback = image.get("isFallback") or image.get("is_fallback")
                    if is_fallback:
                        st.warning("⚠️ 폴백 이미지 (AI 생성 실패 시 대체)")
                    
                    # Selection button
                    if not is_selected:
                        if st.button(f"이 디자인 선택", key=f"select_signboard_{i}"):
                            select_signboard_image(image.get("url"))
                    else:
                        st.success("✓ 선택됨")
            

        else:
            st.warning("간판 이미지가 없습니다.")
            if st.button("간판 생성 다시 시도"):
                st.session_state.current_step = 2
                st.rerun()
    else:
        st.info("간판 디자인을 생성하려면 상호명을 먼저 선택하세요.")
        if st.button("상호명 선택으로 돌아가기"):
            st.session_state.current_step = 2
            st.rerun()

def manual_refresh_interior_status():
    """Manually refresh interior generation status"""
    try:
        # Rate limiting check
        current_time = time.time()
        last_refresh = st.session_state.get('last_interior_refresh_time', 0)
        
        if current_time - last_refresh < 2:
            st.warning("⏱️ 너무 빠른 요청입니다. 2초 후에 다시 시도하세요.")
            return
        
        # Update last refresh time
        st.session_state.last_interior_refresh_time = current_time
        
        with st.spinner("🔄 상태를 확인하는 중..."):
            # Query DynamoDB directly via API
            status_data = get_session_status(st.session_state.session_id)
            
            if not status_data:
                st.error("❌ 세션 데이터를 가져올 수 없습니다.")
                return
            
            # Parse interior data (with backward compatibility)
            recommendations = []
            generated_images = 0
            
            # Try new format: 'interiors' field
            if 'interiors' in status_data:
                interior_data = status_data['interiors']
                if isinstance(interior_data, list):
                    recommendations = interior_data
                    generated_images = sum(1 for rec in recommendations if rec.get('imageUrl'))
                elif isinstance(interior_data, dict):
                    recommendations = interior_data.get('recommendations', [])
                    generated_images = interior_data.get('generatedImages', 0)
            
            # Fallback: old format 'interior_recommendations'
            elif 'interior_recommendations' in status_data:
                try:
                    interior_str = status_data['interior_recommendations']
                    if isinstance(interior_str, str):
                        interior_parsed = json.loads(interior_str)
                        recommendations = interior_parsed.get('recommendations', [])
                        generated_images = sum(1 for rec in recommendations if rec.get('imageUrl'))
                    else:
                        recommendations = interior_str.get('recommendations', [])
                        generated_images = sum(1 for rec in recommendations if rec.get('imageUrl'))
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {str(e)}")
                    st.error("❌ 데이터 형식 오류가 발생했습니다.")
                    return
            
            total_recommendations = len(recommendations)
            interior_status = status_data.get('interiorGenerationStatus', 'unknown')
            
            # Update session state
            if recommendations:
                if not st.session_state.session_data:
                    st.session_state.session_data = {}
                if 'results' not in st.session_state.session_data:
                    st.session_state.session_data['results'] = {}
                st.session_state.session_data['results']['interiors'] = {
                    'recommendations': recommendations,
                    'generatedImages': generated_images,
                    'totalRecommendations': total_recommendations
                }
            
            # Show result
            if interior_status == "completed" or generated_images == total_recommendations:
                st.success(f"✅ 인테리어 생성 완료! ({generated_images}/{total_recommendations} 이미지)")
                st.session_state.current_step = 4
                st.session_state.interior_timeout = False
                time.sleep(1)
                st.rerun()
            elif generated_images > 0:
                st.info(f"🎨 진행 중: {generated_images}/{total_recommendations} 이미지 생성됨")
            else:
                st.warning(f"⏳ 아직 생성 중입니다... (상태: {interior_status})")
                
    except Exception as e:
        logger.error(f"Manual refresh error: {str(e)}")
        st.error(f"❌ 새로고침 오류: {str(e)}")

def display_interior_options():
    """Display interior design options with selection interface"""
    results = st.session_state.session_data.get("results", {}) if st.session_state.session_data else {}
    interior_data = results.get("interiors")
    
    # Show manual refresh button if timeout occurred or in progress
    # Check both session_data root level and results level for interiorGenerationStatus
    interior_status = None
    if st.session_state.session_data:
        interior_status = st.session_state.session_data.get('interiorGenerationStatus')
        if not interior_status and results:
            interior_status = results.get('interiorGenerationStatus')
    
    show_refresh = st.session_state.get('interior_timeout', False) or interior_status == "in_progress"
    
    if show_refresh and not interior_data:
        st.markdown("### 🏠 인테리어 추천")
        st.info("🎨 인테리어 이미지를 생성하고 있습니다...")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 상태 새로고침", key="refresh_interior_status", use_container_width=True):
                manual_refresh_interior_status()
        
        st.markdown("---")
        return
    
    if interior_data:
        recommendations = interior_data.get("recommendations", [])
        selected_style = interior_data.get("selected_style")
        
        st.markdown("### 🏠 인테리어 추천")
        
        if recommendations:
            # Display interior recommendations
            for i, rec in enumerate(recommendations):
                style = rec.get("style", "N/A")
                is_selected = selected_style == style
                border_color = "#4CAF50" if is_selected else "#ddd"
                
                # Expandable card for each recommendation
                with st.expander(f"{'✓ ' if is_selected else ''}옵션 {i+1}: {style.upper()} 스타일", expanded=(i == 0)):
                    st.markdown(f"""
                    <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 15px; margin: 10px 0;">
                    """, unsafe_allow_html=True)
                    
                    # Interior image (if available)
                    image_url = rec.get("imageUrl")
                    provider = rec.get("provider")
                    
                    if image_url:
                        try:
                            # Provider badge
                            provider_label = ""
                            if provider == "bedrock-sdxl":
                                provider_label = "🎨 Amazon Bedrock SDXL"
                            elif provider == "openai-dalle3":
                                provider_label = "🤖 OpenAI DALL-E 3"
                            else:
                                provider_label = "🎨 AI Generated"
                            
                            st.image(image_url, caption=f"{style.upper()} 스타일 인테리어", use_container_width=True)
                            st.caption(f"생성: {provider_label}")
                        except Exception as e:
                            st.warning(f"이미지 로드 실패: {str(e)}")
                    else:
                        st.info("🎨 인테리어 이미지 생성 중...")
                    
                    # Description
                    st.markdown(f"**설명:**")
                    st.write(rec.get("description", ""))
                    
                    # Suitability score
                    score = rec.get("suitabilityScore", 0)
                    st.progress(score / 100.0)
                    st.caption(f"적합도: {score}/100")
                    
                    # Details in columns
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Color scheme
                        st.markdown("**색상 팔레트:**")
                        colors = rec.get("colorScheme", [])
                        for color in colors:
                            st.markdown(f"- {color}")
                        
                        # Materials
                        st.markdown("**소재:**")
                        materials = rec.get("materials", [])
                        for material in materials:
                            st.markdown(f"- {material}")
                    
                    with col2:
                        # Furniture
                        st.markdown("**가구:**")
                        furniture = rec.get("furniture", [])
                        for item in furniture:
                            st.markdown(f"- {item}")
                        
                        # Cost
                        st.markdown(f"**예상 비용:** {rec.get('estimatedCost', 'N/A')}")
                    
                    # Pros and Cons
                    col3, col4 = st.columns(2)
                    
                    with col3:
                        st.markdown("**장점:**")
                        pros = rec.get("pros", [])
                        for pro in pros:
                            st.markdown(f"✅ {pro}")
                    
                    with col4:
                        st.markdown("**단점:**")
                        cons = rec.get("cons", [])
                        for con in cons:
                            st.markdown(f"⚠️ {con}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Selection button
                    if not is_selected:
                        if st.button(f"이 스타일 선택", key=f"select_interior_{i}"):
                            select_interior_option(style)
                    else:
                        st.success("✓ 선택된 스타일")
        else:
            st.info("인테리어 추천 데이터가 없습니다.")
    else:
        st.info("인테리어 추천을 생성하려면 간판 디자인을 먼저 선택하세요.")

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
    """Select a business name and trigger signboard generation"""
    try:
        logger.info(f"Selecting business name: {name}")
        
        # Update session state with selected name
        if not st.session_state.session_data:
            st.session_state.session_data = {}
        if 'results' not in st.session_state.session_data:
            st.session_state.session_data['results'] = {}
        if 'names' not in st.session_state.session_data['results']:
            st.session_state.session_data['results']['names'] = {}
        
        st.session_state.session_data['results']['names']['selected_name'] = name
        
        st.success(f"✅ '{name}' 상호명이 선택되었습니다!")
        
        # 비동기 폴링 방식으로 간판 생성 (상호명 생성과 동일한 패턴)
        try:
            logger.info(f"Starting async signboard generation for session: {st.session_state.session_id}")
            logger.info(f"API URL: {API_BASE_URL}/signboards/generate")
            
            # 1. 비동기 요청 시작 (재시도 포함)
            with st.spinner("🚀 간판 생성 요청 중..."):
                start_success = False
                for start_attempt in range(3):  # 최대 3회 재시도
                    try:
                        logger.info(f"Async signboard request attempt {start_attempt + 1}/3")
                        start_response = requests.post(
                            f"{API_BASE_URL}/signboards/generate",
                            headers={'x-async-mode': 'true'},
                            json={
                                "sessionId": st.session_state.session_id,
                                "selectedName": name,
                                "businessInfo": st.session_state.business_info
                            },
                            timeout=10  # 짧은 타임아웃 (비동기 시작만)
                        )
                        
                        if start_response.status_code == 202:
                            logger.info("Signboard generation started successfully")
                            start_success = True
                            st.success("✅ 간판 생성이 시작되었습니다!")
                            break
                        else:
                            error_msg = f"간판 생성 시작 실패: {start_response.status_code}"
                            logger.error(error_msg)
                            logger.error(f"Response: {start_response.text}")
                            if start_attempt >= 2:  # 마지막 시도
                                st.error(error_msg)
                                try:
                                    st.json(start_response.json())
                                except:
                                    st.text(start_response.text)
                                return
                            time.sleep(1)
                    
                    except requests.Timeout:
                        logger.warning(f"Signboard start request timeout (attempt {start_attempt + 1}/3)")
                        if start_attempt >= 2:
                            st.error("⏱️ 요청 시작 타임아웃: Lambda 함수가 응답하지 않습니다.")
                            st.info("💡 잠시 후 다시 시도하거나, CloudWatch 로그를 확인하세요.")
                            return
                        time.sleep(1)
                    
                    except Exception as e:
                        logger.error(f"Signboard start request error: {str(e)}")
                        if start_attempt >= 2:
                            raise
                        time.sleep(1)
            
            if not start_success:
                st.error("간판 생성을 시작할 수 없습니다.")
                return
            
            # 2. 폴링으로 결과 대기 - 진행률 표시
            st.info(f"💡 AI가 '{name}' 상호명으로 3가지 스타일의 간판을 생성하고 있습니다...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            max_attempts = 30  # 30 * 3초 = 90초 (이미지 생성 시간 고려)
            for attempt in range(max_attempts):
                time.sleep(3)  # 폴링 주기: 3초
                
                try:
                    # 세션 데이터에서 간판 이미지 확인
                    session_response = requests.get(
                        f"{API_BASE_URL}/sessions/{st.session_state.session_id}",
                        timeout=10
                    )
                    
                    progress = min((attempt + 1) / max_attempts, 0.95)
                    progress_bar.progress(progress)
                    elapsed = (attempt + 1) * 3
                    status_text.text(f"🔄 간판 생성 중... ({elapsed}초 경과 / 최대 90초)")
                    
                    if session_response.status_code == 200:
                        session_data = session_response.json()
                        # Try both field names (camelCase and snake_case)
                        signboard_images = session_data.get('signboardImages') or session_data.get('signboard_images')
                        
                        if signboard_images:
                            # JSON 문자열인 경우 파싱
                            if isinstance(signboard_images, str):
                                signboard_images = json.loads(signboard_images)
                            
                            images = signboard_images.get('images', [])
                            
                            if images and len(images) > 0:
                                # 완료!
                                progress_bar.progress(1.0)
                                status_text.text("✅ 완료!")
                                logger.info(f"Signboard generation completed: {len(images)} images")
                                
                                # 세션 데이터 업데이트
                                if not st.session_state.session_data:
                                    st.session_state.session_data = {}
                                if 'results' not in st.session_state.session_data:
                                    st.session_state.session_data['results'] = {}
                                
                                st.session_state.session_data['results']['signboard'] = {
                                    'signboards': images
                                }
                                
                                st.success(f"✅ 간판 디자인 생성 완료! ({len(images)}개)")
                                time.sleep(1)
                                st.session_state.current_step = 3
                                st.rerun()
                                return
                
                except Exception as poll_error:
                    logger.warning(f"Poll attempt {attempt + 1} failed: {poll_error}")
                    continue
            
            # 타임아웃
            progress_bar.progress(1.0)
            status_text.text("⏱️ 타임아웃")
            st.error("⏱️ 간판 생성 타임아웃: 90초를 초과했습니다.")
            st.info("💡 Lambda 함수가 계속 실행 중일 수 있습니다. 잠시 후 페이지를 새로고침하세요.")
            
        except Exception as e:
            error_msg = f"간판 생성 오류: {str(e)}"
            logger.error(error_msg)
            logger.exception("Full traceback:")
            st.error(error_msg)
            
    except Exception as e:
        error_msg = f"상호명 선택 오류: {str(e)}"
        logger.error(error_msg)
        logger.exception("Full traceback:")
        st.error(error_msg)

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
    """Select a signboard image and start interior generation"""
    try:
        # Step 1: Select signboard
        response = requests.post(
            f"{API_BASE_URL}/signboards/select",
            json={"sessionId": st.session_state.session_id, "selectedImageUrl": image_url},
            timeout=10
        )
        
        if response.status_code == 200:
            st.success("✅ 간판 디자인이 선택되었습니다!")
            
            # Update session state
            if not st.session_state.session_data:
                st.session_state.session_data = {}
            if 'results' not in st.session_state.session_data:
                st.session_state.session_data['results'] = {}
            if 'signboards' not in st.session_state.session_data['results']:
                st.session_state.session_data['results']['signboards'] = {}
            st.session_state.session_data['results']['signboards']['selected_image_url'] = image_url
            
            # Step 2: Automatically start interior generation
            start_interior_generation()
            
        else:
            st.error("❌ 간판 선택에 실패했습니다.")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API 호출 오류: {str(e)}")

def start_interior_generation():
    """Start interior generation with async polling"""
    try:
        st.info("🎨 인테리어 추천 생성을 시작합니다...")
        
        # Start async interior generation
        interior_response = requests.post(
            f"{API_BASE_URL}/interiors/generate",
            headers={'x-async-mode': 'true'},  # Async mode
            json={
                "sessionId": st.session_state.session_id,
                "businessInfo": st.session_state.business_info
            },
            timeout=10
        )
        
        if interior_response.status_code == 202:
            st.success("✅ 인테리어 생성이 시작되었습니다!")
            
            # Poll for completion
            st.info("💡 AI가 인테리어 추천을 생성하고 있습니다...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            max_attempts = 45  # 45 * 2초 = 90초 (이미지 생성 시간 고려)
            for attempt in range(max_attempts):
                time.sleep(2)
                
                # Calculate elapsed time
                elapsed = (attempt + 1) * 2
                
                # Get session status
                status_data = get_session_status(st.session_state.session_id)
                
                if status_data:
                    # Check if interior data exists (with backward compatibility)
                    results = status_data.get('results', {})
                    interior_data = None
                    recommendations = []
                    generated_images = 0
                    
                    # Try new format first: 'interiors' field in results (Map type)
                    interior_data = results.get('interiors')
                    if interior_data:
                        if isinstance(interior_data, list):
                            recommendations = interior_data
                            # Count images with valid URLs
                            generated_images = sum(1 for rec in recommendations if rec.get('imageUrl'))
                        elif isinstance(interior_data, dict):
                            recommendations = interior_data.get('recommendations', [])
                            generated_images = interior_data.get('generatedImages', 0)
                            # Also count from recommendations if generatedImages is 0
                            if generated_images == 0 and recommendations:
                                generated_images = sum(1 for rec in recommendations if rec.get('imageUrl'))
                    
                    # Fallback: Try old format 'interior_recommendations' in root (JSON string)
                    elif 'interior_recommendations' in status_data:
                        try:
                            interior_str = status_data['interior_recommendations']
                            if isinstance(interior_str, str):
                                interior_parsed = json.loads(interior_str)
                                recommendations = interior_parsed.get('recommendations', [])
                                # Count images with valid URLs
                                generated_images = sum(1 for rec in recommendations if rec.get('imageUrl'))
                                logger.info(f"Parsed legacy JSON string format: {len(recommendations)} recommendations")
                            else:
                                recommendations = interior_str.get('recommendations', [])
                                generated_images = sum(1 for rec in recommendations if rec.get('imageUrl'))
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse interior_recommendations JSON: {str(e)}")
                            logger.error(f"Raw data: {status_data.get('interior_recommendations', '')[:200]}")
                    
                    # Check interiorGenerationStatus field (can be in root or results)
                    interior_status = status_data.get('interiorGenerationStatus')
                    if not interior_status:
                        interior_status = results.get('interiorGenerationStatus')
                    
                    total_recommendations = len(recommendations)
                    
                    # Debug logging
                    logger.info(f"Polling attempt {attempt + 1}: {generated_images}/{total_recommendations} images generated, status={interior_status}")
                    
                    # Check if all images are generated
                    if interior_status == "completed" or (total_recommendations > 0 and generated_images == total_recommendations):
                        # All images generated - complete!
                        progress_bar.progress(1.0)
                        status_text.text("✅ 완료!")
                        logger.info(f"Interior generation complete! {generated_images} images generated")
                        
                        # Update session state
                        if not st.session_state.session_data:
                            st.session_state.session_data = {}
                        if 'results' not in st.session_state.session_data:
                            st.session_state.session_data['results'] = {}
                        st.session_state.session_data['results']['interiors'] = {
                            'recommendations': recommendations,
                            'generatedImages': generated_images,
                            'totalRecommendations': total_recommendations
                        }
                        
                        st.success(f"✅ 인테리어 추천 완료! ({generated_images}개 이미지 생성)")
                        st.session_state.current_step = 4
                        time.sleep(1)
                        st.rerun()
                        return
                    elif total_recommendations > 0:
                        # Partial progress - show image generation status
                        status_text.text(f"🎨 인테리어 이미지 생성 중... ({generated_images}/{total_recommendations} 완료, {elapsed}초 경과)")
                
                # Update progress
                progress = min((attempt + 1) / max_attempts, 0.95)
                progress_bar.progress(progress)
                
                # Default status message
                if not status_data or not interior_data:
                    status_text.text(f"🔄 인테리어 생성 중... ({elapsed}초 경과 / 최대 90초)")
            
            # Timeout - show manual refresh button
            st.warning("⏱️ 인테리어 이미지 생성이 예상보다 오래 걸리고 있습니다.")
            st.info("💡 아래 '상태 새로고침' 버튼을 눌러 현재 상태를 확인하세요.")
            
            # Store timeout state and show refresh button immediately
            st.session_state.interior_timeout = True
            
            # Show manual refresh button right here
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🔄 상태 새로고침", key="refresh_interior_timeout", use_container_width=True):
                    # Query status immediately
                    status_data = get_session_status(st.session_state.session_id)
                    if status_data:
                        results = status_data.get('results', {})
                        interior_data = results.get('interiors')
                        if interior_data:
                            recommendations = interior_data.get('recommendations', [])
                            generated_images = interior_data.get('generatedImages', 0)
                            if generated_images > 0:
                                st.success(f"✅ 인테리어 생성 완료! ({generated_images}개 이미지)")
                                st.session_state.current_step = 4
                                st.session_state.interior_timeout = False
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.info(f"🎨 아직 생성 중입니다... ({generated_images}/{len(recommendations)} 완료)")
                        else:
                            st.warning("⏳ 아직 데이터가 없습니다. 잠시 후 다시 시도하세요.")
                    else:
                        st.error("❌ 세션 데이터를 가져올 수 없습니다.")
            
        else:
            st.warning(f"⚠️ 인테리어 생성 시작 실패: {interior_response.status_code}")
            
    except Exception as e:
        st.error(f"❌ 인테리어 생성 오류: {str(e)}")

def select_interior_option(style: str):
    """Select an interior option and trigger report generation"""
    try:
        logger.info(f"Selecting interior style: {style}")
        
        # Update session state with selected interior
        if not st.session_state.session_data:
            st.session_state.session_data = {}
        if 'results' not in st.session_state.session_data:
            st.session_state.session_data['results'] = {}
        if 'interiors' not in st.session_state.session_data['results']:
            st.session_state.session_data['results']['interiors'] = {}
        
        st.session_state.session_data['results']['interiors']['selected_style'] = style
        
        # Save selected interior to DynamoDB via API
        try:
            save_response = requests.post(
                f"{API_BASE_URL}/interiors/select",
                json={
                    "sessionId": st.session_state.session_id,
                    "selectedStyle": style
                },
                timeout=10
            )
            if save_response.status_code == 200:
                logger.info(f"Selected interior saved to session: {style}")
            else:
                logger.warning(f"Failed to save selected interior: {save_response.status_code}")
        except Exception as e:
            logger.warning(f"Error saving selected interior: {str(e)}")
        
        st.success("✅ 인테리어 옵션이 선택되었습니다!")
        
        # Automatically trigger report generation
        with st.spinner("📄 AI가 분석, 상호명, 간판, 인테리어를 종합하여 최종 브랜딩 보고서를 생성하고 있습니다... (최대 60초 소요)"):
            try:
                report_response = requests.post(
                    f"{API_BASE_URL}/report/generate",  # Fixed: /report not /reports
                    json={
                        "sessionId": st.session_state.session_id,
                        "businessInfo": st.session_state.business_info
                    },
                    timeout=120  # Extended timeout for Bedrock processing
                )
                
                logger.info(f"Report API response: {report_response.status_code}")
                
                if report_response.status_code == 200:
                    result = report_response.json()
                    logger.info(f"Report result: {result}")
                    
                    # Store report data
                    st.session_state.session_data['results']['report'] = result
                    
                    st.success("✅ 보고서 생성 완료!")
                    st.balloons()  # Celebration!
                    time.sleep(1)
                    st.session_state.current_step = 5
                    st.rerun()
                else:
                    error_msg = f"보고서 생성 실패: {report_response.status_code}"
                    logger.error(error_msg)
                    logger.error(f"Response: {report_response.text}")
                    st.error(error_msg)
                    
            except requests.Timeout:
                st.error("⏱️ 보고서 생성 타임아웃: 60초를 초과했습니다.")
                st.info("💡 Lambda 함수가 계속 실행 중일 수 있습니다. 잠시 후 페이지를 새로고침하세요.")
            except Exception as e:
                error_msg = f"보고서 생성 오류: {str(e)}"
                logger.error(error_msg)
                logger.exception("Full traceback:")
                st.error(error_msg)
            
    except Exception as e:
        error_msg = f"인테리어 선택 오류: {str(e)}"
        logger.error(error_msg)
        logger.exception("Full traceback:")
        st.error(error_msg)

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
            # downloadUrl (camelCase) 또는 download_url (snake_case) 모두 지원
            download_url = data.get("downloadUrl") or data.get("download_url")
            file_name = data.get("fileName", "branding_report")
            
            if download_url:
                st.markdown(f"### 📥 보고서 다운로드")
                st.markdown(f"[**{file_name} 다운로드**]({download_url})")
                st.info("💡 링크는 10분간 유효합니다.")
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
    
    # Load session data if session exists but data is not loaded
    if st.session_state.session_id and not st.session_state.session_data:
        logger.info(f"Loading session data for {st.session_state.session_id}")
        status_data = get_session_status(st.session_state.session_id)
        if status_data:
            st.session_state.session_data = status_data
            st.session_state.current_step = status_data.get("currentStep", 1)
            logger.info(f"Session data loaded: currentStep={st.session_state.current_step}")
    
    # Header
    st.title("🎨 AI 브랜딩 챗봇")
    st.markdown("**5단계 자동 워크플로로 완전한 브랜딩 패키지를 생성하세요**")
    
    # Sidebar with session info
    with st.sidebar:
        st.markdown("### 세션 정보")
        if st.session_state.session_id:
            st.success(f"세션 ID: {st.session_state.session_id[:8]}...")
            st.write(f"현재 단계: {st.session_state.current_step}/5")
            
            # Auto-refresh toggle
            auto_refresh = st.checkbox("자동 새로고침", value=st.session_state.polling_active)
            st.session_state.polling_active = auto_refresh
            
            # Manual refresh button
            if st.button("상태 새로고침"):
                poll_session_status()
                st.rerun()
            
            # Force next step button (for debugging)
            st.markdown("---")
            st.markdown("### 🔧 디버그 도구")
            
            if st.button("🔄 강제로 다음 단계 실행"):
                current_step = st.session_state.current_step
                session_id = st.session_state.session_id
                business_info = st.session_state.business_info
                
                st.write(f"현재 단계: {current_step}")
                
                if current_step == 1:
                    # Force analysis
                    with st.spinner("분석 강제 실행 중..."):
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/analysis",
                                json={"sessionId": session_id, "businessInfo": business_info},
                                timeout=90  # Increased for Bedrock processing
                            )
                            st.write(f"응답 상태: {response.status_code}")
                            st.json(response.json())
                        except Exception as e:
                            st.error(f"오류: {str(e)}")
                
                elif current_step == 2:
                    # Force name generation
                    with st.spinner("상호명 강제 생성 중..."):
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/names/suggest",
                                json={"sessionId": session_id, "businessInfo": business_info},
                                timeout=90  # Increased for Bedrock reasoning
                            )
                            st.write(f"응답 상태: {response.status_code}")
                            st.json(response.json())
                        except Exception as e:
                            st.error(f"오류: {str(e)}")
            
            # Reset session button
            st.markdown("---")
            if st.button("🆕 새 세션 시작", type="primary"):
                logger.info("Resetting session")
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
        # Debug banner at top
        with st.expander("🔍 디버그 정보", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("세션 ID", st.session_state.session_id[:12] + "...")
                st.metric("현재 단계", f"{st.session_state.current_step}/5")
            with col2:
                st.metric("폴링 상태", "활성" if st.session_state.polling_active else "비활성")
                has_analysis = bool(st.session_state.session_data and st.session_state.session_data.get("results", {}).get("analysis"))
                st.metric("분석 결과", "있음" if has_analysis else "없음")
            with col3:
                if st.button("📊 세션 상태 조회", key="check_status"):
                    with st.spinner("세션 상태 조회 중..."):
                        try:
                            status_response = requests.get(
                                f"{API_BASE_URL}/status/{st.session_state.session_id}",
                                timeout=10
                            )
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                st.json(status_data)
                                # Update session data
                                st.session_state.session_data = status_data
                            else:
                                st.error(f"상태 조회 실패: {status_response.status_code}")
                        except Exception as e:
                            st.error(f"오류: {str(e)}")
        
        # Display progress bar
        display_progress_bar()
        
        # Display agent status
        display_agent_status()
        
        # Display error recovery if there are errors
        display_error_recovery()
        
        # Display reasoning chain
        display_reasoning_chain()
        
        # Poll status if active (optimized to 2 seconds)
        if st.session_state.polling_active:
            poll_session_status()
            time.sleep(2)  # Optimized: 5초 → 2초
            st.rerun()
        
        # Display current step content
        if st.session_state.current_step == 1:
            display_analysis_results()
            if not st.session_state.session_data or not st.session_state.session_data.get("results", {}).get("analysis"):
                st.warning("⚠️ 비즈니스 분석 결과가 없습니다!")
                st.info("💡 사이드바의 '강제로 다음 단계 실행' 버튼을 눌러 분석을 시작하세요.")
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