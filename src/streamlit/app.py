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
    {"id": 1, "name": "Business Analysis", "agent": "product_insight", "description": "Industry/Region/Size Analysis"},
    {"id": 2, "name": "Name Suggestions", "agent": "reporter", "description": "Generate 3 Business Names"},
    {"id": 3, "name": "Signboard Design", "agent": "signboard", "description": "AI Signboard Image Generation"},
    {"id": 4, "name": "Interior Recommendations", "agent": "interior", "description": "Customized Interior Design"},
    {"id": 5, "name": "Report Generation", "agent": "report_generator", "description": "Comprehensive Branding Report"}
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
    st.markdown("### Workflow Progress")
    
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
        st.metric("Progress", f"{int(progress * 100)}%")
    with col2:
        st.metric("Current Step", f"{st.session_state.current_step}/{len(WORKFLOW_STEPS)}")
    with col3:
        # Calculate estimated time remaining (rough estimate)
        if st.session_state.current_step > 1:
            # Estimate based on average time per step (assuming 1 minute per step)
            remaining_steps = len(WORKFLOW_STEPS) - st.session_state.current_step
            estimated_minutes = remaining_steps * 1
            st.metric("Est. Time Remaining", f"~{estimated_minutes}min")

def display_agent_status():
    """Display real-time agent execution status"""
    if st.session_state.agent_status:
        st.markdown("### Agent Execution Status")
        
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
                latency_text = f"{latency}ms" if latency > 0 else "Waiting"
                
                st.markdown(f"""
                <div style="padding: 8px; border: 1px solid #ddd; border-radius: 5px; margin: 2px;">
                    <div>{status_icon} <strong>{agent_name}</strong></div>
                    <div style="font-size: 12px;">Response Time: {latency_text}</div>
                </div>
                """, unsafe_allow_html=True)

