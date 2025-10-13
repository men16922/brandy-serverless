"""
데이터 로더 - 초기화 데이터를 DynamoDB에 로드하고 관리
"""

import json
import os
import boto3
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class DataLoader:
    """초기화 데이터를 DynamoDB에 로드하고 관리하는 클래스"""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv('ENVIRONMENT', 'local')
        self.dynamodb = self._get_dynamodb_client()
        self.table_name = self._get_table_name()
        
    def _get_dynamodb_client(self):
        """환경에 따른 DynamoDB 클라이언트 생성"""
        if self.environment == 'local':
            return boto3.client(
                'dynamodb',
                endpoint_url='http://localhost:8000',
                region_name='us-east-1',
                aws_access_key_id='dummy',
                aws_secret_access_key='dummy'
            )
        else:
            return boto3.client('dynamodb')
    
    def _get_table_name(self) -> str:
        """환경에 따른 테이블 이름 반환"""
        base_name = "InteriorData"
        if self.environment == 'local':
            return f"{base_name}-local"
        else:
            return f"{base_name}-{self.environment}"
    
    def create_table_if_not_exists(self) -> bool:
        """테이블이 없으면 생성"""
        try:
            # 테이블 존재 확인
            self.dynamodb.describe_table(TableName=self.table_name)
            logger.info(f"Table {self.table_name} already exists")
            return True
        except self.dynamodb.exceptions.ResourceNotFoundException:
            # 테이블 생성
            try:
                self.dynamodb.create_table(
                    TableName=self.table_name,
                    KeySchema=[
                        {
                            'AttributeName': 'data_type',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'data_key',
                            'KeyType': 'RANGE'
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'data_type',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'data_key',
                            'AttributeType': 'S'
                        }
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                
                # 테이블 생성 완료 대기
                waiter = self.dynamodb.get_waiter('table_exists')
                waiter.wait(TableName=self.table_name)
                
                logger.info(f"Table {self.table_name} created successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to create table {self.table_name}: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Error checking table {self.table_name}: {str(e)}")
            return False
    
    def load_data_from_files(self, data_dir: str = "data") -> bool:
        """JSON 파일들로부터 데이터를 로드"""
        try:
            # 데이터 파일 목록
            data_files = {
                'interior_styles': 'interior_styles.json',
                'industry_characteristics': 'industry_characteristics.json',
                'regional_trends': 'regional_trends.json',
                'size_considerations': 'size_considerations.json'
            }
            
            success_count = 0
            total_count = len(data_files)
            
            for data_type, filename in data_files.items():
                file_path = os.path.join(data_dir, filename)
                if self._load_single_file(data_type, file_path):
                    success_count += 1
                    logger.info(f"Successfully loaded {data_type} from {filename}")
                else:
                    logger.error(f"Failed to load {data_type} from {filename}")
            
            logger.info(f"Data loading completed: {success_count}/{total_count} files loaded")
            return success_count == total_count
            
        except Exception as e:
            logger.error(f"Error loading data from files: {str(e)}")
            return False
    
    def _load_single_file(self, data_type: str, file_path: str) -> bool:
        """단일 JSON 파일을 로드"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 각 항목을 DynamoDB에 저장
            for key, value in data.items():
                item = {
                    'data_type': {'S': data_type},
                    'data_key': {'S': key},
                    'data_value': {'S': json.dumps(value, ensure_ascii=False)},
                    'updated_at': {'S': datetime.now(timezone.utc).isoformat()},
                    'version': {'N': '1'}
                }
                
                self.dynamodb.put_item(
                    TableName=self.table_name,
                    Item=item
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            return False
    
    def get_data(self, data_type: str, data_key: str = None) -> Optional[Dict[str, Any]]:
        """DynamoDB에서 데이터 조회"""
        try:
            if data_key:
                # 특정 키의 데이터 조회
                response = self.dynamodb.get_item(
                    TableName=self.table_name,
                    Key={
                        'data_type': {'S': data_type},
                        'data_key': {'S': data_key}
                    }
                )
                
                if 'Item' in response:
                    return json.loads(response['Item']['data_value']['S'])
                else:
                    return None
            else:
                # 데이터 타입의 모든 데이터 조회
                response = self.dynamodb.query(
                    TableName=self.table_name,
                    KeyConditionExpression='data_type = :dt',
                    ExpressionAttributeValues={
                        ':dt': {'S': data_type}
                    }
                )
                
                result = {}
                for item in response.get('Items', []):
                    key = item['data_key']['S']
                    value = json.loads(item['data_value']['S'])
                    result[key] = value
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting data {data_type}/{data_key}: {str(e)}")
            return None
    
    def update_data(self, data_type: str, data_key: str, data_value: Dict[str, Any]) -> bool:
        """데이터 업데이트"""
        try:
            # 현재 버전 조회
            current_item = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={
                    'data_type': {'S': data_type},
                    'data_key': {'S': data_key}
                }
            )
            
            current_version = 1
            if 'Item' in current_item:
                current_version = int(current_item['Item']['version']['N']) + 1
            
            # 업데이트된 데이터 저장
            item = {
                'data_type': {'S': data_type},
                'data_key': {'S': data_key},
                'data_value': {'S': json.dumps(data_value, ensure_ascii=False)},
                'updated_at': {'S': datetime.now(timezone.utc).isoformat()},
                'version': {'N': str(current_version)}
            }
            
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=item
            )
            
            logger.info(f"Updated {data_type}/{data_key} to version {current_version}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating data {data_type}/{data_key}: {str(e)}")
            return False
    
    def initialize_all_data(self, data_dir: str = "data", force_reload: bool = False) -> bool:
        """모든 데이터 초기화"""
        try:
            # 테이블 생성
            if not self.create_table_if_not_exists():
                return False
            
            # 기존 데이터 확인
            if not force_reload:
                existing_data = self.get_data('interior_styles')
                if existing_data:
                    logger.info("Data already exists, skipping initialization")
                    return True
            
            # 데이터 로드
            return self.load_data_from_files(data_dir)
            
        except Exception as e:
            logger.error(f"Error initializing data: {str(e)}")
            return False
    
    def get_all_interior_data(self) -> Dict[str, Dict[str, Any]]:
        """모든 인테리어 관련 데이터 조회"""
        try:
            return {
                'interior_styles': self.get_data('interior_styles') or {},
                'industry_characteristics': self.get_data('industry_characteristics') or {},
                'regional_trends': self.get_data('regional_trends') or {},
                'size_considerations': self.get_data('size_considerations') or {}
            }
        except Exception as e:
            logger.error(f"Error getting all interior data: {str(e)}")
            return {
                'interior_styles': {},
                'industry_characteristics': {},
                'regional_trends': {},
                'size_considerations': {}
            }


# 싱글톤 인스턴스
_data_loader_instance = None

def get_data_loader(environment: str = None) -> DataLoader:
    """DataLoader 싱글톤 인스턴스 반환"""
    global _data_loader_instance
    if _data_loader_instance is None:
        _data_loader_instance = DataLoader(environment)
    return _data_loader_instance

def initialize_data(data_dir: str = "data", force_reload: bool = False, environment: str = None) -> bool:
    """데이터 초기화 헬퍼 함수"""
    loader = get_data_loader(environment)
    return loader.initialize_all_data(data_dir, force_reload)