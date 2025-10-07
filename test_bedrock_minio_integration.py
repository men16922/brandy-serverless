#!/usr/bin/env python3
"""
Bedrock + MinIO 통합 테스트
Local 환경에서 Bedrock SDXL로 이미지 생성 후 MinIO에 업로드 테스트
"""

import sys
import os
import base64
import uuid
from datetime import datetime

# 환경 변수 설정 (local 환경)
os.environ['ENVIRONMENT'] = 'local'
os.environ['S3_ENDPOINT'] = 'http://localhost:9000'
os.environ['S3_ACCESS_KEY'] = 'minioadmin'
os.environ['S3_SECRET_KEY'] = 'minioadmin'
os.environ['S3_BUCKET'] = 'ai-branding-chatbot-assets-local'

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'lambda'))

from shared.bedrock_client import create_bedrock_client
from shared.s3_client import S3Client


def test_bedrock_minio_integration():
    """Bedrock 이미지 생성 → MinIO 업로드 통합 테스트"""
    
    print("=" * 80)
    print("🧪 Bedrock + MinIO 통합 테스트")
    print("=" * 80)
    
    # 1. MinIO 연결 확인
    print("\n📦 Step 1: MinIO 연결 확인...")
    try:
        s3_client = S3Client(environment='local')
        print(f"   ✅ MinIO 클라이언트 생성 성공")
        print(f"   📍 Endpoint: {os.getenv('S3_ENDPOINT')}")
        print(f"   🪣 Bucket: {s3_client.bucket_name}")
        
        # 버킷 목록 확인
        buckets = s3_client.client.list_buckets()
        print(f"   📋 사용 가능한 버킷: {[b['Name'] for b in buckets['Buckets']]}")
    except Exception as e:
        print(f"   ❌ MinIO 연결 실패: {e}")
        print("\n💡 Docker Compose를 시작하세요:")
        print("   docker-compose -f docker-compose.local.yml up -d")
        return False
    
    # 2. Bedrock 클라이언트 초기화
    print("\n🎨 Step 2: Bedrock 클라이언트 초기화...")
    try:
        bedrock_client = create_bedrock_client(region='us-east-1')
        print(f"   ✅ Bedrock 클라이언트 생성 성공")
        print(f"   🤖 Claude Model: {bedrock_client.claude_model_id}")
        print(f"   🖼️  SDXL Model: {bedrock_client.sdxl_model_id}")
    except Exception as e:
        print(f"   ❌ Bedrock 클라이언트 초기화 실패: {e}")
        return False
    
    # 3. Bedrock SDXL로 이미지 생성
    print("\n🎨 Step 3: Bedrock SDXL 이미지 생성...")
    prompt = "A modern Korean restaurant signboard with elegant typography, warm lighting"
    print(f"   📝 Prompt: {prompt}")
    print(f"   ⏳ 생성 중... (20-30초 소요)")
    
    try:
        result = bedrock_client.invoke_sdxl(
            prompt=prompt,
            width=512,  # 테스트용 작은 크기
            height=512,
            steps=20,   # 테스트용 적은 스텝
            seed=42
        )
        
        print(f"   ✅ 이미지 생성 성공!")
        print(f"   ⏱️  Latency: {result['latency_ms']}ms")
        print(f"   🎲 Seed: {result['seed']}")
        print(f"   📊 Finish Reason: {result['finish_reason']}")
        
        image_base64 = result['image_base64']
        print(f"   📦 Image Size: {len(image_base64):,} characters (base64)")
        
    except Exception as e:
        print(f"   ❌ 이미지 생성 실패: {e}")
        return False
    
    # 4. Base64 이미지를 MinIO에 업로드
    print("\n📤 Step 4: MinIO에 이미지 업로드...")
    try:
        # Base64 디코딩
        image_data = base64.b64decode(image_base64)
        print(f"   📦 Decoded Size: {len(image_data):,} bytes")
        
        # S3 키 생성
        session_id = f"test-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        s3_key = f"signboards/{session_id}/bedrock_sdxl_{timestamp}_seed{result['seed']}.png"
        
        print(f"   🔑 S3 Key: {s3_key}")
        
        # MinIO에 업로드
        upload_result = s3_client.upload_file(
            file_content=image_data,
            key=s3_key,
            content_type='image/png',
            metadata={
                'session_id': session_id,
                'provider': 'bedrock-sdxl',
                'seed': str(result['seed']),
                'prompt': prompt,
                'test': 'true'
            }
        )
        
        if upload_result.get('success'):
            print(f"   ✅ 업로드 성공!")
            
            # URL 확인
            stored_url = upload_result.get('url') or upload_result.get('public_url')
            print(f"   🔗 URL: {stored_url}")
            
            # 5. MinIO에서 파일 확인
            print("\n🔍 Step 5: MinIO에서 파일 확인...")
            try:
                # 파일 메타데이터 조회
                head_result = s3_client.client.head_object(
                    Bucket=s3_client.bucket_name,
                    Key=s3_key
                )
                
                print(f"   ✅ 파일 존재 확인!")
                print(f"   📊 Content-Type: {head_result.get('ContentType')}")
                print(f"   📦 Content-Length: {head_result.get('ContentLength'):,} bytes")
                print(f"   📅 Last-Modified: {head_result.get('LastModified')}")
                
                # 메타데이터 출력
                if 'Metadata' in head_result:
                    print(f"   🏷️  Metadata:")
                    for key, value in head_result['Metadata'].items():
                        print(f"      - {key}: {value}")
                
                # 6. 다운로드 URL 생성
                print("\n🔗 Step 6: Presigned URL 생성...")
                presigned_url = s3_client.generate_presigned_url(
                    key=s3_key,
                    expiration=3600
                )
                print(f"   ✅ Presigned URL 생성 성공!")
                print(f"   🔗 URL (1시간 유효): {presigned_url}")
                
                # 7. 최종 결과
                print("\n" + "=" * 80)
                print("✅ 통합 테스트 성공!")
                print("=" * 80)
                print(f"\n📋 테스트 결과 요약:")
                print(f"   • Session ID: {session_id}")
                print(f"   • S3 Key: {s3_key}")
                print(f"   • Image Size: {len(image_data):,} bytes")
                print(f"   • Generation Time: {result['latency_ms']}ms")
                print(f"   • Storage: MinIO (local)")
                
                print(f"\n🌐 MinIO Console에서 확인:")
                print(f"   1. 브라우저에서 열기: http://localhost:9001")
                print(f"   2. 로그인: minioadmin / minioadmin")
                print(f"   3. 버킷: {s3_client.bucket_name}")
                print(f"   4. 경로: signboards/{session_id}/")
                
                print(f"\n🖼️  이미지 다운로드:")
                print(f"   curl '{presigned_url}' -o test_image.png")
                print(f"   open test_image.png")
                
                return True
                
            except Exception as e:
                print(f"   ❌ 파일 확인 실패: {e}")
                return False
        else:
            print(f"   ❌ 업로드 실패: {upload_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ 업로드 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    try:
        success = test_bedrock_minio_integration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  테스트 중단됨")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