def display_reasoning_chain():
    """Display reasoning chain from Bedrock Claude (expandable section)"""
    if st.session_state.reasoning_chain and len(st.session_state.reasoning_chain) > 0:
        with st.expander("🧠 AI Decision-Making Process (Reasoning Chain)", expanded=False):
            st.markdown("**Bedrock Claude's Chain-of-Thought Reasoning Process**")
            
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
                    confidence_label = "High"
                elif confidence >= 0.6:
                    confidence_color = "orange"
                    confidence_label = "Medium"
                else:
                    confidence_color = "red"
                    confidence_label = "Low"
                
                st.markdown(f"""
                <div style="border-left: 4px solid #4CAF50; padding: 10px; margin: 10px 0; background-color: #f9f9f9;">
                    <div style="font-weight: bold; margin-bottom: 5px;">
                        Step {step_number}: {agent_name}
                        <span style="float: right; color: {confidence_color};">
                            Confidence: {confidence:.2f} ({confidence_label})
                        </span>
                    </div>
                    <div style="font-size: 12px; color: #666; margin-bottom: 8px;">
                        {timestamp[:19] if timestamp else ""}
                    </div>
                    <div style="margin-bottom: 8px;">
                        <strong>Reasoning Process:</strong><br/>
                        {reasoning}
                    </div>
                    <div style="background-color: #e8f5e9; padding: 8px; border-radius: 4px;">
                        <strong>Decision:</strong> {decision}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show alternatives if available
                alternatives = step.get("alternatives", [])
                if alternatives:
                    st.markdown("**Alternatives Considered:**")
                    for alt in alternatives[:3]:  # Show max 3 alternatives
                        st.markdown(f"- {alt}")
                
                st.markdown("---")

def display_error_recovery():
    """Display error recovery strategy when errors occur"""
    if st.session_state.error_recovery:
        error_info = st.session_state.error_recovery
        
        st.warning("⚠️ Error Occurred - Auto Recovery in Progress")
        
        with st.expander("🔧 Error Recovery Strategy", expanded=True):
            error_type = error_info.get("error_type", "Unknown")
            error_message = error_info.get("error_message", "")
            recovery_strategy = error_info.get("recovery_strategy", "")
            retry_count = error_info.get("retry_count", 0)
            max_retries = error_info.get("max_retries", 3)
            fallback_used = error_info.get("fallback_used", False)
            
            st.markdown(f"""
            <div style="padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                <div style="font-weight: bold; margin-bottom: 10px;">
                    Error Type: {error_type}
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>Error Message:</strong><br/>
                    {error_message}
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>Recovery Strategy:</strong><br/>
                    {recovery_strategy}
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>retry Count:</strong> {retry_count}/{max_retries}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if fallback_used:
                st.info("🔄 Fallback mechanism activated. Continuing with OpenAI/Gemini.")
            
            # Show recovery actions
            recovery_actions = error_info.get("recovery_actions", [])
            if recovery_actions:
                st.markdown("**Recovery Actions Performed:**")
                for action in recovery_actions:
                    st.markdown(f"✓ {action}")
            
            # Show next steps
            if retry_count < max_retries:
                st.info(f"🔄 Automatically retrying... ({retry_count + 1}/{max_retries})")
            elif not fallback_used:
                st.warning("⚠️ Maximum retry count reached. Attempting fallback mechanism.")
            else:
                st.error("❌ Recovery failed. User intervention required.")

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
            st.error(f"Session creation failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                st.error(f"Error details: {error_data}")
            except:
                st.error(f"Response content: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API server")
        st.info("Start the API server: `./scripts/dev.sh api`")
        return None
    except requests.exceptions.Timeout:
        st.error("⏰ API response timeout (30s)")
        st.info("Server may be starting or overloaded. Please try again later.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"API call error: {str(e)}")
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
                st.success("Workflow completed!")
            elif status_data.get("status") == "failed":
                st.session_state.polling_active = False
                st.error("An error occurred during workflow execution.")

def step1_business_analysis():
    """Step 1: Business Information Input and Analysis"""
    st.markdown("## Step 1: Business Information Input")
    
    with st.form("business_info_form"):
        st.markdown("### Basic Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            industry = st.selectbox(
                "Select Industry",
                options=INDUSTRIES,
                format_func=lambda x: {
                    "restaurant": "Restaurant/Cafe",
                    "retail": "Retail",
                    "service": "Service",
                    "healthcare": "Healthcare",
                    "education": "Education",
                    "technology": "Technology/IT",
                    "manufacturing": "Manufacturing",
                    "construction": "Construction",
                    "finance": "Finance",
                    "other": "Other"
                }.get(x, x)
            )
            
            region = st.selectbox(
                "Select Region",
                options=REGIONS,
                format_func=lambda x: {
                    "seoul": "Seoul",
                    "busan": "Busan",
                    "daegu": "Daegu",
                    "incheon": "Incheon",
                    "gwangju": "Gwangju",
                    "daejeon": "Daejeon",
                    "ulsan": "Ulsan",
                    "gyeonggi": "Gyeonggi",
                    "gangwon": "Gangwon",
                    "chungbuk": "Chungbuk",
                    "chungnam": "Chungnam",
                    "jeonbuk": "Jeonbuk",
                    "jeonnam": "Jeonnam",
                    "gyeongbuk": "Gyeongbuk",
                    "gyeongnam": "Gyeongnam",
                    "jeju": "Jeju"
                }.get(x, x)
            )
        
        with col2:
            size = st.selectbox(
                "Business Size",
                options=SIZES,
                format_func=lambda x: {
                    "small": "Small (1-10 employees)",
                    "medium": "Medium (11-50 employees)",
                    "large": "Large (50+ employees)"
                }.get(x, x)
            )
        
        description = st.text_area(
            "Business Description (Optional)",
            placeholder="Enter a brief description of your business...",
            height=100
        )
        
        # Image upload
        uploaded_file = st.file_uploader(
            "Upload Reference Image (Optional)",
            type=['png', 'jpg', 'jpeg'],
            help="Upload an image for branding reference"
        )
        
        submitted = st.form_submit_button("Start Analysis", type="primary")
        
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
                st.info("Image uploaded. (Actual S3 upload is handled by backend)")
            
            # Create session
            with st.spinner("Creating session and starting analysis..."):
                # Create session without autoStart (we'll trigger steps manually)
                session_request = {
                    "businessInfo": business_info
                }
                logger.info(f"Creating session with: {session_request}")
                st.write("🔍 **Debug:** Requesting session creation...")
                
                session_id = create_session(session_request)
                
                if session_id:
                    logger.info(f"Session created: {session_id}")
                    st.write(f"✅ **Debug:** Session created - {session_id}")
                    
                    st.session_state.session_id = session_id
                    st.session_state.business_info = business_info
                    st.session_state.current_step = 1
                    st.session_state.polling_active = True
                    st.success(f"Session created: {session_id}")
                    
                    # Start Step 1: Business Analysis
                    st.write("🔍 **Debug:** Calling business analysis API...")
                    with st.spinner("🔍 AI is analyzing industry, region, and market trends..."):
                        try:
                            analysis_payload = {
                                "sessionId": session_id,
                                "businessInfo": business_info
                            }
                            logger.info(f"Calling analysis API with: {analysis_payload}")
                            st.write(f"📤 **Debug:** analysis Request - {API_BASE_URL}/analysis")
                            
                            analysis_response = requests.post(
                                f"{API_BASE_URL}/analysis",
                                json=analysis_payload,
                                timeout=90  # Increased for Bedrock Claude processing
                            )
                            
                            logger.info(f"Analysis response status: {analysis_response.status_code}")
                            st.write(f"📥 **Debug:** analysis Response Status - {analysis_response.status_code}")
                            
                            if analysis_response.status_code == 200:
                                response_data = analysis_response.json()
                                logger.info(f"Analysis response: {response_data}")
                                st.write("📊 **Debug:** analysis Response Data:")
                                st.json(response_data)
                                
                                # Store analysis result in session state immediately
                                if 'analysis' in response_data:
                                    if not st.session_state.session_data:
                                        st.session_state.session_data = {'results': {}}
                                    if 'results' not in st.session_state.session_data:
                                        st.session_state.session_data['results'] = {}
                                    st.session_state.session_data['results']['analysis'] = response_data['analysis']
                                    st.write("✅ **Debug:** Saved analysis results to session state!")
                                    
                                    # Disable polling since we have the result
                                    st.session_state.polling_active = False
                                    st.write("✅ **Debug:** Polling disabled - Results received!")
                                
                                st.success("✅ Business analysis Complete!")
                                st.info("💡 Refresh the page and the 'Next Step: Business Name Suggestions' button will appear.")
                                st.info("💡 Or scroll down to check the analysis results!")
                            else:
                                st.warning(f"⚠️ analysis Response: {analysis_response.status_code}")
                                st.write(f"❌ **Debug:** Response content: {analysis_response.text}")
                        except Exception as e:
                            logger.error(f"Analysis error: {str(e)}", exc_info=True)
                            st.error(f"analysis Error: {str(e)}")
                            st.write(f"❌ **Debug:** Exception occurred - {type(e).__name__}: {str(e)}")
                    
                    time.sleep(2)  # Give time to read debug info
                    st.rerun()
                else:
                    st.error("Session creation failed.")
                    st.info("**Troubleshooting:**")
                    st.markdown("1. Check if API server is running")
                    st.code("./scripts/dev.sh api")
                    st.markdown("2. Check if environment is configured correctly")
                    st.code("./scripts/dev.sh validate")
                    st.markdown("3. after a moment retrytry")

def display_analysis_results():
    """Display business analysis results"""
    results = st.session_state.session_data.get("results", {}) if st.session_state.session_data else {}
    analysis = results.get("analysis")
    
    if analysis:
        
        st.markdown("### 📊 Business Analysis Results")
        
        # Score display
        score = analysis.get("score", 0)
        st.metric("Overall Score", f"{score:.1f}/100")
        
        # Summary
        if analysis.get("summary"):
            st.markdown("**analysis Summary**")
            st.info(analysis["summary"])
        
        # Insights
        insights = analysis.get("insights", [])
        if insights:
            st.markdown("**Key Insights**")
            for i, insight in enumerate(insights, 1):
                st.markdown(f"{i}. {insight}")
        
        # Market trends
        trends = analysis.get("market_trends", [])
        if trends:
            st.markdown("**Market Trends**")
            for trend in trends:
                st.markdown(f"• {trend}")
        
        # Recommendations
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            st.markdown("**Recommendations**")
            for rec in recommendations:
                st.markdown(f"• {rec}")
        
        # Next step button
        st.markdown("---")
        if st.button("➡️ Next Step: Business Name Suggestions", key="next_to_names", type="primary"):
            # Generating business names using async polling method
            try:
                logger.info(f"Starting async name generation for session: {st.session_state.session_id}")
                logger.info(f"API URL: {API_BASE_URL}/names/suggest")
                
                # 1. Starting async request (with retries) - showing loading
                with st.spinner("🚀 Business Name Requesting generation..."):
                    start_success = False
                    for start_attempt in range(3):  # Maximum 3retries
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
                                st.success("✅ Business Name generation started!")
                                break
                            else:
                                error_msg = f"Business Name Failed to start generation: {start_response.status_code}"
                                logger.error(error_msg)
                                logger.error(f"Response: {start_response.text}")
                                if start_attempt >= 2:  # last attempt
                                    st.error(error_msg)
                                    st.json(start_response.json())
                                    return
                                time.sleep(1)  # waiting before retry (2s → 1s)
                        
                        except requests.Timeout:
                            logger.warning(f"Start request timeout (attempt {start_attempt + 1}/3)")
                            if start_attempt >= 2:  # last attempt
                                st.error("⏱️ Request start timeout: Lambda function not responding.")
                                st.info("💡 Retry after a moment or check CloudWatch logs.")
                                return
                            time.sleep(1)  # waiting before retry (2s → 1s)
                        
                        except Exception as e:
                            logger.error(f"Start request error: {str(e)}")
                            if start_attempt >= 2:  # last attempt
                                raise
                            time.sleep(1)  # waiting before retry (2s → 1s)
                
                if not start_success:
                    st.error("Cannot start business name generation.")
                    return
                
                # 2. Waiting for results with polling - showing progress
                st.info("💡 AI is generating business names optimized for your business...")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                max_attempts = 90  # 90 * 2s = 180s (considering Lambda maximum execution time)
                for attempt in range(max_attempts):
                    time.sleep(2)  # Polling interval: 3s → 2s
                    
                    try:
                        status_response = requests.get(
                            f"{API_BASE_URL}/names/status/{st.session_state.session_id}",
                            timeout=15  # Status check is fast but with buffer
                        )
                        
                        progress = min((attempt + 1) / max_attempts, 0.95)
                        progress_bar.progress(progress)
                        elapsed = (attempt + 1) * 2  # Changed to 2s interval
                        status_text.text(f"🔄 Generating business names... ({elapsed}s elapsed / Maximum 180s)")
                        
                        # Check body's statusCode, not HTTP status code
                        status_data = status_response.json()
                        body_status_code = status_data.get('statusCode')
                        
                        if body_status_code == 200:
                            # Complete
                            progress_bar.progress(1.0)
                            status_text.text("✅ Complete!")
                            logger.info("Name generation completed successfully")
                            
                            # Update Session Data
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
                            
                            st.success("✅ Business name generation complete!")
                            time.sleep(1)
                            st.session_state.current_step = 2
                            st.rerun()
                            return
                        
                        elif body_status_code == 202:
                            # In progress
                            logger.debug(f"Still processing... (attempt {attempt + 1}/{max_attempts})")
                            continue
                        
                        elif body_status_code == 500:
                            # Failed
                            error_msg = f"Business Name generation failed: {status_data.get('error', 'Unknown error')}"
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
                
                # Timeout
                error_msg = "⏱️ Request timeout: exceeded 180s."
                logger.error(error_msg)
                st.error(error_msg)
                st.info("💡 Lambda function may still be running. Refresh the page after a moment.")
                st.info("💡 Check CloudWatch logs to verify Lambda execution status.")
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Network error: {str(e)}"
                logger.error(error_msg)
                st.error(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
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
        
        st.markdown("### 🏷️ Business Name Candidates")
        
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
                            <div>Pronunciation: {suggestion.get("pronunciationScore", 0):.1f}/100</div>
                            <div>Search: {suggestion.get("searchScore", 0):.1f}/100</div>
                            <div><strong>Overall: {suggestion.get("overallScore", 0):.1f}/100</strong></div>
                        </div>
                        {"<div style='color: green; font-weight: bold; margin-top: 10px;'>✓ Selected</div>" if is_selected else ""}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Selection button
                    if not is_selected:
                        if st.button(f"Select", key=f"select_name_{i}"):
                            select_business_name(suggestion.get("name"))
            
            # Regeneration option
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"Regenerations: {regen_count}/{max_regens}")
                if regen_count < max_regens:
                    st.info("If you don't like any business names, you can regenerate.")
                else:
                    st.warning("All regeneration attempts used.")
            
            with col2:
                if regen_count < max_regens:
                    if st.button("Regenerate", type="secondary"):
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
        
        st.markdown("### 🪧 Signboard designs")
        
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
                                caption=f"{image.get('style', 'Modern')} Style",
                                width='stretch'
                            )
                        except Exception as e:
                            logger.error(f"Image load error: {str(e)}")
                            st.error("Image load failed")
                            st.code(image_url)
                    
                    # Image details
                    st.write(f"**Style:** {image.get('style', 'N/A')}")
                    
                    # Check both 'generatedAt' and 'generated_at'
                    generated_at = image.get('generatedAt') or image.get('generated_at')
                    if generated_at:
                        st.write(f"**Generated:** {generated_at[:16]}")
                    
                    # Check both 'isFallback' and 'is_fallback'
                    is_fallback = image.get("isFallback") or image.get("is_fallback")
                    if is_fallback:
                        st.warning("⚠️ Fallback image (used when AI generation fails)")
                    
                    # Selection button
                    if not is_selected:
                        if st.button(f"Select This Design", key=f"select_signboard_{i}"):
                            select_signboard_image(image.get("url"))
                    else:
                        st.success("✓ Selected")
            

        else:
            st.warning("No signboard images available.")
            if st.button("Retry Signboard Generation"):
                st.session_state.current_step = 2
                st.rerun()
    else:
        st.info("Please select a business name first to generate signboard designs.")
        if st.button("Back to Business Name Selection"):
            st.session_state.current_step = 2
            st.rerun()

def manual_refresh_interior_status():
    """Manually refresh interior generation status"""
    try:
        # Rate limiting check
        current_time = time.time()
        last_refresh = st.session_state.get('last_interior_refresh_time', 0)
        
        if current_time - last_refresh < 2:
            st.warning("⏱️ Request too fast. Retry after 2s.")
            return
        
        # Update last refresh time
        st.session_state.last_interior_refresh_time = current_time
        
        with st.spinner("🔄 Checking status..."):
            # Query DynamoDB directly via API
            status_data = get_session_status(st.session_state.session_id)
            
            if not status_data:
                st.error("❌ Cannot retrieve session data.")
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
                    st.error("❌ Data format error occurred.")
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
                st.success(f"✅ Interior generation complete! ({generated_images}/{total_recommendations} images)")
                st.session_state.current_step = 4
                st.session_state.interior_timeout = False
                time.sleep(1)
                st.rerun()
            elif generated_images > 0:
                st.info(f"🎨 In progress: {generated_images}/{total_recommendations} images generated")
            else:
                st.warning(f"⏳ Still generating... (Status: {interior_status})")
                
    except Exception as e:
        logger.error(f"Manual refresh error: {str(e)}")
        st.error(f"❌ Refresh error: {str(e)}")

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
        st.markdown("### 🏠 Interior recommendations")
        st.info("🎨 Generating interior images...")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Refresh Status", key="refresh_interior_status", use_container_width=True):
                manual_refresh_interior_status()
        
        st.markdown("---")
        return
    
    if interior_data:
        recommendations = interior_data.get("recommendations", [])
        selected_style = interior_data.get("selected_style")
        
        st.markdown("### 🏠 Interior recommendations")
        
        if recommendations:
            # Display interior recommendations
            for i, rec in enumerate(recommendations):
                style = rec.get("style", "N/A")
                is_selected = selected_style == style
                border_color = "#4CAF50" if is_selected else "#ddd"
                
                # Expandable card for each recommendation
                with st.expander(f"{'✓ ' if is_selected else ''}Option {i+1}: {style.upper()} Style", expanded=(i == 0)):
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
                            
                            st.image(image_url, caption=f"{style.upper()} Style Interior", use_container_width=True)
                            st.caption(f"Generated by: {provider_label}")
                        except Exception as e:
                            st.warning(f"Image load failed: {str(e)}")
                    else:
                        st.info("🎨 Generating interior image...")
                    
                    # Description
                    st.markdown(f"**Description:**")
                    st.write(rec.get("description", ""))
                    
                    # Suitability score
                    score = rec.get("suitabilityScore", 0)
                    st.progress(score / 100.0)
                    st.caption(f"Suitability: {score}/100")
                    
                    # Details in columns
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Color scheme
                        st.markdown("**Color Palette:**")
                        colors = rec.get("colorScheme", [])
                        for color in colors:
                            st.markdown(f"- {color}")
                        
                        # Materials
                        st.markdown("**Materials:**")
                        materials = rec.get("materials", [])
                        for material in materials:
                            st.markdown(f"- {material}")
                    
                    with col2:
                        # Furniture
                        st.markdown("**Furniture:**")
                        furniture = rec.get("furniture", [])
                        for item in furniture:
                            st.markdown(f"- {item}")
                        
                        # Cost
                        st.markdown(f"**Estimated Cost:** {rec.get('estimatedCost', 'N/A')}")
                    
                    # Pros and Cons
                    col3, col4 = st.columns(2)
                    
                    with col3:
                        st.markdown("**Advantages:**")
                        pros = rec.get("pros", [])
                        for pro in pros:
                            st.markdown(f"✅ {pro}")
                    
                    with col4:
                        st.markdown("**Disadvantages:**")
                        cons = rec.get("cons", [])
                        for con in cons:
                            st.markdown(f"⚠️ {con}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Selection button
                    if not is_selected:
                        if st.button(f"Select This Style", key=f"select_interior_{i}"):
                            select_interior_option(style)
                    else:
                        st.success("✓ Selected Style")
        else:
            st.info("No interior recommendations data available.")
    else:
        st.info("Please select signboard designs first to generate interior recommendations.")

def display_report_download():
    """Display PDF report download interface"""
    results = st.session_state.session_data.get("results", {}) if st.session_state.session_data else {}
    report_data = results.get("report")
    
    if report_data:
        
        st.markdown("### 📄 Branding Report")
        
        st.success("Branding Report has been generated!")
        
        # Report info
        st.info("""
        **Contents:**
        - Business Analysis Results
        - Selected business name and candidates
        - Signboard designs (selected + all options)
        - Interior recommendations (selected + all options)
        - Color palette and budget guide
        - Customized branding recommendations
        """)
        
        # Download button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📥 Download Report", type="primary", use_container_width=True):
                download_report()
        
        # Additional options
        st.markdown("---")
        st.markdown("**Additional Options:**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Start New Workflow"):
                start_new_workflow()
        
        with col2:
            if st.button("📧 Send via Email"):
                st.info("Email sending feature will be implemented later.")

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
        
        st.success(f"✅ '{name}' Business name has been selected!")
        
        # Using async polling method signboard generation (same pattern as business name generation)
        try:
            logger.info(f"Starting async signboard generation for session: {st.session_state.session_id}")
            logger.info(f"API URL: {API_BASE_URL}/signboards/generate")
            
            # 1. Starting async request (with retries)
            with st.spinner("🚀 Requesting signboard generation..."):
                start_success = False
                for start_attempt in range(3):  # Maximum 3retries
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
                            timeout=10  # Short timeout (async start only)
                        )
                        
                        if start_response.status_code == 202:
                            logger.info("Signboard generation started successfully")
                            start_success = True
                            st.success("✅ Signboard generation started!")
                            break
                        else:
                            error_msg = f"Failed to start signboard generation: {start_response.status_code}"
                            logger.error(error_msg)
                            logger.error(f"Response: {start_response.text}")
                            if start_attempt >= 2:  # last attempt
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
                            st.error("⏱️ Request start timeout: Lambda function not responding.")
                            st.info("💡 Retry after a moment or check CloudWatch logs.")
                            return
                        time.sleep(1)
                    
                    except Exception as e:
                        logger.error(f"Signboard start request error: {str(e)}")
                        if start_attempt >= 2:
                            raise
                        time.sleep(1)
            
            if not start_success:
                st.error("Cannot start signboard generation.")
                return
            
            # 2. Waiting for results with polling - showing progress
            st.info(f"💡 AI is '{name}' is generating 3 styles of signboards with business name ...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            max_attempts = 30  # 30 * 3s = 90s (considering image generation time)
            for attempt in range(max_attempts):
                time.sleep(3)  # Polling interval: 3s
                
                try:
                    # Check signboard images in session data
                    session_response = requests.get(
                        f"{API_BASE_URL}/sessions/{st.session_state.session_id}",
                        timeout=10
                    )
                    
                    progress = min((attempt + 1) / max_attempts, 0.95)
                    progress_bar.progress(progress)
                    elapsed = (attempt + 1) * 3
                    status_text.text(f"🔄 Generating signboards... ({elapsed}s elapsed / Maximum 90s)")
                    
                    if session_response.status_code == 200:
                        session_data = session_response.json()
                        # Try both field names (camelCase and snake_case)
                        signboard_images = session_data.get('signboardImages') or session_data.get('signboard_images')
                        
                        if signboard_images:
                            # Parse if JSON string
                            if isinstance(signboard_images, str):
                                signboard_images = json.loads(signboard_images)
                            
                            images = signboard_images.get('images', [])
                            
                            if images and len(images) > 0:
                                # Complete!
                                progress_bar.progress(1.0)
                                status_text.text("✅ Complete!")
                                logger.info(f"Signboard generation completed: {len(images)} images")
                                
                                # Update Session Data
                                if not st.session_state.session_data:
                                    st.session_state.session_data = {}
                                if 'results' not in st.session_state.session_data:
                                    st.session_state.session_data['results'] = {}
                                
                                st.session_state.session_data['results']['signboard'] = {
                                    'signboards': images
                                }
                                
                                st.success(f"✅ Signboard designs generation complete! ({len(images)}items)")
                                time.sleep(1)
                                st.session_state.current_step = 3
                                st.rerun()
                                return
                
                except Exception as poll_error:
                    logger.warning(f"Poll attempt {attempt + 1} failed: {poll_error}")
                    continue
            
            # Timeout
            progress_bar.progress(1.0)
            status_text.text("⏱️ Timeout")
            st.error("⏱️ Signboard generation timeout: 90s exceeded.")
            st.info("💡 Lambda function may still be running. Refresh the page after a moment.")
            
        except Exception as e:
            error_msg = f"Signboard generation error: {str(e)}"
            logger.error(error_msg)
            logger.exception("Full traceback:")
            st.error(error_msg)
            
    except Exception as e:
        error_msg = f"Business Name Select Error: {str(e)}"
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
            st.success("Generating new business name ...")
            st.session_state.polling_active = True
            poll_session_status()
            st.rerun()
        else:
            st.error("Business name regeneration failed.")
            
    except requests.exceptions.RequestException as e:
        st.error(f"API call error: {str(e)}")

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
            st.success("✅ Signboard design has been selected!")
            
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
            st.error("❌ Signboard selection failed.")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API call error: {str(e)}")

def start_interior_generation():
    """Start interior generation with async polling"""
    try:
        st.info("🎨 Starting interior recommendations generation...")
        
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
            st.success("✅ Interior generation started!")
            
            # Poll for completion
            st.info("💡 AI is is generating interior recommendations ...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            max_attempts = 45  # 45 * 2s = 90s (considering image generation time)
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
                        status_text.text("✅ Complete!")
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
                        
                        st.success(f"✅ Interior recommendations complete! ({generated_images}items images generated)")
                        st.session_state.current_step = 4
                        time.sleep(1)
                        st.rerun()
                        return
                    elif total_recommendations > 0:
                        # Partial progress - show image generation status
                        status_text.text(f"🎨 Generating interior images... ({generated_images}/{total_recommendations} Complete, {elapsed}s elapsed)")
                
                # Update progress
                progress = min((attempt + 1) / max_attempts, 0.95)
                progress_bar.progress(progress)
                
                # Default status message
                if not status_data or not interior_data:
                    status_text.text(f"🔄 Generating interior... ({elapsed}s elapsed / Maximum 90s)")
            
            # Timeout - show manual refresh button
            st.warning("⏱️ Interior image generation is taking longer than expected.")
            st.info("💡 Click the 'Refresh Status' button below to check current status.")
            
            # Store timeout state and show refresh button immediately
            st.session_state.interior_timeout = True
            
            # Show manual refresh button right here
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🔄 Refresh Status", key="refresh_interior_timeout", use_container_width=True):
                    # Query status immediately
                    status_data = get_session_status(st.session_state.session_id)
                    if status_data:
                        results = status_data.get('results', {})
                        interior_data = results.get('interiors')
                        if interior_data:
                            recommendations = interior_data.get('recommendations', [])
                            generated_images = interior_data.get('generatedImages', 0)
                            if generated_images > 0:
                                st.success(f"✅ Interior generation complete! ({generated_images} images)")
                                st.session_state.current_step = 4
                                st.session_state.interior_timeout = False
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.info(f"🎨 Still generating... ({generated_images}/{len(recommendations)} Complete)")
                        else:
                            st.warning("⏳ No data yet. Retry after a moment.")
                    else:
                        st.error("❌ Cannot retrieve session data.")
            
        else:
            st.warning(f"⚠️ Failed to start interior generation: {interior_response.status_code}")
            
    except Exception as e:
        st.error(f"❌ Interior generation error: {str(e)}")

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
        
        # saved selected interior to DynamoDB via API
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
        
        st.success("✅ Interior option has been selected!")
        
        # Automatically trigger report generation (async mode)
        with st.spinner("📄 Starting report generation..."):
            try:
                # Start async report generation
                report_response = requests.post(
                    f"{API_BASE_URL}/report/generate",
                    json={
                        "sessionId": st.session_state.session_id,
                        "businessInfo": st.session_state.business_info
                    },
                    headers={"x-async-mode": "true"},  # Enable async mode
                    timeout=30
                )
                
                logger.info(f"Report API response: {report_response.status_code}")
                
                if report_response.status_code == 202:
                    # Async processing started - poll for completion
                    st.info("📄 Report is being generated in the background...")
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    max_wait_time = 180  # 3 minutes max
                    poll_interval = 3  # Check every 3 seconds
                    elapsed_time = 0
                    
                    while elapsed_time < max_wait_time:
                        try:
                            # Check session status
                            status_response = requests.get(
                                f"{API_BASE_URL}/session/{st.session_state.session_id}",
                                timeout=10
                            )
                            
                            if status_response.status_code == 200:
                                session_data = status_response.json()
                                report_status = session_data.get('reportGenerationStatus')
                                
                                if report_status == 'completed':
                                    progress_bar.progress(100)
                                    status_text.success("✅ Report generated successfully!")
                                    
                                    # Get report URL
                                    report_url = session_data.get('reportUrl')
                                    if report_url:
                                        st.session_state.session_data['results']['report'] = {
                                            "reportUrl": report_url,
                                            "sessionId": st.session_state.session_id
                                        }
                                        
                                        st.success("✅ Report generation complete!")
                                        st.balloons()
                                        time.sleep(1)
                                        st.session_state.current_step = 5
                                        st.rerun()
                                    break
                                    
                                elif report_status == 'failed':
                                    progress_bar.progress(100)
                                    status_text.error("❌ Report generation failed")
                                    st.error("Report generation failed. Please try again.")
                                    break
                                    
                                else:
                                    # Still processing
                                    progress = min((elapsed_time / max_wait_time) * 100, 95)
                                    progress_bar.progress(int(progress))
                                    status_text.info(f"⏳ Generating report... ({elapsed_time}s elapsed)")
                            
                            time.sleep(poll_interval)
                            elapsed_time += poll_interval
                            
                        except Exception as poll_error:
                            logger.warning(f"Status check failed: {str(poll_error)}")
                            time.sleep(poll_interval)
                            elapsed_time += poll_interval
                    
                    if elapsed_time >= max_wait_time:
                        progress_bar.progress(100)
                        status_text.warning("⏰ Report generation is taking longer than expected")
                        st.warning("Report generation is taking longer than expected. Please check back later.")
                        
                elif report_response.status_code == 200:
                    # Sync processing (fallback)
                    result = report_response.json()
                    logger.info(f"Report result: {result}")
                    
                    st.session_state.session_data['results']['report'] = result
                    
                    st.success("✅ Report generation complete!")
                    st.balloons()
                    time.sleep(1)
                    st.session_state.current_step = 5
                    st.rerun()
                    
                else:
                    error_msg = f"Report generation failed: {report_response.status_code}"
                    logger.error(error_msg)
                    logger.error(f"Response: {report_response.text}")
                    st.error(error_msg)
                    
            except requests.Timeout:
                st.error("⏱️ Request timeout. Report may still be processing in background.")
                st.info("💡 Please refresh the page in a moment to check status.")
            except Exception as e:
                error_msg = f"Report generation error: {str(e)}"
                logger.error(error_msg)
                logger.exception("Full traceback:")
                st.error(error_msg)
            
    except Exception as e:
        error_msg = f"Interior selection error: {str(e)}"
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
            # Supports both downloadUrl (camelCase) and download_url (snake_case)
            download_url = data.get("downloadUrl") or data.get("download_url")
            file_name = data.get("fileName", "branding_report")
            
            if download_url:
                st.markdown(f"### 📥 Download Report")
                st.markdown(f"[**{file_name} Download**]({download_url})")
                st.info("💡 Link is valid for 10 minutes.")
            else:
                st.error("Cannot generate download link.")
        else:
            st.error("Failed to generate download report link.")
            
    except requests.exceptions.RequestException as e:
        st.error(f"API call error: {str(e)}")

def start_new_workflow():
    """Start a new workflow"""
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("Starting new workflow!")
    st.rerun()

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="AI Branding Chatbot",
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
    st.title("🎨 AI Branding Chatbot")
    st.markdown("**Generate complete branding package with 5-step automated workflow**")
    
    # Sidebar with session info
    with st.sidebar:
        st.markdown("### Session Information")
        if st.session_state.session_id:
            st.success(f"Session ID: {st.session_state.session_id[:8]}...")
            st.write(f"Current Step: {st.session_state.current_step}/5")
            
            # Auto-refresh toggle
            auto_refresh = st.checkbox("Auto Refresh", value=st.session_state.polling_active)
            st.session_state.polling_active = auto_refresh
            
            # Manual refresh button
            if st.button("Refresh Status"):
                poll_session_status()
                st.rerun()
            
            # Force next step button (for debugging)
            st.markdown("---")
            st.markdown("### 🔧 Debug Tools")
            
            if st.button("🔄 Force Execute Next Step"):
                current_step = st.session_state.current_step
                session_id = st.session_state.session_id
                business_info = st.session_state.business_info
                
                st.write(f"Current Step: {current_step}")
                
                if current_step == 1:
                    # Force analysis
                    with st.spinner("Forcing analysis execution..."):
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/analysis",
                                json={"sessionId": session_id, "businessInfo": business_info},
                                timeout=90  # Increased for Bedrock processing
                            )
                            st.write(f"Response Status: {response.status_code}")
                            st.json(response.json())
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                elif current_step == 2:
                    # Force name generation
                    with st.spinner("Forcing business name generation..."):
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/names/suggest",
                                json={"sessionId": session_id, "businessInfo": business_info},
                                timeout=90  # Increased for Bedrock reasoning
                            )
                            st.write(f"Response Status: {response.status_code}")
                            st.json(response.json())
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            
            # Reset session button
            st.markdown("---")
            if st.button("🆕 Start New Session", type="primary"):
                logger.info("Resetting session")
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        else:
            st.info("No session. Starting new workflow.")
        
        # API connection status
        st.markdown("### API Connection Status")
        try:
            # Try to connect to the API Gateway (test with a simple request)
            response = requests.get(f"{API_BASE_URL}/", timeout=5)
            if response.status_code in [200, 404]:  # 404 is OK for API Gateway root
                st.success("✅ API Gateway connected")
            else:
                st.warning(f"⚠️ API response abnormal ({response.status_code})")
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API server")
            st.info("**Solution:**")
            st.code("./scripts/dev.sh api")
            st.info("Or run directly:")
            st.code("sam build && sam local start-api --port 3000")
        except requests.exceptions.Timeout:
            st.warning("⚠️ API response timeout")
            st.info("API server may be starting. Retry after a moment.")
        except Exception as e:
            st.error(f"❌ API connection error: {str(e)}")
        
        # Development info
        st.markdown("### About")
        st.code(f"API URL: {API_BASE_URL}")
        
        # Show session info
        if st.session_state.session_id:
            st.code(f"Session ID: {st.session_state.session_id}")
            st.code(f"Current Step: {st.session_state.current_step}")
            st.code(f"Polling Active: {st.session_state.polling_active}")
        
        # Show raw session data
        if st.session_state.session_data:
            with st.expander("Session Data (JSON)", expanded=False):
                st.json(st.session_state.session_data)
        
        # Show business info
        if st.session_state.business_info:
            with st.expander("Business About", expanded=False):
                st.json(st.session_state.business_info)
        
        # Show agent status
        if st.session_state.agent_status:
            with st.expander("Agent Status", expanded=False):
                st.json(st.session_state.agent_status)
    
    # Main content area
    if st.session_state.session_id:
        # Debug banner at top
        with st.expander("🔍 Debug About", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Session ID", st.session_state.session_id[:12] + "...")
                st.metric("Current Step", f"{st.session_state.current_step}/5")
            with col2:
                st.metric("Polling Status", "Active" if st.session_state.polling_active else "Inactive")
                has_analysis = bool(st.session_state.session_data and st.session_state.session_data.get("results", {}).get("analysis"))
                st.metric("Analysis Results", "Available" if has_analysis else "Not Available")
            with col3:
                if st.button("📊 Check Session Status", key="check_status"):
                    with st.spinner("Checking session status..."):
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
                                st.error(f"Status check failed: {status_response.status_code}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
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
            time.sleep(2)  # Optimized: 5s → 2s
            st.rerun()
        
        # Display current step content
        if st.session_state.current_step == 1:
            display_analysis_results()
            if not st.session_state.session_data or not st.session_state.session_data.get("results", {}).get("analysis"):
                st.warning("⚠️ No business analysis results!")
                st.info("💡 Click 'Force Execute Next Step' button in sidebar to start analysis.")
        elif st.session_state.current_step == 2:
            display_analysis_results()  # Keep showing analysis
            st.markdown("---")
            display_business_names()
            if not st.session_state.session_data or not st.session_state.session_data.get("results", {}).get("names"):
                st.info("🔄 Business name generation in progress...")
        elif st.session_state.current_step == 3:
            display_analysis_results()  # Keep showing analysis
            st.markdown("---")
            display_business_names()    # Keep showing selected name
            st.markdown("---")
            display_signboard_gallery()
            if not st.session_state.session_data or not st.session_state.session_data.get("results", {}).get("signboards"):
                st.info("🔄 Signboard designs generation in progress...")
        elif st.session_state.current_step == 4:
            display_analysis_results()
            st.markdown("---")
            display_business_names()
            st.markdown("---")
            display_signboard_gallery()
            st.markdown("---")
            display_interior_options()
            if not st.session_state.session_data or not st.session_state.session_data.get("results", {}).get("interiors"):
                st.info("🔄 Interior recommendations in progress...")
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
                st.info("🔄 Report generation in progress...")
        else:
            st.info(f"Step {st.session_state.current_step}is not yet implemented.")
    else:
        # Step 1: Business information input
        step1_business_analysis()

if __name__ == "__main__":
    main()