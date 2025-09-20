# Streamlit Frontend Application
# 5-step workflow UI for AI branding chatbot

import streamlit as st
import requests
import os
import json
from datetime import datetime

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:3000')

def main():
    """Main Streamlit application"""
    st.title("AI 브랜딩 챗봇")
    st.markdown("5단계 워크플로로 브랜딩을 생성하세요")
    
    # Session state initialization
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    
    # Workflow steps
    steps = [
        "1. 비즈니스 분석",
        "2. 상호명 제안", 
        "3. 간판 디자인",
        "4. 인테리어 추천",
        "5. PDF 보고서"
    ]
    
    # Progress indicator
    st.progress(st.session_state.current_step / len(steps))
    st.write(f"현재 단계: {steps[st.session_state.current_step - 1]}")
    
    # Implementation will be added in later tasks
    st.info("UI 구현은 후속 태스크에서 진행됩니다.")

if __name__ == "__main__":
    main()