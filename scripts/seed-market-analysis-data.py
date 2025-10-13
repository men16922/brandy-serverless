#!/usr/bin/env python3
"""
Market Analysis Data Seeder
DynamoDB MarketAnalysisData 테이블에 초기 데이터를 로드하는 스크립트
"""

import sys
import os
import boto3
from datetime import datetime, timedelta
import json

# Add project path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda', 'agents', 'market-analyst'))

from dynamodb_loader import MarketAnalysisDynamoDBLoader


def seed_behavioral_changes(loader: MarketAnalysisDynamoDBLoader):
    """업종별 소비자 행동 변화 데이터 시딩"""
    print("\n[1/8] Seeding Behavioral Changes...")
    
    data_by_industry = {
        "restaurant": {
            "changes": [
                {"change": "배달 앱 사용 증가", "percentage": "+78%"},
                {"change": "건강 메뉴 선호", "percentage": "+45%"},
                {"change": "인스타그래머블 중시", "percentage": "+62%"},
                {"change": "개인 다이닝 선호", "percentage": "+38%"}
            ]
        },
        "retail": {
            "changes": [
                {"change": "온라인 우선 구매", "percentage": "+85%"},
                {"change": "리뷰 의존도 증가", "percentage": "+72%"},
                {"change": "지속가능성 고려", "percentage": "+55%"},
                {"change": "개인화 상품 선호", "percentage": "+48%"}
            ]
        },
        "service": {
            "changes": [
                {"change": "비대면 서비스 선호", "percentage": "+68%"},
                {"change": "구독 서비스 선호", "percentage": "+52%"},
                {"change": "개인 맞춤 서비스", "percentage": "+65%"},
                {"change": "투명한 가격 정책", "percentage": "+58%"}
            ]
        }
    }
    
    for industry, data in data_by_industry.items():
        success = loader.put_item(
            data_type=loader.DATA_TYPE_BEHAVIORAL_CHANGES,
            industry=industry,
            region="GLOBAL",
            data=data,
            ttl_days=90  # 3개월 TTL
        )
        if success:
            print(f"  ✓ {industry}")
        else:
            print(f"  ✗ {industry} (failed)")


def seed_industry_risks(loader: MarketAnalysisDynamoDBLoader):
    """업종별 특화 위험 데이터 시딩"""
    print("\n[2/8] Seeding Industry Risks...")
    
    data_by_industry = {
        "restaurant": {
            "risks": [
                {"risk": "식자재 가격 변동", "impact": "높음"},
                {"risk": "배달비 상승", "impact": "중간"},
                {"risk": "위생 규제 강화", "impact": "중간"}
            ]
        },
        "retail": {
            "risks": [
                {"risk": "온라인 플랫폼 의존", "impact": "높음"},
                {"risk": "재고 관리 복잡성", "impact": "중간"},
                {"risk": "물류비 상승", "impact": "중간"}
            ]
        },
        "technology": {
            "risks": [
                {"risk": "기술 변화 속도", "impact": "매우 높음"},
                {"risk": "인재 확보 경쟁", "impact": "높음"},
                {"risk": "보안 위협 증가", "impact": "높음"}
            ]
        }
    }
    
    for industry, data in data_by_industry.items():
        success = loader.put_item(
            data_type=loader.DATA_TYPE_INDUSTRY_RISKS,
            industry=industry,
            region="GLOBAL",
            data=data,
            ttl_days=180  # 6개월 TTL
        )
        if success:
            print(f"  ✓ {industry}")
        else:
            print(f"  ✗ {industry} (failed)")


def seed_benchmark_metrics(loader: MarketAnalysisDynamoDBLoader):
    """벤치마크 지표 데이터 시딩"""
    print("\n[3/8] Seeding Benchmark Metrics...")
    
    data_by_industry = {
        "restaurant": {
            "metrics": {
                "고객 재방문율": "60-70%",
                "평균 객단가": "15,000-25,000원",
                "월 매출": "3,000-8,000만원"
            }
        },
        "retail": {
            "metrics": {
                "고객 전환율": "15-25%",
                "평균 객단가": "30,000-50,000원",
                "재고 회전율": "월 2-3회"
            }
        },
        "service": {
            "metrics": {
                "고객 만족도": "85-95%",
                "재계약율": "70-80%",
                "평균 서비스 단가": "50,000-200,000원"
            }
        }
    }
    
    for industry, data in data_by_industry.items():
        success = loader.put_item(
            data_type=loader.DATA_TYPE_BENCHMARK_METRICS,
            industry=industry,
            region="GLOBAL",
            data=data,
            ttl_days=180  # 6개월 TTL
        )
        if success:
            print(f"  ✓ {industry}")
        else:
            print(f"  ✗ {industry} (failed)")


