# 통합 테스트 빠른 참조 카드

## 🚀 빠른 시작

### 로컬 테스트
```bash
./venv/bin/python scripts/run_integration_tests.py local
```

### AWS Dev 테스트
```bash
./venv/bin/python scripts/run_integration_tests.py dev
```

---

## 📝 주요 명령어

| 명령어 | 설명 |
|--------|------|
| `./venv/bin/python scripts/run_integration_tests.py list` | 테스트 목록 보기 |
| `./venv/bin/python scripts/run_integration_tests.py local` | 로컬 테스트 실행 |
| `./venv/bin/python scripts/run_integration_tests.py dev` | AWS Dev 테스트 실행 |
| `./venv/bin/python scripts/run_integration_tests.py specific <test>` | 특정 테스트 실행 |

---

## 🐳 Docker 명령어

```bash
# 서비스 시작
docker-compose -f docker-compose.local.yml up -d

# 서비스 중지
docker-compose -f docker-compose.local.yml down

# 서비스 중지 + 데이터 삭제
docker-compose -f docker-compose.local.yml down -v

# 서비스 상태 확인
docker-compose -f docker-compose.local.yml ps

# 로그 확인
docker-compose -f docker-compose.local.yml logs -f
```

---

## 🔗 로컬 서비스 URL

| 서비스 | URL | 자격 증명 |
|--------|-----|----------|
| DynamoDB Admin | http://localhost:8002 | - |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| Chroma API | http://localhost:8001 | - |
| DynamoDB Local | http://localhost:8000 | - |
| MinIO API | http://localhost:9000 | - |

---

## 🧪 개별 테스트 실행

```bash
# 전체 워크플로 테스트
./venv/bin/python scripts/run_integration_tests.py specific TestFullWorkflowWithBedrock

# 자율 실행 테스트
./venv/bin/python scripts/run_integration_tests.py specific TestAutonomousExecution

# Fallback 메커니즘 테스트
./venv/bin/python scripts/run_integration_tests.py specific TestFallbackMechanism

# PDF 생성 테스트
./venv/bin/python scripts/run_integration_tests.py specific TestPDFReportGeneration

# 동시 세션 테스트
./venv/bin/python scripts/run_integration_tests.py specific TestConcurrentSessions

# 상태 관리 테스트
./venv/bin/python scripts/run_integration_tests.py specific TestWorkflowStateManagement
```

---

## 🔧 문제 해결

### Docker 서비스 재시작
```bash
docker-compose -f docker-compose.local.yml restart
```

### 포트 충돌 해결
```bash
lsof -i :8000,8001,8002,9000,9001
sudo lsof -ti:8000 | xargs kill -9
```

### 테스트 데이터 정리
```bash
docker-compose -f docker-compose.local.yml down -v
```

### AWS 자격 증명 확인
```bash
aws sts get-caller-identity
```

---

## 📊 테스트 결과 확인

### 로컬 환경
- DynamoDB: http://localhost:8002
- MinIO: http://localhost:9001

### AWS Dev 환경
```bash
# DynamoDB 테이블
aws dynamodb scan --table-name ai-branding-chatbot-sessions --region us-east-1

# S3 버킷
aws s3 ls s3://ai-branding-chatbot-assets/ --recursive
```

---

## ⚡ 고급 옵션

```bash
# 상세 출력
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py -v -s

# 실패 시 디버거 실행
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py --pdb

# 커버리지 리포트
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py --cov

# 실행 시간 측정
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py --durations=10
```

---

## 📈 성능 벤치마크

| 테스트 | 예상 시간 |
|--------|----------|
| TestFullWorkflowWithBedrock | ~1.5s |
| TestAutonomousExecution | ~1.0s |
| TestFallbackMechanism | ~0.8s |
| TestPDFReportGeneration | ~0.9s |
| TestConcurrentSessions | ~2.5s |
| TestWorkflowStateManagement | ~1.3s |
| **전체** | **~8s** |

---

## ✅ 체크리스트

### 로컬 테스트 전
- [ ] Docker 실행 중
- [ ] 가상환경 활성화
- [ ] 포트 8000, 8001, 8002, 9000, 9001 사용 가능

### AWS Dev 테스트 전
- [ ] AWS 자격 증명 설정
- [ ] SAM 스택 배포 완료
- [ ] Bedrock 접근 권한 확인

---

**빠른 도움말**: `./venv/bin/python scripts/run_integration_tests.py list`
