# AgentCore & Bedrock Knowledge Base 활용 분석

## 현재 상태 분석

### 1. Knowledge Base 현황
- ✅ **인터페이스 구현 완료**: `shared/knowledge_base.py`
- ✅ **BedrockKnowledgeBase 클래스 존재**: Bedrock KB 연동 준비됨
- ⚠️ **실제 사용 중**: `product-insight`, `market-analyst` agents에서 초기화
- ❌ **실제 데이터 없음**: S3에 벡터 데이터 미구축
- ❌ **환경변수 미설정**: `BEDROCK_KNOWLEDGE_BASE_ID` 없음

### 2. AgentCore 현황
- ❌ **미구현**: Supervisor Agent에 AgentCore 통합 안됨
- ❌ **Tool Use primitive 미사용**: Agent 간 통신이 직접 호출 방식
- ❌ **Memory primitive 미사용**: DynamoDB 직접 사용 중

---

## 🎯 AgentCore 활용 방안

### 1. Supervisor Agent 개선 (필수 - Hackathon 요구사항)

**현재 문제점:**
```python
# 현재: 직접 Lambda 호출
lambda_client.invoke(
    FunctionName=agent_function_name,
    InvocationType='Event',
    Payload=json.dumps(event)
)
```

**AgentCore 적용:**
```python
# AgentCore Tool Use primitive 사용
from bedrock_agent_runtime import BedrockAgentRuntimeClient

agent_runtime = BedrockAgentRuntimeClient()

response = agent_runtime.invoke_agent(
    agentId=AGENT_ID,
    agentAliasId=AGENT_ALIAS_ID,
    sessionId=session_id,
    inputText=json.dumps({
        "action": "analyze_business",
        "data": business_info
    })
)
```

**장점:**
- ✅ Hackathon 필수 요구사항 충족
- ✅ Agent 간 통신 표준화
- ✅ 자동 재시도 및 오류 처리
- ✅ 실행 추적 및 모니터링

**예상 구현 시간:** 4-6시간

---

### 2. Memory Primitive 활용

**현재 문제점:**
```python
# 현재: DynamoDB 직접 관리
dynamodb.put_item(
    TableName='sessions',
    Item={'sessionId': session_id, 'data': data}
)
```

**AgentCore Memory 적용:**
```python
# Memory primitive 사용
agent_runtime.put_session_memory(
    agentId=AGENT_ID,
    agentAliasId=AGENT_ALIAS_ID,
    sessionId=session_id,
    memoryType='SESSION_SUMMARY',
    memoryContents=[{
        'sessionSummary': {
            'summaryText': workflow_summary
        }
    }]
)
```

**장점:**
- ✅ 세션 상태 자동 관리
- ✅ 대화 컨텍스트 유지
- ✅ 메모리 최적화

**예상 구현 시간:** 2-3시간

---

## 📚 Bedrock Knowledge Base 활용 방안

### 1. Market Analyst Agent 강화 (권장)

**활용 시나리오:**
- 16개 업종별 시장 데이터 (현재 JSON)
- 17개 지역별 특성 데이터
- 시장 트렌드, 경쟁 분석 데이터

**구현 방법:**
```python
# 1. S3에 문서 업로드
s3://ai-branding-kb/
  ├── industries/
  │   ├── restaurant.txt
  │   ├── retail.txt
  │   └── ...
  ├── regions/
  │   ├── seoul.txt
  │   ├── busan.txt
  │   └── ...
  └── trends/
      ├── consumer_trends.txt
      └── market_trends.txt

# 2. Bedrock KB 생성 및 동기화
aws bedrock-agent create-knowledge-base \
  --name ai-branding-knowledge \
  --role-arn arn:aws:iam::xxx:role/BedrockKBRole \
  --knowledge-base-configuration '{
    "type": "VECTOR",
    "vectorKnowledgeBaseConfiguration": {
      "embeddingModelArn": "arn:aws:bedrock:us-west-2::foundation-model/amazon.titan-embed-text-v1"
    }
  }'

# 3. Agent에서 사용
results = knowledge_base.search(
    query=f"What are the market trends for {industry} in {region}?",
    top_k=5
)
```