def seed_market_gaps(loader: MarketAnalysisDynamoDBLoader):
    """시장 갭 분석 데이터 시딩"""
    print("\n[4/8] Seeding Market Gaps...")
    
    data_by_industry = {
        "restaurant": {
            "gaps": [
                {"gap": "건강한 야식 옵션", "size": "중간", "difficulty": "낮음"},
                {"gap": "1인 가구 맞춤 메뉴", "size": "높음", "difficulty": "중간"},
                {"gap": "시니어 친화 메뉴", "size": "높음", "difficulty": "낮음"}
            ]
        },
        "retail": {
            "gaps": [
                {"gap": "지속가능한 패션", "size": "높음", "difficulty": "중간"},
                {"gap": "AR 체험 쇼핑", "size": "중간", "difficulty": "높음"},
                {"gap": "로컬 브랜드 큐레이션", "size": "중간", "difficulty": "낮음"}
            ]
        },
        "service": {
            "gaps": [
                {"gap": "AI 기반 개인 상담", "size": "높음", "difficulty": "높음"},
                {"gap": "구독형 전문 서비스", "size": "중간", "difficulty": "중간"},
                {"gap": "하이브리드 서비스 모델", "size": "높음", "difficulty": "중간"}
            ]
        }
    }
    
    for industry, data in data_by_industry.items():
        success = loader.put_item(
            data_type=loader.DATA_TYPE_MARKET_GAPS,
            industry=industry,
            region="GLOBAL",
            data=data,
            ttl_days=90  # 3개월 TTL
        )
        if success:
            print(f"  ✓ {industry}")
        else:
            print(f"  ✗ {industry} (failed)")


def seed_customer_segments(loader: MarketAnalysisDynamoDBLoader):
    """신규 고객 세그먼트 데이터 시딩"""
    print("\n[5/8] Seeding Customer Segments...")
    
    data = {
        "segments": [
            {
                "segment": "디지털 네이티브 시니어",
                "size": "증가 중",
                "characteristics": "기술 친화적 50-60대",
                "opportunity": "높음"
            },
            {
                "segment": "가치 소비 MZ세대",
                "size": "대형",
                "characteristics": "의미 있는 소비 추구",
                "opportunity": "매우 높음"
            },
            {
                "segment": "1인 가구 프리미엄",
                "size": "증가 중",
                "characteristics": "고품질 개인 서비스 선호",
                "opportunity": "높음"
            }
        ]
    }
    
    success = loader.put_item(
        data_type=loader.DATA_TYPE_CUSTOMER_SEGMENTS,
        industry="GENERAL",
        region="GLOBAL",
        data=data,
        ttl_days=180  # 6개월 TTL
    )
    
    if success:
        print(f"  ✓ Customer segments")
    else:
        print(f"  ✗ Customer segments (failed)")


def seed_tech_opportunities(loader: MarketAnalysisDynamoDBLoader):
    """기술 기회 데이터 시딩"""
    print("\n[6/8] Seeding Tech Opportunities...")
    
    data_by_industry = {
        "restaurant": {
            "opportunities": [
                {"tech": "AI 메뉴 추천", "maturity": "중간", "impact": "높음"},
                {"tech": "무인 주문 시스템", "maturity": "높음", "impact": "중간"},
                {"tech": "IoT 재고 관리", "maturity": "중간", "impact": "중간"}
            ]
        },
        "retail": {
            "opportunities": [
                {"tech": "AR/VR 쇼핑", "maturity": "중간", "impact": "높음"},
                {"tech": "AI 개인화 추천", "maturity": "높음", "impact": "높음"},
                {"tech": "블록체인 인증", "maturity": "낮음", "impact": "중간"}
            ]
        },
        "service": {
            "opportunities": [
                {"tech": "AI 챗봇", "maturity": "높음", "impact": "높음"},
                {"tech": "예측 분석", "maturity": "중간", "impact": "높음"},
                {"tech": "자동화 워크플로", "maturity": "중간", "impact": "중간"}
            ]
        }
    }
    
    for industry, data in data_by_industry.items():
        success = loader.put_item(
            data_type=loader.DATA_TYPE_TECH_OPPORTUNITIES,
            industry=industry,
            region="GLOBAL",
            data=data,
            ttl_days=90  # 3개월 TTL
        )
        if success:
            print(f"  ✓ {industry}")
        else:
            print(f"  ✗ {industry} (failed)")


