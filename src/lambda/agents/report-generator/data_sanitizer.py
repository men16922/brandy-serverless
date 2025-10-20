"""
Data Sanitizer Module
DynamoDB 데이터 정제 및 변환
"""

import json
from decimal import Decimal
from typing import Dict, Any
import logging


class DataSanitizer:
    """DynamoDB 데이터 정제 클래스"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
    
    def sanitize_session_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """세션 데이터 정제 - DynamoDB 형식 및 Decimal 타입 제거"""
        try:
            sanitized = self._convert_value(data)
            
            # 추가 검증: business_names가 리스트인지 확인
            if 'business_names' in sanitized:
                sanitized['business_names'] = self._ensure_list(sanitized['business_names'])
            
            self.logger.info("Successfully sanitized session data")
            return sanitized
            
        except Exception as e:
            self.logger.error(f"Failed to sanitize session data: {str(e)}")
            import traceback
            self.logger.error(f"Sanitization traceback: {traceback.format_exc()}")
            # 실패 시 원본 반환
            return data
    
    def _convert_value(self, obj):
        """재귀적으로 값 변환"""
        if isinstance(obj, Decimal):
            # Decimal을 float로 변환
            return float(obj)
        elif isinstance(obj, dict):
            # DynamoDB 형식 확인 ({'S': 'value'}, {'N': '123'} 등)
            if len(obj) == 1:
                key = list(obj.keys())[0]
                if key in ['S', 'N', 'BOOL', 'NULL', 'M', 'L', 'SS', 'NS', 'BS']:
                    # DynamoDB 형식인 경우 값만 추출
                    value = obj[key]
                    if key == 'N':
                        return float(value) if '.' in str(value) else int(value)
                    elif key == 'BOOL':
                        return value
                    elif key == 'NULL':
                        return None
                    elif key == 'M':
                        return self._convert_value(value)
                    elif key == 'L':
                        # List 형식 변환
                        if isinstance(value, list):
                            return [self._convert_value(item) for item in value]
                        else:
                            return []
                    elif key == 'S':
                        # String 형식 - JSON 파싱 시도
                        try:
                            parsed = json.loads(value)
                            return self._convert_value(parsed)
                        except:
                            return value
                    else:
                        return value
            
            # 일반 딕셔너리 처리
            return {k: self._convert_value(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_value(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            # 기타 타입은 문자열로 변환
            return str(obj)
    
    def _ensure_list(self, value):
        """값이 리스트인지 확인하고 변환"""
        if isinstance(value, list):
            return value
        elif isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except:
                pass
        return []
