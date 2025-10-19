"""
File validation utilities for secure file handling
"""

import hashlib
import mimetypes
import os
from typing import Dict, List, Optional, Tuple
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available, image validation will be limited")

import io

class FileValidator:
    """Comprehensive file validation for security and integrity"""
    
    # File type signatures (magic numbers)
    FILE_SIGNATURES = {
        'image/jpeg': [
            b'\xFF\xD8\xFF\xE0',
            b'\xFF\xD8\xFF\xE1',
            b'\xFF\xD8\xFF\xE2',
            b'\xFF\xD8\xFF\xE3',
            b'\xFF\xD8\xFF\xE8',
            b'\xFF\xD8\xFF\xDB'
        ],
        'image/png': [b'\x89PNG\r\n\x1a\n'],
        'image/gif': [b'GIF87a', b'GIF89a'],
        'image/webp': [b'RIFF'],
        'application/pdf': [b'%PDF-'],
        'text/plain': [],  # Text files don't have reliable signatures
        'application/json': []  # JSON files don't have reliable signatures
    }
    
    # Maximum file sizes by type (in bytes)
    MAX_FILE_SIZES = {
        'image/jpeg': 10 * 1024 * 1024,  # 10MB
        'image/png': 10 * 1024 * 1024,   # 10MB
        'image/gif': 5 * 1024 * 1024,    # 5MB
        'image/webp': 10 * 1024 * 1024,  # 10MB
        'application/pdf': 50 * 1024 * 1024,  # 50MB
        'text/plain': 1 * 1024 * 1024,   # 1MB
        'application/json': 1 * 1024 * 1024  # 1MB
    }
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/png': ['.png'],
        'image/gif': ['.gif'],
        'image/webp': ['.webp'],
        'application/pdf': ['.pdf'],
        'text/plain': ['.txt'],
        'application/json': ['.json']
    }
    
    def __init__(self):
        self.magic_mime = None
        try:
            # Try to initialize python-magic for better MIME detection
            import magic
            self.magic_mime = magic.Magic(mime=True)
        except ImportError:
            # Fallback to basic validation if python-magic is not available
            print("Warning: python-magic not available, using basic file validation")
            pass
        except Exception:
            # Fallback to basic validation if python-magic initialization fails
            pass
    
    def validate_file(self, file_content: bytes, filename: str = None, 
                     expected_content_type: str = None) -> Dict[str, any]:
        """
        Comprehensive file validation
        
        Args:
            file_content: File content as bytes
            filename: Original filename (optional)
            expected_content_type: Expected MIME type (optional)
            
        Returns:
            Dict with validation results and file info
        """
        result = {
            'valid': False,
            'content_type': None,
            'size': len(file_content),
            'filename': filename,
            'errors': [],
            'warnings': [],
            'metadata': {}
        }
        
        try:
            # Basic size check
            if len(file_content) == 0:
                result['errors'].append("File is empty")
                return result
            
            # Detect content type
            detected_type = self._detect_content_type(file_content, filename)
            result['content_type'] = detected_type
            
            # Validate against expected type
            if expected_content_type and detected_type != expected_content_type:
                result['errors'].append(
                    f"Content type mismatch: expected {expected_content_type}, "
                    f"detected {detected_type}"
                )
            
            # Check if content type is allowed
            if detected_type not in self.MAX_FILE_SIZES:
                result['errors'].append(f"File type not allowed: {detected_type}")
                return result
            
            # Size validation
            max_size = self.MAX_FILE_SIZES[detected_type]
            if len(file_content) > max_size:
                result['errors'].append(
                    f"File too large: {len(file_content)} bytes "
                    f"(max {max_size} bytes)"
                )
            
            # File signature validation
            if not self._validate_file_signature(file_content, detected_type):
                result['errors'].append("Invalid file signature")
            
            # Content-specific validation
            content_validation = self._validate_content_specific(file_content, detected_type)
            result['errors'].extend(content_validation.get('errors', []))
            result['warnings'].extend(content_validation.get('warnings', []))
            result['metadata'].update(content_validation.get('metadata', {}))
            
            # Security checks
            security_check = self._security_scan(file_content, detected_type)
            result['errors'].extend(security_check.get('errors', []))
            result['warnings'].extend(security_check.get('warnings', []))
            
            # Final validation
            result['valid'] = len(result['errors']) == 0
            
        except Exception as e:
            result['errors'].append(f"Validation error: {str(e)}")
        
        return result
    
    def _detect_content_type(self, file_content: bytes, filename: str = None) -> str:
        """Detect file content type using multiple methods"""
        
        # Try python-magic first (most reliable)
        if self.magic_mime:
            try:
                detected_type = self.magic_mime.from_buffer(file_content)
                if detected_type and detected_type != 'application/octet-stream':
                    return detected_type
            except Exception:
                pass
        
        # Try file signature detection
        for content_type, signatures in self.FILE_SIGNATURES.items():
            for signature in signatures:
                if file_content.startswith(signature):
                    return content_type
        
        # Try filename extension
        if filename:
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type:
                return mime_type
        
        # Default fallback
        return 'application/octet-stream'
    
    def _validate_file_signature(self, file_content: bytes, content_type: str) -> bool:
        """Validate file signature matches content type"""
        signatures = self.FILE_SIGNATURES.get(content_type, [])
        
        # If no signatures defined, assume valid (for text files)
        if not signatures:
            return True
        
        # Check if content starts with any valid signature
        for signature in signatures:
            if file_content.startswith(signature):
                return True
        
        return False
    
    def _validate_content_specific(self, file_content: bytes, content_type: str) -> Dict:
        """Content-specific validation"""
        result = {'errors': [], 'warnings': [], 'metadata': {}}
        
        if content_type.startswith('image/'):
            return self._validate_image_content(file_content)
        elif content_type == 'application/pdf':
            return self._validate_pdf_content(file_content)
        elif content_type == 'application/json':
            return self._validate_json_content(file_content)
        
        return result
    
    def _validate_image_content(self, file_content: bytes) -> Dict:
        """Validate image content using PIL if available"""
        result = {'errors': [], 'warnings': [], 'metadata': {}}
        
        if not PIL_AVAILABLE:
            result['warnings'].append("PIL not available, skipping detailed image validation")
            return result
        
        try:
            with Image.open(io.BytesIO(file_content)) as img:
                result['metadata'] = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode
                }
                
                # Check image dimensions
                if img.width > 4096 or img.height > 4096:
                    result['warnings'].append(
                        f"Large image dimensions: {img.width}x{img.height}"
                    )
                
                if img.width < 100 or img.height < 100:
                    result['warnings'].append(
                        f"Small image dimensions: {img.width}x{img.height}"
                    )
                
                # Check for suspicious metadata
                if hasattr(img, '_getexif') and img._getexif():
                    result['warnings'].append("Image contains EXIF data")
                
        except Exception as e:
            result['errors'].append(f"Invalid image file: {str(e)}")
        
        return result
    
    def _validate_pdf_content(self, file_content: bytes) -> Dict:
        """Basic PDF validation"""
        result = {'errors': [], 'warnings': [], 'metadata': {}}
        
        try:
            # Basic PDF structure check
            if not file_content.startswith(b'%PDF-'):
                result['errors'].append("Invalid PDF header")
            
            if b'%%EOF' not in file_content[-1024:]:
                result['warnings'].append("PDF may be truncated (no EOF marker)")
            
            # Check for suspicious content
            suspicious_keywords = [b'/JavaScript', b'/JS', b'/Launch', b'/EmbeddedFile']
            for keyword in suspicious_keywords:
                if keyword in file_content:
                    result['warnings'].append(f"PDF contains potentially unsafe content: {keyword.decode()}")
            
        except Exception as e:
            result['errors'].append(f"PDF validation error: {str(e)}")
        
        return result
    
    def _validate_json_content(self, file_content: bytes) -> Dict:
        """Validate JSON content"""
        result = {'errors': [], 'warnings': [], 'metadata': {}}
        
        try:
            import json
            data = json.loads(file_content.decode('utf-8'))
            result['metadata']['json_keys'] = list(data.keys()) if isinstance(data, dict) else []
            result['metadata']['json_type'] = type(data).__name__
            
        except json.JSONDecodeError as e:
            result['errors'].append(f"Invalid JSON: {str(e)}")
        except UnicodeDecodeError as e:
            result['errors'].append(f"Invalid UTF-8 encoding: {str(e)}")
        
        return result
    
    def _security_scan(self, file_content: bytes, content_type: str) -> Dict:
        """Basic security scanning"""
        result = {'errors': [], 'warnings': []}
        
        # Check for embedded scripts or suspicious content
        suspicious_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'onload=',
            b'onerror=',
            b'eval(',
            b'document.cookie',
            b'window.location'
        ]
        
        content_lower = file_content.lower()
        for pattern in suspicious_patterns:
            if pattern in content_lower:
                result['warnings'].append(f"Potentially suspicious content detected: {pattern.decode()}")
        
        # Check for null bytes (potential for bypassing filters)
        if b'\x00' in file_content:
            result['warnings'].append("File contains null bytes")
        
        return result
    
    def generate_file_hash(self, file_content: bytes, algorithm: str = 'md5') -> str:
        """Generate file hash for integrity checking"""
        if algorithm == 'md5':
            return hashlib.md5(file_content).hexdigest()
        elif algorithm == 'sha256':
            return hashlib.sha256(file_content).hexdigest()
        elif algorithm == 'sha1':
            return hashlib.sha1(file_content).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        if not filename:
            return "unnamed_file"
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Replace dangerous characters
        dangerous_chars = '<>:"/\\|?*'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Remove control characters
        filename = ''.join(char for char in filename if ord(char) >= 32)
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        # Ensure it's not empty
        if not filename or filename == '.':
            filename = "unnamed_file"
        
        return filename


# Convenience functions
def validate_uploaded_file(file_content: bytes, filename: str = None, 
                          expected_type: str = None) -> Dict:
    """Convenience function for file validation"""
    validator = FileValidator()
    return validator.validate_file(file_content, filename, expected_type)

def is_safe_image(file_content: bytes) -> bool:
    """Quick check if image file is safe"""
    validator = FileValidator()
    result = validator.validate_file(file_content)
    return result['valid'] and result['content_type'].startswith('image/')

def generate_secure_filename(original_filename: str = None) -> str:
    """Generate secure filename with UUID"""
    import uuid
    
    validator = FileValidator()
    
    if original_filename:
        sanitized = validator.sanitize_filename(original_filename)
        name, ext = os.path.splitext(sanitized)
        return f"{uuid.uuid4()}_{name}{ext}"
    else:
        return str(uuid.uuid4())