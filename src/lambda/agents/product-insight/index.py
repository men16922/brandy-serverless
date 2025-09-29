"""
Product Insight Agent - Simple version for testing
"""

import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Product Insight Agent Lambda handler - Simple test version
    """
    try:
        logger.info(f"Product Insight Agent received event: {json.dumps(event, default=str)}")
        
        # Extract parameters from body
        body = event.get('body', '{}')
        if isinstance(body, str):
            try:
                body_data = json.loads(body)
            except:
                body_data = {}
        else:
            body_data = body or {}
        
        session_id = body_data.get('sessionId')
        business_info = body_data.get('businessInfo', {})
        
        if not session_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Session ID is required'
                })
            }
        
        # Mock business analysis
        industry = business_info.get('industry', '일반 업종')
        region = business_info.get('region', '일반 지역')
        size = business_info.get('size', '중간 규모')
        
        analysis_result = {
            'sessionId': session_id,
            'analysis': {
                'summary': f'{region} 지역의 {size} {industry} 사업에 대한 분석 결과입니다.',
                'score': 85.5,
                'insights': [
                    f'{industry} 업종은 {region} 지역에서 좋은 성장 잠재력을 보입니다.',
                    f'{size} 규모로 시작하기에 적절한 시장 환경입니다.',
                    '경쟁사 분석 결과 차별화 포인트가 필요합니다.'
                ],
                'recommendations': [
                    '타겟 고객층을 명확히 정의하세요.',
                    '지역 특성을 반영한 마케팅 전략을 수립하세요.',
                    '초기 투자 비용을 최적화하세요.'
                ],
                'market_potential': 'HIGH',
                'risk_level': 'MEDIUM'
            },
            'metadata': {
                'analyzed_at': '2025-09-29T11:22:00Z',
                'agent': 'product-insight',
                'version': '1.0.0'
            }
        }
        
        logger.info(f"Generated analysis for {industry} business in {region}")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(analysis_result)
        }
        
    except Exception as e:
        logger.error(f"Error in Product Insight Agent: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }