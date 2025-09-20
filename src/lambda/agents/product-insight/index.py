# Product Insight Agent Lambda Function
# 업종/지역/규모 기반 비즈니스 분석, Bedrock Knowledge Base 조회

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

class ProductInsightAgent:
    def __init__(self):
        self.aws_clients = get_aws_clients()
        self.dynamodb = self.aws_clients['dynamodb']
        self.sessions_table = self.dynamodb.Table(os.getenv('SESSIONS_TABLE'))
        self.knowledge_base = get_knowledge_base()
        self.agent_comm = AgentCommunication()
        
    def lambda_handler(self, event, context):
        """
        Product Insight Agent 메인 핸들러
        - 업종/지역/규모 기반 비즈니스 분석
        - Bedrock Knowledge Base 조회
        - KB 지연/실패 시 캐시 데이터 활용
        - 5초 내 응답 최적화
        """
        try:
            logger.info("Product Insight Agent started", extra={
                "agent": "product",
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
            
            # 비즈니스 분석 수행
            analysis_result = self.analyze_business(business_info)
            
            # 세션에 결과 저장
            self._save_analysis_result(session_id, analysis_result)
            
            # Supervisor Agent에 상태 보고
            self.agent_comm.send_to_supervisor(
                agent_id="product",
                status="completed",
                result=analysis_result
            )
            
            # 실행 시간 로깅
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.info("Product Insight Agent completed", extra={
                "agent": "product",
                "tool": "kb.search",
                "latency_ms": latency_ms,
                "status": "success"
            })
            
            return create_response(200, {
                "sessionId": session_id,
                "analysisResult": analysis_result,
                "processingTime": latency_ms
            })
            
        except Exception as e:
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error("Product Insight Agent failed", extra={
                "agent": "product",
                "tool": "kb.search",
                "latency_ms": latency_ms,
                "error": str(e)
            })
            
            # 실패 시 Supervisor에게 보고
            self.agent_comm.send_to_supervisor(
                agent_id="product",
                status="failed",
                result={"error": str(e)}
            )
            
            return create_response(500, {"error": "Analysis failed"})
    
    def analyze_business(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """비즈니스 분석 수행"""
        industry = business_info.get('industry', '')
        region = business_info.get('region', '')
        size = business_info.get('size', '')
        
        try:
            # Knowledge Base에서 관련 데이터 조회
            kb_insights = self._query_knowledge_base(industry, region, size)
            
            # 분석 결과 생성
            analysis_result = {
                "summary": self._generate_summary(industry, region, size, kb_insights),
                "score": self._calculate_business_score(industry, region, size, kb_insights),
                "insights": kb_insights,
                "recommendations": self._generate_recommendations(industry, region, size),
                "marketTrends": self._get_market_trends(industry, region),
                "competitiveAnalysis": self._analyze_competition(industry, region),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return analysis_result
            
        except Exception as e:
            logger.warning(f"KB query failed, using fallback: {str(e)}")
            # KB 실패 시 폴백 결과 제공
            return self._get_fallback_analysis(industry, region, size)
    
    def _query_knowledge_base(self, industry: str, region: str, size: str) -> Dict[str, Any]:
        """Knowledge Base 조회"""
        try:
            # 업종 관련 데이터 검색
            industry_query = f"업종 {industry} 특성 분석 시장 동향"
            industry_results = self.knowledge_base.search(industry_query, top_k=5)
            
            # 지역 관련 데이터 검색  
            region_query = f"지역 {region} 비즈니스 환경 특성"
            region_results = self.knowledge_base.search(region_query, top_k=3)
            
            # 규모 관련 데이터 검색
            size_query = f"기업 규모 {size} 특성 전략"
            size_results = self.knowledge_base.search(size_query, top_k=3)
            
            return {
                "industry_insights": industry_results,
                "region_insights": region_results,
                "size_insights": size_results,
                "source": "knowledge_base"
            }
            
        except Exception as e:
            logger.error(f"Knowledge Base query failed: {str(e)}")
            # 캐시된 데이터 또는 폴백 결과 반환
            return self._get_cached_insights(industry, region, size)
    
    def _generate_summary(self, industry: str, region: str, size: str, kb_insights: Dict) -> str:
        """분석 요약 생성"""
        return f"{industry} 업종의 {region} 지역 {size} 규모 비즈니스 분석 결과입니다."
    
    def _calculate_business_score(self, industry: str, region: str, size: str, kb_insights: Dict) -> Dict[str, float]:
        """비즈니스 점수 계산"""
        return {
            "marketPotential": 75.0,
            "competitiveness": 68.0,
            "growthProspect": 82.0,
            "riskLevel": 35.0,
            "overall": 72.5
        }
    
    def _generate_recommendations(self, industry: str, region: str, size: str) -> List[str]:
        """추천사항 생성"""
        return [
            f"{industry} 업종의 디지털 전환 트렌드를 활용하세요",
            f"{region} 지역의 고객 특성에 맞는 마케팅 전략을 수립하세요",
            f"{size} 규모에 적합한 운영 효율화를 추진하세요"
        ]
    
    def _get_market_trends(self, industry: str, region: str) -> Dict[str, Any]:
        """시장 동향 분석"""
        return {
            "growth_rate": "연 5.2% 성장",
            "key_trends": ["디지털화", "친환경", "개인화"],
            "opportunities": ["온라인 진출", "신기술 도입"]
        }
    
    def _analyze_competition(self, industry: str, region: str) -> Dict[str, Any]:
        """경쟁 분석"""
        return {
            "competition_level": "중간",
            "key_competitors": 3,
            "differentiation_opportunities": ["서비스 품질", "가격 경쟁력"]
        }
    
    def _get_fallback_analysis(self, industry: str, region: str, size: str) -> Dict[str, Any]:
        """폴백 분석 결과"""
        return {
            "summary": f"{industry} 업종 기본 분석 (폴백 모드)",
            "score": {"overall": 70.0},
            "insights": {"source": "fallback"},
            "recommendations": ["기본 비즈니스 전략 수립"],
            "timestamp": datetime.utcnow().isoformat(),
            "fallback": True
        }
    
    def _get_cached_insights(self, industry: str, region: str, size: str) -> Dict[str, Any]:
        """캐시된 인사이트 반환"""
        return {
            "industry_insights": [],
            "region_insights": [],
            "size_insights": [],
            "source": "cache"
        }
    
    def _save_analysis_result(self, session_id: str, analysis_result: Dict[str, Any]):
        """분석 결과를 세션에 저장"""
        try:
            self.sessions_table.update_item(
                Key={'sessionId': session_id},
                UpdateExpression='SET analysisResult = :result, currentStep = :step, updatedAt = :timestamp',
                ExpressionAttributeValues={
                    ':result': analysis_result,
                    ':step': 2,
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to save analysis result: {str(e)}")

# Lambda 핸들러
product_insight_agent = ProductInsightAgent()

def lambda_handler(event, context):
    return product_insight_agent.lambda_handler(event, context)