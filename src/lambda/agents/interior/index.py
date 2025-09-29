"""
Interior Agent - 인테리어 스타일 추천 및 디자인 가이드 제공
"""

import json
import sys
import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add shared modules to path
sys.path.append('/opt/python')

try:
    from shared.base_agent import BaseAgent
    from shared.models import AgentType, InteriorRecommendation, InteriorRecommendations, BusinessInfo
    from shared.utils import create_response
    from shared.data_loader import get_data_loader
    HAS_SHARED_MODULES = True
except ImportError:
    HAS_SHARED_MODULES = False
    # For testing purposes, create mock implementations
    from datetime import datetime
    from typing import Dict, Any, List
    from enum import Enum
    import time
    
    class AgentType(Enum):
        INTERIOR = "interior"
    
    class InteriorRecommendation:
        def __init__(self, style: str, description: str, color_scheme: List[str],
                     materials: List[str], furniture: List[str], estimated_cost: str,
                     suitability_score: float = 0.0, pros: List[str] = None, cons: List[str] = None):
            self.style = style
            self.description = description
            self.color_scheme = color_scheme
            self.materials = materials
            self.furniture = furniture
            self.estimated_cost = estimated_cost
            self.suitability_score = suitability_score
            self.pros = pros or []
            self.cons = cons or []
            self.generated_at = datetime.utcnow().isoformat()
        
        def validate(self) -> bool:
            return bool(self.style and self.description and self.color_scheme and 
                       self.materials and self.furniture and self.estimated_cost)
    
    class InteriorRecommendations:
        def __init__(self, recommendations: List[InteriorRecommendation] = None):
            self.recommendations = recommendations or []
        
        def validate(self) -> bool:
            return len(self.recommendations) <= 3 and all(rec.validate() for rec in self.recommendations)
    
    class BusinessInfo:
        def __init__(self, industry: str, region: str, size: str, **kwargs):
            self.industry = industry
            self.region = region
            self.size = size
    
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
        
        def get_session_data(self, session_id: str):
            return None
        
        def update_session_data(self, session_id: str, updates: Dict[str, Any]):
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


