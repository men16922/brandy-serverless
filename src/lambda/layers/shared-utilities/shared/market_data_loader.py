"""
Market Data Loader - DynamoDB에서 시장 분석 데이터 조회
"""

import json
import boto3
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class MarketDataLoader:
    def __init__(self, dynamodb_client=None, table_name='MarketData'):
        self.dynamodb = dynamodb_client
        self.table_name = table_name
        self._cache = {}  # 메모리 캐시
        
    def _get_dynamodb_client(self):
        """DynamoDB 클라이언트 lazy loading"""
        if self.dynamodb is None:
            import os
            endpoint_url = os.getenv('DYNAMODB_ENDPOINT')
            
            if endpoint_url:  # 로컬 환경
                self.dynamodb = boto3.client(
                    'dynamodb',
                    endpoint_url=endpoint_url,
                    region_name=os.getenv('AWS_REGION', 'us-east-1'),
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'dummy'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'dummy')
                )
            else:  # AWS 환경
                self.dynamodb = boto3.client('dynamodb')
        
        return self.dynamodb
    
    def _get_data_from_dynamodb(self, data_type: str, data_key: str) -> Optional[Dict[str, Any]]:
        """DynamoDB에서 데이터 조회"""
        cache_key = f"{data_type}#{data_key}"
        
        # 캐시 확인
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            dynamodb = self._get_dynamodb_client()
            
            response = dynamodb.get_item(
                TableName=self.table_name,
                Key={
                    'dataType': {'S': data_type},
                    'dataKey': {'S': data_key}
                }
            )
            
            if 'Item' in response:
                data_str = response['Item']['data']['S']
                data = json.loads(data_str)
                
                # 캐시에 저장
                self._cache[cache_key] = data
                return data
            else:
                logger.warning(f"Data not found: {data_type} - {data_key}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get data from DynamoDB: {str(e)}")
            return None
    
    def _query_data_by_type(self, data_type: str) -> List[Dict[str, Any]]:
        """데이터 타입별 모든 데이터 조회"""
        try:
            dynamodb = self._get_dynamodb_client()
            
            response = dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='dataType = :dt',
                ExpressionAttributeValues={
                    ':dt': {'S': data_type}
                }
            )
            
            results = []
            for item in response.get('Items', []):
                data_key = item['dataKey']['S']
                data_str = item['data']['S']
                data = json.loads(data_str)
                
                results.append({
                    'dataKey': data_key,
                    'data': data
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to query data by type: {str(e)}")
            return []
    
    def get_industry_market_size(self, industry: str) -> Optional[Dict[str, Any]]:
        """업종별 시장 규모 데이터 조회"""
        return self._get_data_from_dynamodb('INDUSTRY_MARKET_SIZE', industry)
    
    def get_regional_multiplier(self, region: str) -> Optional[Dict[str, Any]]:
        """지역별 조정 계수 데이터 조회"""
        return self._get_data_from_dynamodb('REGIONAL_MULTIPLIER', region)
    
    def get_industry_competitors(self, industry: str) -> Optional[Dict[str, Any]]:
        """업종별 경쟁사 데이터 조회"""
        return self._get_data_from_dynamodb('INDUSTRY_COMPETITOR', industry)
    
    def get_industry_trends(self, industry: str) -> Optional[Dict[str, Any]]:
        """업종별 트렌드 데이터 조회"""
        return self._get_data_from_dynamodb('INDUSTRY_TREND', industry)
    
    def get_all_industries(self) -> List[str]:
        """모든 업종 목록 조회"""
        try:
            market_size_data = self._query_data_by_type('INDUSTRY_MARKET_SIZE')
            return [item['dataKey'] for item in market_size_data]
        except Exception as e:
            logger.error(f"Failed to get all industries: {str(e)}")
            return ['restaurant', 'retail', 'service', 'healthcare', 'education', 'technology']
    
    def get_all_regions(self) -> List[str]:
        """모든 지역 목록 조회"""
        try:
            regional_data = self._query_data_by_type('REGIONAL_MULTIPLIER')
            return [item['dataKey'] for item in regional_data]
        except Exception as e:
            logger.error(f"Failed to get all regions: {str(e)}")
            return ['seoul', 'busan', 'gyeonggi', 'incheon', 'daegu', 'daejeon', 'gwangju', 'ulsan', 'sejong', 'jeju']
    
    def calculate_regional_market_size(self, industry: str, region: str) -> Dict[str, Any]:
        """지역별 시장 규모 계산"""
        try:
            # 업종별 시장 규모 조회
            market_size_data = self.get_industry_market_size(industry)
            if not market_size_data:
                return {"error": f"Industry data not found: {industry}"}
            
            # 지역별 조정 계수 조회
            regional_data = self.get_regional_multiplier(region)
            if not regional_data:
                return {"error": f"Regional data not found: {region}"}
            
            # 시장 규모 계산
            total_market = market_size_data.get('total', '0조원')
            multiplier = regional_data.get('multiplier', 1.0)
            
            # 숫자 추출 (예: "45조원" -> 45)
            total_numeric = float(total_market.replace('조원', '').replace(',', ''))
            regional_size = total_numeric * multiplier
            target_size = regional_size * 0.05  # 5% 목표
            
            return {
                "totalMarketSize": total_market,
                "regionalMarketSize": f"{regional_size:.1f}조원",
                "targetMarketSize": f"{target_size:.1f}조원",
                "growthRate": market_size_data.get('growth_rate', '분석 중'),
                "marketMaturity": market_size_data.get('maturity', '분석 중'),
                "regionalMultiplier": f"{multiplier * 100:.0f}%",
                "competitiveIntensity": self._assess_competitive_intensity(industry, region),
                "marketSegments": market_size_data.get('segments', {}),
                "regionalCharacteristics": regional_data.get('characteristics', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate regional market size: {str(e)}")
            return {"error": "Market size calculation failed"}
    
    def _assess_competitive_intensity(self, industry: str, region: str) -> str:
        """경쟁 강도 평가"""
        # 업종별 기본 경쟁 강도
        industry_competition = {
            "restaurant": "매우 높음",
            "retail": "높음",
            "service": "중간",
            "healthcare": "중간",
            "education": "높음",
            "technology": "매우 높음"
        }
        
        base_intensity = industry_competition.get(industry, "중간")
        
        # 지역별 조정 (서울/경기는 경쟁이 더 치열)
        if region in ["seoul", "gyeonggi"]:
            return base_intensity
        else:
            # 지방은 한 단계 낮춤
            intensity_levels = ["낮음", "중간", "높음", "매우 높음"]
            try:
                current_index = intensity_levels.index(base_intensity)
                adjusted_index = max(0, current_index - 1)
                return intensity_levels[adjusted_index]
            except ValueError:
                return "중간"
    
    def get_fallback_data(self, data_type: str, data_key: str) -> Dict[str, Any]:
        """폴백 데이터 반환"""
        fallback_data = {
            'INDUSTRY_MARKET_SIZE': {
                'total': '추정 불가',
                'growth_rate': '일반적 성장률',
                'maturity': '분석 불가',
                'segments': {}
            },
            'REGIONAL_MULTIPLIER': {
                'multiplier': 0.5,
                'description': '기본 조정 계수',
                'characteristics': ['일반적 특성']
            },
            'INDUSTRY_COMPETITOR': {
                'major_competitors': [
                    {'name': '일반 경쟁사', 'type': '기본', 'strength': '일반적 강점'}
                ],
                'market_share_distribution': {'기타': '100%'},
                'competitive_advantages': ['품질', '서비스'],
                'competitive_threats': ['가격 경쟁', '신규 진입']
            },
            'INDUSTRY_TREND': {
                'hot_trends': [],
                'declining_trends': [],
                'consumer_behaviors': []
            }
        }
        
        return fallback_data.get(data_type, {})
    
    def clear_cache(self):
        """캐시 클리어"""
        self._cache.clear()
        logger.info("Market data cache cleared")

# 전역 인스턴스
_market_data_loader = None

def get_market_data_loader() -> MarketDataLoader:
    """Market Data Loader 싱글톤 인스턴스 반환"""
    global _market_data_loader
    if _market_data_loader is None:
        _market_data_loader = MarketDataLoader()
    return _market_data_loader