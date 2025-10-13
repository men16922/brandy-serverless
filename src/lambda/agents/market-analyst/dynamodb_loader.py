"""
Market Analyst Agent - DynamoDB Data Loader
DynamoDB에서 동적 시장 분석 데이터를 로드하는 유틸리티
"""

import boto3
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MarketAnalysisDynamoDBLoader:
    """Market Analyst Agent의 DynamoDB 데이터 로더 (Single Table Design)"""
    
    # Data type constants
    DATA_TYPE_BEHAVIORAL_CHANGES = "BEHAVIORAL_CHANGES"
    DATA_TYPE_INDUSTRY_RISKS = "INDUSTRY_RISKS"
    DATA_TYPE_BENCHMARK_METRICS = "BENCHMARK_METRICS"
    DATA_TYPE_MARKET_GAPS = "MARKET_GAPS"
    DATA_TYPE_CUSTOMER_SEGMENTS = "CUSTOMER_SEGMENTS"
    DATA_TYPE_TECH_OPPORTUNITIES = "TECH_OPPORTUNITIES"
    DATA_TYPE_PREFERENCE_INSIGHTS = "PREFERENCE_INSIGHTS"
    DATA_TYPE_FUTURE_PROJECTIONS = "FUTURE_PROJECTIONS"
    
    def __init__(self, table_name: Optional[str] = None):
        """
        Initialize DynamoDB loader
        
        Args:
            table_name: DynamoDB table name (default: from environment)
        """
        self.table_name = table_name or os.getenv(
            'MARKET_ANALYSIS_TABLE',
            f"ai-branding-chatbot-market-analysis-{os.getenv('ENVIRONMENT', 'dev')}"
        )
        
        try:
            dynamodb = boto3.resource('dynamodb')
            self.table = dynamodb.Table(self.table_name)
            logger.info(f"DynamoDB loader initialized: {self.table_name}")
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB table: {str(e)}")
            self.table = None
    
    def _get_item(
        self,
        data_type: str,
        industry: str,
        region: str = "GLOBAL"
    ) -> Optional[Dict[str, Any]]:
        """
        Get item from DynamoDB
        
        Args:
            data_type: Data type (e.g., BEHAVIORAL_CHANGES)
            industry: Industry name
            region: Region name (default: GLOBAL)
        
        Returns:
            Item data or None if not found
        """
        if not self.table:
            logger.warning("DynamoDB table not initialized")
            return None
        
        try:
            pk = f"{data_type}#{industry}"
            
            # Query with SK prefix to get latest data
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :region)',
                ExpressionAttributeValues={
                    ':pk': pk,
                    ':region': region
                },
                ScanIndexForward=False,  # Sort descending (latest first)
                Limit=1
            )
            
            items = response.get('Items', [])
            if items:
                logger.info(f"Retrieved {data_type} for {industry}/{region}")
                return items[0]
            else:
                logger.warning(f"No data found for {data_type}/{industry}/{region}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving {data_type}: {str(e)}")
            return None
    
    def _query_by_data_type(
        self,
        data_type: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query all items of a specific data type (using GSI)
        
        Args:
            data_type: Data type to query
            limit: Maximum number of items to return
        
        Returns:
            List of items
        """
        if not self.table:
            return []
        
        try:
            response = self.table.query(
                IndexName='DataTypeIndex',
                KeyConditionExpression='dataType = :dt',
                ExpressionAttributeValues={':dt': data_type},
                ScanIndexForward=False,  # Latest first
                Limit=limit
            )
            
            items = response.get('Items', [])
            logger.info(f"Retrieved {len(items)} items for {data_type}")
            return items
            
        except Exception as e:
            logger.error(f"Error querying {data_type}: {str(e)}")
            return []
    
    def get_behavioral_changes(
        self,
        industry: str,
        region: str = "GLOBAL"
    ) -> List[Dict[str, Any]]:
        """업종별 소비자 행동 변화 데이터 조회"""
        item = self._get_item(self.DATA_TYPE_BEHAVIORAL_CHANGES, industry, region)
        if item and 'data' in item:
            return item['data'].get('changes', [])
        return []
    
    def get_industry_risks(
        self,
        industry: str,
        region: str = "GLOBAL"
    ) -> List[Dict[str, str]]:
        """업종별 특화 위험 데이터 조회"""
        item = self._get_item(self.DATA_TYPE_INDUSTRY_RISKS, industry, region)
        if item and 'data' in item:
            return item['data'].get('risks', [])
        return []
    
    def get_benchmark_metrics(
        self,
        industry: str,
        region: str = "GLOBAL"
    ) -> Dict[str, str]:
        """벤치마크 지표 데이터 조회"""
        item = self._get_item(self.DATA_TYPE_BENCHMARK_METRICS, industry, region)
        if item and 'data' in item:
            return item['data'].get('metrics', {})
        return {}
    
    def get_market_gaps(
        self,
        industry: str,
        region: str = "GLOBAL"
    ) -> List[Dict[str, Any]]:
        """시장 갭 분석 데이터 조회"""
        item = self._get_item(self.DATA_TYPE_MARKET_GAPS, industry, region)
        if item and 'data' in item:
            return item['data'].get('gaps', [])
        return []
    
    def get_customer_segments(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """신규 고객 세그먼트 데이터 조회 (전체)"""
        items = self._query_by_data_type(self.DATA_TYPE_CUSTOMER_SEGMENTS, limit)
        segments = []
        for item in items:
            if 'data' in item:
                segments.extend(item['data'].get('segments', []))
        return segments
    
    def get_tech_opportunities(
        self,
        industry: str,
        region: str = "GLOBAL"
    ) -> List[Dict[str, Any]]:
        """기술 기회 데이터 조회"""
        item = self._get_item(self.DATA_TYPE_TECH_OPPORTUNITIES, industry, region)
        if item and 'data' in item:
            return item['data'].get('opportunities', [])
        return []
    
    def get_preference_insights(
        self,
        industry: str,
        region: str = "GLOBAL"
    ) -> List[str]:
        """선호도 변화 인사이트 조회"""
        item = self._get_item(self.DATA_TYPE_PREFERENCE_INSIGHTS, industry, region)
        if item and 'data' in item:
            return item['data'].get('insights', [])
        return []
    
    def get_future_projections(
        self,
        industry: str,
        region: str = "GLOBAL"
    ) -> Dict[str, Any]:
        """미래 선호도 전망 조회"""
        item = self._get_item(self.DATA_TYPE_FUTURE_PROJECTIONS, industry, region)
        if item and 'data' in item:
            return item['data'].get('projection', {})
        return {}
    
    def put_item(
        self,
        data_type: str,
        industry: str,
        region: str,
        data: Dict[str, Any],
        ttl_days: int = 365
    ) -> bool:
        """
        Put item to DynamoDB
        
        Args:
            data_type: Data type
            industry: Industry name
            region: Region name
            data: Data to store
            ttl_days: TTL in days (default: 365)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.table:
            return False
        
        try:
            now = datetime.utcnow()
            ttl_timestamp = int((now + timedelta(days=ttl_days)).timestamp())
            
            item = {
                'PK': f"{data_type}#{industry}",
                'SK': f"{region}#{now.isoformat()}",
                'dataType': data_type,
                'industry': industry,
                'region': region,
                'data': data,
                'lastUpdated': now.isoformat(),
                'ttl': ttl_timestamp
            }
            
            self.table.put_item(Item=item)
            logger.info(f"Stored {data_type} for {industry}/{region}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing {data_type}: {str(e)}")
            return False


# Singleton instance
_dynamodb_loader_instance = None


def get_dynamodb_loader() -> MarketAnalysisDynamoDBLoader:
    """MarketAnalysisDynamoDBLoader 싱글톤 인스턴스 반환"""
    global _dynamodb_loader_instance
    if _dynamodb_loader_instance is None:
        _dynamodb_loader_instance = MarketAnalysisDynamoDBLoader()
    return _dynamodb_loader_instance
