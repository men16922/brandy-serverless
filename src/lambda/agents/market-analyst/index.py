# Market Analyst Agent Lambda Function
# 시장 동향 및 경쟁사 분석, Bedrock KB에서 관련 데이터 검색

import json
import boto3
import logging
from datetime import datetime
import os
from typing import Dict, Any, List

# 공통 유틸리티 import - Lambda Layer structure
import sys
sys.path.insert(0, '/opt/python/python')
from shared.utils import setup_logging, get_aws_clients, create_response
from shared.agent_communication import AgentCommunication
from shared.knowledge_base import get_knowledge_base
from shared.bedrock_client import BedrockClient, BedrockException
from shared.reasoning_engine import ReasoningEngine

logger = setup_logging()

class MarketAnalystAgent:
    def __init__(self):
        self.aws_clients = get_aws_clients()
        self.dynamodb = self.aws_clients['dynamodb']
        self.sessions_table = self.dynamodb.Table(os.getenv('SESSIONS_TABLE'))
        self.knowledge_base = get_knowledge_base()
        self.agent_comm = AgentCommunication()
        
        # Bedrock integration (Requirement 1.3, 3.2, 5.2)
        self.enable_fallback = os.getenv('ENABLE_FALLBACK', 'true').lower() == 'true'
        self.dev_profile = os.getenv('DEV_PROFILE', 'false').lower() == 'true'
        
        try:
            self.bedrock_client = BedrockClient(logger=logger)
            self.reasoning_engine = ReasoningEngine(bedrock_client=self.bedrock_client, logger=logger)
            logger.info("Market Analyst Agent initialized with Bedrock integration")
        except Exception as e:
            logger.warning(f"Bedrock initialization failed: {str(e)}. Using fallback mode.")
            self.bedrock_client = None
            self.reasoning_engine = None
            self.enable_fallback = True
        
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
        """최신 시장 트렌드 분석 - Bedrock Claude reasoning 사용 (Requirement 3.2)"""
        try:
            from shared.market_data_loader import get_market_data_loader
            
            market_loader = get_market_data_loader()
            trend_data = market_loader.get_industry_trends(industry)
            
            if trend_data:
                hot_trends = trend_data.get("hot_trends", [])
                declining_trends = trend_data.get("declining_trends", [])
                
                # Use Bedrock Claude for trend reasoning (Requirement 3.2)
                if self.reasoning_engine and not self.dev_profile:
                    try:
                        logger.info(f"Using Bedrock reasoning for trend analysis: {industry}")
                        
                        # Prepare context for reasoning
                        context = {
                            "industry": industry,
                            "region": region,
                            "hot_trends": hot_trends,
                            "declining_trends": declining_trends,
                            "consumer_behaviors": trend_data.get("consumer_behaviors", [])
                        }
                        
                        # Use reasoning engine to analyze trend implications
                        reasoning_result = self.reasoning_engine.reason_and_decide(
                            context=context,
                            options=["aggressive_adoption", "cautious_adoption", "wait_and_see"],
                            decision_criteria="Determine the best strategy for adopting these market trends based on industry dynamics and regional characteristics",
                            temperature=0.4
                        )
                        
                        # Enhance trend data with reasoning insights
                        return {
                            "hotTrends": hot_trends,
                            "decliningTrends": declining_trends,
                            "trendVelocity": self._calculate_trend_velocity(hot_trends),
                            "regionalAdaptation": self._analyze_regional_trend_adaptation(region, trend_data),
                            "competitorAdoption": self._analyze_competitor_trend_adoption(industry, trend_data),
                            "consumerBehaviors": trend_data.get("consumer_behaviors", []),
                            "aiRecommendedStrategy": reasoning_result.get('decision'),
                            "strategyReasoning": reasoning_result.get('reasoning'),
                            "strategyConfidence": reasoning_result.get('confidence'),
                            "source": "bedrock_reasoning"
                        }
                    except BedrockException as e:
                        logger.warning(f"Bedrock reasoning failed: {str(e)}. Using fallback.")
                        # Continue with fallback logic below
                
                # Fallback: return trend data without AI reasoning
                return {
                    "hotTrends": hot_trends,
                    "decliningTrends": declining_trends,
                    "trendVelocity": self._calculate_trend_velocity(hot_trends),
                    "regionalAdaptation": self._analyze_regional_trend_adaptation(region, trend_data),
                    "competitorAdoption": self._analyze_competitor_trend_adoption(industry, trend_data),
                    "consumerBehaviors": trend_data.get("consumer_behaviors", []),
                    "source": "fallback"
                }
            else:
                logger.warning(f"Trend data not found for {industry}, using fallback")
                return self._get_fallback_trend_data(industry)
                
        except Exception as e:
            logger.error(f"Latest trends analysis failed: {str(e)}")
            return self._get_fallback_trend_data(industry)
    
    def _analyze_consumer_preferences(self, industry: str, region: str) -> Dict[str, Any]:
        """소비자 선호도 변화 분석 - JSON + DynamoDB 로더 사용"""
        from data_loader import get_data_loader
        from dynamodb_loader import get_dynamodb_loader
        
        # JSON에서 정적 데이터 로드
        json_loader = get_data_loader()
        generational_preferences = json_loader.get_generational_preferences()
        regional_preferences = json_loader.get_regional_preferences()
        
        # DynamoDB에서 동적 데이터 로드
        db_loader = get_dynamodb_loader()
        behavioral_changes_data = db_loader.get_behavioral_changes(industry, region="GLOBAL")
        
        # Fallback for behavioral changes
        if not behavioral_changes_data:
            behavioral_changes_data = [
                {"change": "디지털 전환 가속화", "percentage": "+60%"},
                {"change": "개인화 서비스 선호", "percentage": "+55%"}
            ]
        
        return {
            "generationalPreferences": generational_preferences,
            "regionalPreferences": regional_preferences.get(region, regional_preferences.get("seoul", [])),
            "behavioralChanges": behavioral_changes_data,
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
        """트렌드 관련 위험 분석 - JSON + DynamoDB 로더 사용"""
        from data_loader import get_data_loader
        from dynamodb_loader import get_dynamodb_loader
        
        # JSON에서 일반 트렌드 위험 로드
        json_loader = get_data_loader()
        trend_risks = json_loader.get_trend_risks()
        
        # DynamoDB에서 업종별 특화 위험 로드
        db_loader = get_dynamodb_loader()
        industry_specific_risks = db_loader.get_industry_risks(industry, region="GLOBAL")
        
        # Fallback for industry risks
        if not industry_specific_risks:
            industry_specific_risks = [
                {"risk": "시장 변동성", "impact": "중간"},
                {"risk": "경쟁 심화", "impact": "높음"}
            ]
        
        return {
            "generalRisks": trend_risks,
            "industryRisks": industry_specific_risks,
            "riskMatrix": self._create_risk_matrix(trend_risks, industry_specific_risks),
            "mitigationStrategies": self._develop_mitigation_strategies(industry, trend_risks)
        }
    
    def _query_market_data(self, industry: str, region: str) -> Dict[str, Any]:
        """Knowledge Base에서 시장 데이터 조회 - Bedrock KB 우선, Chroma fallback"""
        try:
            # Try Bedrock Knowledge Base first (Requirement 5.2)
            if self.bedrock_client and not self.dev_profile:
                logger.info(f"Querying Bedrock KB for market data: {industry}, {region}")
                
                # 시장 규모 및 성장률 데이터
                market_size_query = f"{industry} 시장 규모 성장률 전망"
                market_size_result = self.bedrock_client.query_knowledge_base(
                    query=market_size_query,
                    max_results=5,
                    min_score=0.5
                )
                market_size_data = [
                    {'content': r['content'], 'score': r['score']}
                    for r in market_size_result.get('results', [])
                ]
                
                # 시장 트렌드 데이터
                trends_query = f"{industry} 시장 트렌드 변화 동향"
                trends_result = self.bedrock_client.query_knowledge_base(
                    query=trends_query,
                    max_results=5,
                    min_score=0.5
                )
                trends_data = [
                    {'content': r['content'], 'score': r['score']}
                    for r in trends_result.get('results', [])
                ]
                
                # 지역별 시장 특성
                regional_query = f"{region} {industry} 시장 특성 현황"
                regional_result = self.bedrock_client.query_knowledge_base(
                    query=regional_query,
                    max_results=3,
                    min_score=0.5
                )
                regional_data = [
                    {'content': r['content'], 'score': r['score']}
                    for r in regional_result.get('results', [])
                ]
                
                logger.info(
                    f"Bedrock KB query successful: "
                    f"market_size={len(market_size_data)}, "
                    f"trends={len(trends_data)}, "
                    f"regional={len(regional_data)}"
                )
                
                return {
                    "market_size_data": market_size_data,
                    "trends_data": trends_data,
                    "regional_data": regional_data,
                    "source": "bedrock_kb"
                }
            
            # Fallback to Chroma (local development)
            elif self.enable_fallback:
                logger.info(f"Using Chroma fallback for market data: {industry}, {region}")
                
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
                    "source": "chroma_fallback"
                }
            
            else:
                logger.warning("No knowledge base available and fallback disabled")
                return {"source": "none"}
            
        except BedrockException as e:
            logger.error(f"Bedrock KB query failed: {str(e)}")
            # Fallback to Chroma if Bedrock fails
            if self.enable_fallback:
                logger.info("Falling back to Chroma after Bedrock failure")
                return self._query_market_data_fallback(industry, region)
            return {"source": "error"}
        except Exception as e:
            logger.error(f"Market data query failed: {str(e)}")
            return {"source": "fallback"}
    
    def _query_market_data_fallback(self, industry: str, region: str) -> Dict[str, Any]:
        """Fallback method for market data query using Chroma"""
        try:
            market_size_query = f"{industry} 시장 규모 성장률 전망"
            market_size_data = self.knowledge_base.search(market_size_query, top_k=5)
            
            trends_query = f"{industry} 시장 트렌드 변화 동향"
            trends_data = self.knowledge_base.search(trends_query, top_k=5)
            
            regional_query = f"{region} {industry} 시장 특성 현황"
            regional_data = self.knowledge_base.search(regional_query, top_k=3)
            
            return {
                "market_size_data": market_size_data,
                "trends_data": trends_data,
                "regional_data": regional_data,
                "source": "chroma_fallback"
            }
        except Exception as e:
            logger.error(f"Fallback market data query failed: {str(e)}")
            return {"source": "error"}
    
    def _analyze_competitors(self, industry: str, region: str) -> Dict[str, Any]:
        """경쟁사 분석 - Bedrock Claude reasoning 사용 (Requirement 3.2)"""
        try:
            # Query knowledge base for competitor data
            if self.bedrock_client and not self.dev_profile:
                # Use Bedrock KB
                competitors_query = f"{industry} 주요 경쟁사 시장 점유율"
                kb_result = self.bedrock_client.query_knowledge_base(
                    query=competitors_query,
                    max_results=5,
                    min_score=0.5
                )
                competitor_kb_data = [
                    {'content': r['content'], 'score': r['score']}
                    for r in kb_result.get('results', [])
                ]
            elif self.enable_fallback:
                # Fallback to Chroma
                competitors_query = f"{industry} 주요 경쟁사 시장 점유율"
                competitor_kb_data = self.knowledge_base.search(competitors_query, top_k=5)
            else:
                competitor_kb_data = []
            
            # 업종별 주요 경쟁사 데이터
            industry_competitors = self._get_industry_competitors(industry, region)
            
            # Use Bedrock Claude for competitive positioning reasoning
            if self.reasoning_engine and not self.dev_profile:
                try:
                    logger.info(f"Using Bedrock reasoning for competitive analysis: {industry}")
                    
                    # Prepare context for reasoning
                    context = {
                        "industry": industry,
                        "region": region,
                        "major_competitors": industry_competitors["major"],
                        "market_share": industry_competitors["market_share"],
                        "kb_insights": competitor_kb_data[:3] if competitor_kb_data else []
                    }
                    
                    # Use reasoning engine for competitive positioning
                    positioning_result = self.reasoning_engine.reason_and_decide(
                        context=context,
                        options=["differentiation", "cost_leadership", "niche_focus", "innovation"],
                        decision_criteria="Determine the best competitive positioning strategy based on market dynamics, competitor landscape, and regional characteristics",
                        temperature=0.4
                    )
                    
                    return {
                        "majorCompetitors": industry_competitors["major"],
                        "marketShare": industry_competitors["market_share"],
                        "competitiveAdvantages": self._identify_competitive_advantages(industry),
                        "competitiveThreats": self._identify_competitive_threats(industry, region),
                        "entryBarriers": self._analyze_entry_barriers(industry),
                        "competitivePositioning": self._suggest_competitive_positioning(industry, region),
                        "benchmarkMetrics": self._get_benchmark_metrics(industry),
                        "aiRecommendedStrategy": positioning_result.get('decision'),
                        "strategyReasoning": positioning_result.get('reasoning'),
                        "strategyConfidence": positioning_result.get('confidence'),
                        "alternativeStrategies": positioning_result.get('alternatives', []),
                        "source": "bedrock_reasoning"
                    }
                except BedrockException as e:
                    logger.warning(f"Bedrock reasoning failed: {str(e)}. Using fallback.")
                    # Continue with fallback logic below
            
            # Fallback: return competitor analysis without AI reasoning
            return {
                "majorCompetitors": industry_competitors["major"],
                "marketShare": industry_competitors["market_share"],
                "competitiveAdvantages": self._identify_competitive_advantages(industry),
                "competitiveThreats": self._identify_competitive_threats(industry, region),
                "entryBarriers": self._analyze_entry_barriers(industry),
                "competitivePositioning": self._suggest_competitive_positioning(industry, region),
                "benchmarkMetrics": self._get_benchmark_metrics(industry),
                "source": "fallback"
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
        """진입 장벽 분석 - JSON 로더 사용"""
        from data_loader import get_data_loader
        
        loader = get_data_loader()
        barriers_data = loader.get_entry_barriers()
        
        return barriers_data.get(industry, barriers_data.get("service", []))
    
    def _suggest_competitive_positioning(self, industry: str, region: str) -> Dict[str, Any]:
        """경쟁 포지셔닝 제안"""
        return {
            "recommendedStrategy": self._get_positioning_strategy(industry, region),
            "differentiationFactors": self._get_differentiation_factors(industry),
            "targetSegment": self._get_target_segment(industry, region),
            "valueProposition": self._get_value_proposition(industry)
        }
    
    def _get_positioning_strategy(self, industry: str, region: str) -> str:
        """포지셔닝 전략 - JSON 로더 사용"""
        from data_loader import get_data_loader
        
        loader = get_data_loader()
        strategies = loader.get_positioning_strategies()
        
        return strategies.get(industry, "고품질 서비스 차별화")
    
    def _get_differentiation_factors(self, industry: str) -> List[str]:
        """차별화 요소 - JSON 로더 사용"""
        from data_loader import get_data_loader
        
        loader = get_data_loader()
        factors = loader.get_differentiation_factors()
        
        return factors.get(industry, ["품질", "서비스", "가격", "편의성"])
    
    def _get_target_segment(self, industry: str, region: str) -> str:
        """타겟 세그먼트 - JSON 로더 사용"""
        from data_loader import get_data_loader
        
        loader = get_data_loader()
        segments = loader.get_target_segments()
        
        return segments.get(industry, "품질 중시 고객층")
    
    def _get_value_proposition(self, industry: str) -> str:
        """가치 제안 - JSON 로더 사용"""
        from data_loader import get_data_loader
        
        loader = get_data_loader()
        propositions = loader.get_value_propositions()
        
        return propositions.get(industry, "고품질 서비스로 고객 만족")
    
    def _get_benchmark_metrics(self, industry: str) -> Dict[str, str]:
        """벤치마크 지표 - DynamoDB 로더 사용"""
        from dynamodb_loader import get_dynamodb_loader
        
        loader = get_dynamodb_loader()
        metrics = loader.get_benchmark_metrics(industry, region="GLOBAL")
        
        # Fallback
        if not metrics:
            metrics = {"고객 만족도": "85%", "재이용률": "70%"}
        
        return metrics
    
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
        """지역별 트렌드 적응도 분석 - JSON 로더 사용"""
        from data_loader import get_data_loader
        
        loader = get_data_loader()
        adaptation_rates = loader.get_regional_adaptation_rates()
        
        return adaptation_rates.get(region, {"rate": "중간", "speed": "보통", "openness": "중간"})
    
    def _analyze_competitor_trend_adoption(self, industry: str, trends: Dict) -> Dict[str, str]:
        """경쟁사 트렌드 도입 현황 - JSON 로더 사용"""
        from data_loader import get_data_loader
        
        loader = get_data_loader()
        return loader.get_competitor_adoption()
    
    def _extract_preference_insights(self, industry: str, region: str) -> List[str]:
        """선호도 변화 핵심 인사이트 - DynamoDB 로더 사용"""
        from dynamodb_loader import get_dynamodb_loader
        
        loader = get_dynamodb_loader()
        insights = loader.get_preference_insights(industry, region="GLOBAL")
        
        # Fallback
        if not insights:
            insights = [
                "고품질 서비스 선호",
                "개인화 경험 중시",
                "투명성 요구 증가"
            ]
        
        return insights
    
    def _project_future_preferences(self, industry: str) -> Dict[str, Any]:
        """미래 선호도 전망 - DynamoDB 로더 사용"""
        from dynamodb_loader import get_dynamodb_loader
        
        loader = get_dynamodb_loader()
        projection = loader.get_future_projections(industry, region="GLOBAL")
        
        # Fallback
        if not projection:
            projection = {
                "timeframe": "2025-2027",
                "keyChanges": [
                    "AI 기반 개인화 서비스 확산",
                    "지속가능성 중시 확대",
                    "경험 중심 소비 증가"
                ],
                "impactLevel": "높음"
            }
        
        return projection
    
    def _identify_market_gaps(self, industry: str, region: str) -> List[Dict[str, Any]]:
        """시장 갭 분석 - DynamoDB 로더 사용"""
        from dynamodb_loader import get_dynamodb_loader
        
        loader = get_dynamodb_loader()
        gaps = loader.get_market_gaps(industry, region="GLOBAL")
        
        # Fallback
        if not gaps:
            gaps = [
                {"gap": "미충족 고객 니즈", "size": "중간", "difficulty": "중간"}
            ]
        
        return gaps
    
    def _identify_new_segments(self, industry: str, region: str) -> List[Dict[str, Any]]:
        """신규 고객 세그먼트 - DynamoDB 로더 사용"""
        from dynamodb_loader import get_dynamodb_loader
        
        loader = get_dynamodb_loader()
        segments = loader.get_customer_segments(limit=10)
        
        # Fallback
        if not segments:
            segments = [
                {
                    "segment": "디지털 네이티브 시니어",
                    "size": "증가 중",
                    "characteristics": "기술 친화적 50-60대",
                    "opportunity": "높음"
                }
            ]
        
        return segments
    
    def _identify_tech_opportunities(self, industry: str) -> List[Dict[str, Any]]:
        """기술 기회 분석 - DynamoDB 로더 사용"""
        from dynamodb_loader import get_dynamodb_loader
        
        loader = get_dynamodb_loader()
        opportunities = loader.get_tech_opportunities(industry, region="GLOBAL")
        
        # Fallback
        if not opportunities:
            opportunities = [
                {"tech": "AI 챗봇", "maturity": "높음", "impact": "높음"},
                {"tech": "예측 분석", "maturity": "중간", "impact": "높음"},
                {"tech": "자동화 워크플로", "maturity": "중간", "impact": "중간"}
            ]
        }
        
        return opportunities.get(industry, opportunities["service"])
    
    def _identify_partnership_opportunities(self, industry: str, size: str) -> List[Dict[str, Any]]:
        """파트너십 기회 - JSON 로더 사용"""
        from data_loader import get_data_loader
        
        loader = get_data_loader()
        return loader.get_partnership_opportunities()
    
    def _identify_expansion_opportunities(self, industry: str, region: str, size: str) -> List[Dict[str, Any]]:
        """확장 기회 - JSON 로더 사용"""
        from data_loader import get_data_loader
        
        loader = get_data_loader()
        return loader.get_expansion_opportunities()
    
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
        """기술 트렌드 영향 분석 - JSON 로더 사용"""
        from data_loader import get_data_loader
        
        loader = get_data_loader()
        tech_impacts = loader.get_tech_impacts()
        
        impact = tech_impacts.get(industry, {
            "currentImpact": "중간",
            "futureImpact": "높음",
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
        """시장 분석 기반 추천사항 생성 - Bedrock Claude synthesis 사용 (Requirement 3.2)"""
        # Use Bedrock Claude for insight synthesis
        if self.reasoning_engine and not self.dev_profile:
            try:
                logger.info("Using Bedrock Claude for market recommendations synthesis")
                
                # Prepare agent outputs for synthesis
                agent_outputs = {
                    "market_analysis": {
                        "market_size": market_analysis.get("marketSize", {}),
                        "growth_trends": market_analysis.get("growthTrends", {}),
                        "opportunities": market_analysis.get("marketOpportunities", []),
                        "risks": market_analysis.get("riskFactors", []),
                        "competitor_analysis": market_analysis.get("competitorAnalysis", {})
                    },
                    "trend_analysis": {
                        "hot_trends": trend_analysis.get("latestTrends", {}).get("hotTrends", []),
                        "consumer_preferences": trend_analysis.get("consumerPreferences", {}),
                        "opportunities": trend_analysis.get("opportunities", {}),
                        "risks": trend_analysis.get("risks", {}),
                        "technology_impact": trend_analysis.get("technologyImpact", {})
                    }
                }
                
                # Synthesize insights using Bedrock Claude
                synthesis = self.reasoning_engine.synthesize_insights(
                    agent_outputs=agent_outputs,
                    temperature=0.5
                )
                
                # Extract structured recommendations from synthesis
                recommendations = self._extract_recommendations_from_synthesis(synthesis)
                
                logger.info(f"Generated {len(recommendations)} recommendations using Bedrock synthesis")
                return recommendations
                
            except BedrockException as e:
                logger.warning(f"Bedrock synthesis failed: {str(e)}. Using fallback.")
                # Continue with fallback logic below
        
        # Fallback: generate recommendations using rule-based logic
        recommendations = [
            {
                "category": "시장 진입 전략",
                "recommendation": "차별화된 포지셔닝으로 틈새시장 공략",
                "priority": "높음",
                "timeline": "1-3개월",
                "expectedImpact": "높음",
                "source": "fallback"
            },
            {
                "category": "디지털 전환",
                "recommendation": "온라인 채널 강화 및 디지털 마케팅 확대",
                "priority": "높음",
                "timeline": "즉시",
                "expectedImpact": "중간",
                "source": "fallback"
            },
            {
                "category": "고객 경험",
                "recommendation": "개인화 서비스 도입으로 고객 만족도 향상",
                "priority": "중간",
                "timeline": "3-6개월",
                "expectedImpact": "높음",
                "source": "fallback"
            },
            {
                "category": "운영 효율성",
                "recommendation": "자동화 시스템 도입으로 운영 비용 절감",
                "priority": "중간",
                "timeline": "6-12개월",
                "expectedImpact": "중간",
                "source": "fallback"
            }
        ]
        
        return recommendations
    
    def _extract_recommendations_from_synthesis(self, synthesis: str) -> List[Dict[str, Any]]:
        """Extract structured recommendations from Bedrock synthesis text"""
        # Parse synthesis text to extract recommendations
        # This is a simple implementation - could be enhanced with more sophisticated parsing
        recommendations = []
        
        # Split synthesis into sections and extract key recommendations
        lines = synthesis.split('\n')
        current_category = "일반 전략"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for recommendation patterns
            if any(keyword in line.lower() for keyword in ['recommend', '추천', 'should', '해야', 'suggest', '제안']):
                # Extract recommendation
                recommendation_text = line.strip('- •*').strip()
                
                # Determine priority based on keywords
                priority = "높음" if any(word in line.lower() for word in ['critical', '중요', 'urgent', '즉시', 'priority']) else "중간"
                
                # Determine timeline based on keywords
                if any(word in line.lower() for word in ['immediate', '즉시', 'now', '지금']):
                    timeline = "즉시"
                elif any(word in line.lower() for word in ['short', '단기', '1-3']):
                    timeline = "1-3개월"
                elif any(word in line.lower() for word in ['medium', '중기', '3-6']):
                    timeline = "3-6개월"
                else:
                    timeline = "6-12개월"
                
                recommendations.append({
                    "category": current_category,
                    "recommendation": recommendation_text,
                    "priority": priority,
                    "timeline": timeline,
                    "expectedImpact": "높음",
                    "source": "bedrock_synthesis"
                })
            
            # Update category if we find a section header
            elif line.endswith(':') or any(word in line for word in ['전략', 'Strategy', '방안', 'Approach']):
                current_category = line.rstrip(':').strip()
        
        # If no recommendations extracted, create a general one from the synthesis
        if not recommendations:
            recommendations.append({
                "category": "종합 전략",
                "recommendation": synthesis[:200] + "..." if len(synthesis) > 200 else synthesis,
                "priority": "높음",
                "timeline": "1-3개월",
                "expectedImpact": "높음",
                "source": "bedrock_synthesis"
            })
        
        return recommendations[:5]  # Return top 5 recommendations
    
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
        """경쟁 강도 평가 - JSON 로더 사용"""
        from data_loader import get_data_loader
        
        loader = get_data_loader()
        industry_competition = loader.get_industry_competition()
        
        # 지역별 조정 (서울/경기는 경쟁이 더 치열)
        if region in ["seoul", "gyeonggi"]:
            return industry_competition.get(industry, "높음")
        else:
            competition_levels = ["낮음", "중간", "높음", "매우 높음"]
            current_level = industry_competition.get(industry, "중간")
            if current_level in competition_levels:
                current_index = competition_levels.index(current_level)
                adjusted_index = max(0, current_index - 1)
                return competition_levels[adjusted_index]
            return current_level
    
    def _analyze_growth_trends(self, market_data: Dict) -> Dict[str, Any]:
        """성장 트렌드 분석 - JSON 로더 사용"""
        from data_loader import get_data_loader
        
        loader = get_data_loader()
        
        # JSON에서 메가트렌드와 소비자 트렌드 로드
        mega_trends = loader.get_mega_trends()
        consumer_trends = loader.get_consumer_trends()
        
        # industry_trends는 간단한 fallback으로 처리
        industry_trends = {
            "restaurant": [{"trend": "배달/테이크아웃 확산", "growth": "+25%"}],
            "retail": [{"trend": "O2O 통합 서비스", "growth": "+30%"}],
            "service": [{"trend": "비대면 서비스", "growth": "+40%"}],
            "healthcare": [{"trend": "원격 의료", "growth": "+50%"}],
            "education": [{"trend": "온라인/블렌디드 교육", "growth": "+60%"}],
            "technology": [{"trend": "클라우드 전환", "growth": "+45%"}]
        }
        
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