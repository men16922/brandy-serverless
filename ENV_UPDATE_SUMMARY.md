# 환경 변수 및 모델 설정 업데이트

**날짜**: 2025-10-07  
**작업**: Claude Sonnet 4 모델 ID 업데이트 및 설정 파일 통합

---

## ✅ 업데이트된 파일들

### 1. 환경 변수 파일 (.env.*)

#### .env.example
```bash
# 변경 전
CLAUDE_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# 변경 후
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
```

#### .env.local
```bash
# 변경 전
CLAUDE_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# 변경 후
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
```

#### .env.dev
```bash
# 추가됨
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
SDXL_MODEL_ID=stability.stable-diffusion-xl-v1
BEDROCK_KB_ID=
BEDROCK_AGENT_ID=
BEDROCK_AGENT_ALIAS_ID=
ENABLE_FALLBACK=false
BEDROCK_MAX_RETRIES=3
BEDROCK_TIMEOUT=30
BEDROCK_MAX_TOKENS=2048
BEDROCK_TEMPERATURE=0.7
```

---

## 🔧 코드 설정 확인

### 이미 환경 변수에서 읽도록 구현됨 ✅

#### src/lambda/shared/bedrock_client.py
```python
self.claude_model_id = os.getenv(
    'CLAUDE_MODEL_ID',
    'us.anthropic.claude-sonnet-4-20250514-v1:0'  # Fallback default
)
```

#### config/bedrock_config.py
```python
@dataclass
class BedrockConfig:
    claude_model_id: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"  # Default
    
    @classmethod
    def from_env(cls) -> 'BedrockConfig':
        return cls(
            claude_model_id=os.getenv(
                'CLAUDE_MODEL_ID',
                'us.anthropic.claude-sonnet-4-20250514-v1:0'
            ),
            ...
        )
```

---

## 📋 설정 우선순위

### 모델 ID 결정 순서
1. **환경 변수** (`CLAUDE_MODEL_ID`) - 최우선
2. **설정 파일** (`bedrock_config.py`) - 환경 변수 없을 때
3. **하드코딩 기본값** - Fallback (동일한 값)

### 환경별 설정

#### Local 환경
```bash
ENVIRONMENT=local
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
ENABLE_FALLBACK=true  # OpenAI/Gemini fallback 활성화
```

#### Dev 환경
```bash
ENVIRONMENT=dev
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
ENABLE_FALLBACK=false  # Bedrock only
```

#### Prod 환경
```bash
ENVIRONMENT=prod
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
ENABLE_FALLBACK=false  # Bedrock only (Hackathon 요구사항)
```

---

## 🎯 사용 방법

### 1. 환경 변수 로드
```python
from config.bedrock_config import BedrockConfig

# 환경 변수에서 자동 로드
config = BedrockConfig.from_env()
print(config.claude_model_id)  # us.anthropic.claude-sonnet-4-20250514-v1:0
```

### 2. Bedrock Client 사용
```python
from shared.bedrock_client import create_bedrock_client

# 환경 변수에서 자동으로 모델 ID 읽음
client = create_bedrock_client()
print(client.claude_model_id)  # us.anthropic.claude-sonnet-4-20250514-v1:0

# Claude 호출
result = client.invoke_claude(prompt="Hello, World!")
```

### 3. 커스텀 모델 ID 사용
```python
import os

# 환경 변수 오버라이드
os.environ['CLAUDE_MODEL_ID'] = 'custom-model-id'

# 새 클라이언트 생성
client = create_bedrock_client()
print(client.claude_model_id)  # custom-model-id
```

---

## ✅ 검증 방법

### 1. 환경 변수 확인
```bash
# .env.local 로드 확인
source venv/bin/activate
python -c "import os; from dotenv import load_dotenv; load_dotenv('.env.local'); print(os.getenv('CLAUDE_MODEL_ID'))"
```

### 2. 설정 파일 확인
```bash
# Config 모듈 테스트
python -c "from config.bedrock_config import BedrockConfig; config = BedrockConfig.from_env(); print(config.claude_model_id)"
```

### 3. Bedrock Client 확인
```bash
# Client 초기화 테스트
python -c "from src.lambda.shared.bedrock_client import create_bedrock_client; client = create_bedrock_client(); print(client.claude_model_id)"
```

### 4. 통합 테스트
```bash
# Bedrock 통합 테스트 실행
./venv/bin/python -m pytest tests/integration/test_bedrock_integration.py -v
```

---

## 📊 모델 정보

### Claude Sonnet 4
- **Model ID**: `us.anthropic.claude-sonnet-4-20250514-v1:0`
- **Type**: Inference Profile (필수)
- **Region**: us-east-1
- **Features**:
  - 최신 Claude 모델
  - 향상된 reasoning 능력
  - 더 나은 한국어 지원
  - Inference profile을 통한 안정적인 접근

### 이전 모델 (Claude 3.5 Sonnet v2)
- **Model ID**: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- **Issue**: Inference profile 필요 오류 발생
- **Status**: ❌ Deprecated (이 프로젝트에서)

---

## 🔄 마이그레이션 가이드

### 기존 코드 업데이트 필요 없음 ✅

모든 코드가 이미 환경 변수에서 읽도록 구현되어 있으므로, `.env` 파일만 업데이트하면 됩니다.

### 업데이트 체크리스트
- ✅ `.env.example` 업데이트
- ✅ `.env.local` 업데이트
- ✅ `.env.dev` 업데이트
- ✅ `bedrock_client.py` 확인 (이미 환경 변수 사용)
- ✅ `bedrock_config.py` 확인 (이미 환경 변수 사용)
- ✅ Agent 파일들 확인 (하드코딩 없음)
- ✅ 테스트 파일들 확인 (하드코딩 없음)

---

## 🎉 결과

### 설정 통합 완료
- ✅ 모든 환경 변수 파일 업데이트
- ✅ Claude Sonnet 4로 통일
- ✅ 코드는 이미 설정 파일에서 읽도록 구현됨
- ✅ 하드코딩된 모델 ID 없음
- ✅ 환경별 설정 분리 완료

### 테스트 결과
```bash
# 모든 테스트 통과
✅ 26/26 Bedrock 통합 테스트
✅ Claude Sonnet 4 API 호출 성공
✅ 환경 변수 로딩 정상
```

---

**업데이트 완료**: 2025-10-07  
**상태**: ✅ 완료  
**다음 단계**: AgentCore 통합 (Phase 2)