**장점:**
- ✅ 의미 기반 검색 (단순 키 매칭보다 정확)
- ✅ 자동 임베딩 및 벡터화
- ✅ 확장 가능 (새 데이터 추가 용이)
- ✅ Hackathon 요구사항 충족

**예상 구현 시간:** 6-8시간

---

### 2. Reporter Agent 강화 (선택)

**활용 시나리오:**
- 성공적인 브랜드명 사례 데이터베이스
- 업종별 네이밍 트렌드
- 지역별 선호 키워드

**구현 방법:**
```python
# KB에서 유사 브랜드명 검색
similar_names = kb.search(
    query=f"Successful {industry} business names in {region}",
    top_k=10
)

# Claude에게 컨텍스트 제공
prompt = f"""
Based on these successful examples:
{similar_names}

Generate 3 creative business names for:
- Industry: {industry}
- Region: {region}
- Style: Modern, memorable
"""
```

**장점:**
- ✅ 데이터 기반 네이밍
- ✅ 트렌드 반영
- ✅ 중복 방지 강화

**예상 구현 시간:** 4-5시간

---

## 💰 예상 비용 분석

### 1. AgentCore 비용

**Bedrock Agent 가격 (us-west-2):**
- Agent 호출: **$0.00025 per request**
- Tool Use: 추가 비용 없음 (Agent 호출에 포함)
- Memory: 추가 비용 없음

**월간 예상 사용량 (개발/테스트):**
- 세션 수: 100 sessions/month
- 세션당 Agent 호출: 7 calls (7 agents)
- 총 호출: 700 calls/month

**월간 비용:**
```
700 calls × $0.00025 = $0.175/month ≈ $0.18/month
```

**연간 비용:** ~$2.16/year

---

### 2. Bedrock Knowledge Base 비용

**구성 요소:**

#### A. 임베딩 비용 (Titan Embeddings)
- **가격**: $0.0001 per 1,000 tokens
- **초기 데이터**: ~500KB (약 125,000 tokens)
- **초기 임베딩**: 125 × $0.0001 = **$0.0125 (1회)**

#### B. 벡터 스토리지 (OpenSearch Serverless)
- **가격**: $0.24 per OCU-hour
- **최소 OCU**: 2 OCUs (인덱싱 1 + 검색 1)
- **월간 비용**: 2 × $0.24 × 730 hours = **$350.40/month**

⚠️ **주의**: OpenSearch Serverless는 비쌈!

#### C. 대안: S3 + Bedrock KB (권장)
- **S3 스토리지**: $0.023 per GB/month
- **데이터 크기**: ~1MB
- **S3 비용**: $0.023 × 0.001 = **$0.00002/month**
- **KB 쿼리**: $0.0001 per query
- **월간 쿼리**: 700 queries
- **쿼리 비용**: 700 × $0.0001 = **$0.07/month**

**월간 총 비용 (S3 방식):** ~$0.07/month
**연간 비용:** ~$0.84/year

---

### 3. 총 예상 비용 요약

| 항목 | 월간 비용 | 연간 비용 | 비고 |
|------|----------|----------|------|
| **AgentCore** | $0.18 | $2.16 | 필수 (Hackathon) |
| **Bedrock KB (S3)** | $0.07 | $0.84 | 권장 |
| **OpenSearch Serverless** | $350.40 | $4,204.80 | ❌ 비추천 |
| **총계 (권장)** | **$0.25** | **$3.00** | 매우 저렴 |

---

## 🎯 권장 구현 우선순위

### Phase 1: 필수 (Hackathon 제출용) - 6-8시간
1. ✅ **AgentCore Tool Use** - Supervisor Agent 통합
2. ✅ **AgentCore Memory** - 세션 관리 개선
3. ✅ **비용**: ~$0.18/month

