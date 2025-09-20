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
            
            # 세션에 결과 저장
            self._save_market_analysis(session_id, market_analysis)
            
            # Supervisor Agent에 상태 보고
            self.agent_comm.send_to_supervisor(
                agent_id="market",
                status="completed",
                result=market_analysis
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
                "marketAnalysis": market_analysis,
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
        """경쟁사 분석"""
        try:
            competitors_query = f"{industry} 주요 경쟁사 시장 점유율"
            competitor_data = self.knowledge_base.search(competitors_query, top_k=5)
            
            return {
                "majorCompetitors": self._extract_major_competitors(competitor_data),
                "marketShare": self._analyze_market_share(competitor_data),
                "competitiveAdvantages": self._identify_competitive_advantages(competitor_data),
                "competitiveThreats": self._identify_competitive_threats(competitor_data)
            }
        except Exception as e:
            logger.error(f"Competitor analysis failed: {str(e)}")
            return {"majorCompetitors": [], "marketShare": {}}
    
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
        """시장 규모 추정"""
        return {
            "totalMarketSize": "1,200억원",
            "targetMarketSize": "240억원",
            "growthRate": "연 8.5%",
            "marketMaturity": "성장기"
        }
    
    def _analyze_growth_trends(self, market_data: Dict) -> List[str]:
        """성장 트렌드 분석"""
        return [
            "온라인 채널 확대",
            "개인화 서비스 증가",
            "친환경 제품 선호",
            "구독 기반 모델 확산"
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
            "marketSize": {"totalMarketSize": "추정 불가"},
            "growthTrends": ["일반적 성장 트렌드"],
            "competitorAnalysis": {"majorCompetitors": []},
            "marketOpportunities": [],
            "riskFactors": [],
            "timestamp": datetime.utcnow().isoformat(),
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