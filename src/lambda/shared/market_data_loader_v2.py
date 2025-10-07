"""
Market Data Loader V2 - 확장된 데이터 포맷 지원
다양한 데이터 구조와 새로운 데이터 타입을 지원하는 확장 버전
"""

import json
import boto3
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class MarketDataLoaderV2:
    """확장 가능한 Market Data Loader"""
    
    def __init__(self, dynamodb_client=None, table_name='MarketData'):
        self.dynamodb = dynamodb_client
        self.table_name = table_name
        self._cache = {}
        self._schema_cache = {}  # 스키마 캐시
        
    def register_data_type(self, data_type: str, schema: Dict[str, Any]):
        """새로운 데이터 타입 등록"""
        self._schema_cache[data_type] = schema
        logger.info(f"Registered new data type: {data_type}")
    
    def get_data_with_schema_validation(self, data_type: str, data_key: str) -> Optional[Dict[str, Any]]:
        """스키마 검증을 포함한 데이터 조회"""
        data = self._get_data_from_dynamodb(data_type, data_key)
        
        if data and data_type in self._schema_cache:
            # 스키마 검증 수행
            schema = self._schema_cache[data_type]
            if self._validate_schema(data, schema):
                return data
            else:
                logger.warning(f"Schema validation failed for {data_type}:{data_key}")
                return self._get_fallback_data_by_schema(schema)
        
        return data
    
    def _validate_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """데이터 스키마 검증"""
        required_fields = schema.get('required_fields', [])
        
        for field in required_fields:
            if field not in data:
                return False
        
        return True
    
    def _get_fallback_data_by_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """스키마 기반 폴백 데이터 생성"""
        fallback = {}
        default_values = schema.get('default_values', {})
        
        for field, default_value in default_values.items():
            fallback[field] = default_value
        
        fallback['fallback'] = True
        return fallback
    
    def get_data_with_transformation(self, data_type: str, data_key: str, 
                                   transform_func: Optional[callable] = None) -> Optional[Dict[str, Any]]:
        """데이터 변환 함수를 적용한 조회"""
        data = self._get_data_from_dynamodb(data_type, data_key)
        
        if data and transform_func:
            try:
                return transform_func(data)
            except Exception as e:
                logger.error(f"Data transformation failed: {str(e)}")
                return data
        
        return data
    
    def bulk_insert_with_validation(self, data_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """벌크 데이터 삽입 (검증 포함)"""
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for item in data_items:
            try:
                data_type = item.get('dataType')
                data_key = item.get('dataKey')
                data = item.get('data')
                
                # 스키마 검증
                if data_type in self._schema_cache:
                    if not self._validate_schema(data, self._schema_cache[data_type]):
                        results['failed'] += 1
                        results['errors'].append(f"Schema validation failed: {data_type}:{data_key}")
                        continue
                
                # DynamoDB에 삽입
                dynamodb_item = {
                    'dataType': {'S': data_type},
                    'dataKey': {'S': data_key},
                    'category': {'S': item.get('category', 'general')},
                    'data': {'S': json.dumps(data, ensure_ascii=False)},
                    'createdAt': {'S': datetime.now().isoformat()},
                    'updatedAt': {'S': datetime.now().isoformat()}
                }
                
                dynamodb = self._get_dynamodb_client()
                dynamodb.put_item(TableName=self.table_name, Item=dynamodb_item)
                
                results['success'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Insert failed for {item}: {str(e)}")
        
        return results
    
    def query_with_filters(self, data_type: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """필터를 적용한 데이터 조회"""
        try:
            dynamodb = self._get_dynamodb_client()
            
            # 기본 쿼리
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
                
                # 필터 적용
                if filters and not self._apply_filters(data, filters):
                    continue
                
                results.append({
                    'dataKey': data_key,
                    'data': data,
                    'category': item.get('category', {}).get('S', 'general'),
                    'updatedAt': item.get('updatedAt', {}).get('S', '')
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Query with filters failed: {str(e)}")
            return []
    
    def _apply_filters(self, data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """데이터에 필터 적용"""
        for filter_key, filter_value in filters.items():
            if filter_key not in data:
                return False
            
            data_value = data[filter_key]
            
            # 다양한 필터 타입 지원
            if isinstance(filter_value, dict):
                if 'min' in filter_value and data_value < filter_value['min']:
                    return False
                if 'max' in filter_value and data_value > filter_value['max']:
                    return False
                if 'contains' in filter_value and filter_value['contains'] not in str(data_value):
                    return False
            elif isinstance(filter_value, list):
                if data_value not in filter_value:
                    return False
            else:
                if data_value != filter_value:
                    return False
        
        return True
    
    def get_data_aggregation(self, data_type: str, aggregation_func: str, field: str) -> Any:
        """데이터 집계 함수"""
        try:
            all_data = self.query_with_filters(data_type)
            values = []
            
            for item in all_data:
                data = item['data']
                if field in data:
                    try:
                        # 숫자 값 추출 (예: "45조원" -> 45)
                        value = data[field]
                        if isinstance(value, str):
                            # 숫자 추출 시도
                            import re
                            numbers = re.findall(r'[\d.]+', value)
                            if numbers:
                                value = float(numbers[0])
                        
                        if isinstance(value, (int, float)):
                            values.append(value)
                    except:
                        continue
            
            if not values:
                return None
            
            # 집계 함수 적용
            if aggregation_func == 'sum':
                return sum(values)
            elif aggregation_func == 'avg':
                return sum(values) / len(values)
            elif aggregation_func == 'max':
                return max(values)
            elif aggregation_func == 'min':
                return min(values)
            elif aggregation_func == 'count':
                return len(values)
            
            return None
            
        except Exception as e:
            logger.error(f"Data aggregation failed: {str(e)}")
            return None
    
    def _get_dynamodb_client(self):
        """DynamoDB 클라이언트 lazy loading"""
        if self.dynamodb is None:
            import os
            endpoint_url = os.getenv('DYNAMODB_ENDPOINT')
            
            if endpoint_url:
                self.dynamodb = boto3.client(
                    'dynamodb',
                    endpoint_url=endpoint_url,
                    region_name=os.getenv('AWS_REGION', 'us-east-1'),
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'dummy'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'dummy')
                )
            else:
                self.dynamodb = boto3.client('dynamodb')
        
        return self.dynamodb
    
    def _get_data_from_dynamodb(self, data_type: str, data_key: str) -> Optional[Dict[str, Any]]:
        """DynamoDB에서 데이터 조회 (기존 메서드)"""
        cache_key = f"{data_type}#{data_key}"
        
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
                
                self._cache[cache_key] = data
                return data
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get data from DynamoDB: {str(e)}")
            return None

# 확장 예시: 새로운 데이터 타입 등록
def register_extended_data_types(loader: MarketDataLoaderV2):
    """확장된 데이터 타입들을 등록"""
    
    # 시장 예측 데이터 스키마
    market_forecast_schema = {
        'required_fields': ['industry', 'forecast_period', 'predictions'],
        'default_values': {
            'industry': 'unknown',
            'forecast_period': '2025-2027',
            'predictions': {'market_growth': '0%'}
        }
    }
    
    # 규제 정보 스키마
    regulatory_schema = {
        'required_fields': ['region', 'regulations'],
        'default_values': {
            'region': 'general',
            'regulations': []
        }
    }
    
    # 고객 세그먼트 스키마
    customer_segment_schema = {
        'required_fields': ['industry', 'segments'],
        'default_values': {
            'industry': 'general',
            'segments': []
        }
    }
    
    loader.register_data_type('MARKET_FORECAST', market_forecast_schema)
    loader.register_data_type('REGULATORY_INFO', regulatory_schema)
    loader.register_data_type('CUSTOMER_SEGMENT', customer_segment_schema)

# 사용 예시
def example_usage():
    """확장된 기능 사용 예시"""
    loader = MarketDataLoaderV2()
    register_extended_data_types(loader)
    
    # 1. 스키마 검증을 포함한 데이터 조회
    forecast_data = loader.get_data_with_schema_validation('MARKET_FORECAST', 'restaurant')
    
    # 2. 데이터 변환 함수 적용
    def transform_market_size(data):
        # 시장 규모를 숫자로 변환
        if 'total' in data:
            import re
            numbers = re.findall(r'[\d.]+', data['total'])
            if numbers:
                data['total_numeric'] = float(numbers[0])
        return data
    
    market_data = loader.get_data_with_transformation(
        'INDUSTRY_MARKET_SIZE', 
        'restaurant', 
        transform_market_size
    )
    
    # 3. 필터를 적용한 조회
    high_growth_industries = loader.query_with_filters(
        'INDUSTRY_MARKET_SIZE',
        filters={
            'growth_rate': {'contains': '5%'}  # 5% 이상 성장률
        }
    )
    
    # 4. 데이터 집계
    avg_market_size = loader.get_data_aggregation(
        'INDUSTRY_MARKET_SIZE',
        'avg',
        'total'
    )
    
    return {
        'forecast_data': forecast_data,
        'market_data': market_data,
        'high_growth_industries': high_growth_industries,
        'avg_market_size': avg_market_size
    }