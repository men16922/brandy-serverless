# Market Analyst Agent Lambda Function
# 시장 동향 및 경쟁사 분석, Bedrock KB에서 관련 데이터 검색

import json
import boto3
import logging
from datetime import datetime
import os
from typing import Dict, Any, List

# 공통 유틸리티 import
import sys
sys.path.append('/opt/python')
from shared.utils import setup_logging, get_aws_clients, create_response
from shared.agent_communication import AgentCommunication
from shared.knowledge_base import get_knowledge_base

logger = setup_logging()

class MarketAnalystAgent:
    def __init__(self):
        self.aws_clients = get_aws_clients()
        self.dynamodb = self.aws_clients['dynamodb']
        self.sessions_table = self.dynamodb.Table(os.getenv('SESSIONS_TABLE'))
        self.knowledge_base = get_knowledge_base()
        self.agent_comm = AgentCommunication()
        
    def lambda_handler(self, event, context):
        """
        Market Analyst Agent 메인 핸들러
        - 시장 동향 및 경쟁사 분석
        - Bedrock KB에서 관련 데이터 검색
        - Product Insight와 협력하여 종합 분석
        """
        try:
            logger.info("Market Analyst Agent started", extra={
                "agent": "market",
                "tool": "kb.search",
                "session_id": event.get('sessionId')
            })
            
            start_time = datetime.now()
            
            # 요청 파싱
            if isinstance(event.get('body'), str):
                body = json.loads(event['body'])
            else:
                body = event.get('body', event)
            
            session_id = body.get('sessionId')
            business_info = body.get('businessInfo', {})
            product_analysis = body.get('productAnalysis', {})
            
            # 시장 분석 수행
            market_analysis = self.analyze_market(business_info, product_analysis)
            
            # 트렌드 분석 수행
            trend_analysis = self.analyze_trends(business_info, market_analysis)
            
            # 종합 분석 결과 생성
            comprehensive_analysis = {
                **market_analysis,
                "trendAnalysis": trend_analysis,
                "recommendations": self._generate_market_recommendations(market_analysis, trend_analysis)
            }
            
            # 세션에 결과 저장
            self._save_market_analysis(session_id, comprehensive_analysis)
            
            # Supervisor Agent에 상태 보고
            self.agent_comm.send_to_supervisor(
                agent_id="market",
                status="completed",
                result=comprehensive_analysis
            )
            
            # 실행 시간 로깅
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.info("Market Analyst Agent completed", extra={
                "agent": "market",
                "tool": "kb.search",
                "latency_ms": latency_ms,
                "status": "success"
            })
            
            return create_response(200, {
                "sessionId": session_id,
                "marketAnalysis": comprehensive_analysis,
                "processingTime": latency_ms
            })
            
        except Exception as e:
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error("Market Analyst Agent failed", extra={
                "agent": "market",
                "tool": "kb.search",
                "latency_ms": latency_ms,
                "error": str(e)
            })
            
            # 실패 시 Supervisor에게 보고
            self.agent_comm.send_to_supervisor(
                agent_id="market",
                status="failed",
                result={"error": str(e)}
            )
            
            return create_response(500, {"error": "Market analysis failed"})
    
    def analyze_market(self, business_info: Dict[str, Any], product_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """시장 분석 수행"""
        industry = business_info.get('industry', '')
        region = business_info.get('region', '')
        
        try:
            # Knowledge Base에서 시장 데이터 조회
            market_data = self._query_market_data(industry, region)
            
            # 경쟁사 분석
            competitor_analysis = self._analyze_competitors(industry, region)
            
            # 시장 기회 분석
            opportunities = self._identify_opportunities(industry, region, market_data)
            
            # 위험 요소 분석
            risks = self._analyze_risks(industry, region, market_data)
            
            market_analysis = {
                "marketSize": self._estimate_market_size(industry, region, market_data),
                "growthTrends": self._analyze_growth_trends(market_data),
                "competitorAnalysis": competitor_analysis,
                "marketOpportunities": opportunities,
                "riskFactors": risks,
                "customerSegments": self._analyze_customer_segments(industry, region),
                "pricingTrends": self._analyze_pricing_trends(industry, market_data),
                "regulatoryEnvironment": self._analyze_regulatory_environment(industry, region),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return market_analysis
            
        except Exception as e:
            logger.warning(f"Market analysis failed, using fallback: {str(e)}")
            return self._get_fallback_market_analysis(industry, region)
    
    def analyze_trends(self, business_info: Dict[str, Any], market_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """트렌드 분석 수행"""
        industry = business_info.get('industry', '')
        region = business_info.get('region', '')
        size = business_info.get('size', '')
        
        try:
            # 최신 시장 트렌드 분석
            latest_trends = self._analyze_latest_trends(industry, region)
            
            # 소비자 선호도 변화 분석
            consumer_preference_changes = self._analyze_consumer_preferences(industry, region)
            
            # 기회 요소 발굴
            opportunity_analysis = self._discover_opportunities(industry, region, size, market_analysis)
            
            # 위험 요소 분석
            risk_analysis = self._analyze_trend_risks(industry, region, latest_trends)
            
            # 기술 트렌드 영향 분석
            tech_impact = self._analyze_technology_impact(industry)
            
            # 사회적 트렌드 영향 분석
            social_impact = self._analyze_social_trends_impact(industry, region)
            
            trend_analysis = {
                "latestTrends": latest_trends,
                "consumerPreferences": consumer_preference_changes,
                "opportunities": opportunity_analysis,
                "risks": risk_analysis,
                "technologyImpact": tech_impact,
                "socialTrends": social_impact,
                "trendScore": self._calculate_trend_score(latest_trends, opportunity_analysis),
                "actionableInsights": self._generate_actionable_insights(latest_trends, opportunity_analysis),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return trend_analysis
            
        except Exception as e:
            logger.warning(f"Trend analysis failed, using fallback: {str(e)}")
            return self._get_fallback_trend_analysis(industry, region)
    
    def _analyze_latest_trends(self, industry: str, region: str) -> Dict[str, Any]:
        """최신 시장 트렌드 분석 - DynamoDB에서 조회"""
        try:
            from shared.market_data_loader import get_market_data_loader
            
            market_loader = get_market_data_loader()
            trend_data = market_loader.get_industry_trends(industry)
            
            if trend_data:
                hot_trends = trend_data.get("hot_trends", [])
                declining_trends = trend_data.get("declining_trends", [])
                
                return {
                    "hotTrends": hot_trends,
                    "decliningTrends": declining_trends,
                    "trendVelocity": self._calculate_trend_velocity(hot_trends),
                    "regionalAdaptation": self._analyze_regional_trend_adaptation(region, trend_data),
                    "competitorAdoption": self._analyze_competitor_trend_adoption(industry, trend_data),
                    "consumerBehaviors": trend_data.get("consumer_behaviors", [])
                }
            else:
                logger.warning(f"Trend data not found for {industry}, using fallback")
                return self._get_fallback_trend_data(industry)
                
        except Exception as e:
            logger.error(f"Latest trends analysis failed: {str(e)}")
            return self._get_fallback_trend_data(industry)
    
    def _analyze_consumer_preferences(self, industry: str, region: str) -> Dict[str, Any]:
        """소비자 선호도 변화 분석"""
        
        # 세대별 선호도 변화
        generational_preferences = {
            "MZ세대": {
                "priorities": ["경험", "가치 소비", "개성", "편의성"],
                "spending_pattern": "선택적 집중",
                "decision_factors": ["SNS 후기", "브랜드 가치", "개인화"],
                "growth_rate": "+25%"
            },
            "X세대": {
                "priorities": ["품질", "가성비", "실용성", "안정성"],
                "spending_pattern": "신중한 소비",
                "decision_factors": ["품질", "가격", "브랜드 신뢰도"],
                "growth_rate": "+8%"
            },
            "베이비부머": {
                "priorities": ["품질", "서비스", "신뢰성", "전통"],
                "spending_pattern": "보수적 소비",
                "decision_factors": ["브랜드 역사", "서비스 품질", "추천"],
                "growth_rate": "+12%"
            }
        }
        
        # 지역별 선호도 특성
        regional_preferences = {
            "seoul": ["트렌디함", "혁신성", "브랜드 가치", "차별화"],
            "busan": ["실용성", "가성비", "지역 특색", "편안함"],
            "gyeonggi": ["가족 친화", "편의성", "안전성", "실용성"],
            "jeju": ["자연 친화", "힐링", "특별함", "지속가능성"]
        }
        
        # 업종별 소비자 행동 변화
        behavioral_changes = {
            "restaurant": [
                {"change": "배달 앱 사용 증가", "percentage": "+78%"},
                {"change": "건강 메뉴 선호", "percentage": "+45%"},
                {"change": "인스타그래머블 중시", "percentage": "+62%"},
                {"change": "개인 다이닝 선호", "percentage": "+38%"}
            ],
            "retail": [
                {"change": "온라인 우선 구매", "percentage": "+85%"},
                {"change": "리뷰 의존도 증가", "percentage": "+72%"},
                {"change": "지속가능성 고려", "percentage": "+55%"},
                {"change": "개인화 상품 선호", "percentage": "+48%"}
            ],
            "service": [
                {"change": "비대면 서비스 선호", "percentage": "+68%"},
                {"change": "구독 서비스 선호", "percentage": "+52%"},
                {"change": "개인 맞춤 서비스", "percentage": "+65%"},
                {"change": "투명한 가격 정책", "percentage": "+58%"}
            ]
        }
        
        return {
            "generationalPreferences": generational_preferences,
            "regionalPreferences": regional_preferences.get(region, regional_preferences["seoul"]),
            "behavioralChanges": behavioral_changes.get(industry, behavioral_changes["service"]),
            "keyInsights": self._extract_preference_insights(industry, region),
            "futureProjections": self._project_future_preferences(industry)
        }
    
    def _discover_opportunities(self, industry: str, region: str, size: str, market_analysis: Dict) -> Dict[str, Any]:
        """기회 요소 발굴"""
        
        # 시장 갭 분석
        market_gaps = self._identify_market_gaps(industry, region)
        
        # 신규 고객 세그먼트
        new_segments = self._identify_new_segments(industry, region)
        
        # 기술 기회
        tech_opportunities = self._identify_tech_opportunities(industry)
        
        # 파트너십 기회
        partnership_opportunities = self._identify_partnership_opportunities(industry, size)
        
        # 확장 기회
        expansion_opportunities = self._identify_expansion_opportunities(industry, region, size)
        
        return {
            "marketGaps": market_gaps,
            "newSegments": new_segments,
            "technologyOpportunities": tech_opportunities,
            "partnershipOpportunities": partnership_opportunities,
            "expansionOpportunities": expansion_opportunities,
            "priorityOpportunities": self._prioritize_opportunities(market_gaps, new_segments, tech_opportunities),
            "implementationTimeline": self._create_opportunity_timeline(market_gaps, tech_opportunities)
        }
    
    def _analyze_trend_risks(self, industry: str, region: str, trends: Dict) -> Dict[str, Any]:
        """트렌드 관련 위험 분석"""
        
        # 트렌드 변화 위험
        trend_risks = [
            {
                "risk": "트렌드 급변",
                "probability": "중간",
                "impact": "높음",
                "description": "소비자 트렌드의 급격한 변화",
                "mitigation": "다양한 트렌드 모니터링 및 빠른 적응"
            },
            {
                "risk": "경쟁사 선점",
                "probability": "높음",
                "impact": "중간",
                "description": "경쟁사의 트렌드 선점",
                "mitigation": "차별화된 접근 방식 개발"
            },
            {
                "risk": "투자 회수 실패",
                "probability": "중간",
                "impact": "높음",
                "description": "트렌드 투자 대비 수익 미달",
                "mitigation": "단계적 투자 및 성과 측정"
            }
        ]
        
        # 업종별 특화 위험
        industry_specific_risks = {
            "restaurant": [
                {"risk": "식자재 가격 변동", "impact": "높음"},
                {"risk": "배달비 상승", "impact": "중간"},
                {"risk": "위생 규제 강화", "impact": "중간"}
            ],
            "retail": [
                {"risk": "온라인 플랫폼 의존", "impact": "높음"},
                {"risk": "재고 관리 복잡성", "impact": "중간"},
                {"risk": "물류비 상승", "impact": "중간"}
            ],
            "technology": [
                {"risk": "기술 변화 속도", "impact": "매우 높음"},
                {"risk": "인재 확보 경쟁", "impact": "높음"},
                {"risk": "보안 위협 증가", "impact": "높음"}
            ]
        }
        
        return {
            "generalRisks": trend_risks,
            "industryRisks": industry_specific_risks.get(industry, []),
            "riskMatrix": self._create_risk_matrix(trend_risks, industry_specific_risks.get(industry, [])),
            "mitigationStrategies": self._develop_mitigation_strategies(industry, trend_risks)
        }
    
    def _query_market_data(self, industry: str, region: str) -> Dict[str, Any]:
        """Knowledge Base에서 시장 데이터 조회"""
        try:
            # 시장 규모 및 성장률 데이터
            market_size_query = f"{industry} 시장 규모 성장률 전망"
            market_size_data = self.knowledge_base.search(market_size_query, top_k=5)
            
            # 시장 트렌드 데이터
            trends_query = f"{industry} 시장 트렌드 변화 동향"
            trends_data = self.knowledge_base.search(trends_query, top_k=5)
            
            # 지역별 시장 특성
            regional_query = f"{region} {industry} 시장 특성 현황"
            regional_data = self.knowledge_base.search(regional_query, top_k=3)
            
            return {
                "market_size_data": market_size_data,
                "trends_data": trends_data,
                "regional_data": regional_data,
                "source": "knowledge_base"
            }
            
        except Exception as e:
            logger.error(f"Market data query failed: {str(e)}")
            return {"source": "fallback"}
    
    def _analyze_competitors(self, industry: str, region: str) -> Dict[str, Any]:
        """경쟁사 분석 - 업종별/지역별 세분화"""
        try:
            competitors_query = f"{industry} 주요 경쟁사 시장 점유율"
            competitor_data = self.knowledge_base.search(competitors_query, top_k=5)
            
            # 업종별 주요 경쟁사 데이터
            industry_competitors = self._get_industry_competitors(industry, region)
            
            return {
                "majorCompetitors": industry_competitors["major"],
                "marketShare": industry_competitors["market_share"],
                "competitiveAdvantages": self._identify_competitive_advantages(industry),
                "competitiveThreats": self._identify_competitive_threats(industry, region),
                "entryBarriers": self._analyze_entry_barriers(industry),
                "competitivePositioning": self._suggest_competitive_positioning(industry, region),
                "benchmarkMetrics": self._get_benchmark_metrics(industry)
            }
        except Exception as e:
            logger.error(f"Competitor analysis failed: {str(e)}")
            return self._get_fallback_competitor_analysis(industry, region)
    
    def _get_industry_competitors(self, industry: str, region: str) -> Dict[str, Any]:
        """업종별 주요 경쟁사 정보 - DynamoDB에서 조회"""
        try:
            from shared.market_data_loader import get_market_data_loader
            
            market_loader = get_market_data_loader()
            competitor_data = market_loader.get_industry_competitors(industry)
            
            if competitor_data:
                return {
                    "major": competitor_data.get("major_competitors", []),
                    "market_share": competitor_data.get("market_share_distribution", {})
                }
            else:
                logger.warning(f"Competitor data not found for {industry}, using fallback")
                return self._get_fallback_competitor_data(industry)
                
        except Exception as e:
            logger.error(f"Failed to get industry competitors: {str(e)}")
            return self._get_fallback_competitor_data(industry)
    
    def _analyze_entry_barriers(self, industry: str) -> List[Dict[str, str]]:
        """진입 장벽 분석"""
        barriers_data = {
            "restaurant": [
                {"barrier": "초기 투자비", "level": "중간", "description": "인테리어, 장비 비용"},
                {"barrier": "위치 선정", "level": "높음", "description": "임대료, 유동인구"},
                {"barrier": "인허가", "level": "중간", "description": "영업신고, 위생허가"}
            ],
            "retail": [
                {"barrier": "재고 투자", "level": "높음", "description": "초기 상품 구매비용"},
                {"barrier": "유통망", "level": "높음", "description": "공급업체 확보"},
                {"barrier": "브랜드 인지도", "level": "중간", "description": "마케팅 비용"}
            ],
            "service": [
                {"barrier": "전문성", "level": "높음", "description": "자격증, 경험"},
                {"barrier": "신뢰 구축", "level": "높음", "description": "평판, 실적"},
                {"barrier": "초기 투자", "level": "낮음", "description": "상대적으로 적은 비용"}
            ],
            "healthcare": [
                {"barrier": "면허/자격", "level": "매우 높음", "description": "의료진 확보"},
                {"barrier": "시설 투자", "level": "매우 높음", "description": "의료장비, 시설"},
                {"barrier": "규제 준수", "level": "매우 높음", "description": "의료법 준수"}
            ],
            "education": [
                {"barrier": "강사 확보", "level": "중간", "description": "우수 강사진"},
                {"barrier": "커리큘럼", "level": "중간", "description": "교육 프로그램"},
                {"barrier": "시설 투자", "level": "중간", "description": "교육 시설"}
            ],
            "technology": [
                {"barrier": "기술력", "level": "매우 높음", "description": "R&D 투자"},
                {"barrier": "인재 확보", "level": "매우 높음", "description": "개발자, 엔지니어"},
                {"barrier": "자본 조달", "level": "높음", "description": "개발 비용"}
            ]
        }
        
        return barriers_data.get(industry, barriers_data["service"])
    
    def _suggest_competitive_positioning(self, industry: str, region: str) -> Dict[str, Any]:
        """경쟁 포지셔닝 제안"""
        return {
            "recommendedStrategy": self._get_positioning_strategy(industry, region),
            "differentiationFactors": self._get_differentiation_factors(industry),
            "targetSegment": self._get_target_segment(industry, region),
            "valueProposition": self._get_value_proposition(industry)
        }
    
    def _get_positioning_strategy(self, industry: str, region: str) -> str:
        """포지셔닝 전략"""
        strategies = {
            "restaurant": "지역 특색과 개성을 살린 차별화",
            "retail": "전문성과 고객 서비스 중심",
            "service": "개인 맞춤형 서비스 특화",
            "healthcare": "전문성과 신뢰성 강조",
            "education": "개별 맞춤 교육 프로그램",
            "technology": "혁신적 기술과 사용자 경험"
        }
        return strategies.get(industry, "고품질 서비스 차별화")
    
    def _get_differentiation_factors(self, industry: str) -> List[str]:
        """차별화 요소"""
        factors = {
            "restaurant": ["독특한 메뉴", "분위기", "서비스 품질", "가성비"],
            "retail": ["상품 큐레이션", "고객 서비스", "매장 경험", "전문성"],
            "service": ["개인화", "전문성", "신속성", "신뢰성"],
            "healthcare": ["의료진 전문성", "시설", "서비스", "접근성"],
            "education": ["맞춤 교육", "성과", "강사진", "시설"],
            "technology": ["기술 혁신", "사용자 경험", "성능", "지원"]
        }
        return factors.get(industry, ["품질", "서비스", "가격", "편의성"])
    
    def _get_target_segment(self, industry: str, region: str) -> str:
        """타겟 세그먼트"""
        segments = {
            "restaurant": "지역 주민 및 직장인",
            "retail": "품질 중시 고객층",
            "service": "전문 서비스 수요층",
            "healthcare": "건강 관심 고객",
            "education": "교육 투자 적극층",
            "technology": "얼리어답터층"
        }
        return segments.get(industry, "품질 중시 고객층")
    
    def _get_value_proposition(self, industry: str) -> str:
        """가치 제안"""
        propositions = {
            "restaurant": "맛있고 건강한 음식을 편안한 공간에서",
            "retail": "엄선된 상품과 전문적인 서비스",
            "service": "개인 맞춤형 전문 서비스",
            "healthcare": "안전하고 전문적인 의료 서비스",
            "education": "개별 맞춤 교육으로 확실한 성과",
            "technology": "혁신적 기술로 더 나은 경험"
        }
        return propositions.get(industry, "고품질 서비스로 고객 만족")
    
    def _get_benchmark_metrics(self, industry: str) -> Dict[str, str]:
        """벤치마크 지표"""
        metrics = {
            "restaurant": {
                "고객 재방문율": "60-70%",
                "평균 객단가": "15,000-25,000원",
                "월 매출": "3,000-8,000만원"
            },
            "retail": {
                "고객 전환율": "15-25%",
                "평균 객단가": "30,000-50,000원",
                "재고 회전율": "월 2-3회"
            },
            "service": {
                "고객 만족도": "85-95%",
                "재계약율": "70-80%",
                "평균 서비스 단가": "50,000-200,000원"
            },
            "healthcare": {
                "환자 만족도": "90-95%",
                "재방문율": "80-90%",
                "평균 진료비": "30,000-100,000원"
            },
            "education": {
                "학생 만족도": "85-95%",
                "성적 향상률": "70-80%",
                "재등록률": "75-85%"
            },
            "technology": {
                "사용자 만족도": "80-90%",
                "기술 혁신 지수": "상위 20%",
                "시장 점유율": "5-15%"
            }
        }
        return metrics.get(industry, {"고객 만족도": "85%", "재이용률": "70%"})
    
    def _calculate_trend_velocity(self, hot_trends: List[Dict]) -> str:
        """트렌드 변화 속도 계산"""
        if not hot_trends:
            return "보통"
        
        avg_growth = sum(int(trend["growth"].replace("+", "").replace("%", "")) for trend in hot_trends) / len(hot_trends)
        
        if avg_growth > 50:
            return "매우 빠름"
        elif avg_growth > 30:
            return "빠름"
        elif avg_growth > 15:
            return "보통"
        else:
            return "느림"
    
    def _analyze_regional_trend_adaptation(self, region: str, trends: Dict) -> Dict[str, Any]:
        """지역별 트렌드 적응도 분석"""
        adaptation_rates = {
            "seoul": {"rate": "매우 높음", "speed": "빠름", "openness": "높음"},
            "busan": {"rate": "높음", "speed": "보통", "openness": "중간"},
            "gyeonggi": {"rate": "높음", "speed": "보통", "openness": "높음"},
            "jeju": {"rate": "중간", "speed": "느림", "openness": "중간"}
        }
        
        return adaptation_rates.get(region, {"rate": "중간", "speed": "보통", "openness": "중간"})
    
    def _analyze_competitor_trend_adoption(self, industry: str, trends: Dict) -> Dict[str, str]:
        """경쟁사 트렌드 도입 현황"""
        return {
            "earlyAdopters": "20%",
            "mainstream": "60%", 
            "laggards": "20%",
            "recommendedPosition": "early mainstream"
        }
    
    def _extract_preference_insights(self, industry: str, region: str) -> List[str]:
        """선호도 변화 핵심 인사이트"""
        insights = {
            "restaurant": [
                "건강과 맛의 균형 추구",
                "개인화된 다이닝 경험 선호",
                "지속가능성 고려 증가",
                "소셜미디어 공유 가치 중시"
            ],
            "retail": [
                "온라인-오프라인 통합 경험 요구",
                "개인 맞춤 상품 큐레이션 선호",
                "투명한 브랜드 스토리 중시",
                "즉시 배송 서비스 기대"
            ],
            "service": [
                "24/7 접근 가능한 서비스 요구",
                "개인 데이터 기반 맞춤 서비스",
                "투명한 가격 정책 선호",
                "셀프 서비스 옵션 확대"
            ]
        }
        
        return insights.get(industry, insights["service"])
    
    def _project_future_preferences(self, industry: str) -> Dict[str, Any]:
        """미래 선호도 전망"""
        return {
            "timeframe": "2025-2027",
            "keyChanges": [
                "AI 기반 개인화 서비스 확산",
                "지속가능성 중시 확대",
                "경험 중심 소비 증가",
                "구독 경제 확산"
            ],
            "impactLevel": "높음"
        }
    
    def _identify_market_gaps(self, industry: str, region: str) -> List[Dict[str, Any]]:
        """시장 갭 분석"""
        gaps = {
            "restaurant": [
                {"gap": "건강한 야식 옵션", "size": "중간", "difficulty": "낮음"},
                {"gap": "1인 가구 맞춤 메뉴", "size": "높음", "difficulty": "중간"},
                {"gap": "시니어 친화 메뉴", "size": "높음", "difficulty": "낮음"}
            ],
            "retail": [
                {"gap": "지속가능한 패션", "size": "높음", "difficulty": "중간"},
                {"gap": "AR 체험 쇼핑", "size": "중간", "difficulty": "높음"},
                {"gap": "로컬 브랜드 큐레이션", "size": "중간", "difficulty": "낮음"}
            ],
            "service": [
                {"gap": "AI 기반 개인 상담", "size": "높음", "difficulty": "높음"},
                {"gap": "구독형 전문 서비스", "size": "중간", "difficulty": "중간"},
                {"gap": "하이브리드 서비스 모델", "size": "높음", "difficulty": "중간"}
            ]
        }
        
        return gaps.get(industry, gaps["service"])
    
    def _identify_new_segments(self, industry: str, region: str) -> List[Dict[str, Any]]:
        """신규 고객 세그먼트"""
        segments = [
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
        
        return segments
    
    def _identify_tech_opportunities(self, industry: str) -> List[Dict[str, Any]]:
        """기술 기회 분석"""
        opportunities = {
            "restaurant": [
                {"tech": "AI 메뉴 추천", "maturity": "중간", "impact": "높음"},
                {"tech": "무인 주문 시스템", "maturity": "높음", "impact": "중간"},
                {"tech": "IoT 재고 관리", "maturity": "중간", "impact": "중간"}
            ],
            "retail": [
                {"tech": "AR/VR 쇼핑", "maturity": "중간", "impact": "높음"},
                {"tech": "AI 개인화 추천", "maturity": "높음", "impact": "높음"},
                {"tech": "블록체인 인증", "maturity": "낮음", "impact": "중간"}
            ],
            "service": [
                {"tech": "AI 챗봇", "maturity": "높음", "impact": "높음"},
                {"tech": "예측 분석", "maturity": "중간", "impact": "높음"},
                {"tech": "자동화 워크플로", "maturity": "중간", "impact": "중간"}
            ]
        }
        
        return opportunities.get(industry, opportunities["service"])
    
    def _identify_partnership_opportunities(self, industry: str, size: str) -> List[Dict[str, Any]]:
        """파트너십 기회"""
        partnerships = [
            {
                "type": "기술 파트너십",
                "partner": "IT 스타트업",
                "benefit": "디지털 전환 가속화",
                "feasibility": "높음"
            },
            {
                "type": "유통 파트너십", 
                "partner": "온라인 플랫폼",
                "benefit": "고객 접점 확대",
                "feasibility": "중간"
            },
            {
                "type": "브랜드 협업",
                "partner": "로컬 브랜드",
                "benefit": "상호 시너지",
                "feasibility": "높음"
            }
        ]
        
        return partnerships
    
    def _identify_expansion_opportunities(self, industry: str, region: str, size: str) -> List[Dict[str, Any]]:
        """확장 기회"""
        opportunities = [
            {
                "type": "지역 확장",
                "target": "인근 지역",
                "timeline": "6-12개월",
                "investment": "중간"
            },
            {
                "type": "서비스 확장",
                "target": "관련 서비스",
                "timeline": "3-6개월", 
                "investment": "낮음"
            },
            {
                "type": "온라인 확장",
                "target": "디지털 채널",
                "timeline": "1-3개월",
                "investment": "낮음"
            }
        ]
        
        return opportunities
    
    def _prioritize_opportunities(self, market_gaps: List, new_segments: List, tech_opportunities: List) -> List[Dict[str, Any]]:
        """기회 우선순위 설정"""
        return [
            {"opportunity": "디지털 전환", "priority": "높음", "impact": "높음", "effort": "중간"},
            {"opportunity": "신규 세그먼트 진입", "priority": "중간", "impact": "높음", "effort": "높음"},
            {"opportunity": "서비스 차별화", "priority": "높음", "impact": "중간", "effort": "낮음"}
        ]
    
    def _create_opportunity_timeline(self, market_gaps: List, tech_opportunities: List) -> Dict[str, List[str]]:
        """기회 구현 타임라인"""
        return {
            "단기 (1-3개월)": ["디지털 마케팅 강화", "고객 서비스 개선"],
            "중기 (3-12개월)": ["기술 도입", "신규 서비스 개발"],
            "장기 (1-2년)": ["시장 확장", "브랜드 강화"]
        }
    
    def _analyze_technology_impact(self, industry: str) -> Dict[str, Any]:
        """기술 트렌드 영향 분석"""
        tech_impacts = {
            "restaurant": {
                "currentImpact": "중간",
                "futureImpact": "높음",
                "keyTechnologies": ["AI 추천", "무인 시스템", "배달 로봇"],
                "adoptionBarriers": ["비용", "기술 이해도", "고객 수용성"]
            },
            "retail": {
                "currentImpact": "높음",
                "futureImpact": "매우 높음",
                "keyTechnologies": ["AR/VR", "AI 개인화", "블록체인"],
                "adoptionBarriers": ["초기 투자", "기술 복잡성", "데이터 보안"]
            },
            "service": {
                "currentImpact": "높음",
                "futureImpact": "매우 높음",
                "keyTechnologies": ["AI 자동화", "예측 분석", "클라우드"],
                "adoptionBarriers": ["인력 재교육", "시스템 통합", "보안 우려"]
            }
        }
        
        return tech_impacts.get(industry, tech_impacts["service"])
    
    def _analyze_social_trends_impact(self, industry: str, region: str) -> Dict[str, Any]:
        """사회적 트렌드 영향 분석"""
        return {
            "demographicChanges": {
                "aging": "고령화 가속화",
                "singleHouseholds": "1인 가구 증가",
                "urbanization": "도시 집중화"
            },
            "culturalShifts": {
                "workLifeBalance": "워라밸 중시",
                "sustainability": "지속가능성 관심",
                "digitalization": "디지털 라이프스타일"
            },
            "economicFactors": {
                "incomeInequality": "소득 양극화",
                "sharingEconomy": "공유 경제 확산",
                "subscriptionModel": "구독 경제 성장"
            },
            "impactAssessment": "높음"
        }
    
    def _calculate_trend_score(self, trends: Dict, opportunities: Dict) -> int:
        """트렌드 점수 계산"""
        # 트렌드 성장률과 기회 요소를 종합하여 점수 산출
        base_score = 70
        
        # 핫 트렌드 가산점
        if trends.get("hotTrends"):
            hot_trend_count = len(trends["hotTrends"])
            base_score += min(hot_trend_count * 5, 20)
        
        # 기회 요소 가산점
        if opportunities.get("marketGaps"):
            gap_count = len(opportunities["marketGaps"])
            base_score += min(gap_count * 3, 15)
        
        return min(base_score, 100)
    
    def _generate_actionable_insights(self, trends: Dict, opportunities: Dict) -> List[str]:
        """실행 가능한 인사이트 생성"""
        insights = [
            "디지털 채널 강화를 통한 고객 접점 확대 필요",
            "개인화 서비스 도입으로 고객 만족도 향상 기대",
            "지속가능성 요소를 브랜드 가치에 반영 권장",
            "데이터 기반 의사결정 체계 구축 필요"
        ]
        
        return insights
    
    def _create_risk_matrix(self, general_risks: List, industry_risks: List) -> Dict[str, Any]:
        """위험 매트릭스 생성"""
        return {
            "highImpactHighProbability": ["트렌드 급변", "경쟁사 선점"],
            "highImpactLowProbability": ["규제 변화", "기술 혁신"],
            "lowImpactHighProbability": ["소비자 선호 변화"],
            "lowImpactLowProbability": ["경제 위기"]
        }
    
    def _develop_mitigation_strategies(self, industry: str, risks: List) -> List[Dict[str, str]]:
        """위험 완화 전략"""
        strategies = [
            {
                "risk": "트렌드 급변",
                "strategy": "다양한 트렌드 모니터링 시스템 구축",
                "timeline": "즉시"
            },
            {
                "risk": "경쟁사 선점",
                "strategy": "차별화된 가치 제안 개발",
                "timeline": "3개월"
            },
            {
                "risk": "투자 회수 실패",
                "strategy": "단계적 투자 및 성과 측정",
                "timeline": "지속적"
            }
        ]
        
        return strategies
    
    def _generate_market_recommendations(self, market_analysis: Dict, trend_analysis: Dict) -> List[Dict[str, Any]]:
        """시장 분석 기반 추천사항 생성"""
        recommendations = [
            {
                "category": "시장 진입 전략",
                "recommendation": "차별화된 포지셔닝으로 틈새시장 공략",
                "priority": "높음",
                "timeline": "1-3개월",
                "expectedImpact": "높음"
            },
            {
                "category": "디지털 전환",
                "recommendation": "온라인 채널 강화 및 디지털 마케팅 확대",
                "priority": "높음",
                "timeline": "즉시",
                "expectedImpact": "중간"
            },
            {
                "category": "고객 경험",
                "recommendation": "개인화 서비스 도입으로 고객 만족도 향상",
                "priority": "중간",
                "timeline": "3-6개월",
                "expectedImpact": "높음"
            },
            {
                "category": "운영 효율성",
                "recommendation": "자동화 시스템 도입으로 운영 비용 절감",
                "priority": "중간",
                "timeline": "6-12개월",
                "expectedImpact": "중간"
            }
        ]
        
        return recommendations
    
    def _get_fallback_market_size(self, industry: str, region: str) -> Dict[str, Any]:
        """폴백 시장 규모 데이터"""
        return {
            "totalMarketSize": "추정 불가",
            "regionalMarketSize": "데이터 없음",
            "targetMarketSize": "분석 필요",
            "growthRate": "일반적 성장률",
            "marketMaturity": "분석 불가",
            "regionalMultiplier": "50%",
            "competitiveIntensity": "중간",
            "marketSegments": {},
            "fallback": True
        }
    
    def _get_fallback_competitor_data(self, industry: str) -> Dict[str, Any]:
        """폴백 경쟁사 데이터"""
        return {
            "major": [
                {"name": "일반 경쟁사", "type": "기본", "strength": "일반적 강점"}
            ],
            "market_share": {"기타": "100%"},
            "fallback": True
        }
    
    def _get_fallback_trend_data(self, industry: str) -> Dict[str, Any]:
        """폴백 트렌드 데이터"""
        return {
            "hotTrends": [
                {"trend": "디지털 전환", "growth": "+20%", "period": "2024년"}
            ],
            "decliningTrends": [
                {"trend": "전통적 방식", "decline": "-10%", "reason": "기술 발전"}
            ],
            "trendVelocity": "보통",
            "regionalAdaptation": {"rate": "중간", "speed": "보통"},
            "competitorAdoption": {"earlyAdopters": "20%", "mainstream": "60%"},
            "consumerBehaviors": [],
            "fallback": True
        }
    
    def _get_fallback_trend_analysis(self, industry: str, region: str) -> Dict[str, Any]:
        """폴백 트렌드 분석"""
        return {
            "latestTrends": {"hotTrends": [], "decliningTrends": []},
            "consumerPreferences": {"behavioralChanges": []},
            "opportunities": {"marketGaps": []},
            "risks": {"generalRisks": []},
            "technologyImpact": {"currentImpact": "중간"},
            "socialTrends": {"impactAssessment": "중간"},
            "trendScore": 50,
            "actionableInsights": ["일반적인 시장 분석 필요"],
            "timestamp": datetime.utcnow().isoformat(),
            "fallback": True
        }
    
    def _identify_opportunities(self, industry: str, region: str, market_data: Dict) -> List[Dict[str, Any]]:
        """시장 기회 분석"""
        opportunities = [
            {
                "type": "digital_transformation",
                "description": f"{industry} 업종의 디지털 전환 가속화",
                "potential": "high",
                "timeframe": "1-2년"
            },
            {
                "type": "regional_expansion", 
                "description": f"{region} 지역 내 미개척 시장 존재",
                "potential": "medium",
                "timeframe": "6개월-1년"
            }
        ]
        return opportunities
    
    def _analyze_risks(self, industry: str, region: str, market_data: Dict) -> List[Dict[str, Any]]:
        """위험 요소 분석"""
        risks = [
            {
                "type": "market_saturation",
                "description": f"{industry} 시장 포화 위험",
                "probability": "medium",
                "impact": "high"
            },
            {
                "type": "regulatory_changes",
                "description": "규제 환경 변화 가능성",
                "probability": "low",
                "impact": "medium"
            }
        ]
        return risks
    
    def _estimate_market_size(self, industry: str, region: str, market_data: Dict) -> Dict[str, Any]:
        """시장 규모 추정 - DynamoDB에서 데이터 조회"""
        try:
            from shared.market_data_loader import get_market_data_loader
            
            market_loader = get_market_data_loader()
            result = market_loader.calculate_regional_market_size(industry, region)
            
            if "error" in result:
                logger.warning(f"Market data not found, using fallback: {result['error']}")
                return self._get_fallback_market_size(industry, region)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to estimate market size: {str(e)}")
            return self._get_fallback_market_size(industry, region)
    
    def _parse_market_size(self, size_str: str) -> float:
        """시장 규모 문자열을 숫자로 변환"""
        if "조원" in size_str:
            return float(size_str.replace("조원", ""))
        return 0.0
    
    def _assess_competitive_intensity(self, industry: str, region: str) -> str:
        """경쟁 강도 평가"""
        # 업종별 경쟁 강도
        industry_competition = {
            "restaurant": "매우 높음",
            "retail": "높음", 
            "service": "중간",
            "healthcare": "중간",
            "education": "높음",
            "technology": "매우 높음"
        }
        
        # 지역별 조정 (서울/경기는 경쟁이 더 치열)
        if region in ["seoul", "gyeonggi"]:
            return industry_competition.get(industry, "높음")
        else:
            competition_levels = ["낮음", "중간", "높음", "매우 높음"]
            current_level = industry_competition.get(industry, "중간")
            current_index = competition_levels.index(current_level)
            adjusted_index = max(0, current_index - 1)
            return competition_levels[adjusted_index]
    
    def _analyze_growth_trends(self, market_data: Dict) -> Dict[str, Any]:
        """성장 트렌드 분석 - 업종별 세분화"""
        
        # 전체 시장 메가트렌드
        mega_trends = [
            {
                "trend": "디지털 전환 가속화",
                "impact": "높음",
                "timeline": "현재 진행중",
                "description": "코로나19 이후 디지털 채널 확산"
            },
            {
                "trend": "개인화/맞춤화 서비스",
                "impact": "높음", 
                "timeline": "2-3년",
                "description": "AI 기반 개인 맞춤 서비스 확산"
            },
            {
                "trend": "ESG 경영 확산",
                "impact": "중간",
                "timeline": "3-5년",
                "description": "환경, 사회적 책임 중시"
            },
            {
                "trend": "구독 경제 확산",
                "impact": "중간",
                "timeline": "1-2년",
                "description": "소유에서 이용으로 패러다임 변화"
            }
        ]
        
        # 업종별 특화 트렌드
        industry_trends = {
            "restaurant": [
                {"trend": "배달/테이크아웃 확산", "growth": "+25%"},
                {"trend": "건강식 메뉴 선호", "growth": "+18%"},
                {"trend": "무인 주문 시스템", "growth": "+35%"},
                {"trend": "로컬 푸드 트렌드", "growth": "+22%"}
            ],
            "retail": [
                {"trend": "O2O 통합 서비스", "growth": "+30%"},
                {"trend": "라이브 커머스", "growth": "+45%"},
                {"trend": "친환경 제품", "growth": "+28%"},
                {"trend": "개인화 큐레이션", "growth": "+20%"}
            ],
            "service": [
                {"trend": "비대면 서비스", "growth": "+40%"},
                {"trend": "AI 상담 서비스", "growth": "+35%"},
                {"trend": "구독형 서비스", "growth": "+25%"},
                {"trend": "플랫폼 기반 서비스", "growth": "+30%"}
            ],
            "healthcare": [
                {"trend": "원격 의료", "growth": "+50%"},
                {"trend": "예방 중심 헬스케어", "growth": "+32%"},
                {"trend": "개인 맞춤 의료", "growth": "+28%"},
                {"trend": "디지털 헬스케어", "growth": "+42%"}
            ],
            "education": [
                {"trend": "온라인/블렌디드 교육", "growth": "+60%"},
                {"trend": "AI 맞춤 학습", "growth": "+38%"},
                {"trend": "마이크로 러닝", "growth": "+25%"},
                {"trend": "실무 중심 교육", "growth": "+30%"}
            ],
            "technology": [
                {"trend": "클라우드 전환", "growth": "+45%"},
                {"trend": "AI/ML 도입", "growth": "+55%"},
                {"trend": "사이버 보안", "growth": "+40%"},
                {"trend": "메타버스/AR/VR", "growth": "+65%"}
            ]
        }
        
        # 소비자 행동 변화 트렌드
        consumer_trends = [
            {
                "behavior": "온라인 우선 구매",
                "percentage": "78%",
                "age_group": "20-40대"
            },
            {
                "behavior": "가성비 중시",
                "percentage": "85%", 
                "age_group": "전 연령"
            },
            {
                "behavior": "브랜드 가치 중시",
                "percentage": "65%",
                "age_group": "30-50대"
            },
            {
                "behavior": "개인화 서비스 선호",
                "percentage": "72%",
                "age_group": "20-30대"
            }
        ]
        
        return {
            "megaTrends": mega_trends,
            "industryTrends": industry_trends.get("service", []),  # 기본값
            "consumerTrends": consumer_trends,
            "emergingOpportunities": self._identify_emerging_opportunities(),
            "disruptiveFactors": self._identify_disruptive_factors()
        }
    
    def _identify_emerging_opportunities(self) -> List[Dict[str, str]]:
        """신흥 기회 요소"""
        return [
            {
                "opportunity": "시니어 시장 확대",
                "potential": "높음",
                "timeline": "1-2년",
                "description": "고령화로 인한 새로운 수요 창출"
            },
            {
                "opportunity": "1인 가구 증가",
                "potential": "높음", 
                "timeline": "현재",
                "description": "개인 맞춤형 서비스 수요 증가"
            },
            {
                "opportunity": "지방 소멸 대응",
                "potential": "중간",
                "timeline": "3-5년",
                "description": "지역 특화 서비스 기회"
            },
            {
                "opportunity": "MZ세대 소비 패턴",
                "potential": "높음",
                "timeline": "현재",
                "description": "경험 중심, 가치 소비 확산"
            }
        ]
    
    def _identify_disruptive_factors(self) -> List[Dict[str, str]]:
        """파괴적 변화 요소"""
        return [
            {
                "factor": "AI 자동화",
                "impact": "높음",
                "timeline": "2-3년",
                "description": "인간 업무의 AI 대체 가속화"
            },
            {
                "factor": "플랫폼 경제",
                "impact": "높음",
                "timeline": "현재",
                "description": "중간 유통업체 역할 변화"
            },
            {
                "factor": "규제 변화",
                "impact": "중간",
                "timeline": "1-2년", 
                "description": "새로운 규제로 인한 시장 변화"
            },
            {
                "factor": "글로벌 공급망 변화",
                "impact": "중간",
                "timeline": "2-3년",
                "description": "공급망 재편으로 인한 비용 구조 변화"
            }
        ]
    
    def _analyze_customer_segments(self, industry: str, region: str) -> List[Dict[str, Any]]:
        """고객 세그먼트 분석"""
        return [
            {
                "segment": "주요 타겟층",
                "characteristics": "25-40세, 중간 소득층",
                "size": "전체의 45%",
                "growth": "연 12% 증가"
            },
            {
                "segment": "신규 타겟층",
                "characteristics": "40-55세, 고소득층",
                "size": "전체의 25%",
                "growth": "연 18% 증가"
            }
        ]
    
    def _analyze_pricing_trends(self, industry: str, market_data: Dict) -> Dict[str, Any]:
        """가격 트렌드 분석"""
        return {
            "averagePrice": "중간 수준",
            "priceTrend": "안정적",
            "priceElasticity": "중간",
            "competitivePricing": "필요"
        }
    
    def _analyze_regulatory_environment(self, industry: str, region: str) -> Dict[str, Any]:
        """규제 환경 분석"""
        return {
            "currentRegulations": "일반적 수준",
            "upcomingChanges": "없음",
            "complianceRequirements": "기본 사업자 등록",
            "regulatoryRisk": "낮음"
        }
    
    def _extract_major_competitors(self, competitor_data: List) -> List[str]:
        """주요 경쟁사 추출"""
        return ["경쟁사 A", "경쟁사 B", "경쟁사 C"]
    
    def _analyze_market_share(self, competitor_data: List) -> Dict[str, str]:
        """시장 점유율 분석"""
        return {
            "경쟁사 A": "25%",
            "경쟁사 B": "18%",
            "경쟁사 C": "15%",
            "기타": "42%"
        }
    
    def _identify_competitive_advantages(self, competitor_data: List) -> List[str]:
        """경쟁 우위 요소"""
        return ["브랜드 인지도", "유통망", "기술력"]
    
    def _identify_competitive_threats(self, competitor_data: List) -> List[str]:
        """경쟁 위협 요소"""
        return ["가격 경쟁", "신규 진입자", "대체재"]
    
    def _get_fallback_market_analysis(self, industry: str, region: str) -> Dict[str, Any]:
        """폴백 시장 분석"""
        return {
            "marketSize": {
                "totalMarketSize": "추정 불가",
                "regionalMarketSize": "데이터 없음",
                "growthRate": "일반적 성장률",
                "marketMaturity": "분석 불가"
            },
            "growthTrends": {
                "megaTrends": [],
                "industryTrends": [],
                "consumerTrends": []
            },
            "competitorAnalysis": {
                "majorCompetitors": [],
                "marketShare": {},
                "competitiveAdvantages": [],
                "competitiveThreats": []
            },
            "marketOpportunities": [],
            "riskFactors": [],
            "timestamp": datetime.utcnow().isoformat(),
            "fallback": True
        }
    
    def _get_fallback_competitor_analysis(self, industry: str, region: str) -> Dict[str, Any]:
        """폴백 경쟁사 분석"""
        return {
            "majorCompetitors": [
                {"name": "일반 경쟁사", "type": "기본", "strength": "일반적 강점"}
            ],
            "marketShare": {"기타": "100%"},
            "competitiveAdvantages": ["품질", "서비스"],
            "competitiveThreats": ["가격 경쟁", "신규 진입"],
            "entryBarriers": [
                {"barrier": "초기 투자", "level": "중간", "description": "일반적 투자 필요"}
            ],
            "competitivePositioning": {
                "recommendedStrategy": "차별화 전략",
                "differentiationFactors": ["품질", "서비스"],
                "targetSegment": "일반 고객층",
                "valueProposition": "고품질 서비스"
            },
            "benchmarkMetrics": {"고객 만족도": "80%"},
            "fallback": True
        }
    
    def _save_market_analysis(self, session_id: str, market_analysis: Dict[str, Any]):
        """시장 분석 결과를 세션에 저장"""
        try:
            self.sessions_table.update_item(
                Key={'sessionId': session_id},
                UpdateExpression='SET marketAnalysis = :analysis, updatedAt = :timestamp',
                ExpressionAttributeValues={
                    ':analysis': market_analysis,
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to save market analysis: {str(e)}")

# Lambda 핸들러
market_analyst_agent = MarketAnalystAgent()

def lambda_handler(event, context):
    return market_analyst_agent.lambda_handler(event, context)