#!/usr/bin/env python3
"""
AI Branding Chatbot 통합 테스트
"""

import sys
import os
import asyncio
import json

# 프로젝트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'lambda'))

# 환경변수 로드
from shared.env_loader import load_env_file
load_env_file()

class IntegrationTester:
    """통합 테스트 클래스"""
    
    def __init__(self):
        self.success_count = 0
        self.total_tests = 0
    
    async def run_test(self, test_name: str, test_func):
        """테스트 실행 및 결과 기록"""
        print(f"\n🔄 {test_name}")
        self.total_tests += 1
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                print(f"✅ {test_name} 성공")
                self.success_count += 1
            else:
                print(f"❌ {test_name} 실패")
        except Exception as e:
            print(f"❌ {test_name} 오류: {str(e)}")
    
    def test_environment_setup(self) -> bool:
        """환경 설정 테스트"""
        try:
            from shared.env_loader import get_env_var, is_local_environment
            
            # 필수 환경변수 확인
            required_vars = [
                'ENVIRONMENT', 'OPENAI_API_KEY', 'S3_BUCKET', 'SESSIONS_TABLE'
            ]
            
            for var in required_vars:
                value = get_env_var(var)
                if not value:
                    print(f"   ❌ 필수 환경변수 누락: {var}")
                    return False
                print(f"   ✅ {var}: {value[:20]}..." if len(value) > 20 else f"   ✅ {var}: {value}")
            
            print(f"   📍 환경: {'로컬' if is_local_environment() else '개발/운영'}")
            return True
            
        except Exception as e:
            print(f"   ❌ 환경 설정 오류: {e}")
            return False
    
    def test_s3_client(self) -> bool:
        """S3/MinIO 클라이언트 테스트"""
        try:
            from shared.s3_client import get_s3_client
            
            s3_client = get_s3_client()
            print(f"   📦 버킷: {s3_client.bucket_name}")
            
            # 테스트 파일 업로드
            test_content = b"Integration test file"
            test_key = "test/integration-test.txt"
            
            upload_result = s3_client.upload_file(
                file_content=test_content,
                key=test_key,
                content_type="text/plain",
                metadata={"test": "integration"}
            )
            
            if not upload_result.get('success'):
                print(f"   ❌ 업로드 실패: {upload_result.get('error')}")
                return False
            
            print(f"   ✅ 파일 업로드 성공 ({len(test_content)} bytes)")
            
            # 파일 삭제
            if s3_client.delete_object(test_key):
                print("   ✅ 파일 삭제 성공")
            else:
                print("   ⚠️  파일 삭제 실패")
            
            return True
            
        except Exception as e:
            print(f"   ❌ S3 클라이언트 오류: {e}")
            return False
    
    def test_dynamodb_connection(self) -> bool:
        """DynamoDB 연결 테스트"""
        try:
            import boto3
            from shared.env_loader import get_env_var, is_local_environment
            
            if is_local_environment():
                dynamodb = boto3.client(
                    'dynamodb',
                    endpoint_url='http://localhost:8000',
                    region_name='us-east-1',
                    aws_access_key_id='dummy',
                    aws_secret_access_key='dummy'
                )
            else:
                dynamodb = boto3.client('dynamodb', region_name=get_env_var('AWS_REGION'))
            
            table_name = get_env_var('SESSIONS_TABLE')
            
            # 테이블 존재 확인
            try:
                response = dynamodb.describe_table(TableName=table_name)
                print(f"   ✅ 테이블 존재: {table_name}")
                print(f"   📊 상태: {response['Table']['TableStatus']}")
                return True
            except dynamodb.exceptions.ResourceNotFoundException:
                print(f"   ❌ 테이블 없음: {table_name}")
                return False
            
        except Exception as e:
            print(f"   ❌ DynamoDB 연결 오류: {e}")
            return False
    
    async def test_openai_api(self) -> bool:
        """OpenAI API 테스트"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'lambda', 'agents', 'signboard'))
            from index import OpenAIClient
            
            client = OpenAIClient()
            print(f"   🔑 API 키: {client.api_key[:20]}...")
            
            # 간단한 이미지 생성 테스트
            result = await client.generate_image(
                prompt="A simple test signboard",
                size="1024x1024"
            )
            
            if result.get("success"):
                print("   ✅ 이미지 생성 성공")
                print(f"   🖼️  URL: {result.get('image_url')[:50]}...")
                return True
            else:
                print(f"   ❌ 이미지 생성 실패: {result.get('error')}")
                return False
            
        except Exception as e:
            print(f"   ❌ OpenAI API 오류: {e}")
            return False
    
    async def test_signboard_agent(self) -> bool:
        """Signboard Agent 통합 테스트"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'lambda', 'agents', 'signboard'))
            from index import SignboardAgent
            
            agent = SignboardAgent()
            print("   🤖 Agent 초기화 성공")
            
            # 테스트 이벤트
            test_event = {
                'body': json.dumps({
                    'sessionId': 'integration-test-session',
                    'selectedName': '통합테스트 카페',
                    'businessInfo': {
                        'industry': 'restaurant',
                        'region': 'seoul',
                        'size': 'small'
                    },
                    'action': 'generate'
                })
            }
            
            class MockContext:
                function_name = "test-signboard-agent"
                aws_request_id = "test-request-id"
            
            # Agent 실행
            result = agent.execute(test_event, MockContext())
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                signboards = body.get('signboards', [])
                print(f"   ✅ Agent 실행 성공 ({len(signboards)}개 간판 생성)")
                
                # 실제 이미지가 생성되었는지 확인
                dalle_images = [s for s in signboards if s.get('provider') == 'dalle']
                if dalle_images:
                    print(f"   🎨 실제 이미지 생성: {len(dalle_images)}개")
                else:
                    print("   ⚠️  폴백 이미지만 생성됨")
                
                return True
            else:
                print(f"   ❌ Agent 실행 실패: {result.get('statusCode')}")
                return False
            
        except Exception as e:
            print(f"   ❌ Signboard Agent 오류: {e}")
            return False
    
    def test_stored_images(self) -> bool:
        """저장된 이미지 확인"""
        try:
            from shared.s3_client import get_s3_client
            
            s3_client = get_s3_client()
            
            # 간판 이미지들 조회
            signboard_objects = s3_client.list_objects(prefix="signboards/", max_keys=10)
            
            if signboard_objects:
                print(f"   ✅ 저장된 간판 이미지: {len(signboard_objects)}개")
                for obj in signboard_objects[-3:]:  # 최근 3개만 표시
                    size_mb = obj['size'] / (1024 * 1024)
                    print(f"      📁 {obj['key']} ({size_mb:.1f}MB)")
            else:
                print("   ⚠️  저장된 간판 이미지 없음")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 이미지 확인 오류: {e}")
            return False
    
    def print_summary(self):
        """테스트 결과 요약"""
        print(f"\n📊 통합 테스트 결과: {self.success_count}/{self.total_tests} 성공")
        
        if self.success_count == self.total_tests:
            print("🎉 모든 테스트 통과!")
            print("\n💡 접근 URL:")
            print("   MinIO Console: http://localhost:9001 (minioadmin/minioadmin)")
            print("   DynamoDB Admin: http://localhost:8002")
        else:
            print("❌ 일부 테스트 실패")
        
        return self.success_count == self.total_tests

async def main():
    """메인 테스트 함수"""
    print("🚀 AI Branding Chatbot 통합 테스트 시작\n")
    
    tester = IntegrationTester()
    
    # 테스트 실행
    await tester.run_test("환경 설정 확인", tester.test_environment_setup)
    await tester.run_test("S3/MinIO 클라이언트", tester.test_s3_client)
    await tester.run_test("DynamoDB 연결", tester.test_dynamodb_connection)
    await tester.run_test("OpenAI API", tester.test_openai_api)
    await tester.run_test("Signboard Agent", tester.test_signboard_agent)
    await tester.run_test("저장된 이미지 확인", tester.test_stored_images)
    
    # 결과 요약
    return tester.print_summary()

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)