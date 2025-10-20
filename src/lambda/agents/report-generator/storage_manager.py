"""
Storage management for reports and images
Handles S3 uploads, presigned URLs, and file management
"""
from typing import Dict, Any, List
from datetime import datetime
import logging


class StorageManager:
    """Manages storage operations for reports and images"""
    
    def __init__(self, logger=None, s3_client=None):
        self.logger = logger or logging.getLogger(__name__)
        self.s3_client = s3_client or self._get_s3_client()
    
    def _get_s3_client(self):
        """Get S3 client with fallback import"""
        try:
            from shared.s3_client import get_s3_client
        except ImportError:
            from s3_client import get_s3_client
        return get_s3_client()
    
    def store_report(
        self,
        content: bytes or str,
        session_id: str,
        format_type: str,
        content_type: str,
        file_extension: str = None
    ) -> Dict[str, Any]:
        """
        Store report to S3 and return storage info
        
        Args:
            content: Report content (bytes or string)
            session_id: Session ID
            format_type: Report format (html, json, text, pdf)
            content_type: MIME type
            file_extension: File extension (optional, defaults to format_type)
        
        Returns:
            Dict with presigned_url, direct_url, file_name, file_size, s3_key, report_type
        """
        try:
            if not self.s3_client:
                raise ValueError("S3 client not available")
            
            # Generate file info
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            ext = file_extension or format_type
            file_name = f"branding_report_{timestamp}.{ext}"
            s3_key = f"reports/{session_id}/{file_name}"
            
            # Metadata
            metadata = {
                'session_id': session_id,
                'report_type': 'branding_report',
                'report_format': format_type,
                'generated_by': 'report-generator-agent',
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Encode content
            if isinstance(content, str):
                content_bytes = content.encode('utf-8')
            elif isinstance(content, bytes):
                content_bytes = content
            else:
                content_bytes = str(content).encode('utf-8')
            
            # Upload to S3
            upload_result = self.s3_client.upload_file(
                file_content=content_bytes,
                key=s3_key,
                content_type=content_type,
                metadata=metadata
            )
            
            if not upload_result.get('success'):
                raise ValueError(f"Failed to upload {format_type} report: {upload_result}")
            
            self.logger.info(f"Successfully stored {format_type} report: {s3_key} ({len(content_bytes)} bytes)")
            
            # Generate presigned URL (10 minutes expiry)
            presigned_url = self.s3_client.generate_presigned_url(s3_key, expiration=600)
            
            return {
                "presigned_url": presigned_url,
                "direct_url": upload_result.get('url'),
                "file_name": file_name,
                "file_size": len(content_bytes),
                "report_type": format_type,
                "s3_key": s3_key
            }
            
        except Exception as e:
            self.logger.error(f"Error storing report: {str(e)}")
            raise
    
    def add_presigned_urls_to_images(self, images: List[Dict]) -> List[Dict]:
        """
        Add presigned URLs to image list
        
        Args:
            images: List of image dicts with 'key' field
        
        Returns:
            List of image dicts with added 'presigned_url' and 'url' fields
        """
        try:
            if not self.s3_client:
                self.logger.warning("S3 client not available, returning images without presigned URLs")
                return images
            
            enhanced_images = []
            for img in images:
                enhanced_img = img.copy()
                
                # Generate presigned URL from S3 key
                s3_key = img.get('key', '')
                if s3_key:
                    try:
                        # 10 minutes validity
                        presigned_url = self.s3_client.generate_presigned_url(s3_key, expiration=600)
                        enhanced_img['presigned_url'] = presigned_url
                        
                        # Set as default URL if not present
                        if not enhanced_img.get('url'):
                            enhanced_img['url'] = presigned_url
                        
                        self.logger.debug(f"Generated presigned URL for image: {s3_key}")
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to generate presigned URL for {s3_key}: {str(e)}")
                        # Keep original image info even if presigned URL generation fails
                
                enhanced_images.append(enhanced_img)
            
            self.logger.info(f"Added presigned URLs to {len(enhanced_images)} images")
            return enhanced_images
            
        except Exception as e:
            self.logger.error(f"Error adding presigned URLs to images: {str(e)}")
            # Return original images on error
            return images
    
    def get_download_url(self, session_id: str) -> Dict[str, Any]:
        """
        Get presigned download URL for existing report
        
        Args:
            session_id: Session ID
        
        Returns:
            Dict with sessionId, downloadUrl, fileName, fileSize, expiresIn, success
        """
        try:
            if not self.s3_client:
                raise ValueError("S3 client not available")
            
            # Find latest report file
            report_objects = self.s3_client.list_objects(prefix=f"reports/{session_id}/")
            
            if not report_objects:
                raise ValueError(f"No report found for session {session_id}")
            
            # Select most recent file
            latest_report = max(report_objects, key=lambda x: x.get('last_modified', ''))
            
            # Generate presigned URL (10 minutes validity)
            download_url = self.s3_client.generate_presigned_url(
                key=latest_report['key'],
                expiration=600
            )
            
            result = {
                "sessionId": session_id,
                "downloadUrl": download_url,
                "fileName": latest_report['key'].split('/')[-1],
                "fileSize": latest_report.get('size', 0),
                "expiresIn": "10 minutes",
                "success": True
            }
            
            self.logger.info(f"Generated download URL for session {session_id}: {result['fileName']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get download URL: {str(e)}")
            raise
    
    def update_session_with_report_info(
        self,
        session_id: str,
        storage_info: Dict[str, Any],
        update_session_callback
    ) -> None:
        """
        Update session with report information
        
        Args:
            session_id: Session ID
            storage_info: Storage info dict from store_report()
            update_session_callback: Callback function to update session data
        """
        try:
            update_data = {
                "pdf_report_path": storage_info["s3_key"],
                "pdf_report_url": storage_info["presigned_url"],
                "pdf_file_name": storage_info["file_name"],
                "pdf_file_size": storage_info["file_size"],
                "report_generated_at": datetime.utcnow().isoformat(),
                "current_step": 5  # Report generation complete
            }
            
            update_session_callback(session_id, update_data)
            self.logger.info(f"Updated session {session_id} with report information")
            
        except Exception as e:
            self.logger.error(f"Failed to update session with report info: {str(e)}")
            # Session update failure is not critical, continue execution