class InteriorAgent(BaseAgent):
    """Interior Agent - 인테리어 스타일 추천"""
    
    def __init__(self):
        super().__init__(AgentType.INTERIOR)
        
        # 데이터 로더 초기화 (shared 모듈이 있는 경우만)
        if HAS_SHARED_MODULES:
            self.data_loader = get_data_loader()
            # 데이터 초기화 (필요시)
            self._ensure_data_initialized()
            # 인테리어 관련 데이터 로드
            self._load_all_data()
        else:
            # 폴백 데이터 사용
            self.data_loader = None
            self._load_fallback_data()
    
    def _ensure_data_initialized(self) -> None:
        """데이터가 초기화되었는지 확인하고 필요시 초기화"""
        try:
            # 데이터 디렉토리 경로 설정
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(current_dir, '..', '..', '..')
            data_dir = os.path.join(project_root, 'data')
            
            # 데이터 초기화
            self.data_loader.initialize_all_data(data_dir, force_reload=False)
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize data from files: {str(e)}")
            # 폴백: 하드코딩된 기본 데이터 사용
            self._load_fallback_data()
    
    def _load_all_data(self) -> None:
        """DynamoDB에서 모든 인테리어 데이터 로드"""
        try:
            if not self.data_loader:
                self._load_fallback_data()
                return
                
            all_data = self.data_loader.get_all_interior_data()
            
            self.interior_styles = all_data.get('interior_styles', {})
            self.industry_characteristics = all_data.get('industry_characteristics', {})
            self.regional_trends = all_data.get('regional_trends', {})
            self.size_considerations = all_data.get('size_considerations', {})
            
            # 데이터가 비어있으면 폴백 데이터 사용
            if not self.interior_styles:
                self.logger.warning("No data found in DynamoDB, using fallback data")
                self._load_fallback_data()
                
        except Exception as e:
            self.logger.error(f"Failed to load data from DynamoDB: {str(e)}")
            self._load_fallback_data()
    
    def _load_fallback_data(self) -> None:
        """폴백용 기본 데이터 로드"""
        self.interior_styles = self._get_fallback_interior_styles()
        self.industry_characteristics = self._get_fallback_industry_characteristics()
        self.regional_trends = self._get_fallback_regional_trends()
        self.size_considerations = self._get_fallback_size_considerations()
    
    def _get_fallback_interior_styles(self) -> Dict[str, Dict[str, Any]]:
        """인테리어 스타일 데이터 로드"""
        return {
            "modern": {
                "name": "모던 스타일",
                "description": "깔끔하고 세련된 현대적 디자인으로 심플함과 기능성을 강조합니다.",
                "color_scheme": ["화이트", "그레이", "블랙", "실버"],
                "materials": ["스테인리스 스틸", "유리", "콘크리트", "인조대리석"],
                "furniture": ["미니멀 테이블", "모던 의자", "LED 조명", "심플 수납장"],
                "estimated_cost": "중간",
                "pros": [
                    "세련되고 전문적인 이미지",
                    "청결하고 위생적인 느낌",
                    "관리가 용이함",
                    "시대를 타지 않는 디자인"
                ],
                "cons": [
                    "차가운 느낌을 줄 수 있음",
                    "개성이 부족할 수 있음",
                    "초기 비용이 다소 높음"
                ]
            },
            "cozy": {
                "name": "코지 스타일",
                "description": "따뜻하고 아늑한 분위기로 고객에게 편안함과 친근감을 제공합니다.",
                "color_scheme": ["따뜻한 브라운", "크림", "베이지", "소프트 오렌지"],
                "materials": ["원목", "패브릭", "자연석", "라탄"],
                "furniture": ["편안한 소파", "원목 테이블", "따뜻한 조명", "쿠션"],
                "estimated_cost": "낮음",
                "pros": [
                    "친근하고 편안한 분위기",
                    "고객 체류시간 증가",
                    "상대적으로 저렴한 비용",
                    "다양한 연령층에게 어필"
                ],
                "cons": [
                    "관리가 다소 까다로움",
                    "트렌디함이 부족할 수 있음",
                    "공간이 답답해 보일 수 있음"
                ]
            },
            "industrial": {
                "name": "인더스트리얼 스타일",
                "description": "산업적이고 독특한 매력으로 개성 있는 공간을 연출합니다.",
                "color_scheme": ["다크 그레이", "러스트", "블랙", "브론즈"],
                "materials": ["노출 벽돌", "철재", "재활용 목재", "콘크리트"],
                "furniture": ["인더스트리얼 테이블", "메탈 의자", "펜던트 조명", "파이프 선반"],
                "estimated_cost": "높음",
                "pros": [
                    "독특하고 개성적인 분위기",
                    "매우 내구성이 높음",
                    "인스타그래머블한 공간",
                    "브랜드 차별화 효과"
                ],
                "cons": [
                    "높은 초기 투자 비용",
                    "일부 고객에게 부담스러울 수 있음",
                    "유지보수가 복잡함",
                    "계절감이 부족함"
                ]
            },
            "scandinavian": {
                "name": "스칸디나비안 스타일",
                "description": "북유럽의 심플하고 자연친화적인 디자인으로 편안하면서도 세련된 공간을 만듭니다.",
                "color_scheme": ["화이트", "라이트 그레이", "내추럴 우드", "파스텔 블루"],
                "materials": ["자작나무", "린넨", "울", "세라믹"],
                "furniture": ["심플 우드 테이블", "패브릭 의자", "자연광 활용", "식물 장식"],
                "estimated_cost": "중간",
                "pros": [
                    "밝고 쾌적한 분위기",
                    "자연친화적 이미지",
                    "MZ세대에게 인기",
                    "사진 찍기 좋은 공간"
                ],
                "cons": [
                    "개성이 부족할 수 있음",
                    "유행에 민감함",
                    "일부 소재의 내구성 우려"
                ]
            },
            "vintage": {
                "name": "빈티지 스타일",
                "description": "과거의 향수를 불러일으키는 클래식한 매력으로 특별한 경험을 제공합니다.",
                "color_scheme": ["앤틱 브라운", "딥 그린", "골드", "버건디"],
                "materials": ["앤틱 우드", "가죽", "브라스", "벨벳"],
                "furniture": ["앤틱 테이블", "클래식 의자", "빈티지 조명", "장식장"],
                "estimated_cost": "높음",
                "pros": [
                    "고급스럽고 우아한 분위기",
                    "독특한 스토리텔링",
                    "시간이 지날수록 가치 상승",
                    "차별화된 브랜드 이미지"
                ],
                "cons": [
                    "높은 초기 비용",
                    "관리가 까다로움",
                    "젊은 층에게 어필 부족",
                    "공간 활용도가 낮을 수 있음"
                ]
            }
        }
    
    def _get_fallback_industry_characteristics(self) -> Dict[str, Dict[str, Any]]:
        """폴백용 업종별 인테리어 특성"""
        return {
            "restaurant": {
                "priority_factors": ["위생성", "편안함", "분위기", "효율성"],
                "recommended_styles": ["modern", "cozy", "scandinavian"],
                "avoid_styles": ["industrial"],
                "special_requirements": [
                    "위생적인 소재 사용",
                    "청소가 용이한 구조",
                    "적절한 조명 설계",
                    "소음 차단 고려"
                ],
                "customer_considerations": [
                    "식사 시간 고려한 편안한 좌석",
                    "음식과 어울리는 색상",
                    "가족 단위 고객 배려"
                ]
            },
            "retail": {
                "priority_factors": ["상품 진열", "고객 동선", "브랜드 이미지", "조명"],
                "recommended_styles": ["modern", "scandinavian", "industrial"],
                "avoid_styles": [],
                "special_requirements": [
                    "상품이 돋보이는 조명",
                    "효율적인 진열 공간",
                    "고객 동선 최적화",
                    "브랜드 컬러 반영"
                ],
                "customer_considerations": [
                    "쇼핑하기 편한 환경",
                    "상품 체험 공간",
                    "대기 공간 마련"
                ]
            },
            "service": {
                "priority_factors": ["전문성", "신뢰감", "편안함", "프라이버시"],
                "recommended_styles": ["modern", "scandinavian"],
                "avoid_styles": ["industrial", "vintage"],
                "special_requirements": [
                    "전문적인 이미지 연출",
                    "상담 공간 분리",
                    "차분한 색상 사용",
                    "소음 차단"
                ],
                "customer_considerations": [
                    "프라이버시 보호",
                    "편안한 상담 환경",
                    "신뢰감 조성"
                ]
            }
        }
    
    def _get_fallback_regional_trends(self) -> Dict[str, Dict[str, Any]]:
        """폴백용 지역별 인테리어 트렌드"""
        return {
            "seoul": {
                "trending_styles": ["modern", "scandinavian"],
                "characteristics": ["트렌디", "세련됨", "효율성"],
                "budget_range": "높음",
                "customer_preferences": ["인스타그래머블", "브랜드 가치", "차별화"]
            },
            "busan": {
                "trending_styles": ["cozy", "scandinavian"],
                "characteristics": ["편안함", "자연친화적", "실용성"],
                "budget_range": "중간",
                "customer_preferences": ["편안함", "가성비", "지역 특색"]
            }
        }
    
    def _get_fallback_size_considerations(self) -> Dict[str, Dict[str, Any]]:
        """폴백용 규모별 인테리어 고려사항"""
        return {
            "small": {
                "budget_constraint": "높음",
                "space_efficiency": "매우 중요",
                "cost_saving_tips": [
                    "기존 구조 최대한 활용",
                    "포인트 컬러로 변화 주기",
                    "조명으로 분위기 연출",
                    "식물로 자연스러운 장식"
                ]
            },
            "medium": {
                "budget_constraint": "보통",
                "space_efficiency": "중요",
                "investment_priorities": [
                    "핵심 공간 집중 투자",
                    "내구성 있는 소재 선택",
                    "확장 가능한 구조",
                    "에너지 효율성 고려"
                ]
            },
            "large": {
                "budget_constraint": "낮음",
                "space_efficiency": "보통",
                "luxury_elements": [
                    "고급 마감재 사용",
                    "맞춤형 가구 제작",
                    "스마트 시스템 도입",
                    "아트워크 및 조각품 활용"
                ]
            }
        }
    
    def execute(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Interior Agent 실행 로직"""
        try:
            # 요청 파싱
            if isinstance(event.get('body'), str):
                body = json.loads(event['body'])
            else:
                body = event.get('body', event)
            
            session_id = body.get('sessionId')
            business_info_data = body.get('businessInfo', {})
            selected_signboard = body.get('selectedSignboard')
            action = body.get('action', 'recommend')
            
            if not session_id:
                return self.create_lambda_response(400, {
                    "error": "sessionId is required"
                })
            
            # 실행 시작
            self.start_execution(session_id, "interior.recommend")
            
            # 비즈니스 정보 파싱
            if isinstance(business_info_data, str):
                business_info_data = json.loads(business_info_data)
            
            business_info = BusinessInfo(**business_info_data)
            
            # 인테리어 추천 생성
            if action == 'recommend':
                result = self._generate_interior_recommendations(session_id, business_info, selected_signboard)
            else:
                raise ValueError(f"Unknown action: {action}")
            
            # 실행 완료
            self.end_execution("success", result=result)
            
            return self.create_lambda_response(200, result)
            
        except Exception as e:
            error_message = f"Interior Agent execution failed: {str(e)}"
            self.end_execution("error", error_message)
            
            error_response = self.handle_error(e, "execute")
            return self.create_lambda_response(500, error_response)
    
    def _generate_interior_recommendations(self, session_id: str, business_info: BusinessInfo, 
                                         selected_signboard: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """인테리어 추천 생성"""
        try:
            industry = business_info.industry.lower()
            region = business_info.region.lower()
            size = business_info.size.lower()
            
            # 업종별 특성 가져오기
            industry_info = self.industry_characteristics.get(industry, self.industry_characteristics["retail"])
            
            # 지역별 트렌드 가져오기
            regional_info = self.regional_trends.get(region, self.regional_trends["seoul"])
            
            # 규모별 고려사항 가져오기
            size_info = self.size_considerations.get(size, self.size_considerations["medium"])
            
            # 추천 스타일 결정
            recommended_styles = self._determine_recommended_styles(
                industry_info, regional_info, selected_signboard
            )
            
            # 각 스타일별 추천 생성
            recommendations = []
            for style_name in recommended_styles[:3]:  # 최대 3개
                recommendation = self._create_style_recommendation(
                    style_name, business_info, industry_info, size_info, selected_signboard
                )
                recommendations.append(recommendation)
            
            # InteriorRecommendations 객체 생성
            interior_recommendations = InteriorRecommendations(recommendations=recommendations)
            
            # 세션에 저장
            self._save_interior_recommendations(session_id, interior_recommendations)
            
            return {
                "sessionId": session_id,
                "recommendations": [self._recommendation_to_dict(rec) for rec in recommendations],
                "totalRecommendations": len(recommendations),
                "industryInsights": {
                    "priorityFactors": industry_info["priority_factors"],
                    "specialRequirements": industry_info["special_requirements"],
                    "customerConsiderations": industry_info["customer_considerations"]
                },
                "regionalTrends": {
                    "trendingStyles": regional_info["trending_styles"],
                    "characteristics": regional_info["characteristics"],
                    "customerPreferences": regional_info["customer_preferences"]
                },
                "budgetGuidance": self._generate_budget_guidance(size_info, recommendations),
                "implementationGuide": self._generate_implementation_guide(size_info, recommendations),
                "nextSteps": [
                    "추천된 스타일 중 하나를 선택하세요",
                    "선택한 스타일에 대한 상세 가이드를 확인하세요",
                    "예산에 맞는 실행 계획을 수립하세요"
                ],
                "canProceed": len(recommendations) > 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate interior recommendations: {str(e)}")
            raise
    
    def _determine_recommended_styles(self, industry_info: Dict[str, Any], 
                                    regional_info: Dict[str, Any], 
                                    selected_signboard: Optional[Dict[str, Any]] = None) -> List[str]:
        """추천 스타일 결정"""
        # 업종별 추천 스타일
        industry_styles = set(industry_info["recommended_styles"])
        
        # 지역별 트렌드 스타일
        regional_styles = set(regional_info["trending_styles"])
        
        # 간판 스타일과의 조화 고려
        signboard_compatible_styles = set()
        if selected_signboard:
            signboard_style = selected_signboard.get('style', '').lower()
            if signboard_style == 'modern':
                signboard_compatible_styles = {'modern', 'scandinavian'}
            elif signboard_style == 'classic':
                signboard_compatible_styles = {'vintage', 'cozy'}
            elif signboard_style == 'vibrant':
                signboard_compatible_styles = {'industrial', 'cozy'}
        
        # 우선순위 계산
        style_scores = {}
        for style in self.interior_styles.keys():
            score = 0
            
            # 업종 적합성 (가중치 40%)
            if style in industry_styles:
                score += 40
            elif style in industry_info.get("avoid_styles", []):
                score -= 20
            
            # 지역 트렌드 (가중치 30%)
            if style in regional_styles:
                score += 30
            
            # 간판과의 조화 (가중치 20%)
            if style in signboard_compatible_styles:
                score += 20
            
            # 기본 인기도 (가중치 10%)
            popularity_scores = {
                'modern': 10, 'scandinavian': 9, 'cozy': 8, 
                'industrial': 6, 'vintage': 5
            }
            score += popularity_scores.get(style, 5)
            
            style_scores[style] = score
        
        # 점수 순으로 정렬하여 상위 3개 반환
        sorted_styles = sorted(style_scores.items(), key=lambda x: x[1], reverse=True)
        return [style for style, score in sorted_styles[:3]]
    
    def _create_style_recommendation(self, style_name: str, business_info: BusinessInfo,
                                   industry_info: Dict[str, Any], size_info: Dict[str, Any],
                                   selected_signboard: Optional[Dict[str, Any]] = None) -> InteriorRecommendation:
        """스타일별 추천 생성"""
        style_data = self.interior_styles[style_name]
        
        # 적합성 점수 계산
        suitability_score = self._calculate_suitability_score(
            style_name, business_info, industry_info, size_info
        )
        
        # 규모별 맞춤 조언 추가
        customized_pros = style_data["pros"].copy()
        customized_cons = style_data["cons"].copy()
        
        if business_info.size == "small":
            if style_name in ["modern", "scandinavian"]:
                customized_pros.append("작은 공간을 넓어 보이게 하는 효과")
            if style_name in ["industrial", "vintage"]:
                customized_cons.append("작은 공간에서는 압박감을 줄 수 있음")
        
        return InteriorRecommendation(
            style=style_data["name"],
            description=style_data["description"],
            color_scheme=style_data["color_scheme"],
            materials=style_data["materials"],
            furniture=style_data["furniture"],
            estimated_cost=style_data["estimated_cost"],
            suitability_score=suitability_score,
            pros=customized_pros,
            cons=customized_cons
        )
    
    def _calculate_suitability_score(self, style_name: str, business_info: BusinessInfo,
                                   industry_info: Dict[str, Any], size_info: Dict[str, Any]) -> float:
        """적합성 점수 계산 (0-100)"""
        score = 50.0  # 기본 점수
        
        # 업종 적합성
        if style_name in industry_info["recommended_styles"]:
            score += 25
        elif style_name in industry_info.get("avoid_styles", []):
            score -= 20
        
        # 규모 적합성
        if business_info.size == "small":
            if style_name in ["modern", "scandinavian"]:
                score += 15
            elif style_name in ["industrial", "vintage"]:
                score -= 10
        elif business_info.size == "large":
            if style_name in ["industrial", "vintage"]:
                score += 10
        
        # 지역 트렌드 반영
        regional_info = self.regional_trends.get(business_info.region.lower(), {})
        if style_name in regional_info.get("trending_styles", []):
            score += 10
        
        return max(0, min(100, round(score, 1)))
    
    def _generate_budget_guidance(self, size_info: Dict[str, Any], 
                                recommendations: List[InteriorRecommendation]) -> Dict[str, Any]:
        """예산 가이드 생성"""
        # 비용 레벨별 예상 금액 (평방미터당)
        cost_estimates = {
            "낮음": {"min": 300000, "max": 500000, "description": "기본적인 인테리어 비용"},
            "중간": {"min": 500000, "max": 800000, "description": "중급 수준의 인테리어 비용"},
            "높음": {"min": 800000, "max": 1200000, "description": "고급 인테리어 비용"}
        }
        
        budget_guidance = {
            "constraint_level": size_info["budget_constraint"],
            "recommendations_by_cost": {},
            "cost_saving_tips": size_info.get("cost_saving_tips", []),
            "investment_priorities": size_info.get("investment_priorities", []),
            "financing_options": self._generate_financing_options()
        }
        
        # 추천별 예산 정보
        for rec in recommendations:
            cost_level = rec.estimated_cost
            if cost_level in cost_estimates:
                cost_info = cost_estimates[cost_level]
                budget_guidance["recommendations_by_cost"][rec.style] = {
                    "cost_level": cost_level,
                    "per_sqm_range": {
                        "min": cost_info["min"],
                        "max": cost_info["max"],
                        "description": cost_info["description"]
                    }
                }
        
        return budget_guidance
    
    def _generate_financing_options(self) -> Dict[str, Any]:
        """자금 조달 옵션 가이드"""
        return {
            "payment_methods": {
                "lump_sum": {
                    "name": "일시불 결제",
                    "pros": ["총 비용 절약", "빠른 완공", "업체 할인 혜택"],
                    "cons": ["높은 초기 부담", "현금 흐름 압박"],
                    "recommended_for": ["충분한 자금 보유", "빠른 오픈 필요"]
                },
                "installment": {
                    "name": "분할 결제",
                    "pros": ["현금 흐름 관리", "단계별 품질 확인", "리스크 분산"],
                    "cons": ["총 비용 증가", "관리 복잡성"],
                    "recommended_for": ["자금 여유 부족", "단계별 진행 선호"]
                }
            },
            "funding_sources": [
                "정부 창업 지원금",
                "소상공인 대출",
                "인테리어 전용 대출",
                "카드 무이자 할부"
            ]
        }
    
    def _generate_implementation_guide(self, size_info: Dict[str, Any], 
                                     recommendations: List[InteriorRecommendation]) -> Dict[str, Any]:
        """실행 가이드 생성"""
        return {
            "step_by_step_process": {
                "1": {
                    "title": "스타일 선택 및 컨셉 확정",
                    "duration": "1-2일",
                    "activities": [
                        "추천 스타일 중 최종 선택",
                        "세부 컨셉 및 테마 결정",
                        "참고 이미지 수집",
                        "우선순위 설정"
                    ]
                },
                "2": {
                    "title": "예산 계획 및 자금 준비",
                    "duration": "3-5일",
                    "activities": [
                        "상세 예산 계획 수립",
                        "자금 조달 방법 결정",
                        "예비비 확보",
                        "결제 일정 계획"
                    ]
                },
                "3": {
                    "title": "업체 선정 및 계약",
                    "duration": "1주",
                    "activities": [
                        "인테리어 업체 리서치",
                        "견적 비교 및 협상",
                        "포트폴리오 검토",
                        "계약서 작성 및 체결"
                    ]
                }
            },
            "success_factors": [
                "명확한 컨셉과 목표 설정",
                "충분한 사전 계획",
                "신뢰할 수 있는 업체 선정",
                "적극적인 소통과 관리"
            ]
        }
    
    def _save_interior_recommendations(self, session_id: str, 
                                     interior_recommendations: InteriorRecommendations) -> None:
        """InteriorRecommendations를 세션에 저장"""
        try:
            recommendations_data = {
                "recommendations": [self._recommendation_to_dict(rec) for rec in interior_recommendations.recommendations]
            }
            
            updates = {
                "interior_recommendations": json.dumps(recommendations_data)
            }
            
            success = self.update_session_data(session_id, updates)
            if not success:
                raise Exception("Failed to update session data")
                
        except Exception as e:
            self.logger.error(f"Failed to save interior recommendations: {str(e)}")
            raise
    
    def _recommendation_to_dict(self, recommendation: InteriorRecommendation) -> Dict[str, Any]:
        """InteriorRecommendation을 딕셔너리로 변환"""
        return {
            "style": recommendation.style,
            "description": recommendation.description,
            "colorScheme": recommendation.color_scheme,
            "materials": recommendation.materials,
            "furniture": recommendation.furniture,
            "estimatedCost": recommendation.estimated_cost,
            "suitabilityScore": recommendation.suitability_score,
            "pros": recommendation.pros,
            "cons": recommendation.cons,
            "generatedAt": recommendation.generated_at
        }


# Lambda 핸들러
def lambda_handler(event, context):
    """Lambda 핸들러 함수"""
    agent = InteriorAgent()
    return agent.lambda_handler(event, context)