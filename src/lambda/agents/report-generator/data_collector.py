"""
Data Collector Module
세션 데이터 및 이미지 수집
"""

import json
from typing import Dict, Any, List
from datetime import datetime
import logging


class DataCollector:
    """세션 데이터 수집 클래스"""
    
    def __init__(self, base_agent, logger=None):
        self.base_agent = base_agent
        self.logger = logger or logging.getLogger(__name__)
    
    def collect_comprehensive_session_data(self, session_id: str, s3_client, sanitizer) -> Dict[str, Any]:
        """종합 세션 데이터 수집 - 모든 선택 사항 통합"""
        try:
            # DynamoDB에서 세션 데이터 조회
            session_data = self.base_agent.get_session_data(session_id)
            
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            # 데이터 정제
            session_data = sanitizer.sanitize_session_data(session_data)
            
            # 이미지 데이터 수집
            signboard_images, interior_images = self._collect_images(session_id, s3_client)
            
            # 비즈니스 정보 추출
            business_info = session_data.get("businessInfo") or session_data.get("business_info", {})
            
            # 분석 결과 파싱
            analysis_result = self._parse_analysis_result(session_data)
            
            # 상호명 후보들 파싱
            business_names = self._parse_business_names(session_data)
            
            # 선택된 항목들
            selected_name = session_data.get("selected_name", "")
            selected_signboard = session_data.get("selected_signboard", "")
            selected_interior = session_data.get("selected_interior", "")
            
            self.logger.info(f"Selected items - name: {selected_name}, signboard: {selected_signboard}, interior: {selected_interior}")
            
            return {
                "session": session_data,
                "session_id": session_id,
                "business_info": business_info,
                "analysis_result": analysis_result,
                "business_names": business_names,
                "selected_name": selected_name,
                "selected_signboard": selected_signboard,
                "selected_interior": selected_interior,
                "signboard_images": signboard_images,
                "interior_images": interior_images,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect comprehensive session data: {str(e)}")
            return None

    def _collect_images(self, session_id: str, s3_client) -> tuple:
        """이미지 데이터 수집"""
        # 간판 이미지
        signboard_images = s3_client.list_objects(prefix=f"signboards/{session_id}/")
        
        # 인테리어 이미지 (세션 ID가 파일명에 포함)
        all_interior_images = s3_client.list_objects(prefix="interiors/")
        interior_images = [img for img in all_interior_images if session_id in img.get('key', '')]
        
        # presigned URL 추가
        signboard_images = self._add_presigned_urls(s3_client, signboard_images)
        interior_images = self._add_presigned_urls(s3_client, interior_images)
        
        return signboard_images, interior_images
    
    def _add_presigned_urls(self, s3_client, images: List[Dict]) -> List[Dict]:
        """이미지 리스트에 presigned URL 추가"""
        try:
            enhanced_images = []
            for img in images:
                enhanced_img = img.copy()
                s3_key = img.get('key', '')
                if s3_key:
                    try:
                        presigned_url = s3_client.generate_presigned_url(s3_key, expiration=600)
                        enhanced_img['presigned_url'] = presigned_url
                        if not enhanced_img.get('url'):
                            enhanced_img['url'] = presigned_url
                    except Exception as e:
                        self.logger.warning(f"Failed to generate presigned URL for {s3_key}: {str(e)}")
                enhanced_images.append(enhanced_img)
            return enhanced_images
        except Exception as e:
            self.logger.error(f"Error adding presigned URLs: {str(e)}")
            return images
    
    def _parse_analysis_result(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """분석 결과 파싱"""
        analysis_result = session_data.get("analysis_result", {})
        if isinstance(analysis_result, str):
            try:
                analysis_result = json.loads(analysis_result)
            except:
                analysis_result = {}
        return analysis_result
    
    def _parse_business_names(self, session_data: Dict[str, Any]) -> List[str]:
        """상호명 후보들 파싱"""
        business_names = session_data.get("business_names", [])
        if isinstance(business_names, str):
            try:
                business_names = json.loads(business_names)
            except:
                business_names = []
        return business_names
