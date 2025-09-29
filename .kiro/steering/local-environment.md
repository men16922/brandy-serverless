# Local Development Environment

## Python Virtual Environment Setup

**CRITICAL**: Always use Python virtual environment for local development to ensure dependency isolation and consistency.

### Initial Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Verify activation (should show venv path)
which python
which pip

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Daily Development Workflow
```bash
# 1. Always activate venv first
source venv/bin/activate

# 2. Start Docker services
docker-compose -f docker-compose.local.yml up -d

# 3. Wait for services to be ready
./scripts/setup-local.sh

# 4. Run tests or development
python -m pytest tests/integration/ -v
# OR
cd src/streamlit && streamlit run app.py
```

### Environment Validation
```bash
# Check Python environment
python --version  # Should be 3.11+
pip list | grep boto3  # Should show installed packages

# Check Docker services
docker-compose -f docker-compose.local.yml ps
curl http://localhost:8000  # DynamoDB Local
curl http://localhost:9000/minio/health/live  # MinIO
curl http://localhost:8001  # Chroma
```

## No Mock Testing Policy

**NEVER use mocks in tests**. Always use real services:

- **DynamoDB**: Use DynamoDB Local (localhost:8000)
- **S3**: Use MinIO (localhost:9000)
- **Vector DB**: Use Chroma (localhost:8001)
- **Data Storage**: Store test data in actual databases, not JSON files

### Real Data Testing Pattern
```python
# ✅ CORRECT: Use real DynamoDB
def test_session_storage():
    dynamodb = boto3.client('dynamodb', endpoint_url='http://localhost:8000')
    session_data = create_test_session()
    
    # Store in real DynamoDB
    dynamodb.put_item(TableName='test-sessions', Item=session_data)
    
    # Retrieve and verify
    response = dynamodb.get_item(TableName='test-sessions', Key={'id': session_data['id']})
    assert response['Item'] == session_data

# ❌ WRONG: Don't use mocks or JSON files
def test_session_storage_wrong():
    mock_db = Mock()  # DON'T DO THIS
    with open('test_data.json') as f:  # DON'T DO THIS
        test_data = json.load(f)
```

## Service URLs and Access

### Local Services
- **DynamoDB Local**: http://localhost:8000
- **DynamoDB Admin UI**: http://localhost:8002 (visual table management)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **MinIO API**: http://localhost:9000
- **Chroma**: http://localhost:8001

### Development Tools
- **Streamlit App**: http://localhost:8501 (after running streamlit)
- **SAM Local API**: http://localhost:3000 (after sam local start-api)

## Troubleshooting

### Common Issues
1. **Virtual environment not activated**
   ```bash
   # Check if venv is active
   echo $VIRTUAL_ENV  # Should show path to venv
   
   # If not active, activate it
   source venv/bin/activate
   ```

2. **Port conflicts**
   ```bash
   # Check what's using ports
   lsof -i :8000,8001,8002,9000,9001
   
   # Kill conflicting processes if needed
   sudo lsof -ti:8000 | xargs kill -9
   ```

3. **Docker services not starting**
   ```bash
   # Check Docker status
   docker info
   
   # Restart services
   docker-compose -f docker-compose.local.yml down -v
   docker-compose -f docker-compose.local.yml up -d
   ```

4. **Dependencies missing**
   ```bash
   # Ensure venv is active, then reinstall
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Integration Testing Requirements

### Test Environment Setup
- All tests must use Docker Compose services
- No mocks or fake data allowed
- Test data stored in real databases (DynamoDB, MinIO, Chroma)
- Visual verification available through admin UIs

### Test Data Management
```python
# Store test data in DynamoDB, not JSON files
def setup_test_data():
    dynamodb = boto3.client('dynamodb', endpoint_url='http://localhost:8000')
    
    # Create test session directly in DynamoDB
    test_session = {
        'sessionId': {'S': 'test-123'},
        'businessInfo': {'M': {
            'industry': {'S': 'restaurant'},
            'region': {'S': 'seoul'}
        }},
        'currentStep': {'N': '1'},
        'status': {'S': 'active'}
    }
    
    dynamodb.put_item(TableName='test-sessions', Item=test_session)
    return test_session
```

### Performance Expectations
- Docker services start: < 30 seconds
- Test execution: < 2 minutes per test file
- Service health checks: < 10 seconds
- Data operations: < 1 second per operation