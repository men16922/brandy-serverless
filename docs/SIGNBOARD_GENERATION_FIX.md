# 간판 생성 문제 해결 - 완전 가이드

## 📋 목차
1. [문제 요약](#문제-요약)
2. [발견된 문제들](#발견된-문제들)
3. [해결 방법](#해결-방법)
4. [테스트 가이드](#테스트-가이드)
5. [배포 상태](#배포-상태)

---

## 문제 요약

간판 생성 기능이 실패하여 모든 스타일(classic, vibrant, modern)에서 폴백 이미지("⚠️ 폴백 이미지")만 표시되는 문제가 발생했습니다.

**증상**:
- ❌ AI 생성 이미지 대신 폴백 플레이스홀더만 표시
- ❌ CloudWatch 로그에 "end of life" 오류
- ❌ Streamlit에서 타임아웃 오류 발생

---

## 발견된 문제들

### 1️⃣ 사용 중단된 Bedrock 모델 ID

**오류**: 
```
ResourceNotFoundException: This model version has reached the end of its life
```

**원인**: 
- Lambda 환경 변수: `stability.stable-diffusion-xl-v1` (사용 중단됨)
- CloudFormation 스택 파라미터가 업데이트되지 않음

**해결**:
```bash
sam deploy --config-env dev --parameter-overrides "SdxlModelId=amazon.titan-image-generator-v2:0"
```

### 2️⃣ ImageResult 속성 오류

**오류**: 
```python
AttributeError: 'ImageResult' object has no attribute 'error_message'
```

**원인**:
- `_image_result_to_dict` 메서드가 선택적 속성에 직접 접근
- `_create_image_result` 헬퍼가 새 필드를 초기화하지 않음

**해결**:
```python
# hasattr() 체크 추가
if hasattr(image_result, 'error_message') and image_result.error_message:
    result_dict["errorMessage"] = image_result.error_message
```

### 3️⃣ Lambda Layer 동기화 문제 ⚠️ **가장 중요!**

**원인**:
- 수정: `src/lambda/shared/ai_providers.py`
- 실제 사용: `src/lambda/layers/shared-utilities/python/shared/ai_providers.py`
- 두 파일이 동기화되지 않음

**해결**:
```bash
# 수정된 파일을 Lambda Layer로 복사
cp src/lambda/shared/ai_providers.py src/lambda/layers/shared-utilities/python/shared/
cp src/lambda/shared/models.py src/lambda/layers/shared-utilities/python/shared/

# 재빌드 및 배포
sam build
sam deploy --config-env dev
```

### 4️⃣ Streamlit 타임아웃 문제

**오류**: 
```
HTTPSConnectionPool: Read timed out. (read timeout=30)
```

**원인**:
- Bedrock API 호출이 30초 이상 소요
- Streamlit 기본 타임아웃이 30초로 너무 짧음

**해결**:
```python
# src/streamlit/app.py
timeout=90   # 분석, 상호명 (이전: 30s)
timeout=120  # 간판, 인테리어 (이전: 60s)
```

---

## 해결 방법

### Step 1: CloudFormation 스택 업데이트

```bash
# 1. SAM 빌드
sam build

# 2. 올바른 모델 ID로 배포
sam deploy --config-env dev --parameter-overrides "SdxlModelId=amazon.titan-image-generator-v2:0"

# 3. Lambda 환경 변수 확인
aws lambda get-function-configuration \
  --function-name ai-branding-chatbot-signboard-agent-dev \
  --query 'Environment.Variables.SDXL_MODEL_ID'
```

**예상 결과**: `amazon.titan-image-generator-v2:0`

### Step 2: Lambda Layer 동기화

```bash
# shared 파일을 Lambda Layer로 복사
cp src/lambda/shared/ai_providers.py src/lambda/layers/shared-utilities/python/shared/
cp src/lambda/shared/models.py src/lambda/layers/shared-utilities/python/shared/

# 재빌드 및 배포
sam build
sam deploy --config-env dev

# Lambda Layer 버전 확인
aws lambda get-function-configuration \
  --function-name ai-branding-chatbot-signboard-agent-dev \
  --query 'Layers[*].Arn'
```

**예상 결과**: Layer 버전이 증가함 (예: 21 → 22)

### Step 3: Streamlit 재시작

```bash
# 기존 프로세스 종료
pkill -f streamlit

# 새로 시작
streamlit run src/streamlit/app.py
```

---

## 테스트 가이드

### 1. CloudWatch 로그 모니터링

```bash
aws logs tail /aws/lambda/ai-branding-chatbot-signboard-agent-dev --follow
```

**성공 로그**:
```
✓ Bedrock SDXL provider initialized successfully (PRIMARY)
AWS credentials found: Account=908601828278
Starting SDXL image generation: style=classic
SDXL API call attempt 1/3: model_id=amazon.titan-image-generator-v2:0
SDXL API call successful on attempt 1
Titan image generated successfully: size=XXXXX bytes, latency=XXXXms
```

**실패 로그 (보면 안 됨)**:
```
❌ ResourceNotFoundException: This model version has reached the end of its life
❌ AttributeError: 'ImageResult' object has no attribute 'error_message'
❌ Failed to generate X image with sdxl
```

### 2. Streamlit 워크플로 테스트

1. **세션 생성**
   - 비즈니스 정보 입력 (업종, 지역, 규모)
   - 타임아웃 없이 완료되어야 함

2. **비즈니스 분석**
   - 90초 이내 완료 예상
   - 분석 결과 표시

3. **상호명 제안**
   - 90초 이내 완료 예상
   - 3개 상호명 표시

4. **간판 생성** ⭐ **핵심 테스트**
   - 120초 이내 완료 예상
   - **3개의 실제 AI 생성 이미지 표시**
   - **"⚠️ 폴백 이미지" 메시지 없음**
   - 각 이미지에 스타일 표시 (classic, vibrant, modern)

5. **인테리어 추천**
   - 120초 이내 완료 예상
   - 3개 인테리어 옵션 표시

### 3. DynamoDB 데이터 확인

```bash
aws dynamodb scan \
  --table-name ai-branding-chatbot-sessions \
  --max-items 1 \
  --query 'Items[0].signboardImages'
```

**예상 결과**:
```json
{
  "images": [
    {
      "provider": "sdxl",
      "is_fallback": false,
      "style": "classic",
      "url": "data:image/png;base64,..."
    }
  ]
}
```

---

## 배포 상태

### ✅ 완료된 작업

| 항목 | 상태 | 값 |
|------|------|-----|
| CloudFormation 스택 | ✅ | ai-branding-chatbot-dev |
| Lambda 함수 | ✅ | signboard-agent-dev |
| Lambda Layer | ✅ | 버전 22 |
| 모델 ID | ✅ | amazon.titan-image-generator-v2:0 |
| 코드 수정 | ✅ | ai_providers.py, index.py |
| Layer 동기화 | ✅ | shared → layers/shared-utilities |
| Streamlit 타임아웃 | ✅ | 90-120초로 증가 |

### 📊 타임아웃 설정

| 엔드포인트 | 이전 | 현재 |
|-----------|------|------|
| `/analysis` | 30s | **90s** |
| `/names/suggest` | 30s | **90s** |
| `/signboards` | 60s | **120s** |
| `/interior` | 30-60s | **90-120s** |

---

## 🎓 교훈 및 베스트 프랙티스

### 1. Lambda Layer 관리
- `src/lambda/shared/` = 개발용 디렉토리
- `src/lambda/layers/shared-utilities/python/shared/` = 실제 배포 디렉토리
- **항상 두 디렉토리를 동기화!**

**자동화 스크립트 예시**:
```bash
#!/bin/bash
# sync-shared-layer.sh
cp -r src/lambda/shared/* src/lambda/layers/shared-utilities/python/shared/
echo "✅ Shared files synced to Lambda Layer"
```

### 2. CloudFormation 파라미터 관리
- 템플릿 기본값 변경만으로는 기존 스택이 업데이트되지 않음
- `--parameter-overrides`로 명시적 업데이트 필요

### 3. Bedrock 모델 버전 관리
- 모델 ID는 시간이 지나면 사용 중단될 수 있음
- 정기적으로 최신 모델 확인:
```bash
aws bedrock list-foundation-models --region us-east-1 --by-output-modality IMAGE
```

### 4. 타임아웃 설정
- API Gateway 최대 타임아웃: 30초
- Lambda 타임아웃: 120초
- Streamlit 타임아웃: 요청별로 적절히 설정
- Bedrock API 응답 시간 고려

---

## 🔧 트러블슈팅

### 여전히 폴백 이미지가 나타나는 경우

1. **Lambda 환경 변수 확인**
```bash
aws lambda get-function-configuration \
  --function-name ai-branding-chatbot-signboard-agent-dev \
  --query 'Environment.Variables.SDXL_MODEL_ID'
```

2. **Lambda Layer 버전 확인**
```bash
aws lambda get-function-configuration \
  --function-name ai-branding-chatbot-signboard-agent-dev \
  --query 'Layers[*].Arn'
```

3. **CloudWatch 로그 확인**
```bash
aws logs tail /aws/lambda/ai-branding-chatbot-signboard-agent-dev --since 5m
```

4. **강제 재배포**
```bash
sam build --use-container
sam deploy --config-env dev --force-upload
```

### 타임아웃이 계속 발생하는 경우

1. **Bedrock API 응답 시간 확인**
   - CloudWatch 로그에서 `latency_ms` 확인
   - 30초 이상 걸리는지 확인

2. **API Gateway 제한 확인**
   - API Gateway는 최대 30초 타임아웃
   - 비동기 처리 패턴 고려 필요

3. **임시 해결책**
   - 브라우저 새로고침하지 말고 기다리기
   - Lambda는 백그라운드에서 계속 실행
   - 세션 ID로 나중에 결과 확인 가능

---

## 📚 관련 문서

- [AWS Bedrock Titan Image Generator](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-image-models.html)
- [AWS API Gateway Limits](https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html)
- [AWS Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html)
- [Hackathon Requirements](../docs/AWS%20Hackathon%20rules.md)

---

---

## 🆕 최신 업데이트 (2025-10-19 15:00 KST)

### 추가 수정: Prompt Length Validation

**문제**: Titan Image Generator v2의 512자 제한을 초과하는 프롬프트로 인한 ValidationException

**해결**:
1. `_create_image_prompt()`: 512자 제한 적용 및 지능형 truncation
2. `_optimize_prompt_for_titan()`: 올바른 512자 제한 및 상세 로깅
3. Lambda Layer 동기화 및 재배포

**상세 문서**: [SIGNBOARD_PROMPT_LENGTH_FIX.md](../SIGNBOARD_PROMPT_LENGTH_FIX.md)

---

**작성자**: Kiro AI Assistant  
**마지막 업데이트**: 2025-10-19 15:00 KST  
**상태**: ✅ **모든 수정 완료 + Prompt Length Fix - 프로덕션 준비 완료**
