# Quick Guide: Running Hackathon Workflow Tests

## Prerequisites

1. **Docker Compose Services Running**
   ```bash
   docker-compose -f docker-compose.local.yml up -d
   ```

2. **Virtual Environment Activated**
   ```bash
   source venv/bin/activate
   ```

3. **Verify Services Health**
   ```bash
   # DynamoDB Local
   curl http://localhost:8000
   
   # MinIO
   curl http://localhost:9000/minio/health/live
   
   # Chroma
   curl http://localhost:8001
   ```

## Run All Hackathon Tests

```bash
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py -v
```

**Expected Output**:
```
6 passed in ~8 seconds
```

## Run Individual Tests

### 1. Full Workflow Test
```bash
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py::TestFullWorkflowWithBedrock::test_full_workflow_with_bedrock -v
```

### 2. Autonomous Execution Test
```bash
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py::TestAutonomousExecution::test_autonomous_execution -v
```

### 3. Fallback Mechanism Test
```bash
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py::TestFallbackMechanism::test_fallback_mechanism -v
```

### 4. PDF Report Generation Test
```bash
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py::TestPDFReportGeneration::test_pdf_report_generation -v
```

### 5. Concurrent Sessions Test
```bash
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py::TestConcurrentSessions::test_concurrent_sessions -v
```

### 6. Workflow State Management Test
```bash
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py::TestWorkflowStateManagement::test_workflow_pause_and_resume -v
```

## Verbose Output with Details

```bash
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py -v -s
```

The `-s` flag shows print statements and detailed output.

## Run with Coverage Report

```bash
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py --cov=src/lambda/shared --cov-report=html
```

## Troubleshooting

### Docker Services Not Running
```bash
# Start services
docker-compose -f docker-compose.local.yml up -d

# Check status
docker-compose -f docker-compose.local.yml ps

# View logs
docker-compose -f docker-compose.local.yml logs
```

### Port Conflicts
```bash
# Check what's using ports
lsof -i :8000,8001,8002,9000,9001

# Stop conflicting services
docker-compose -f docker-compose.local.yml down -v
```

### Test Failures
```bash
# Run with full traceback
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py -v --tb=long

# Run with pdb debugger on failure
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py --pdb
```

### Clean Test Data
```bash
# Stop services and remove volumes
docker-compose -f docker-compose.local.yml down -v

# Restart fresh
docker-compose -f docker-compose.local.yml up -d
```

## Verify Test Data

### DynamoDB Admin UI
```
http://localhost:8002
```
- View test sessions
- Inspect agent logs
- Check data structure

### MinIO Console
```
http://localhost:9001
Username: minioadmin
Password: minioadmin
```
- View test PDFs
- Check bucket contents
- Verify file uploads

## Performance Benchmarks

| Test | Expected Time | Status |
|------|--------------|--------|
| Full Workflow | ~1.5s | ✅ |
| Autonomous Execution | ~1.0s | ✅ |
| Fallback Mechanism | ~0.8s | ✅ |
| PDF Generation | ~0.9s | ✅ |
| Concurrent Sessions | ~2.5s | ✅ |
| State Management | ~1.3s | ✅ |
| **Total** | **~8s** | ✅ |

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Hackathon Tests
  run: |
    docker-compose -f docker-compose.local.yml up -d
    sleep 10  # Wait for services
    ./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py -v
```

### Pre-Deployment Check
```bash
# Run before deploying to AWS
./scripts/run-integration-tests.sh
```

## Test Coverage

- ✅ Full 5-step workflow
- ✅ Autonomous execution
- ✅ Fallback mechanisms
- ✅ PDF generation
- ✅ Concurrent sessions (10 simultaneous)
- ✅ Workflow pause/resume
- ✅ DynamoDB persistence
- ✅ S3 storage
- ✅ Performance validation

## Success Indicators

All tests should show:
```
✓ Session created
✓ Product Insight completed
✓ Market Analyst completed
✓ Reporter Agent completed
✓ Signboard Agent completed
✓ Interior Agent completed
✓ Report Generator completed
✅ Full workflow completed successfully!
```

## Quick Validation

```bash
# One-liner to run all tests
docker-compose -f docker-compose.local.yml up -d && \
sleep 5 && \
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py -v
```

## Notes

- Tests automatically clean up after execution
- No manual data cleanup required
- Tests are independent and can run in any order
- Docker Compose must be running before tests
- All tests follow NO MOCKS policy

---

**Last Updated**: October 16, 2025
**Test Status**: ✅ All Passing
**Total Tests**: 6
**Execution Time**: ~8 seconds
