"""
S3/MinIO 클라이언트 - 환경에 따라 AWS S3 또는 로컬 MinIO 사용
"""

import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class S3Client:
    """환경별 S3/MinIO 클라이언트"""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv('ENVIRONMENT', 'local')
        self.bucket_name = self._get_bucket_name()
        self.client = self._create_client()
        
        # 버킷 생성 확인
        self._ensure_bucket_exists()
    
    def _get_bucket_name(self) -> str:
        """환경별 버킷 이름 반환"""
        bucket_name = os.getenv('S3_BUCKET')
        if bucket_name:
            return bucket_name
        
        # 기본 버킷 이름
        return f"ai-branding-chatbot-assets-{self.environment}"
    
    def _create_client(self):
        """환경에 따른 S3 클라이언트 생성"""
        if self.environment == 'local':
            # MinIO 설정
            endpoint_url = os.getenv('S3_ENDPOINT', 'http://localhost:9000')
            access_key = os.getenv('S3_ACCESS_KEY', 'minioadmin')
            secret_key = os.getenv('S3_SECRET_KEY', 'minioadmin')
            region = os.getenv('S3_REGION', 'us-east-1')
            use_ssl = os.getenv('S3_USE_SSL', 'false').lower() == 'true'
            
            return boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
                config=Config(
                    signature_version='s3v4',
                    s3={
                        'addressing_style': 'path'
                    }
                ),
                use_ssl=use_ssl
            )
        else:
            # AWS S3 설정
            region = os.getenv('AWS_REGION', 'us-east-1')
            
            # AWS 자격증명이 환경변수에 있는 경우
            aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            
            if aws_access_key and aws_secret_key:
                return boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=region
                )
            else:
                # IAM Role 사용
                return boto3.client('s3', region_name=region)
    
    def _ensure_bucket_exists(self) -> None:
        """버킷이 존재하지 않으면 생성"""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # 버킷이 없으면 생성
                try:
                    if self.environment == 'local':
                        # MinIO는 간단하게 생성
                        self.client.create_bucket(Bucket=self.bucket_name)
                    else:
                        # AWS S3는 리전 고려
                        region = os.getenv('AWS_REGION', 'us-east-1')
                        if region == 'us-east-1':
                            self.client.create_bucket(Bucket=self.bucket_name)
                        else:
                            self.client.create_bucket(
                                Bucket=self.bucket_name,
                                CreateBucketConfiguration={'LocationConstraint': region}
                            )
                    
                    logger.info(f"Created bucket {self.bucket_name}")
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket {self.bucket_name}: {create_error}")
                    raise
            else:
                logger.error(f"Error checking bucket {self.bucket_name}: {e}")
                raise
    
    def upload_file(self, file_content: bytes, key: str, content_type: str = 'application/octet-stream',
                   metadata: Dict[str, str] = None) -> Dict[str, Any]:
        """
        파일을 S3/MinIO에 업로드
        
        Args:
            file_content: 파일 내용 (bytes)
            key: S3 객체 키
            content_type: MIME 타입
            metadata: 추가 메타데이터
            
        Returns:
            업로드 결과 정보
        """
        try:
            # 메타데이터 준비 (ASCII만 허용)
            upload_metadata = {}
            if metadata:
                for meta_key, meta_value in metadata.items():
                    # 한글 등 non-ASCII 문자를 base64로 인코딩
                    try:
                        str(meta_value).encode('ascii')
                        upload_metadata[meta_key] = str(meta_value)
                    except UnicodeEncodeError:
                        import base64
                        encoded_value = base64.b64encode(str(meta_value).encode('utf-8')).decode('ascii')
                        upload_metadata[f"{meta_key}_encoded"] = encoded_value
            
            upload_metadata.update({
                'uploaded_at': datetime.now(timezone.utc).isoformat(),
                'environment': self.environment,
                'content_length': str(len(file_content))
            })
            
            # 업로드
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                ContentType=content_type,
                Metadata=upload_metadata
            )
            
            # URL 생성
            url = self.get_object_url(key)
            
            logger.info(f"Successfully uploaded {key} to {self.bucket_name}")
            
            return {
                'success': True,
                'bucket': self.bucket_name,
                'key': key,
                'url': url,
                'content_type': content_type,
                'size': len(file_content),
                'metadata': upload_metadata
            }
            
        except ClientError as e:
            logger.error(f"Failed to upload {key} to {self.bucket_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'bucket': self.bucket_name,
                'key': key
            }
    
    def get_object_url(self, key: str, expires_in: int = 3600) -> str:
        """
        객체의 접근 가능한 URL 생성
        
        Args:
            key: S3 객체 키
            expires_in: URL 만료 시간 (초, 기본 1시간)
            
        Returns:
            객체 URL
        """
        try:
            if self.environment == 'local':
                # MinIO는 presigned URL 생성
                url = self.client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=expires_in
                )
                return url
            else:
                # AWS S3는 CloudFront나 직접 URL 사용 가능
                # 여기서는 presigned URL 사용
                url = self.client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=expires_in
                )
                return url
                
        except ClientError as e:
            logger.error(f"Failed to generate URL for {key}: {e}")
            # 폴백: 직접 URL 구성
            if self.environment == 'local':
                endpoint = os.getenv('S3_ENDPOINT', 'http://localhost:9000')
                return f"{endpoint}/{self.bucket_name}/{key}"
            else:
                region = os.getenv('AWS_REGION', 'us-east-1')
                return f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{key}"
    
    def delete_object(self, key: str) -> bool:
        """
        객체 삭제
        
        Args:
            key: S3 객체 키
            
        Returns:
            삭제 성공 여부
        """
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Successfully deleted {key} from {self.bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete {key} from {self.bucket_name}: {e}")
            return False
    
    def list_objects(self, prefix: str = '', max_keys: int = 1000) -> list:
        """
        객체 목록 조회
        
        Args:
            prefix: 키 접두사
            max_keys: 최대 반환 개수
            
        Returns:
            객체 목록
        """
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag']
                })
            
            return objects
            
        except ClientError as e:
            logger.error(f"Failed to list objects in {self.bucket_name}: {e}")
            return []


# 싱글톤 인스턴스
_s3_client_instance = None

def get_s3_client(environment: str = None) -> S3Client:
    """S3Client 싱글톤 인스턴스 반환"""
    global _s3_client_instance
    if _s3_client_instance is None:
        _s3_client_instance = S3Client(environment)
    return _s3_client_instance