### Phase 2: 권장 (경쟁력 강화) - 6-8시간
1. ✅ **Bedrock KB 구축** - Market Analyst 데이터
2. ✅ **S3 벡터 스토리지** - 비용 효율적
3. ✅ **비용**: ~$0.07/month

### Phase 3: 선택 (추가 개선) - 4-5시간
1. ⭐ **Reporter KB** - 브랜드명 사례 DB
2. ⭐ **비용**: 추가 비용 거의 없음

---

## 📋 구현 체크리스트

### AgentCore 구현
- [ ] Bedrock Agent 생성 (AWS Console)
- [ ] Agent ID 환경변수 설정
- [ ] Supervisor Agent에 AgentCore 통합
- [ ] Tool Use primitive 구현
- [ ] Memory primitive 구현
- [ ] 테스트 및 검증

### Bedrock KB 구현
- [ ] S3 버킷 생성 (또는 기존 사용)
- [ ] 문서 준비 및 업로드
- [ ] Bedrock KB 생성
- [ ] 데이터 소스 연결 (S3)
- [ ] 동기화 실행
- [ ] KB ID 환경변수 설정
- [ ] Agent 코드 업데이트
- [ ] 테스트 및 검증

---

## 🚀 빠른 시작 가이드

### 1. AgentCore 설정 (10분)

```bash
# 1. Bedrock Agent 생성
aws bedrock-agent create-agent \
  --agent-name ai-branding-supervisor \
  --foundation-model anthropic.claude-v2 \
  --instruction "Orchestrate AI branding workflow agents"

# 2. Agent Alias 생성
aws bedrock-agent create-agent-alias \
  --agent-id <AGENT_ID> \
  --agent-alias-name prod

# 3. 환경변수 설정
export BEDROCK_AGENT_ID=<AGENT_ID>
export BEDROCK_AGENT_ALIAS_ID=<ALIAS_ID>
```

### 2. Bedrock KB 설정 (20분)

```bash
# 1. 문서 준비
python scripts/prepare_kb_documents.py

# 2. S3 업로드
aws s3 sync ./kb-data s3://ai-branding-kb/

# 3. KB 생성
aws bedrock-agent create-knowledge-base \
  --name ai-branding-knowledge \
  --role-arn <KB_ROLE_ARN> \
  --knowledge-base-configuration file://kb-config.json

# 4. 데이터 소스 연결
aws bedrock-agent create-data-source \
  --knowledge-base-id <KB_ID> \
  --name s3-data-source \
  --data-source-configuration file://data-source-config.json

# 5. 동기화
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id <KB_ID> \
  --data-source-id <DATA_SOURCE_ID>
```

---

## 📊 ROI 분석

### 비용 대비 효과

**투자:**
- 개발 시간: 12-16시간
- 월간 비용: $0.25
- 연간 비용: $3.00

**효과:**
1. **Hackathon 필수 요구사항 충족** ✅
   - AgentCore 사용
   - Bedrock KB 사용
   - 수상 가능성 증가

2. **기술적 개선**
   - Agent 통신 표준화
   - 의미 기반 검색
   - 확장성 향상

3. **비용 효율성**
   - 매우 저렴 ($3/year)
   - 무료 티어 활용 가능
   - 프로덕션 확장 용이

**결론:** 🎯 **강력 권장!**

---

## 🎓 학습 리소스

- [Bedrock Agents Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [AgentCore Primitives](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-action-groups.html)
- [Hackathon Requirements](./AWS%20Hackathon%20rules.md)

---

## 📝 다음 단계

1. **결정**: AgentCore + KB 구현 여부 결정
2. **계획**: 구현 일정 수립 (12-16시간)
3. **실행**: Phase 1 (AgentCore) 먼저 구현
4. **테스트**: 각 Phase별 검증
5. **제출**: Hackathon 제출 전 최종 확인

---

**작성일**: 2025-10-21
**버전**: 1.0
**상태**: 분석 완료, 구현 대기
