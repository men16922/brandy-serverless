"""
File upload handler with validation and S3 integration
"""

import base64
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import uuid

from .s3_utils import S3Manager, get_s3_manager
from .file_validator import FileValidator, validate_uploaded_file, generate_secure_filename

class UploadHandler:
    """Handle file uploads with validation and S3 storage"""
    
    def __init__(self, s3_manager: S3Manager = None):
        self.s3_manager = s3_manager or get_s3_manager()
        self.validator = FileValidator()
    
    def handle_upload(self, upload_data: Dict, session_id: str, 
                     file_type: str = "uploads") -> Dict:
        """
        Handle file upload from various sources
        
        Args:
            upload_data: Upload data (base64, multipart, etc.)
            session_id: Session ID for organization
            file_type: Type of upload (uploads, signs, interiors, reports)
            
        Returns:
            Dict with upload result and file info
        """
        try:
            # Parse upload data
            file_content, filename, content_type = self._parse_upload_data(upload_data)
            
            # Validate file
            validation_result = self.validator.validate_file(
                file_content, filename, content_type
            )
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': 'File validation failed',
                    'details': validation_result['errors'],
                    'warnings': validation_result.get('warnings', [])
                }
            
            # Generate secure filename
            secure_filename = generate_secure_filename(filename)
            
            # Upload to S3
            upload_result = self.s3_manager.upload_file(
                file_content=file_content,
                session_id=session_id,
                file_type=file_type,
                filename=secure_filename,
                content_type=validation_result['content_type']
            )
            
            # Generate download URL
            download_url = self.s3_manager.generate_presigned_url(
                upload_result['key'],
                expiration=3600  # 1 hour
            )
            
            return {
                'success': True,
                'file_info': {
                    **upload_result,
                    'original_filename': filename,
                    'download_url': download_url,
                    'validation': {
                        'warnings': validation_result.get('warnings', []),
                        'metadata': validation_result.get('metadata', {})
                    }
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Upload failed: {str(e)}'
            }
    
    def handle_batch_upload(self, uploads: List[Dict], session_id: str, 
                           file_type: str = "uploads") -> Dict:
        """Handle multiple file uploads"""
        results = []
        successful_uploads = 0
        
        for i, upload_data in enumerate(uploads):
            result = self.handle_upload(upload_data, session_id, file_type)
            result['index'] = i
            results.append(result)
            
            if result['success']:
                successful_uploads += 1
        
        return {
            'total_files': len(uploads),
            'successful_uploads': successful_uploads,
            'failed_uploads': len(uploads) - successful_uploads,
            'results': results
        }
    
    def _parse_upload_data(self, upload_data: Dict) -> tuple:
        """Parse upload data from various formats"""
        
        # Base64 encoded data
        if 'base64_data' in upload_data:
            return self._parse_base64_upload(upload_data)
        
        # Multipart form data
        elif 'multipart_data' in upload_data:
            return self._parse_multipart_upload(upload_data)
        
        # Direct binary data
        elif 'binary_data' in upload_data:
            return self._parse_binary_upload(upload_data)
        
        # URL upload (download from URL)
        elif 'url' in upload_data:
            return self._parse_url_upload(upload_data)
        
        else:
            raise ValueError("Unsupported upload data format")
    
    def _parse_base64_upload(self, upload_data: Dict) -> tuple:
        """Parse base64 encoded upload"""
        base64_data = upload_data['base64_data']
        filename = upload_data.get('filename', 'uploaded_file')
        content_type = upload_data.get('content_type')
        
        # Handle data URL format (data:image/jpeg;base64,...)
        if base64_data.startswith('data:'):
            header, data = base64_data.split(',', 1)
            if 'base64' in header:
                content_type = header.split(';')[0].split(':')[1]
                file_content = base64.b64decode(data)
            else:
                raise ValueError("Non-base64 data URLs not supported")
        else:
            file_content = base64.b64decode(base64_data)
        
        return file_content, filename, content_type
    
    def _parse_multipart_upload(self, upload_data: Dict) -> tuple:
        """Parse multipart form upload"""
        # This would typically be handled by the web framework
        # For Lambda, we'd get the parsed data
        multipart_data = upload_data['multipart_data']
        
        filename = multipart_data.get('filename', 'uploaded_file')
        content_type = multipart_data.get('content_type')
        file_content = multipart_data['content']
        
        if isinstance(file_content, str):
            file_content = file_content.encode('utf-8')
        
        return file_content, filename, content_type
    
    def _parse_binary_upload(self, upload_data: Dict) -> tuple:
        """Parse direct binary upload"""
        binary_data = upload_data['binary_data']
        filename = upload_data.get('filename', 'uploaded_file')
        content_type = upload_data.get('content_type')
        
        if isinstance(binary_data, str):
            binary_data = binary_data.encode('utf-8')
        
        return binary_data, filename, content_type
    
    def _parse_url_upload(self, upload_data: Dict) -> tuple:
        """Parse URL upload (download from URL)"""
        import requests
        
        url = upload_data['url']
        filename = upload_data.get('filename')
        
        # Download file from URL
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        file_content = response.content
        content_type = response.headers.get('content-type')
        
        # Extract filename from URL if not provided
        if not filename:
            filename = url.split('/')[-1] or 'downloaded_file'
        
        return file_content, filename, content_type


class DownloadHandler:
    """Handle file downloads with security and access control"""
    
    def __init__(self, s3_manager: S3Manager = None):
        self.s3_manager = s3_manager or get_s3_manager()
    
    def generate_download_url(self, session_id: str, file_key: str, 
                             expiration: int = 3600, 
                             access_type: str = "download") -> Dict:
        """
        Generate secure download URL
        
        Args:
            session_id: Session ID for access control
            file_key: S3 object key
            expiration: URL expiration in seconds
            access_type: Type of access (download, view, report)
            
        Returns:
            Dict with download URL and metadata
        """
        try:
            # Validate session access to file
            if not self._validate_session_access(session_id, file_key):
                return {
                    'success': False,
                    'error': 'Access denied to file'
                }
            
            # Adjust expiration based on access type
            if access_type == "report":
                expiration = min(expiration, 600)  # Max 10 minutes for reports
            elif access_type == "view":
                expiration = min(expiration, 1800)  # Max 30 minutes for viewing
            
            # Generate presigned URL
            download_url = self.s3_manager.generate_presigned_url(
                file_key, expiration=expiration
            )
            
            # Get file metadata
            try:
                _, metadata = self.s3_manager.get_file(file_key)
            except FileNotFoundError:
                return {
                    'success': False,
                    'error': 'File not found'
                }
            
            return {
                'success': True,
                'download_url': download_url,
                'expires_at': (datetime.utcnow() + timedelta(seconds=expiration)).isoformat(),
                'file_metadata': metadata,
                'access_type': access_type
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to generate download URL: {str(e)}'
            }
    
    def get_file_info(self, session_id: str, file_key: str) -> Dict:
        """Get file information without downloading"""
        try:
            # Validate session access
            if not self._validate_session_access(session_id, file_key):
                return {
                    'success': False,
                    'error': 'Access denied to file'
                }
            
            # Get file metadata
            try:
                _, metadata = self.s3_manager.get_file(file_key)
            except FileNotFoundError:
                return {
                    'success': False,
                    'error': 'File not found'
                }
            
            # Get additional S3 object info
            files = self.s3_manager.list_session_files(session_id)
            file_info = next((f for f in files if f['key'] == file_key), None)
            
            return {
                'success': True,
                'file_info': {
                    'key': file_key,
                    'metadata': metadata,
                    's3_info': file_info
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get file info: {str(e)}'
            }
    
    def list_session_downloads(self, session_id: str, file_type: str = None) -> Dict:
        """List available downloads for a session"""
        try:
            files = self.s3_manager.list_session_files(session_id, file_type)
            
            download_list = []
            for file_info in files:
                # Generate temporary view URL
                view_url_result = self.generate_download_url(
                    session_id, file_info['key'], 
                    expiration=1800, access_type="view"
                )
                
                download_info = {
                    'key': file_info['key'],
                    'filename': file_info['filename'],
                    'size': file_info['size'],
                    'last_modified': file_info['last_modified'],
                    'file_type': file_info['key'].split('/')[-2],  # Extract from path
                    'view_url': view_url_result.get('download_url') if view_url_result['success'] else None
                }
                
                download_list.append(download_info)
            
            return {
                'success': True,
                'session_id': session_id,
                'file_type': file_type,
                'files': download_list,
                'total_files': len(download_list)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to list downloads: {str(e)}'
            }
    
    def _validate_session_access(self, session_id: str, file_key: str) -> bool:
        """Validate that session has access to the file"""
        # Check if file belongs to the session
        expected_prefix = f"sessions/{session_id}/"
        return file_key.startswith(expected_prefix)


# Convenience functions for Lambda handlers
def handle_file_upload(event: Dict, session_id: str, file_type: str = "uploads") -> Dict:
    """Convenience function for Lambda file upload handling"""
    upload_handler = UploadHandler()
    
    # Parse upload data from Lambda event
    if event.get('isBase64Encoded'):
        upload_data = {
            'base64_data': event['body'],
            'filename': event.get('headers', {}).get('x-filename', 'uploaded_file'),
            'content_type': event.get('headers', {}).get('content-type')
        }
    else:
        # Parse JSON body
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        upload_data = body
    
    return upload_handler.handle_upload(upload_data, session_id, file_type)

def generate_file_download_url(session_id: str, file_key: str, 
                              access_type: str = "download") -> Dict:
    """Convenience function for generating download URLs"""
    download_handler = DownloadHandler()
    return download_handler.generate_download_url(session_id, file_key, access_type=access_type)

def list_session_files_for_download(session_id: str, file_type: str = None) -> Dict:
    """Convenience function for listing session files"""
    download_handler = DownloadHandler()
    return download_handler.list_session_downloads(session_id, file_type)