def seed_preference_insights(loader: MarketAnalysisDynamoDBLoader):
    """선호도 변화 인사이트 데이터 시딩"""
    print("\n[7/8] Seeding Preference Insights...")
    
    data_by_industry = {
        "restaurant": {
            "insights": [
                "건강과 맛의 균형 추구",
                "개인화된 다이닝 경험 선호",
                "지속가능성 고려 증가",
                "소셜미디어 공유 가치 중시"
            ]
        },
        "retail": {
            "insights": [
                "온라인-오프라인 통합 경험 요구",
                "개인 맞춤 상품 큐레이션 선호",
                "투명한 브랜드 스토리 중시",
                "즉시 배송 서비스 기대"
            ]
        },
        "service": {
            "insights": [
                "24/7 접근 가능한 서비스 요구",
                "개인 데이터 기반 맞춤 서비스",
                "투명한 가격 정책 선호",
                "셀프 서비스 옵션 확대"
            ]
        }
    }
    
    for industry, data in data_by_industry.items():
        success = loader.put_item(
            data_type=loader.DATA_TYPE_PREFERENCE_INSIGHTS,
            industry=industry,
            region="GLOBAL",
            data=data,
            ttl_days=90  # 3개월 TTL
        )
        if success:
            print(f"  ✓ {industry}")
        else:
            print(f"  ✗ {industry} (failed)")


def seed_future_projections(loader: MarketAnalysisDynamoDBLoader):
    """미래 선호도 전망 데이터 시딩"""
    print("\n[8/8] Seeding Future Projections...")
    
    data_by_industry = {
        "restaurant": {
            "projection": {
                "timeframe": "2025-2027",
                "keyChanges": [
                    "AI 기반 개인화 서비스 확산",
                    "지속가능성 중시 확대",
                    "경험 중심 소비 증가",
                    "구독 경제 확산"
                ],
                "impactLevel": "높음"
            }
        },
        "retail": {
            "projection": {
                "timeframe": "2025-2027",
                "keyChanges": [
                    "메타버스 쇼핑 경험 확대",
                    "AI 스타일리스트 보편화",
                    "순환 경제 모델 확산",
                    "초개인화 상품 증가"
                ],
                "impactLevel": "매우 높음"
            }
        },
        "service": {
            "projection": {
                "timeframe": "2025-2027",
                "keyChanges": [
                    "AI 에이전트 서비스 확산",
                    "예측 기반 서비스 제공",
                    "구독 모델 다양화",
                    "하이브리드 서비스 표준화"
                ],
                "impactLevel": "높음"
            }
        }
    }
    
    for industry, data in data_by_industry.items():
        success = loader.put_item(
            data_type=loader.DATA_TYPE_FUTURE_PROJECTIONS,
            industry=industry,
            region="GLOBAL",
            data=data,
            ttl_days=180  # 6개월 TTL
        )
        if success:
            print(f"  ✓ {industry}")
        else:
            print(f"  ✗ {industry} (failed)")


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("Market Analysis Data Seeder")
    print("=" * 60)
    
    # 환경 변수 확인
    environment = os.getenv('ENVIRONMENT', 'dev')
    table_name = os.getenv(
        'MARKET_ANALYSIS_TABLE',
        f"ai-branding-chatbot-market-analysis-{environment}"
    )
    
    print(f"\nEnvironment: {environment}")
    print(f"Table Name: {table_name}")
    
    # DynamoDB 로더 초기화
    try:
        loader = MarketAnalysisDynamoDBLoader(table_name=table_name)
        if not loader.table:
            print("\n✗ Failed to initialize DynamoDB table")
            print("  Make sure the table exists and AWS credentials are configured")
            return 1
    except Exception as e:
        print(f"\n✗ Error initializing loader: {str(e)}")
        return 1
    
    # 데이터 시딩 실행
    try:
        seed_behavioral_changes(loader)
        seed_industry_risks(loader)
        seed_benchmark_metrics(loader)
        seed_market_gaps(loader)
        seed_customer_segments(loader)
        seed_tech_opportunities(loader)
        seed_preference_insights(loader)
        seed_future_projections(loader)
        
        print("\n" + "=" * 60)
        print("✓ Data seeding completed successfully")
        print("=" * 60)
        print("\nNext Steps:")
        print("  1. Verify data in DynamoDB console")
        print("  2. Test Market Analyst Agent with new data")
        print("  3. Monitor TTL expiration and update schedule")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
