#!/usr/bin/env python3
"""
ChromaDB에 테스트 데이터 설정
"""

import sys
import os
import requests
import json

# 환경 설정
os.environ['ENVIRONMENT'] = 'local'
os.environ['CHROMA_PERSIST_DIR'] = './data/chroma'
os.environ['CHROMA_COLLECTION_NAME'] = 'business_knowledge'

sys.path.append('src/lambda/shared')

def setup_chroma_data():
    """ChromaDB에 테스트 데이터 추가"""
    print("🗃️ Setting up ChromaDB test data...")
    
    try:
        from knowledge_base import ChromaKnowledgeBase
        
        # ChromaDB 인스턴스 생성
        kb = ChromaKnowledgeBase()
        
        # 테스트 데이터 준비
        test_documents = [
            {
                'id': 'cafe_industry_1',
                'content': '카페 업종은 한국에서 지속적으로 성장하고 있는 업종입니다. 특히 프리미엄 커피 문화의 확산과 함께 개인 카페들이 증가하고 있습니다. 주요 특징으로는 높은 초기 투자비용, 입지의 중요성, 그리고 브랜딩의 중요성이 있습니다.',
                'metadata': {
                    'category': 'industry_analysis',
                    'industry': '카페',
                    'type': 'overview'
                }
            },
            {
                'id': 'cafe_gangnam_1',
                'content': '강남구는 서울의 대표적인 상업지역으로 유동인구가 많고 구매력이 높은 지역입니다. 카페 업종에 있어서는 높은 임대료가 부담이지만, 브랜드 인지도 구축에는 유리한 입지입니다. 직장인과 대학생이 주요 고객층입니다.',
                'metadata': {
                    'category': 'regional_analysis',
                    'region': '강남구',
                    'industry': '카페'
                }
            },
            {
                'id': 'small_business_1',
                'content': '소규모 비즈니스는 유연성과 개인화된 서비스가 장점입니다. 하지만 자본력 부족과 마케팅 한계가 단점으로 작용할 수 있습니다. 성공을 위해서는 차별화된 컨셉과 효율적인 운영이 중요합니다.',
                'metadata': {
                    'category': 'size_analysis',
                    'size': '소규모',
                    'type': 'characteristics'
                }
            },
            {
                'id': 'cafe_market_trends_1',
                'content': '카페 시장의 주요 트렌드는 다음과 같습니다: 1) 프리미엄 원두 선호 증가, 2) 디저트 카페 확산, 3) 배달 서비스 도입, 4) 인스타그래머블한 인테리어 중시, 5) 친환경 제품 사용 증가. 시장 규모는 연평균 7-8% 성장하고 있습니다.',
                'metadata': {
                    'category': 'market_trends',
                    'industry': '카페',
                    'year': '2024'
                }
            },
            {
                'id': 'cafe_competitors_1',
                'content': '카페 업종의 주요 경쟁사는 스타벅스(시장점유율 35%), 이디야커피(18%), 투썸플레이스(12%) 등의 대형 프랜차이즈와 개인 카페들(35%)입니다. 경쟁 요소로는 가격, 품질, 서비스, 입지, 브랜드 이미지가 있습니다.',
                'metadata': {
                    'category': 'competitor_analysis',
                    'industry': '카페',
                    'type': 'market_share'
                }
            },
            {
                'id': 'cafe_opportunities_1',
                'content': '카페 업종의 기회 요소: 1) 홈카페 트렌드로 인한 원두 판매 확대, 2) 구독 서비스 도입 가능성, 3) 지역 커뮤니티 공간으로서의 역할, 4) 온라인 마케팅을 통한 젊은층 공략, 5) 특화 메뉴 개발을 통한 차별화.',
                'metadata': {
                    'category': 'opportunities',
                    'industry': '카페',
                    'type': 'business_opportunities'
                }
            },
            {
                'id': 'digital_marketing_1',
                'content': '소규모 카페의 디지털 마케팅 전략: SNS 마케팅이 핵심입니다. 인스타그램과 네이버 블로그를 활용한 시각적 콘텐츠 마케팅, 구글 마이비즈니스 등록, 배달앱 입점, 고객 리뷰 관리가 중요합니다. 예산 대비 효과가 높은 마케팅 방법입니다.',
                'metadata': {
                    'category': 'marketing_strategy',
                    'size': '소규모',
                    'type': 'digital_marketing'
                }
            }
        ]
        
        # 데이터 추가
        print(f"   Adding {len(test_documents)} documents to ChromaDB...")
        kb.add_documents(test_documents)
        
        print("✓ ChromaDB test data setup completed")
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chroma_connection():
    """ChromaDB 연결 테스트"""
    print("🔗 Testing ChromaDB connection...")
    
    try:
        # ChromaDB 클라이언트로 직접 연결 테스트
        import chromadb
        
        # HTTP 클라이언트로 연결
        client = chromadb.HttpClient(host='localhost', port=8001)
        
        # 컬렉션 목록 조회로 연결 테스트
        collections = client.list_collections()
        print(f"✓ ChromaDB server is running ({len(collections)} collections)")
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB connection failed: {e}")
        return False

def test_data_retrieval():
    """데이터 조회 테스트"""
    print("🔍 Testing data retrieval...")
    
    try:
        from knowledge_base import ChromaKnowledgeBase
        
        kb = ChromaKnowledgeBase()
        
        # 검색 테스트
        test_queries = [
            "카페 업종 특성",
            "강남구 지역 분석",
            "소규모 비즈니스",
            "시장 트렌드",
            "경쟁사 분석"
        ]
        
        for query in test_queries:
            results = kb.search(query, top_k=2)
            print(f"   Query: '{query}' → {len(results)} results")
            if results:
                print(f"      Best match: {results[0]['content'][:50]}...")
        
        # 비즈니스 인사이트 테스트
        insights = kb.get_business_insights("카페", "강남구", "소규모")
        print(f"   Business insights: {len(insights['insights'])} items")
        
        # 시장 트렌드 테스트
        trends = kb.get_market_trends("카페")
        print(f"   Market trends: {len(trends['trends'])} items")
        
        print("✓ Data retrieval test completed")
        return True
        
    except Exception as e:
        print(f"❌ Data retrieval test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 실행"""
    print("🚀 ChromaDB Test Data Setup")
    print("=" * 40)
    
    # 1. 연결 테스트
    if not test_chroma_connection():
        print("❌ ChromaDB is not running. Start with: docker-compose -f docker-compose.local.yml up -d")
        return False
    
    # 2. 데이터 설정
    if not setup_chroma_data():
        return False
    
    # 3. 데이터 조회 테스트
    if not test_data_retrieval():
        return False
    
    print("\n🎉 ChromaDB test data setup completed successfully!")
    print("Now you can run the agent tests with real data.")
    
    return True

if __name__ == "__main__":
    main()