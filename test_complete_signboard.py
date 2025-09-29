#!/usr/bin/env python3
"""
완전한 Signboard Agent 워크플로 테스트
"""

import sys
import os
import asyncio
import json

# 프로젝트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'lambda'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'lambda', 'agents', 'signboard'))

# 환경변수 로드
from shared.env_loader import load_env_file
load_env_file()

async def test_complete_signboard_workflow():
    """완전한 Signboard Agent 워크플로 테스트"""
    try:
        print("🎨 완전한 Signboard Agent 워크플로 테스트...")
        
        # SignboardAgent 생성
        from index import SignboardAgent
        agent = SignboardAgent()
        print("✅ Signboard Agent 생성 성공")
        
        # 테스트 데이터 준비
        test_event = {
            'body': json.dumps({
                'sessionId': 'test-session-complete',
                'selectedName': '모던 카페',
                'businessInfo': {
                    'industry': 'restaurant',
                    'region': 'seoul',
                    'size': 'medium'
                },
                'action': 'generate'
            })
        }
        
        print("\n📋 테스트 데이터:")
        print(f"   세션 ID: test-session-complete")
        print(f"   비즈니스명: 모던 카페")
        print(f"   업종: restaurant")
        print(f"   지역: seoul")
        print(f"   규모: medium")
        
        # Agent 실행
        print("\n🚀 Signboard Agent 실행...")
        
        # Mock context 객체
        class MockContext:
            def __init__(self):
                self.function_name = "test-signboard-agent"
                self.aws_request_id = "test-request-id"
        
        context = MockContext()
        
        # Agent 실행
        result = agent.execute(test_event, context)
        
        print("✅ Agent 실행 완료")
        
        # 결과 분석
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            
            print("\n📊 실행 결과:")
            print(f"   세션 ID: {body.get('sessionId')}")
            print(f"   생성된 간판 수: {body.get('totalGenerated', 0)}")
            print(f"   진행 가능: {body.get('canProceed', False)}")
            print(f"   메시지: {body.get('message', 'N/A')}")
            
            # 생성된 간판들 확인
            signboards = body.get('signboards', [])
            if signboards:
                print(f"\n🎨 생성된 간판들 ({len(signboards)}개):")
                for i, signboard in enumerate(signboards, 1):
                    print(f"   {i}. 스타일: {signboard.get('style', 'N/A')}")
                    print(f"      제공자: {signboard.get('provider', 'N/A')}")
                    print(f"      URL: {signboard.get('url', 'N/A')}")
                    print(f"      폴백 여부: {signboard.get('is_fallback', False)}")
                    print()
            
            # 저장된 이미지 확인
            print("🔍 MinIO에 저장된 이미지 확인...")
            from shared.s3_client import get_s3_client
            s3_client = get_s3_client('local')
            
            session_objects = s3_client.list_objects(prefix="signboards/test-session-complete/")
            if session_objects:
                print(f"✅ 세션 이미지 {len(session_objects)}개 발견:")
                for obj in session_objects:
                    print(f"   📁 {obj['key']} ({obj['size']} bytes)")
                    url = s3_client.get_object_url(obj['key'])
                    print(f"      URL: {url}")
            else:
                print("⚠️  세션 이미지가 저장되지 않았습니다")
            
            return True
        else:
            print(f"❌ Agent 실행 실패: {result.get('statusCode')}")
            print(f"   응답: {result}")
            return False
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """메인 테스트 함수"""
    print("🚀 완전한 Signboard Agent 워크플로 테스트 시작\n")
    
    if await test_complete_signboard_workflow():
        print("\n🎉 완전한 워크플로 테스트 성공!")
        print("\n💡 MinIO Console에서 확인:")
        print("   URL: http://localhost:9001")
        print("   로그인: minioadmin / minioadmin")
        print("   버킷: ai-branding-chatbot-assets-local")
        print("   경로: signboards/test-session-complete/")
        return True
    else:
        print("\n❌ 워크플로 테스트 실패")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)