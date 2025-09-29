#!/usr/bin/env python3
"""
Signboard Agent 이미지 저장 기능 테스트
"""

import sys
import os
import asyncio

# 프로젝트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'lambda'))

# 환경변수 로드
from shared.env_loader import load_env_file
load_env_file()

async def test_signboard_image_storage():
    """Signboard Agent 이미지 저장 테스트"""
    try:
        print("🎨 Signboard Agent 이미지 저장 테스트...")
        
        # Signboard Agent 경로 추가
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'lambda', 'agents', 'signboard'))
        
        from index import SignboardAgent
        
        # Agent 인스턴스 생성
        agent = SignboardAgent()
        print("✅ Signboard Agent 인스턴스 생성 성공")
        
        # S3 클라이언트 확인
        if agent.s3_client:
            print(f"✅ S3/MinIO 클라이언트 초기화됨: {agent.s3_client.bucket_name}")
        else:
            print("❌ S3/MinIO 클라이언트 초기화 실패")
            return False
        
        # OpenAI 클라이언트 확인
        if agent.openai_client:
            print("✅ OpenAI 클라이언트 초기화됨")
        else:
            print("❌ OpenAI 클라이언트 초기화 실패")
            return False
        
        # 실제 이미지 생성 테스트
        print("\n🎨 실제 이미지 생성 및 저장 테스트...")
        
        # BusinessInfo 객체 생성
        from shared.models import BusinessInfo
        business_info_obj = BusinessInfo(
            industry='restaurant',
            region='seoul',
            size='medium'
        )
        
        # 단일 이미지 생성 테스트
        image_result = await agent._generate_single_image(
            session_id="test-session-123",
            selected_name="테스트 카페",
            business_info=business_info_obj,
            style="modern"
        )
        
        if image_result and not image_result.is_fallback:
            print("✅ 이미지 생성 및 저장 성공!")
            print(f"🖼️  이미지 URL: {image_result.url}")
            print(f"🎨 스타일: {image_result.style}")
            print(f"🤖 제공자: {image_result.provider}")
            
            # 메타데이터 출력
            if image_result.metadata:
                print("📋 메타데이터:")
                for key, value in image_result.metadata.items():
                    print(f"   - {key}: {value}")
            
            return True
        else:
            print("❌ 이미지 생성 실패 또는 폴백 이미지 반환")
            if image_result:
                print(f"   폴백 여부: {image_result.is_fallback}")
            return False
        
    except Exception as e:
        print(f"❌ Signboard Agent 저장 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """메인 테스트 함수"""
    print("🚀 Signboard Agent 이미지 저장 테스트 시작\n")
    
    if await test_signboard_image_storage():
        print("\n🎉 테스트 완료!")
        return True
    else:
        print("\n❌ 테스트 실패")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)