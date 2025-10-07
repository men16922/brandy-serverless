# AI 브랜딩 챗봇 - AWS Hackathon Spec

이 디렉토리에는 AWS AI Agent Global Hackathon 제출을 위한 통합 spec 문서들이 있습니다.

## 📁 디렉토리 구조

### `aws-hackathon-compliance/` (통합 Spec)
기존 프로젝트와 해커톤 요구사항을 통합한 **최종 구현 계획**입니다.

**문서**:
- `requirements.md` - 통합 요구사항 (기존 기능 + 해커톤 필수 조건)
- `design.md` - Bedrock 통합 설계 (아키텍처, AgentCore, Reasoning Engine)
- `tasks.md` - **통합 구현 계획** (기존 완료 작업 70% + 해커톤 요구사항 30%)
- `*.png` - 아키텍처 다이어그램

**통합 전략**:
- ✅ 기존 완료된 작업 (70%) 유지
- ➕ Bedrock 레이어 추가 방식
- 🔄 점진적 전환 (OpenAI/Gemini → Bedrock Primary + Fallback)
- ⏱️ 2-3주 구현 일정

## 🚀 시작하기

1. **현재 작업할 spec**: `aws-hackathon-compliance/tasks.md`
2. **작업 시작**: tasks.md 파일을 열고 "Start task" 버튼 클릭
3. **우선순위**: Task 1.1 (Bedrock 클라이언트 모듈 구현)부터 시작

## 📊 프로젝트 현황

### ✅ 완료된 부분 (70%)

**인프라 & 아키텍처**:
- AWS SAM 템플릿 (template.yaml) - 완전 구현
- Docker Compose 로컬 환경 (DynamoDB Local, MinIO, Chroma)
- 환경별 설정 (samconfig.toml)

**데이터 & 모델**:
- 데이터 모델 (models.py) - 95% 완성
- BaseAgent 클래스 및 공통 유틸리티
- DynamoDB 세션 관리

**AI 에이전트**:
- ✅ Supervisor Agent (세션 관리, 워크플로 감시)
- ✅ Product Insight Agent (비즈니스 분석)
- ✅ Market Analyst Agent (시장 분석)
- ✅ Reporter Agent (상호명 생성)
- ✅ Signboard Agent (DALL-E, SDXL, Gemini 병렬 처리)
- ✅ Interior Agent (인테리어 추천)
- ✅ Report Generator Agent (HTML/JSON/텍스트 보고서)

**테스트 & UI**:
- 통합 테스트 (29개 테스트 통과)
- Streamlit 웹 인터페이스
- NO MOCKS 정책 (Docker Compose 기반)

### ❌ 해커톤 요구사항 미충족 (30%)

- Amazon Bedrock 통합 (현재: OpenAI, Gemini)
- Bedrock AgentCore 구현
- Reasoning LLM 시스템
- 해커톤 제출 문서 (아키텍처 다이어그램, 데모 비디오)

## 💡 통합 전략

**핵심 원칙**: 기존 완료된 코드를 유지하면서 Bedrock 레이어를 추가

```
기존 완료된 Agent 구조 (70%)
    ↓
+ Bedrock 클라이언트 모듈
+ AgentCore 오케스트레이터
+ Reasoning Engine
    ↓
Bedrock Primary + OpenAI/Gemini Fallback
    ↓
해커톤 요구사항 충족 (100%)
```

**장점**:
- 🔄 기존 작업 재사용 (인프라, 테스트, UI)
- 🛡️ Fallback 유지 (개발 중 안정성)
- ⚡ 빠른 구현 (2-3주)
- 🧪 검증된 테스트 환경

## 📝 참고 문서

- `docs/구현_상태_분석.md` - 현재 프로젝트 상태 상세 분석
- `docs/PROJECT_SUMMARY.md` - 프로젝트 종합 문서
- `README.md` - 프로젝트 README
- `docs/AWS Hackathon overview.md` - 해커톤 개요
- `docs/AWS Hackathon rules.md` - 해커톤 규칙

## 🎯 다음 단계

```bash
# 1. 환경 확인
./scripts/dev.sh validate

# 2. Task 1.1 시작
# .kiro/specs/aws-hackathon-compliance/tasks.md 열기

# 3. Bedrock 클라이언트 구현
# src/lambda/shared/bedrock_client.py 생성
```
