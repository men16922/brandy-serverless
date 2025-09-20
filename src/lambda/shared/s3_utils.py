"""
S3 utilities for file upload/download and bucket management
"""

import boto3
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from botocore.exceptions import ClientError
import mimetypes
import hashlib

class S3Manager:
    """S3 bucket management and file operations"""
    
    def __init__(self, bucket_name: str = None, region: str = None):
        self.bucket_name = bucket_name or os.getenv('STORAGE_BUCKET_NAME')
        self.region = region or os.getenv('AWS_REGION', 'us-east-1')
        self.s3_client = boto3.client('s3', region_name=self.region)
        
        if not self.bucket_name:
            raise ValueError("S3 bucket name must be provided")
    
    def create_session_directory_structure(self, session_id: str) -> Dict[str, str]:
        """
        Create directory structure for a session
        Returns dict with directory paths
        """
        base_path = f"sessions/{session_id}"
        directories = {
            'base': base_path,
            'uploads': f"{base_path}/uploads",
            'signs': f"{base_path}/signs", 
            'interiors': f"{base_path}/interiors",
            'reports': f"{base_path}/reports"
        }
        
        # Create placeholder files to ensure directories exist
        for dir_name, dir_path in directories.items():
            if dir_name != 'base':
                placeholder_key = f"{dir_path}/.placeholder"
                try:
                    self.s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=placeholder_key,
                        Body=b'',
                        ContentType='text/plain'
                    )
                except ClientError as e:
                    print(f"Warning: Could not create placeholder for {dir_path}: {e}")
        
        return directories
    
    def upload_file(self, file_content: bytes, session_id: str, 
                   file_type: str, filename: str = None, 
                   content_type: str = None) -> Dict[str, str]:
        """
        Upload file to appropriate session directory
        
        Args:
            file_content: File content as bytes
            session_id: Session ID for directory structure
            file_type: Type of file (uploads, signs, interiors, reports)
            filename: Optional filename, will generate UUID if not provided
            content_type: MIME type, will detect if not provided
            
        Returns:
            Dict with file info including S3 key and URL
        """
        if not filename:
            file_ext = self._detect_file_extension(content_type or 'application/octet-stream')
            filename = f"{uuid.uuid4()}{file_ext}"
        
        # Validate file type
        valid_types = ['uploads', 'signs', 'interiors', 'reports']
        if file_type not in valid_types:
            raise ValueError(f"Invalid file_type. Must be one of: {valid_types}")
        
        # Generate S3 key
        s3_key = f"sessions/{session_id}/{file_type}/{filename}"
        
        # Detect content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or 'application/octet-stream'
        
        # Validate file content
        self._validate_file_content(file_content, content_type)
        
        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'session-id': session_id,
                    'file-type': file_type,
                    'uploaded-at': datetime.utcnow().isoformat(),
                    'content-hash': hashlib.md5(file_content).hexdigest()
                }
            )
            
            return {
                'key': s3_key,
                'filename': filename,
                'content_type': content_type,
                'size': len(file_content),
                'url': f"s3://{self.bucket_name}/{s3_key}",
                'uploaded_at': datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            raise Exception(f"Failed to upload file: {e}")
    
    def generate_presigned_url(self, s3_key: str, expiration: int = 3600, 
                              method: str = 'get_object') -> str:
        """
        Generate presigned URL for file access
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default 1 hour)
            method: S3 operation (get_object, put_object)
            
        Returns:
            Presigned URL string
        """
        try:
            url = self.s3_client.generate_presigned_url(
                method,
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {e}")
    
    def get_file(self, s3_key: str) -> Tuple[bytes, Dict[str, str]]:
        """
        Download file from S3
        
        Returns:
            Tuple of (file_content, metadata)
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            content = response['Body'].read()
            metadata = response.get('Metadata', {})
            
            return content, metadata
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File not found: {s3_key}")
            raise Exception(f"Failed to get file: {e}")
    
    def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            print(f"Warning: Could not delete file {s3_key}: {e}")
            return False
    
    def list_session_files(self, session_id: str, file_type: str = None) -> List[Dict[str, str]]:
        """
        List files in session directory
        
        Args:
            session_id: Session ID
            file_type: Optional filter by file type
            
        Returns:
            List of file info dicts
        """
        prefix = f"sessions/{session_id}/"
        if file_type:
            prefix += f"{file_type}/"
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                # Skip placeholder files
                if obj['Key'].endswith('/.placeholder'):
                    continue
                    
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'filename': obj['Key'].split('/')[-1]
                })
            
            return files
        except ClientError as e:
            raise Exception(f"Failed to list files: {e}")
    
    def cleanup_session(self, session_id: str) -> bool:
        """Delete all files for a session"""
        try:
            # List all objects with session prefix
            prefix = f"sessions/{session_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            # Delete all objects
            objects_to_delete = []
            for obj in response.get('Contents', []):
                objects_to_delete.append({'Key': obj['Key']})
            
            if objects_to_delete:
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects_to_delete}
                )
            
            return True
        except ClientError as e:
            print(f"Warning: Could not cleanup session {session_id}: {e}")
            return False
    
    def _detect_file_extension(self, content_type: str) -> str:
        """Detect file extension from content type"""
        extension_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'application/pdf': '.pdf',
            'application/json': '.json',
            'text/plain': '.txt'
        }
        return extension_map.get(content_type, '.bin')
    
    def _validate_file_content(self, content: bytes, content_type: str):
        """Validate file content and security"""
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(content) > max_size:
            raise ValueError(f"File too large: {len(content)} bytes (max {max_size})")
        
        # Basic content validation for images
        if content_type.startswith('image/'):
            # Check for basic image file signatures
            image_signatures = {
                b'\xFF\xD8\xFF': 'image/jpeg',
                b'\x89PNG\r\n\x1a\n': 'image/png',
                b'GIF87a': 'image/gif',
                b'GIF89a': 'image/gif',
                b'RIFF': 'image/webp'  # Simplified check
            }
            
            is_valid_image = False
            for signature in image_signatures:
                if content.startswith(signature):
                    is_valid_image = True
                    break
            
            if not is_valid_image:
                raise ValueError("Invalid image file format")


class FallbackImageManager:
    """Manager for fallback images when AI generation fails"""
    
    def __init__(self, s3_manager: S3Manager):
        self.s3_manager = s3_manager
        self.fallback_data_path = "data/fallbacks"
    
    def setup_fallback_images(self):
        """Upload fallback images and data to S3"""
        fallback_types = ['signs', 'interiors']
        
        for fallback_type in fallback_types:
            # Read fallback data
            data_file = f"{self.fallback_data_path}/{fallback_type}/default-{fallback_type[:-1]}.json"
            
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    fallback_data = json.load(f)
                
                # Upload fallback data to S3
                s3_key = f"fallbacks/{fallback_type}/default.json"
                self.s3_manager.s3_client.put_object(
                    Bucket=self.s3_manager.bucket_name,
                    Key=s3_key,
                    Body=json.dumps(fallback_data, ensure_ascii=False, indent=2),
                    ContentType='application/json'
                )
                
                print(f"Uploaded fallback data: {s3_key}")
                
            except FileNotFoundError:
                print(f"Warning: Fallback data file not found: {data_file}")
            except Exception as e:
                print(f"Error uploading fallback data for {fallback_type}: {e}")
    
    def get_fallback_image_info(self, image_type: str) -> Dict:
        """
        Get fallback image information
        
        Args:
            image_type: 'signs' or 'interiors'
            
        Returns:
            Fallback image data dict
        """
        if image_type not in ['signs', 'interiors']:
            raise ValueError("image_type must be 'signs' or 'interiors'")
        
        s3_key = f"fallbacks/{image_type}/default.json"
        
        try:
            content, _ = self.s3_manager.get_file(s3_key)
            return json.loads(content.decode('utf-8'))
        except FileNotFoundError:
            # Return basic fallback if S3 file not found
            return {
                "name": f"기본 {image_type[:-1]} 이미지",
                "description": f"AI 모델 실패시 사용되는 기본 {image_type[:-1]} 디자인",
                "image_url": f"https://via.placeholder.com/512x256/4A90E2/FFFFFF?text={image_type[:-1]}+디자인",
                "style": "modern",
                "colors": ["#4A90E2", "#FFFFFF"],
                "metadata": {
                    "type": "fallback",
                    "category": image_type[:-1]
                }
            }


# Environment-specific configuration
def get_s3_manager() -> S3Manager:
    """Get S3Manager instance based on environment"""
    environment = os.getenv('ENVIRONMENT', 'local')
    
    if environment == 'local':
        # For local development, use MinIO or localstack
        endpoint_url = os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000')
        bucket_name = os.getenv('STORAGE_BUCKET_NAME', 'branding-chatbot-local')
        
        # Create custom S3 client for local development
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'minioadmin'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'minioadmin'),
            region_name='us-east-1'
        )
        
        manager = S3Manager(bucket_name=bucket_name)
        manager.s3_client = s3_client
        return manager
    else:
        # Use AWS S3 for dev/prod
        return S3Manager()


def create_local_bucket_if_not_exists(bucket_name: str):
    """Create local S3 bucket if it doesn't exist (for MinIO/localstack)"""
    try:
        s3_manager = get_s3_manager()
        s3_manager.s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket {bucket_name} already exists")
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            try:
                s3_manager.s3_client.create_bucket(Bucket=bucket_name)
                print(f"Created bucket: {bucket_name}")
            except ClientError as create_error:
                print(f"Failed to create bucket {bucket_name}: {create_error}")
        else:
            print(f"Error checking bucket {bucket_name}: {e}")