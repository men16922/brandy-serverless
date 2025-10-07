#!/usr/bin/env python3
"""
Market Data DynamoDB 테이블 생성 및 초기 데이터 로드
"""

import os
import sys
import json
import time
import boto3
from datetime import datetime
from typing import Dict, Any, List

# 환경 변수 설정
os.environ['AWS_ACCESS_KEY_ID'] = 'dummy'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'dummy'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

class MarketDataTableManager:
    def __init__(self, endpoint_url='http://localhost:8000'):
        self.dynamodb = boto3.client(
            'dynamodb',
            endpoint_url=endpoint_url,
            region_name='us-east-1',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        self.table_name = 'MarketData'
        
    def create_table(self) -> bool:
        """MarketData 테이블 생성"""
        print("=== MarketData 테이블 생성 ===")
        
        try:
            # 기존 테이블 확인
            try:
                self.dynamodb.describe_table(TableName=self.table_name)
                print(f"✓ 테이블 '{self.table_name}' 이미 존재")
                return True
            except self.dynamodb.exceptions.ResourceNotFoundException:
                pass
            
            # 테이블 생성
            table_definition = {
                'TableName': self.table_name,
                'KeySchema': [
                    {'AttributeName': 'dataType', 'KeyType': 'HASH'},
                    {'AttributeName': 'dataKey', 'KeyType': 'RANGE'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'dataType', 'AttributeType': 'S'},
                    {'AttributeName': 'dataKey', 'AttributeType': 'S'},
                    {'AttributeName': 'category', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'CategoryIndex',
                        'KeySchema': [
                            {'AttributeName': 'category', 'KeyType': 'HASH'},
                            {'AttributeName': 'dataKey', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ],
                'BillingMode': 'PAY_PER_REQUEST'
            }
            
            self.dynamodb.create_table(**table_definition)
            print(f"✓ 테이블 '{self.table_name}' 생성 완료")
            
            # 테이블 활성화 대기
            time.sleep(3)
            return True
            
        except Exception as e:
            print(f"❌ 테이블 생성 실패: {str(e)}")
            return False
    
    def load_json_data(self, file_path: str) -> Dict[str, Any]:
        """JSON 파일 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ JSON 파일 로드 실패 ({file_path}): {str(e)}")
            return {}
    
    def insert_industry_market_size(self) -> bool:
        """업종별 시장 규모 데이터 삽입"""
        print("\n--- 업종별 시장 규모 데이터 삽입 ---")
        
        data = self.load_json_data('data/market-data/industry-market-size.json')
        if not data:
            return False
        
        try:
            for industry, market_info in data.items():
                item = {
                    'dataType': {'S': 'INDUSTRY_MARKET_SIZE'},
                    'dataKey': {'S': industry},
                    'category': {'S': 'market_size'},
                    'data': {'S': json.dumps(market_info, ensure_ascii=False)},
                    'createdAt': {'S': datetime.now().isoformat()},
                    'updatedAt': {'S': datetime.now().isoformat()}
                }
                
                self.dynamodb.put_item(TableName=self.table_name, Item=item)
                print(f"✓ {industry} 시장 규모 데이터 삽입")
            
            return True
            
        except Exception as e:
            print(f"❌ 업종별 시장 규모 데이터 삽입 실패: {str(e)}")
            return False
    
    def insert_regional_multipliers(self) -> bool:
        """지역별 조정 계수 데이터 삽입"""
        print("\n--- 지역별 조정 계수 데이터 삽입 ---")
        
        data = self.load_json_data('data/market-data/regional-multipliers.json')
        if not data:
            return False
        
        try:
            for region, multiplier_info in data.items():
                item = {
                    'dataType': {'S': 'REGIONAL_MULTIPLIER'},
                    'dataKey': {'S': region},
                    'category': {'S': 'regional_data'},
                    'data': {'S': json.dumps(multiplier_info, ensure_ascii=False)},
                    'createdAt': {'S': datetime.now().isoformat()},
                    'updatedAt': {'S': datetime.now().isoformat()}
                }
                
                self.dynamodb.put_item(TableName=self.table_name, Item=item)
                print(f"✓ {region} 지역 조정 계수 데이터 삽입")
            
            return True
            
        except Exception as e:
            print(f"❌ 지역별 조정 계수 데이터 삽입 실패: {str(e)}")
            return False
    
    def insert_industry_competitors(self) -> bool:
        """업종별 경쟁사 데이터 삽입"""
        print("\n--- 업종별 경쟁사 데이터 삽입 ---")
        
        data = self.load_json_data('data/market-data/industry-competitors.json')
        if not data:
            return False
        
        try:
            for industry, competitor_info in data.items():
                item = {
                    'dataType': {'S': 'INDUSTRY_COMPETITOR'},
                    'dataKey': {'S': industry},
                    'category': {'S': 'competitor_analysis'},
                    'data': {'S': json.dumps(competitor_info, ensure_ascii=False)},
                    'createdAt': {'S': datetime.now().isoformat()},
                    'updatedAt': {'S': datetime.now().isoformat()}
                }
                
                self.dynamodb.put_item(TableName=self.table_name, Item=item)
                print(f"✓ {industry} 경쟁사 데이터 삽입")
            
            return True
            
        except Exception as e:
            print(f"❌ 업종별 경쟁사 데이터 삽입 실패: {str(e)}")
            return False
    
    def insert_industry_trends(self) -> bool:
        """업종별 트렌드 데이터 삽입"""
        print("\n--- 업종별 트렌드 데이터 삽입 ---")
        
        data = self.load_json_data('data/market-data/industry-trends.json')
        if not data:
            return False
        
        try:
            for industry, trend_info in data.items():
                item = {
                    'dataType': {'S': 'INDUSTRY_TREND'},
                    'dataKey': {'S': industry},
                    'category': {'S': 'trend_analysis'},
                    'data': {'S': json.dumps(trend_info, ensure_ascii=False)},
                    'createdAt': {'S': datetime.now().isoformat()},
                    'updatedAt': {'S': datetime.now().isoformat()}
                }
                
                self.dynamodb.put_item(TableName=self.table_name, Item=item)
                print(f"✓ {industry} 트렌드 데이터 삽입")
            
            return True
            
        except Exception as e:
            print(f"❌ 업종별 트렌드 데이터 삽입 실패: {str(e)}")
            return False
    
    def verify_data(self) -> bool:
        """삽입된 데이터 검증"""
        print("\n=== 삽입된 데이터 검증 ===")
        
        try:
            # 전체 데이터 스캔
            response = self.dynamodb.scan(TableName=self.table_name)
            items = response.get('Items', [])
            
            print(f"✓ 총 레코드 수: {len(items)}")
            
            # 데이터 타입별 카운트
            data_type_counts = {}
            for item in items:
                data_type = item['dataType']['S']
                data_type_counts[data_type] = data_type_counts.get(data_type, 0) + 1
            
            print("\n--- 데이터 타입별 카운트 ---")
            for data_type, count in data_type_counts.items():
                print(f"  {data_type}: {count}개")
            
            # 샘플 데이터 확인
            print("\n--- 샘플 데이터 확인 ---")
            for item in items[:3]:  # 처음 3개만 확인
                data_type = item['dataType']['S']
                data_key = item['dataKey']['S']
                print(f"  {data_type} - {data_key}")
                
                # 데이터 내용 확인
                try:
                    data_content = json.loads(item['data']['S'])
                    if data_type == 'INDUSTRY_MARKET_SIZE':
                        print(f"    시장 규모: {data_content.get('total', 'N/A')}")
                    elif data_type == 'REGIONAL_MULTIPLIER':
                        print(f"    조정 계수: {data_content.get('multiplier', 'N/A')}")
                    elif data_type == 'INDUSTRY_COMPETITOR':
                        competitors = data_content.get('major_competitors', [])
                        print(f"    주요 경쟁사: {len(competitors)}개")
                    elif data_type == 'INDUSTRY_TREND':
                        hot_trends = data_content.get('hot_trends', [])
                        print(f"    핫 트렌드: {len(hot_trends)}개")
                except:
                    print("    데이터 파싱 오류")
            
            return len(items) > 0
            
        except Exception as e:
            print(f"❌ 데이터 검증 실패: {str(e)}")
            return False
    
    def setup_all_data(self) -> bool:
        """모든 데이터 설정"""
        print("Market Data 테이블 및 초기 데이터 설정")
        print("=" * 50)
        
        # 1. 테이블 생성
        if not self.create_table():
            return False
        
        # 2. 데이터 삽입
        results = []
        results.append(self.insert_industry_market_size())
        results.append(self.insert_regional_multipliers())
        results.append(self.insert_industry_competitors())
        results.append(self.insert_industry_trends())
        
        if not all(results):
            print("❌ 일부 데이터 삽입 실패")
            return False
        
        # 3. 데이터 검증
        if not self.verify_data():
            return False
        
        print(f"\n🎉 Market Data 테이블 설정 완료!")
        print(f"📊 DynamoDB Admin UI: http://localhost:8002")
        print(f"📋 테이블명: {self.table_name}")
        
        return True

def main():
    """메인 실행"""
    # 현재 디렉토리를 프로젝트 루트로 변경
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    os.chdir(project_root)
    
    manager = MarketDataTableManager()
    success = manager.setup_all_data()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)