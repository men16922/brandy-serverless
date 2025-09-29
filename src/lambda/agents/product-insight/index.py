"""
Product Insight Agent - Business Analysis Implementation
Provides comprehensive business analysis based on industry, region, and size
"""

import json
import sys
import os
import time
from typing import Dict, Any, List, Tuple
from datetime import datetime

# Add shared modules to path
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

try:
    from base_agent import BaseAgent
    from models import AgentType, AnalysisResult, BusinessInfo
    from knowledge_base import get_knowledge_base
except ImportError:
    # For testing purposes, create mock implementations
    from datetime import datetime
    from typing import Dict, Any, List
    from enum import Enum
    
    class AgentType(Enum):
        PRODUCT_INSIGHT = "product_insight"
    
    class AnalysisResult:
        def __init__(self, summary: str, score: float, insights: List[str], 
                     market_trends: List[str], recommendations: List[str]):
            self.summary = summary
            self.score = score
            self.insights = insights
            self.market_trends = market_trends
            self.recommendations = recommendations
            self.generated_at = datetime.utcnow().isoformat()
        
        def to_dict(self):
            return {
                'summary': self.summary,
                'score': self.score,
                'insights': self.insights,
                'market_trends': self.market_trends,
                'recommendations': self.recommendations,
                'generated_at': self.generated_at
            }
    
    class BusinessInfo:
        def __init__(self, industry: str, region: str, size: str, **kwargs):
            self.industry = industry
            self.region = region
            self.size = size
        
        def validate(self):
            return bool(self.industry and self.region and self.size)
    
    class BaseAgent:
        def __init__(self, agent_type):
            self.agent_type = agent_type
            self.agent_name = agent_type.value
            self.logger = self._create_mock_logger()
        
        def _create_mock_logger(self):
            import logging
            logger = logging.getLogger(self.agent_name)
            logger.setLevel(logging.INFO)
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                logger.addHandler(handler)
            return logger
        
        def start_execution(self, session_id: str, tool: str):
            self.current_session_id = session_id
            self.current_tool = tool
            self.execution_start_time = time.time()
        
        def end_execution(self, status: str = "success", error_message: str = None, result: Any = None):
            if hasattr(self, 'execution_start_time'):
                latency_ms = int((time.time() - self.execution_start_time) * 1000)
                return latency_ms
            return 0
        
        def update_session_data(self, session_id: str, updates: Dict[str, Any]):
            # Mock implementation
            return True
        
        def create_lambda_response(self, status_code: int, body: Any, headers=None):
            return {
                'statusCode': status_code,
                'headers': headers or {'Content-Type': 'application/json'},
                'body': json.dumps(body, ensure_ascii=False)
            }
        
        def handle_error(self, error: Exception, context: str = ""):
            return {
                'error': True,
                'message': str(error),
                'agent': self.agent_name,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        def lambda_handler(self, event: Dict[str, Any], context: Any):
            return self.execute(event, context)
    
    def get_knowledge_base():
        class MockKnowledgeBase:
            def search(self, query: str, top_k: int = 5):
                return []
        return MockKnowledgeBase()


class ProductInsightAgent(BaseAgent):
    """Product Insight Agent for business analysis"""
    
    def __init__(self):
        super().__init__(AgentType.PRODUCT_INSIGHT)
        self.knowledge_base = get_knowledge_base()
        
        # Load industry analysis data
        self.industry_data = self._load_industry_analysis_data()
        self.region_data = self._load_region_analysis_data()
        self.size_data = self._load_size_analysis_data()
    
    def _load_industry_analysis_data(self) -> Dict[str, Dict[str, Any]]:
        """Load 16 industry-specific analysis data"""
        return {
            "restaurant": {
                "characteristics": [
                    "높은 고객 회전율과 지역 밀착형 비즈니스",
                    "식자재 비용과 인건비가 주요 운영비용",
                    "계절성과 트렌드에 민감한 업종"
                ],
                "success_factors": [
                    "맛과 서비스 품질의 일관성",
                    "효율적인 재고 관리와 원가 절감",
                    "고객 재방문율 향상 전략"
                ],
                "market_trends": [
                    "건강식품과 비건 메뉴 수요 증가",
                    "배달 서비스 플랫폼 의존도 상승",
                    "개인화된 고객 경험 중시"
                ],
                "risk_factors": [
                    "높은 창업 실패율 (3년 내 70%)",
                    "식자재 가격 변동성",
                    "코로나19 등 외부 환경 변화에 취약"
                ],
                "base_score": 75,
                "growth_potential": "MEDIUM",
                "competition_level": "HIGH"
            },
            "retail": {
                "characteristics": [
                    "상품 진열과 고객 접점이 핵심",
                    "재고 관리와 매출 예측이 중요",
                    "온라인과 오프라인 채널 통합 필요"
                ],
                "success_factors": [
                    "상품 큐레이션과 진열 전략",
                    "고객 데이터 기반 맞춤 서비스",
                    "효율적인 공급망 관리"
                ],
                "market_trends": [
                    "O2O(Online to Offline) 서비스 확산",
                    "개인 맞춤형 상품 추천 시스템",
                    "친환경 제품에 대한 관심 증가"
                ],
                "risk_factors": [
                    "온라인 쇼핑몰과의 경쟁 심화",
                    "임대료 상승 압박",
                    "소비 패턴 변화에 대한 적응 필요"
                ],
                "base_score": 70,
                "growth_potential": "MEDIUM",
                "competition_level": "HIGH"
            },
            "service": {
                "characteristics": [
                    "무형 서비스 제공으로 품질 표준화 어려움",
                    "고객 만족도가 직접적인 매출 영향",
                    "전문성과 신뢰도가 핵심 경쟁력"
                ],
                "success_factors": [
                    "서비스 품질의 표준화와 일관성",
                    "고객 관계 관리 시스템 구축",
                    "전문 인력 확보와 교육"
                ],
                "market_trends": [
                    "디지털 플랫폼을 통한 서비스 제공",
                    "구독 기반 서비스 모델 확산",
                    "AI와 자동화 기술 도입"
                ],
                "risk_factors": [
                    "서비스 품질 편차로 인한 평판 리스크",
                    "숙련된 인력 확보의 어려움",
                    "경기 변동에 따른 수요 감소"
                ],
                "base_score": 78,
                "growth_potential": "HIGH",
                "competition_level": "MEDIUM"
            },
            "healthcare": {
                "characteristics": [
                    "높은 전문성과 자격 요건 필요",
                    "규제가 엄격하고 안전성이 최우선",
                    "지속적인 교육과 기술 업데이트 필수"
                ],
                "success_factors": [
                    "의료진의 전문성과 경험",
                    "최신 의료 장비와 시설",
                    "환자 중심의 서비스 제공"
                ],
                "market_trends": [
                    "디지털 헬스케어 기술 도입",
                    "예방 중심의 건강 관리",
                    "개인 맞춤형 치료 서비스"
                ],
                "risk_factors": [
                    "의료사고에 따른 법적 책임",
                    "높은 초기 투자 비용",
                    "의료진 수급 불균형"
                ],
                "base_score": 85,
                "growth_potential": "HIGH",
                "competition_level": "LOW"
            },
            "education": {
                "characteristics": [
                    "장기적 관점의 성과 측정",
                    "학습자 개별 특성 고려 필요",
                    "교육 콘텐츠와 방법론이 핵심"
                ],
                "success_factors": [
                    "차별화된 교육 프로그램",
                    "우수한 강사진 확보",
                    "학습 성과 추적 시스템"
                ],
                "market_trends": [
                    "온라인 교육 플랫폼 확산",
                    "개인 맞춤형 학습 경험",
                    "실무 중심의 교육 과정"
                ],
                "risk_factors": [
                    "학령인구 감소",
                    "온라인 교육과의 경쟁",
                    "교육 정책 변화에 따른 영향"
                ],
                "base_score": 72,
                "growth_potential": "MEDIUM",
                "competition_level": "MEDIUM"
            },
            "technology": {
                "characteristics": [
                    "빠른 기술 변화와 혁신 필요",
                    "높은 성장 잠재력과 확장성",
                    "전문 인력과 R&D 투자 중요"
                ],
                "success_factors": [
                    "기술 혁신과 특허 확보",
                    "우수한 개발 인력 확보",
                    "시장 진입 타이밍"
                ],
                "market_trends": [
                    "AI와 머신러닝 기술 확산",
                    "클라우드 서비스 전환",
                    "사이버 보안 중요성 증대"
                ],
                "risk_factors": [
                    "기술 변화 속도에 따른 도태 위험",
                    "높은 초기 개발 비용",
                    "인력 확보 경쟁 심화"
                ],
                "base_score": 82,
                "growth_potential": "HIGH",
                "competition_level": "HIGH"
            },
            "manufacturing": {
                "characteristics": [
                    "생산 효율성과 품질 관리가 핵심",
                    "높은 초기 설비 투자 필요",
                    "공급망 관리와 원자재 조달 중요"
                ],
                "success_factors": [
                    "생산 공정 최적화",
                    "품질 관리 시스템 구축",
                    "안정적인 공급망 확보"
                ],
                "market_trends": [
                    "스마트 팩토리와 자동화",
                    "친환경 생산 공정",
                    "맞춤형 제품 생산"
                ],
                "risk_factors": [
                    "원자재 가격 변동",
                    "환경 규제 강화",
                    "인력 부족과 고령화"
                ],
                "base_score": 76,
                "growth_potential": "MEDIUM",
                "competition_level": "MEDIUM"
            },
            "construction": {
                "characteristics": [
                    "프로젝트 기반의 일회성 사업",
                    "안전 관리와 품질 보증 중요",
                    "계절성과 경기 변동에 민감"
                ],
                "success_factors": [
                    "프로젝트 관리 역량",
                    "안전 사고 예방 시스템",
                    "협력업체 네트워크"
                ],
                "market_trends": [
                    "친환경 건축 기술",
                    "모듈러 건축과 프리팹",
                    "BIM과 디지털 설계"
                ],
                "risk_factors": [
                    "안전사고 발생 위험",
                    "건설 경기 변동",
                    "인력 수급 불안정"
                ],
                "base_score": 68,
                "growth_potential": "LOW",
                "competition_level": "HIGH"
            },
            "finance": {
                "characteristics": [
                    "높은 신뢰성과 보안 요구",
                    "복잡한 규제와 컴플라이언스",
                    "디지털 전환 가속화"
                ],
                "success_factors": [
                    "리스크 관리 시스템",
                    "고객 신뢰도 구축",
                    "디지털 서비스 혁신"
                ],
                "market_trends": [
                    "핀테크와 디지털 뱅킹",
                    "블록체인과 암호화폐",
                    "개인화된 금융 서비스"
                ],
                "risk_factors": [
                    "금융 규제 변화",
                    "사이버 보안 위협",
                    "핀테크 업체와의 경쟁"
                ],
                "base_score": 80,
                "growth_potential": "MEDIUM",
                "competition_level": "HIGH"
            },
            "beauty": {
                "characteristics": [
                    "트렌드와 개인 취향에 민감",
                    "브랜드 이미지와 마케팅 중요",
                    "고객 경험과 서비스 품질 핵심"
                ],
                "success_factors": [
                    "트렌드 대응력과 상품 기획",
                    "고객 맞춤 서비스 제공",
                    "브랜드 차별화 전략"
                ],
                "market_trends": [
                    "K-뷰티 글로벌 확산",
                    "개인 맞춤형 화장품",
                    "친환경 뷰티 제품"
                ],
                "risk_factors": [
                    "트렌드 변화 속도",
                    "온라인 채널과의 경쟁",
                    "원자재 가격 상승"
                ],
                "base_score": 74,
                "growth_potential": "HIGH",
                "competition_level": "HIGH"
            },
            "fitness": {
                "characteristics": [
                    "건강과 웰빙 트렌드 수혜",
                    "개인 맞춤형 서비스 중요",
                    "시설과 장비 투자 필요"
                ],
                "success_factors": [
                    "전문 트레이너 확보",
                    "차별화된 프로그램",
                    "회원 관리 시스템"
                ],
                "market_trends": [
                    "홈트레이닝과 온라인 피트니스",
                    "웨어러블 기기 연동",
                    "기능성 운동과 재활"
                ],
                "risk_factors": [
                    "코로나19 등 감염병 영향",
                    "온라인 서비스와의 경쟁",
                    "회원 이탈률 관리"
                ],
                "base_score": 77,
                "growth_potential": "HIGH",
                "competition_level": "MEDIUM"
            },
            "entertainment": {
                "characteristics": [
                    "창의성과 콘텐츠가 핵심",
                    "트렌드와 대중 취향에 민감",
                    "높은 수익성과 리스크 공존"
                ],
                "success_factors": [
                    "독창적인 콘텐츠 기획",
                    "타겟 고객층 분석",
                    "마케팅과 홍보 전략"
                ],
                "market_trends": [
                    "OTT 플랫폼 확산",
                    "메타버스와 VR 콘텐츠",
                    "개인 방송과 크리에이터"
                ],
                "risk_factors": [
                    "콘텐츠 성공 불확실성",
                    "저작권과 법적 이슈",
                    "플랫폼 의존도"
                ],
                "base_score": 71,
                "growth_potential": "HIGH",
                "competition_level": "HIGH"
            },
            "automotive": {
                "characteristics": [
                    "기술 집약적 산업",
                    "높은 초기 투자와 장기 회수",
                    "안전성과 품질이 최우선"
                ],
                "success_factors": [
                    "기술 혁신과 R&D",
                    "품질 관리 시스템",
                    "고객 서비스 네트워크"
                ],
                "market_trends": [
                    "전기차와 자율주행",
                    "모빌리티 서비스",
                    "친환경 기술"
                ],
                "risk_factors": [
                    "기술 변화 속도",
                    "높은 진입 장벽",
                    "환경 규제 강화"
                ],
                "base_score": 79,
                "growth_potential": "MEDIUM",
                "competition_level": "HIGH"
            },
            "agriculture": {
                "characteristics": [
                    "계절성과 기후 의존도 높음",
                    "전통적 방식과 기술 혁신 공존",
                    "식품 안전과 품질 중요"
                ],
                "success_factors": [
                    "생산성 향상 기술",
                    "품질 관리와 브랜딩",
                    "유통 채널 다양화"
                ],
                "market_trends": [
                    "스마트팜과 정밀농업",
                    "친환경 유기농",
                    "직거래와 온라인 판매"
                ],
                "risk_factors": [
                    "기후 변화 영향",
                    "농산물 가격 변동",
                    "고령화와 인력 부족"
                ],
                "base_score": 65,
                "growth_potential": "MEDIUM",
                "competition_level": "LOW"
            },
            "logistics": {
                "characteristics": [
                    "효율성과 정시성이 핵심",
                    "네트워크와 인프라 중요",
                    "기술 혁신으로 경쟁력 확보"
                ],
                "success_factors": [
                    "배송 네트워크 최적화",
                    "IT 시스템과 자동화",
                    "고객 서비스 품질"
                ],
                "market_trends": [
                    "이커머스 배송 수요 증가",
                    "드론과 자율주행 배송",
                    "친환경 물류"
                ],
                "risk_factors": [
                    "유가 변동과 운송비",
                    "인력 부족",
                    "교통 체증과 인프라"
                ],
                "base_score": 73,
                "growth_potential": "HIGH",
                "competition_level": "MEDIUM"
            },
            "other": {
                "characteristics": [
                    "다양한 업종의 일반적 특성",
                    "시장 상황에 따른 변동성",
                    "차별화 전략 필요"
                ],
                "success_factors": [
                    "시장 분석과 포지셔닝",
                    "고객 니즈 파악",
                    "운영 효율성 개선"
                ],
                "market_trends": [
                    "디지털 전환",
                    "고객 경험 중시",
                    "지속가능성"
                ],
                "risk_factors": [
                    "시장 경쟁 심화",
                    "경기 변동 영향",
                    "규제 변화"
                ],
                "base_score": 70,
                "growth_potential": "MEDIUM",
                "competition_level": "MEDIUM"
            }
        }
    
    def _load_region_analysis_data(self) -> Dict[str, Dict[str, Any]]:
        """Load region-specific market environment analysis data"""
        return {
            "seoul": {
                "market_size": "LARGE",
                "competition_level": "VERY_HIGH",
                "consumer_power": "HIGH",
                "rent_cost": "VERY_HIGH",
                "characteristics": [
                    "국내 최대 소비시장으로 높은 구매력",
                    "치열한 경쟁과 높은 임대료",
                    "트렌드 선도 지역으로 혁신 필요"
                ],
                "advantages": [
                    "대규모 고객층과 높은 접근성",
                    "다양한 비즈니스 기회",
                    "우수한 인프라와 교통망"
                ],
                "challenges": [
                    "높은 운영비용과 임대료",
                    "치열한 경쟁 환경",
                    "빠른 트렌드 변화 대응 필요"
                ],
                "score_modifier": 10
            },
            "busan": {
                "market_size": "LARGE",
                "competition_level": "HIGH",
                "consumer_power": "MEDIUM_HIGH",
                "rent_cost": "MEDIUM",
                "characteristics": [
                    "제2의 도시로 안정적인 시장 규모",
                    "항만도시 특성과 관광업 발달",
                    "서울 대비 상대적으로 낮은 진입비용"
                ],
                "advantages": [
                    "적정한 임대료와 운영비용",
                    "관광객 유입으로 인한 수요",
                    "지역 특색을 활용한 차별화 가능"
                ],
                "challenges": [
                    "서울 대비 상대적으로 작은 시장",
                    "지역 경제 의존도",
                    "젊은 인구 유출"
                ],
                "score_modifier": 5
            },
            "daegu": {
                "market_size": "MEDIUM",
                "competition_level": "MEDIUM",
                "consumer_power": "MEDIUM",
                "rent_cost": "LOW_MEDIUM",
                "characteristics": [
                    "섬유산업 중심의 전통적 상업도시",
                    "보수적 소비성향과 안정적 시장",
                    "의료산업과 교육기관 발달"
                ],
                "advantages": [
                    "안정적인 지역 경제",
                    "합리적인 운영비용",
                    "충성도 높은 고객층"
                ],
                "challenges": [
                    "보수적 소비 패턴",
                    "신규 트렌드 수용 속도 느림",
                    "젊은 층 인구 감소"
                ],
                "score_modifier": 0
            },
            "incheon": {
                "market_size": "MEDIUM_LARGE",
                "competition_level": "MEDIUM_HIGH",
                "consumer_power": "MEDIUM_HIGH",
                "rent_cost": "MEDIUM_HIGH",
                "characteristics": [
                    "인천공항과 항만 중심의 물류도시",
                    "서울 근접성으로 베드타운 역할",
                    "신도시 개발로 인한 인구 증가"
                ],
                "advantages": [
                    "지속적인 인구 유입",
                    "물류와 교통의 요충지",
                    "신규 상권 개발 기회"
                ],
                "challenges": [
                    "서울 의존적 소비 패턴",
                    "상권 분산으로 인한 집객 어려움",
                    "교통비 부담"
                ],
                "score_modifier": 3
            },
            "gwangju": {
                "market_size": "MEDIUM",
                "competition_level": "MEDIUM",
                "consumer_power": "MEDIUM",
                "rent_cost": "LOW_MEDIUM",
                "characteristics": [
                    "호남권 중심도시로 문화예술 발달",
                    "대학가 중심의 젊은 소비층",
                    "전통시장과 현대적 상권 공존"
                ],
                "advantages": [
                    "문화예술 콘텐츠 활용 가능",
                    "대학생 고객층 확보",
                    "지역 특산품과 연계 기회"
                ],
                "challenges": [
                    "상대적으로 작은 시장 규모",
                    "지역 경제 성장 한계",
                    "수도권 대비 구매력 차이"
                ],
                "score_modifier": -2
            },
            "daejeon": {
                "market_size": "MEDIUM",
                "competition_level": "MEDIUM",
                "consumer_power": "MEDIUM_HIGH",
                "rent_cost": "MEDIUM",
                "characteristics": [
                    "과학기술 중심도시로 고학력층 집중",
                    "연구기관과 대학 밀집 지역",
                    "혁신적 소비성향과 기술 수용도 높음"
                ],
                "advantages": [
                    "고학력 고소득층 고객",
                    "기술 혁신에 개방적",
                    "정부기관 밀집으로 안정적 수요"
                ],
                "challenges": [
                    "특화된 고객층으로 제한적 시장",
                    "보수적 관료 문화",
                    "주말 인구 감소"
                ],
                "score_modifier": 2
            },
            "ulsan": {
                "market_size": "MEDIUM",
                "competition_level": "LOW_MEDIUM",
                "consumer_power": "HIGH",
                "rent_cost": "MEDIUM",
                "characteristics": [
                    "중화학공업 중심의 산업도시",
                    "높은 소득수준과 구매력",
                    "남성 중심의 소비 패턴"
                ],
                "advantages": [
                    "높은 평균 소득과 구매력",
                    "상대적으로 낮은 경쟁",
                    "산업단지 근로자 대상 시장"
                ],
                "challenges": [
                    "단조로운 고객층 구성",
                    "경기 변동에 민감",
                    "문화 콘텐츠 부족"
                ],
                "score_modifier": 1
            },
            "gyeonggi": {
                "market_size": "VERY_LARGE",
                "competition_level": "HIGH",
                "consumer_power": "HIGH",
                "rent_cost": "HIGH",
                "characteristics": [
                    "수도권 최대 인구와 다양한 신도시",
                    "서울 접근성과 독립적 상권 형성",
                    "젊은 가족층 중심의 소비 시장"
                ],
                "advantages": [
                    "대규모 인구와 지속적 유입",
                    "다양한 연령층과 소득수준",
                    "신도시 개발로 인한 성장 잠재력"
                ],
                "challenges": [
                    "지역별 편차가 큰 시장",
                    "서울 상권과의 경쟁",
                    "교통 접근성 차이"
                ],
                "score_modifier": 8
            },
            "gangwon": {
                "market_size": "SMALL_MEDIUM",
                "competition_level": "LOW",
                "consumer_power": "LOW_MEDIUM",
                "rent_cost": "LOW",
                "characteristics": [
                    "관광과 레저 중심의 지역 경제",
                    "계절성이 강한 소비 패턴",
                    "자연환경과 연계한 비즈니스 기회"
                ],
                "advantages": [
                    "낮은 진입비용과 임대료",
                    "관광객 대상 시장",
                    "자연환경 활용 가능"
                ],
                "challenges": [
                    "계절적 수요 변동",
                    "상주인구 부족",
                    "접근성과 물류 한계"
                ],
                "score_modifier": -5
            },
            "chungbuk": {
                "market_size": "SMALL_MEDIUM",
                "competition_level": "LOW_MEDIUM",
                "consumer_power": "MEDIUM",
                "rent_cost": "LOW",
                "characteristics": [
                    "농업과 제조업 중심의 안정적 경제",
                    "보수적이고 실용적인 소비성향",
                    "수도권 접근성 양호"
                ],
                "advantages": [
                    "안정적인 지역 경제",
                    "낮은 운영비용",
                    "수도권 물류 접근성"
                ],
                "challenges": [
                    "보수적 소비 패턴",
                    "인구 고령화",
                    "제한적 시장 규모"
                ],
                "score_modifier": -3
            },
            "chungnam": {
                "market_size": "MEDIUM",
                "competition_level": "MEDIUM",
                "consumer_power": "MEDIUM",
                "rent_cost": "LOW_MEDIUM",
                "characteristics": [
                    "천안·아산 등 산업도시 발달",
                    "수도권 근접성과 교통 요충지",
                    "제조업과 물류업 중심"
                ],
                "advantages": [
                    "산업단지 근로자 시장",
                    "교통 접근성 우수",
                    "합리적 운영비용"
                ],
                "challenges": [
                    "지역별 발전 격차",
                    "수도권 의존적 경제구조",
                    "농촌 지역 인구 감소"
                ],
                "score_modifier": -1
            },
            "jeonbuk": {
                "market_size": "SMALL_MEDIUM",
                "competition_level": "LOW_MEDIUM",
                "consumer_power": "LOW_MEDIUM",
                "rent_cost": "LOW",
                "characteristics": [
                    "농업 중심의 전통적 지역 경제",
                    "전주 한옥마을 등 관광자원 보유",
                    "보수적이고 전통적인 소비문화"
                ],
                "advantages": [
                    "전통문화와 관광 연계",
                    "낮은 진입비용",
                    "지역 특산품 활용"
                ],
                "challenges": [
                    "인구 감소와 고령화",
                    "경제 성장 둔화",
                    "젊은 층 유출"
                ],
                "score_modifier": -4
            },
            "jeonnam": {
                "market_size": "SMALL_MEDIUM",
                "competition_level": "LOW",
                "consumer_power": "LOW_MEDIUM",
                "rent_cost": "LOW",
                "characteristics": [
                    "농수산업과 관광업 중심",
                    "순천만, 여수 등 관광지 보유",
                    "느린 생활과 웰빙 트렌드"
                ],
                "advantages": [
                    "자연환경과 관광자원",
                    "매우 낮은 운영비용",
                    "웰빙 라이프스타일 수요"
                ],
                "challenges": [
                    "급속한 인구 감소",
                    "제한적 소비시장",
                    "접근성과 물류 한계"
                ],
                "score_modifier": -6
            },
            "gyeongbuk": {
                "market_size": "MEDIUM",
                "competition_level": "LOW_MEDIUM",
                "consumer_power": "MEDIUM",
                "rent_cost": "LOW",
                "characteristics": [
                    "포항제철 등 중공업과 농업 공존",
                    "경주 등 역사문화 관광지",
                    "보수적이고 안정적인 시장"
                ],
                "advantages": [
                    "산업도시 고소득층",
                    "역사문화 관광 연계",
                    "안정적 지역 경제"
                ],
                "challenges": [
                    "지역별 편차 큰 시장",
                    "고령화 진행",
                    "신규 트렌드 수용 느림"
                ],
                "score_modifier": -2
            },
            "gyeongnam": {
                "market_size": "MEDIUM_LARGE",
                "competition_level": "MEDIUM",
                "consumer_power": "MEDIUM_HIGH",
                "rent_cost": "MEDIUM",
                "characteristics": [
                    "창원·김해 등 제조업 중심지",
                    "부산 인접으로 상권 연계성",
                    "젊은 근로자층 집중"
                ],
                "advantages": [
                    "제조업 근로자 시장",
                    "부산권 연계 효과",
                    "상대적 높은 소득수준"
                ],
                "challenges": [
                    "부산 상권 의존성",
                    "제조업 경기 민감",
                    "지역 내 경쟁 심화"
                ],
                "score_modifier": 1
            },
            "jeju": {
                "market_size": "SMALL",
                "competition_level": "MEDIUM_HIGH",
                "consumer_power": "MEDIUM_HIGH",
                "rent_cost": "HIGH",
                "characteristics": [
                    "관광업 중심의 특수 경제구조",
                    "높은 관광객 유입과 계절성",
                    "독특한 지역 문화와 특산품"
                ],
                "advantages": [
                    "연간 1,500만 관광객 시장",
                    "프리미엄 상품 수용도 높음",
                    "독특한 지역 특색 활용"
                ],
                "challenges": [
                    "극심한 계절적 변동",
                    "높은 임대료와 인건비",
                    "물류비용 부담"
                ],
                "score_modifier": -1
            }
        }
    
    def _load_size_analysis_data(self) -> Dict[str, Dict[str, Any]]:
        """Load business size-specific strategy data"""
        return {
            "small": {
                "characteristics": [
                    "소규모 자본으로 시작 가능",
                    "빠른 의사결정과 유연한 운영",
                    "개인적 관계와 서비스 중심"
                ],
                "advantages": [
                    "낮은 초기 투자비용",
                    "신속한 시장 대응",
                    "개인화된 고객 서비스"
                ],
                "challenges": [
                    "제한적인 자원과 인력",
                    "마케팅 예산 부족",
                    "규모의 경제 한계"
                ],
                "strategies": [
                    "틈새시장 공략과 차별화",
                    "디지털 마케팅 활용",
                    "고객 충성도 극대화"
                ],
                "investment_range": "1천만원 - 5천만원",
                "employee_range": "1-5명",
                "score_modifier": -5,
                "risk_level": "MEDIUM_HIGH"
            },
            "medium": {
                "characteristics": [
                    "적정 규모의 안정적 운영",
                    "체계적 관리와 전문화",
                    "지역 시장에서의 인지도"
                ],
                "advantages": [
                    "안정적인 현금흐름",
                    "전문 인력 확보 가능",
                    "브랜드 구축 기회"
                ],
                "challenges": [
                    "성장 정체 위험",
                    "대기업과의 경쟁",
                    "관리 복잡성 증가"
                ],
                "strategies": [
                    "핵심 역량 강화",
                    "시스템화와 표준화",
                    "전략적 제휴 추진"
                ],
                "investment_range": "5천만원 - 3억원",
                "employee_range": "6-30명",
                "score_modifier": 0,
                "risk_level": "MEDIUM"
            },
            "large": {
                "characteristics": [
                    "대규모 자본과 인프라",
                    "시장 지배력과 브랜드 파워",
                    "복합적 사업 포트폴리오"
                ],
                "advantages": [
                    "규모의 경제 실현",
                    "강력한 브랜드 파워",
                    "다양한 사업 기회"
                ],
                "challenges": [
                    "높은 고정비용",
                    "조직 관리 복잡성",
                    "시장 변화 대응 속도"
                ],
                "strategies": [
                    "시장 점유율 확대",
                    "혁신과 R&D 투자",
                    "글로벌 진출 추진"
                ],
                "investment_range": "3억원 이상",
                "employee_range": "30명 이상",
                "score_modifier": 5,
                "risk_level": "LOW_MEDIUM"
            }
        }
    
    def _calculate_comprehensive_score(self, industry: str, region: str, size: str) -> float:
        """Calculate comprehensive business score (0-100)"""
        # Base score from industry
        industry_data = self.industry_data.get(industry, self.industry_data["other"])
        base_score = industry_data["base_score"]
        
        # Region modifier
        region_data = self.region_data.get(region, self.region_data["seoul"])
        region_modifier = region_data["score_modifier"]
        
        # Size modifier
        size_data = self.size_data.get(size, self.size_data["medium"])
        size_modifier = size_data["score_modifier"]
        
        # Calculate final score
        final_score = base_score + region_modifier + size_modifier
        
        # Ensure score is within 0-100 range
        final_score = max(0, min(100, final_score))
        
        return round(final_score, 1)
    
    def _generate_key_insights(self, industry: str, region: str, size: str) -> List[str]:
        """Generate 3 key business insights"""
        industry_data = self.industry_data.get(industry, self.industry_data["other"])
        region_data = self.region_data.get(region, self.region_data["seoul"])
        size_data = self.size_data.get(size, self.size_data["medium"])
        
        insights = []
        
        # Industry insight
        growth_potential = industry_data["growth_potential"]
        competition = industry_data["competition_level"]
        
        if growth_potential == "HIGH" and competition == "HIGH":
            insights.append(f"{industry} 업종은 높은 성장 잠재력을 가지고 있지만 치열한 경쟁 환경에서 차별화 전략이 필수입니다.")
        elif growth_potential == "HIGH" and competition in ["MEDIUM", "LOW"]:
            insights.append(f"{industry} 업종은 높은 성장 잠재력과 상대적으로 낮은 경쟁으로 진입하기 좋은 시기입니다.")
        elif growth_potential == "MEDIUM":
            insights.append(f"{industry} 업종은 안정적인 성장이 예상되며, 꾸준한 운영 전략이 중요합니다.")
        else:
            insights.append(f"{industry} 업종은 성숙한 시장으로 혁신적인 접근이 필요합니다.")
        
        # Region insight
        market_size = region_data["market_size"]
        consumer_power = region_data["consumer_power"]
        
        if market_size in ["LARGE", "VERY_LARGE"] and consumer_power == "HIGH":
            insights.append(f"{region} 지역은 대규모 시장과 높은 구매력을 가진 최적의 사업 환경입니다.")
        elif market_size in ["MEDIUM", "MEDIUM_LARGE"]:
            insights.append(f"{region} 지역은 적정 규모의 안정적인 시장으로 지역 특성을 활용한 전략이 효과적입니다.")
        else:
            insights.append(f"{region} 지역은 틈새시장 공략과 지역 밀착형 서비스로 경쟁력을 확보해야 합니다.")
        
        # Size insight
        risk_level = size_data["risk_level"]
        investment_range = size_data["investment_range"]
        
        if size == "small":
            insights.append(f"{size} 규모는 {investment_range}의 투자로 시작 가능하며, 빠른 시장 진입과 고객 밀착 서비스가 핵심입니다.")
        elif size == "medium":
            insights.append(f"{size} 규모는 {investment_range}의 투자로 안정적 운영이 가능하며, 체계적 관리와 브랜드 구축이 중요합니다.")
        else:
            insights.append(f"{size} 규모는 {investment_range}의 대규모 투자로 시장 지배력 확보와 규모의 경제 실현이 가능합니다.")
        
        return insights
    
    def execute(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Execute Product Insight Agent business analysis"""
        try:
            # Extract request data
            body = event.get('body', '{}')
            if isinstance(body, str):
                try:
                    body_data = json.loads(body)
                except:
                    body_data = {}
            else:
                body_data = body or {}
            
            session_id = body_data.get('sessionId')
            business_info_data = body_data.get('businessInfo', {})
            
            if not session_id:
                return self.create_lambda_response(400, {
                    'error': 'Session ID is required'
                })
            
            # Start execution tracking
            self.start_execution(session_id, "business_analysis")
            
            # Validate business info
            try:
                business_info = BusinessInfo(**business_info_data)
                if not business_info.validate():
                    raise ValueError("Invalid business information")
            except Exception as e:
                self.end_execution("error", f"Invalid business info: {str(e)}")
                return self.create_lambda_response(400, {
                    'error': 'Invalid business information',
                    'details': str(e)
                })
            
            # Perform business analysis
            industry = business_info.industry.lower()
            region = business_info.region.lower()
            size = business_info.size.lower()
            
            # Calculate comprehensive score
            score = self._calculate_comprehensive_score(industry, region, size)
            
            # Generate key insights
            insights = self._generate_key_insights(industry, region, size)
            
            # Get industry and region data for additional context
            industry_data = self.industry_data.get(industry, self.industry_data["other"])
            region_data = self.region_data.get(region, self.region_data["seoul"])
            size_data = self.size_data.get(size, self.size_data["medium"])
            
            # Create analysis result
            analysis_result = AnalysisResult(
                summary=f"{region} 지역의 {size} 규모 {industry} 사업 분석 결과, 종합 점수 {score}점으로 평가됩니다.",
                score=score,
                insights=insights,
                market_trends=industry_data["market_trends"],
                recommendations=industry_data["success_factors"][:3],  # Top 3 success factors as recommendations
            )
            
            # Update session with analysis result
            session_updates = {
                'analysisResult': analysis_result.to_dict() if hasattr(analysis_result, 'to_dict') else analysis_result.__dict__,
                'currentStep': 2  # Move to naming step
            }
            
            if not self.update_session_data(session_id, session_updates):
                self.logger.warning("Failed to update session data")
            
            # Prepare response
            response_data = {
                'sessionId': session_id,
                'analysis': {
                    'summary': analysis_result.summary,
                    'score': analysis_result.score,
                    'insights': analysis_result.insights,
                    'market_trends': analysis_result.market_trends,
                    'recommendations': analysis_result.recommendations,
                    'industry_characteristics': industry_data["characteristics"],
                    'region_advantages': region_data["advantages"],
                    'size_strategies': size_data["strategies"],
                    'investment_range': size_data["investment_range"],
                    'risk_level': size_data["risk_level"]
                },
                'metadata': {
                    'analyzed_at': datetime.utcnow().isoformat(),
                    'agent': self.agent_name,
                    'version': '2.0.0'
                }
            }
            
            # End execution tracking
            latency_ms = self.end_execution("success", result=response_data)
            
            self.logger.info(f"Business analysis completed for {industry} in {region} (latency: {latency_ms}ms)")
            
            return self.create_lambda_response(200, response_data)
            
        except Exception as e:
            self.end_execution("error", str(e))
            error_response = self.handle_error(e, "execute")
            return self.create_lambda_response(500, error_response)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for Product Insight Agent"""
    agent = ProductInsightAgent()
    return agent.lambda_handler(event, context)