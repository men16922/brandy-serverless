#!/usr/bin/env python3
"""
DynamoDB 테이블 생성 (로컬 환경)
"""

import sys
import os
import boto3
from botocore.exceptions import ClientError

# 프로젝트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'lambda'))

# 환경변수 로드
from shared.env_loader import load_env_file
load_env_file()

def create_dynamodb_tables():
    """DynamoDB 테이블 생성"""
    try:
        # DynamoDB 클라이언트 생성
        dynamodb = boto3.client(
            'dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='us-east-1',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        
        table_name = 'ai-branding-chatbot-sessions-local'
        
        print(f"🔄 DynamoDB 테이블 생성: {table_name}")
        
        # 테이블이 이미 존재하는지 확인
        try:
            response = dynamodb.describe_table(TableName=table_name)
            print(f"✅ 테이블이 이미 존재합니다: {table_name}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise e
        
        # 테이블 생성
        table_definition = {
            'TableName': table_name,
            'KeySchema': [
                {
                    'AttributeName': 'sessionId',
                    'KeyType': 'HASH'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'sessionId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'currentStep',
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': 'createdAt',
                    'AttributeType': 'S'
                }
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'StepIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'currentStep',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'createdAt',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        }
        
        response = dynamodb.create_table(**table_definition)
        print(f"✅ 테이블 생성 성공: {table_name}")
        
        # 테이블 상태 확인
        waiter = dynamodb.get_waiter('table_exists')
        print("🔄 테이블 활성화 대기 중...")
        waiter.wait(TableName=table_name)
        
        print(f"✅ 테이블 활성화 완료: {table_name}")
        
        # TTL 설정 (24시간)
        try:
            dynamodb.update_time_to_live(
                TableName=table_name,
                TimeToLiveSpecification={
                    'AttributeName': 'ttl',
                    'Enabled': True
                }
            )
            print("✅ TTL 설정 완료 (24시간)")
        except Exception as e:
            print(f"⚠️  TTL 설정 실패: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_table_operations():
    """테이블 기본 동작 테스트"""
    try:
        dynamodb = boto3.client(
            'dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='us-east-1',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        
        table_name = 'ai-branding-chatbot-sessions-local'
        
        print(f"\n🧪 테이블 동작 테스트: {table_name}")
        
        # 테스트 세션 데이터
        from datetime import datetime, timezone
        import time
        
        test_session = {
            'sessionId': {'S': 'test-session-123'},
            'currentStep': {'N': '1'},
            'status': {'S': 'active'},
            'createdAt': {'S': datetime.now(timezone.utc).isoformat()},
            'ttl': {'N': str(int(time.time()) + 86400)},  # 24시간 후
            'businessInfo': {
                'M': {
                    'industry': {'S': 'restaurant'},
                    'region': {'S': 'seoul'},
                    'size': {'S': 'medium'}
                }
            }
        }
        
        # 데이터 삽입
        print("🔄 테스트 데이터 삽입...")
        dynamodb.put_item(
            TableName=table_name,
            Item=test_session
        )
        print("✅ 데이터 삽입 성공")
        
        # 데이터 조회
        print("🔄 데이터 조회...")
        response = dynamodb.get_item(
            TableName=table_name,
            Key={'sessionId': {'S': 'test-session-123'}}
        )
        
        if 'Item' in response:
            print("✅ 데이터 조회 성공")
            item = response['Item']
            print(f"   세션 ID: {item['sessionId']['S']}")
            print(f"   현재 단계: {item['currentStep']['N']}")
            print(f"   상태: {item['status']['S']}")
        else:
            print("❌ 데이터 조회 실패")
            return False
        
        # 데이터 삭제
        print("🔄 테스트 데이터 삭제...")
        dynamodb.delete_item(
            TableName=table_name,
            Key={'sessionId': {'S': 'test-session-123'}}
        )
        print("✅ 데이터 삭제 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ 테이블 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 함수"""
    print("🚀 DynamoDB 로컬 테이블 설정 시작\n")
    
    success_count = 0
    
    # 1. 테이블 생성
    if create_dynamodb_tables():
        success_count += 1
    
    # 2. 테이블 동작 테스트
    if test_table_operations():
        success_count += 1
    
    print(f"\n📊 결과: {success_count}/2 성공")
    
    if success_count == 2:
        print("🎉 DynamoDB 설정 완료!")
        print("\n💡 DynamoDB Admin UI에서 확인:")
        print("   URL: http://localhost:8002")
        print("   테이블: ai-branding-chatbot-sessions-local")
        return True
    else:
        print("❌ DynamoDB 설정 실패")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)