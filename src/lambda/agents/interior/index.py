"""
Interior Agent - Generates interior design recommendations
"""

import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Interior Agent Lambda handler
    Generates interior design recommendations based on selected signboard
    """
    try:
        logger.info(f"Interior Agent received event: {json.dumps(event, default=str)}")
        
        # Extract parameters
        session_id = event.get('sessionId')
        selected_signboard = event.get('selectedSignboard')
        business_info = event.get('businessInfo')
        action = event.get('action', 'generate_interiors')
        
        if not all([session_id, selected_signboard, business_info]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameters: sessionId, selectedSignboard, businessInfo'
                })
            }
        
        # TODO: Implement actual interior generation logic
        # This is a placeholder implementation
        
        interior_results = {
            'interiors': [
                {
                    'id': 'interior-1',
                    'url': f's3://interiors/{session_id}/interior-modern.png',
                    'description': '모던 인테리어 - 깔끔하고 세련된 디자인',
                    'style': 'modern',
                    'budget': '중간',
                    'palette': ['#FFFFFF', '#2C3E50', '#3498DB'],
                    'features': ['LED 조명', '미니멀 가구', '유리 파티션']
                },
                {
                    'id': 'interior-2',
                    'url': f's3://interiors/{session_id}/interior-cozy.png',
                    'description': '아늑한 인테리어 - 따뜻하고 편안한 분위기',
                    'style': 'cozy',
                    'budget': '경제적',
                    'palette': ['#F4E4C1', '#8B4513', '#CD853F'],
                    'features': ['원목 가구', '따뜻한 조명', '식물 장식']
                },
                {
                    'id': 'interior-3',
                    'url': f's3://interiors/{session_id}/interior-luxury.png',
                    'description': '럭셔리 인테리어 - 고급스럽고 우아한 디자인',
                    'style': 'luxury',
                    'budget': '고급',
                    'palette': ['#1C1C1C', '#D4AF37', '#FFFFFF'],
                    'features': ['대리석 마감', '샹들리에', '가죽 소파']
                }
            ],
            'metadata': {
                'generated_at': context.aws_request_id,
                'session_id': session_id,
                'signboard_style': selected_signboard.get('style', 'unknown')
            }
        }
        
        logger.info(f"Generated {len(interior_results['interiors'])} interior designs")
        
        return {
            'statusCode': 200,
            'body': json.dumps(interior_results)
        }
        
    except Exception as e:
        logger.error(f"Error in Interior Agent: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }