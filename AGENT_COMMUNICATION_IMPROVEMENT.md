# Agent Communication 개선 방안

## 현재 상태
- ✅ HTTP API 기반 Agent 호출 (잘 작동 중)
- ⚠️ Mock 응답 코드 포함 (사용 안 함)
- ⚠️ AgentCore 코드 포함 (사용 안 함)
- ⚠️ SQS/SNS 코드 포함 (사용 안 함)

## 권장 개선 방안: 코드 정리 및 단순화

### 1. Mock 코드 제거
**이유:** 실제 환경에서 사용하지 않음

```python
# 제거할 부분
def _get_mock_agent_response(...):
    # 650-730 라인의 Mock 응답 코드
```

### 2. 사용하지 않는 AgentCore 코드 정리
**옵션 A:** 완전 제거
**옵션 B:** 주석 처리 + 문서화 (미래 사용 대비)

```python
# 정리할 부분
def _invoke_via_agentcore(...):
    # 450-520 라인
    # 주석: "Future: Bedrock AgentCore integration"
```

### 3. 실제 사용 중인 기능만 유지

```python
class AgentCommunication:
    """Simplified agent communication for HTTP API architecture"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.sessions_table = self.dynamodb.Table(os.getenv('SESSIONS_TABLE'))
    
    def update_agent_status(self, session_id, agent_name, status, result, latency_ms):
        """Update agent execution status in DynamoDB"""
        # 현재 사용 중
        
    def log_agent_interaction(self, source_agent, target_agent, latency_ms):
        """Log agent interaction for monitoring"""
        # CloudWatch Logs
```

### 4. 새로운 간소화된 구조

```
src/lambda/shared/
├── agent_state.py          # DynamoDB 상태 관리
├── agent_logging.py        # CloudWatch 로깅
└── agent_metrics.py        # 성능 메트릭
```

## 구현 단계

### Phase 1: 정리 (즉시)
1. Mock 코드 제거
2. 사용하지 않는 AgentCore 코드 주석 처리
3. SQS/SNS 코드 주석 처리

### Phase 2: 리팩토링 (선택)
1. 3개 모듈로 분리
2. 각 Agent에서 직접 사용
3. 테스트 추가

### Phase 3: 모니터링 강화 (선택)
1. CloudWatch Metrics 추가
2. X-Ray 트레이싱
3. 대시보드 구성

## 코드 예시

### 간소화된 agent_state.py
```python
"""Agent state management for DynamoDB"""
import boto3
import os
from datetime import datetime

class AgentState:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(os.getenv('SESSIONS_TABLE'))
    
    def update_status(self, session_id, agent_name, status, result=None, latency_ms=None):
        """Update agent status in session"""
        update_data = {
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if result:
            update_data['result'] = result
        if latency_ms:
            update_data['latencyMs'] = latency_ms
        
        self.table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression='SET agentStatuses.#agent = :data, updatedAt = :ts',
            ExpressionAttributeNames={'#agent': agent_name},
            ExpressionAttributeValues={
                ':data': update_data,
                ':ts': datetime.utcnow().isoformat()
            }
        )
    
    def get_status(self, session_id, agent_name):
        """Get agent status from session"""
        response = self.table.get_item(Key={'sessionId': session_id})
        if 'Item' in response:
            return response['Item'].get('agentStatuses', {}).get(agent_name)
        return None
```

### 간소화된 agent_logging.py
```python
"""Agent execution logging"""
import logging
import json

class AgentLogger:
    def __init__(self, agent_name):
        self.logger = logging.getLogger(agent_name)
        self.agent_name = agent_name
    
    def log_execution(self, session_id, action, status, latency_ms=None, **kwargs):
        """Log agent execution with structured data"""
        log_data = {
            'agent': self.agent_name,
            'session_id': session_id,
            'action': action,
            'status': status,
            'latency_ms': latency_ms,
            **kwargs
        }
        
        if status == 'success':
            self.logger.info(json.dumps(log_data))
        else:
            self.logger.error(json.dumps(log_data))
```

## 결론

**권장사항:** Phase 1 (정리)만 수행
- 현재 아키텍처가 잘 작동하고 있음
- Mock/미사용 코드만 제거하여 유지보수성 향상
- 복잡도 증가 없이 코드 품질 개선

**선택사항:** Phase 2-3는 필요시에만
- 현재는 불필요
- 미래 확장 시 고려
