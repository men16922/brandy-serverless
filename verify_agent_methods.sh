#!/bin/bash

# Agent 메서드 호출 검증 스크립트

echo "=== Agent Method Call Verification ==="
echo ""

# 1. update_session_data 호출 확인
echo "1. Checking update_session_data calls..."
grep -rn "update_session_data" src/lambda/agents/*/index.py | grep -v "def update_session_data" | wc -l
echo "   Found $(grep -rn 'update_session_data' src/lambda/agents/*/index.py | grep -v 'def update_session_data' | wc -l) calls"
echo ""

# 2. convert_floats_to_decimal 사용 확인
echo "2. Checking convert_floats_to_decimal usage..."
grep -rn "convert_floats_to_decimal" src/lambda/agents/*/index.py | wc -l
echo "   Found $(grep -rn 'convert_floats_to_decimal' src/lambda/agents/*/index.py | wc -l) usages"
echo ""

# 3. json.dumps 사용 확인 (Decimal 문제 가능성)
echo "3. Checking json.dumps calls (potential Decimal issues)..."
grep -rn "json.dumps" src/lambda/agents/*/index.py
echo ""

# 4. Float 리터럴 확인
echo "4. Checking float literals in score assignments..."
grep -rn "score.*=.*\d\+\.\d\+" src/lambda/agents/*/index.py | head -10
echo ""

# 5. BaseAgent 상속 확인
echo "5. Checking BaseAgent inheritance..."
grep -rn "class.*Agent.*BaseAgent" src/lambda/agents/*/index.py
echo ""

# 6. Lambda handler 확인
echo "6. Checking lambda_handler functions..."
grep -rn "def lambda_handler" src/lambda/agents/*/index.py
echo ""

echo "=== Verification Complete ==="
