# Reporter Agent Lambda Function
# 3개 상호명 후보 생성, 중복 회피, 발음/검색 점수 산출

import json
import boto3
import logging
from datetime import datetime
import os
import re
from typing import Dict, Any, List
import random

# 공통 유틸리티 import
import sys
sys.path.append('/opt/python')
from shared.utils import setup_logging, get_aws_clients, create_response
from shared.agent_communication import AgentCommunication

logger = setup_logging()

class ReporterAgent:
    def __init__(self):
        self.aws_clients = get_aws_clients()
        self.dynamodb = self.aws_clients['dynamodb']
        self.sessions_table = self.dynamodb.Table(os.getenv('SESSIONS_TABLE'))
        self.agent_comm = AgentCommunication()
        
    def lambda_handler(self, event, context):
        """
        Reporter Agent 메인 핸들러
        - 3개 상호명 후보 생성
        - 중복 회피 알고리즘 구현
        - 발음/검색 점수 산출
        - 재생성 횟수 제한 (최대 3회)
        """
        try:
            logger.info("Reporter Agent started", extra={
                "agent": "reporter",
                "tool": "name.score",
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
            analysis_result = body.get('analysisResult', {})
            regenerate = body.get('regenerate', False)
            
            # 재생성 횟수 확인
            if regenerate and not self._can_regenerate(session_id):
                return create_response(400, {
                    "error": "Maximum regeneration limit reached (3 times)"
                })
            
            # 상호명 후보 생성
            name_candidates = self.generate_business_names(
                business_info, analysis_result, session_id, regenerate
            )
            
            # 세션에 결과 저장
            self._save_name_candidates(session_id, name_candidates, regenerate)
            
            # Supervisor Agent에 상태 보고
            self.agent_comm.send_to_supervisor(
                agent_id="reporter",
                status="completed",
                result=name_candidates
            )
            
            # 실행 시간 로깅
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.info("Reporter Agent completed", extra={
                "agent": "reporter",
                "tool": "name.score",
                "latency_ms": latency_ms,
                "status": "success"
            })
            
            return create_response(200, {
                "sessionId": session_id,
                "nameCandidates": name_candidates,
                "processingTime": latency_ms,
                "canRegenerate": self._can_regenerate(session_id, check_after_current=True)
            })
            
        except Exception as e:
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error("Reporter Agent failed", extra={
                "agent": "reporter",
                "tool": "name.score",
                "latency_ms": latency_ms,
                "error": str(e)
            })
            
            # 실패 시 Supervisor에게 보고
            self.agent_comm.send_to_supervisor(
                agent_id="reporter",
                status="failed",
                result={"error": str(e)}
            )
            
            return create_response(500, {"error": "Name generation failed"})
    
    def generate_business_names(self, business_info: Dict[str, Any], 
                              analysis_result: Dict[str, Any], 
                              session_id: str, regenerate: bool = False) -> List[Dict[str, Any]]:
        """상호명 후보 생성"""
        industry = business_info.get('industry', '')
        region = business_info.get('region', '')
        size = business_info.get('size', '')
        
        # 기존 후보들 조회 (중복 회피용)
        existing_names = self._get_existing_names(session_id) if regenerate else []
        
        # 상호명 생성 전략
        name_strategies = [
            self._generate_descriptive_names,
            self._generate_creative_names,
            self._generate_location_based_names,
            self._generate_modern_names,
            self._generate_traditional_names
        ]
        
        candidates = []
        attempts = 0
        max_attempts = 50
        
        while len(candidates) < 3 and attempts < max_attempts:
            strategy = random.choice(name_strategies)
            name_candidate = strategy(industry, region, size, analysis_result)
            
            # 중복 확인
            if not self._is_duplicate(name_candidate, existing_names + candidates):
                # 점수 계산
                scores = self._calculate_name_scores(name_candidate, industry, region)
                
                candidate_info = {
                    "name": name_candidate,
                    "description": self._generate_name_description(name_candidate, industry),
                    "scores": scores,
                    "reasoning": self._generate_reasoning(name_candidate, industry, scores)
                }
                
                candidates.append(candidate_info)
            
            attempts += 1
        
        # 점수 순으로 정렬
        candidates.sort(key=lambda x: x['scores']['overall'], reverse=True)
        
        return candidates[:3]
    
    def _generate_descriptive_names(self, industry: str, region: str, size: str, analysis: Dict) -> str:
        """설명적 상호명 생성"""
        descriptors = {
            "카페": ["향기로운", "따뜻한", "아늑한", "모던", "클래식"],
            "음식점": ["맛있는", "정통", "신선한", "건강한", "프리미엄"],
            "의류": ["스타일", "패션", "트렌디", "엘레간트", "모던"],
            "서비스": ["프로", "전문", "신뢰", "품질", "프리미엄"]
        }
        
        industry_key = next((k for k in descriptors.keys() if k in industry), "서비스")
        descriptor = random.choice(descriptors[industry_key])
        
        base_names = ["하우스", "플레이스", "스튜디오", "컴퍼니", "랩"]
        base = random.choice(base_names)
        
        return f"{descriptor}{base}"
    
    def _generate_creative_names(self, industry: str, region: str, size: str, analysis: Dict) -> str:
        """창의적 상호명 생성"""
        prefixes = ["더", "뉴", "스마트", "퓨처", "넥스트", "프라임"]
        suffixes = ["랩", "허브", "존", "스페이스", "웍스", "플러스"]
        
        # 업종별 키워드
        industry_keywords = {
            "카페": ["빈", "로스팅", "브루", "에스프레소"],
            "음식점": ["키친", "테이블", "플레이트", "쿡"],
            "의류": ["스타일", "패션", "룩", "웨어"],
            "서비스": ["솔루션", "서비스", "케어", "프로"]
        }
        
        industry_key = next((k for k in industry_keywords.keys() if k in industry), "서비스")
        keyword = random.choice(industry_keywords[industry_key])
        
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        
        return f"{prefix}{keyword}{suffix}"
    
    def _generate_location_based_names(self, industry: str, region: str, size: str, analysis: Dict) -> str:
        """지역 기반 상호명 생성"""
        region_short = region.split()[0] if region else "서울"
        
        patterns = [
            f"{region_short}하우스",
            f"{region_short}플레이스", 
            f"{region_short}스튜디오",
            f"{region_short}랩"
        ]
        
        return random.choice(patterns)
    
    def _generate_modern_names(self, industry: str, region: str, size: str, analysis: Dict) -> str:
        """모던한 상호명 생성"""
        modern_words = ["디지털", "스마트", "이노베이션", "테크", "퓨처", "넥스트"]
        business_words = ["솔루션", "서비스", "랩", "허브", "스튜디오"]
        
        modern = random.choice(modern_words)
        business = random.choice(business_words)
        
        return f"{modern}{business}"
    
    def _generate_traditional_names(self, industry: str, region: str, size: str, analysis: Dict) -> str:
        """전통적 상호명 생성"""
        traditional_prefixes = ["한국", "전통", "클래식", "오리지널", "마스터"]
        traditional_suffixes = ["하우스", "컴퍼니", "그룹", "엔터프라이즈"]
        
        prefix = random.choice(traditional_prefixes)
        suffix = random.choice(traditional_suffixes)
        
        return f"{prefix}{suffix}"
    
    def _calculate_name_scores(self, name: str, industry: str, region: str) -> Dict[str, float]:
        """상호명 점수 계산"""
        # 발음 점수 (음성학적 분석)
        pronunciation_score = self._calculate_pronunciation_score(name)
        
        # 검색 점수 (SEO 친화성)
        search_score = self._calculate_search_score(name, industry)
        
        # 기억하기 쉬운 정도
        memorability_score = self._calculate_memorability_score(name)
        
        # 브랜딩 적합성
        branding_score = self._calculate_branding_score(name, industry)
        
        # 전체 점수 계산
        overall_score = (
            pronunciation_score * 0.25 +
            search_score * 0.25 +
            memorability_score * 0.25 +
            branding_score * 0.25
        )
        
        return {
            "pronunciation": round(pronunciation_score, 1),
            "search": round(search_score, 1),
            "memorability": round(memorability_score, 1),
            "branding": round(branding_score, 1),
            "overall": round(overall_score, 1)
        }
    
    def _calculate_pronunciation_score(self, name: str) -> float:
        """발음 점수 계산"""
        # 길이 점수 (4-8자가 최적)
        length_score = 100 - abs(len(name) - 6) * 10
        length_score = max(0, min(100, length_score))
        
        # 자음/모음 균형
        consonants = len(re.findall(r'[ㄱ-ㅎ가-힣]', name))
        balance_score = 80 if consonants > 0 else 60
        
        return (length_score + balance_score) / 2
    
    def _calculate_search_score(self, name: str, industry: str) -> float:
        """검색 점수 계산"""
        # 고유성 점수 (일반적인 단어 피하기)
        common_words = ["회사", "기업", "상사", "무역", "개발"]
        uniqueness_score = 90
        for word in common_words:
            if word in name:
                uniqueness_score -= 20
        
        # 키워드 포함 점수
        keyword_score = 70
        if any(keyword in name for keyword in [industry, "프리미엄", "전문"]):
            keyword_score = 85
        
        return (uniqueness_score + keyword_score) / 2
    
    def _calculate_memorability_score(self, name: str) -> float:
        """기억하기 쉬운 정도 계산"""
        # 단순성 점수
        simplicity_score = 100 - len(name) * 5
        simplicity_score = max(50, min(100, simplicity_score))
        
        # 리듬감 점수
        rhythm_score = 75  # 기본 점수
        
        return (simplicity_score + rhythm_score) / 2
    
    def _calculate_branding_score(self, name: str, industry: str) -> float:
        """브랜딩 적합성 점수"""
        # 업종 적합성
        industry_fit_score = 75  # 기본 점수
        
        # 확장성 점수
        scalability_score = 80
        
        return (industry_fit_score + scalability_score) / 2
    
    def _generate_name_description(self, name: str, industry: str) -> str:
        """상호명 설명 생성"""
        descriptions = {
            "모던": f"현대적이고 세련된 느낌의 {industry} 브랜드명",
            "클래식": f"전통적이고 신뢰감 있는 {industry} 브랜드명",
            "창의적": f"독창적이고 기억하기 쉬운 {industry} 브랜드명"
        }
        
        # 이름 특성에 따른 설명 선택
        if any(word in name for word in ["모던", "스마트", "넥스트"]):
            return descriptions["모던"]
        elif any(word in name for word in ["클래식", "전통", "마스터"]):
            return descriptions["클래식"]
        else:
            return descriptions["창의적"]
    
    def _generate_reasoning(self, name: str, industry: str, scores: Dict[str, float]) -> str:
        """선택 이유 생성"""
        best_aspect = max(scores.items(), key=lambda x: x[1] if x[0] != 'overall' else 0)
        
        reasoning_map = {
            "pronunciation": "발음하기 쉽고 기억하기 좋습니다",
            "search": "검색 최적화에 유리하고 고유성이 높습니다",
            "memorability": "고객이 쉽게 기억할 수 있는 이름입니다",
            "branding": "브랜드 이미지 구축에 적합합니다"
        }
        
        return reasoning_map.get(best_aspect[0], "균형잡힌 좋은 브랜드명입니다")
    
    def _is_duplicate(self, name: str, existing_names: List) -> bool:
        """중복 확인"""
        existing_name_strings = []
        for existing in existing_names:
            if isinstance(existing, dict):
                existing_name_strings.append(existing.get('name', ''))
            else:
                existing_name_strings.append(str(existing))
        
        return name in existing_name_strings
    
    def _get_existing_names(self, session_id: str) -> List[str]:
        """기존 생성된 상호명들 조회"""
        try:
            response = self.sessions_table.get_item(Key={'sessionId': session_id})
            if 'Item' in response:
                business_names = response['Item'].get('businessNames', {})
                all_candidates = business_names.get('allCandidates', [])
                return [candidate.get('name', '') for candidate in all_candidates]
            return []
        except Exception as e:
            logger.error(f"Failed to get existing names: {str(e)}")
            return []
    
    def _can_regenerate(self, session_id: str, check_after_current: bool = False) -> bool:
        """재생성 가능 여부 확인"""
        try:
            response = self.sessions_table.get_item(Key={'sessionId': session_id})
            if 'Item' in response:
                regen_count = response['Item'].get('regenCount', 0)
                max_regen = 3
                
                if check_after_current:
                    return (regen_count + 1) < max_regen
                else:
                    return regen_count < max_regen
            return True
        except Exception as e:
            logger.error(f"Failed to check regeneration limit: {str(e)}")
            return False
    
    def _save_name_candidates(self, session_id: str, candidates: List[Dict[str, Any]], regenerate: bool):
        """상호명 후보들을 세션에 저장"""
        try:
            # 현재 재생성 횟수 조회
            current_regen_count = 0
            if regenerate:
                response = self.sessions_table.get_item(Key={'sessionId': session_id})
                if 'Item' in response:
                    current_regen_count = response['Item'].get('regenCount', 0)
            
            # 업데이트 표현식 구성
            update_expression = 'SET businessNames = :names, currentStep = :step, updatedAt = :timestamp'
            expression_values = {
                ':names': {
                    'candidates': candidates,
                    'allCandidates': candidates  # 중복 회피용
                },
                ':step': 3,
                ':timestamp': datetime.utcnow().isoformat()
            }
            
            if regenerate:
                update_expression += ', regenCount = :regen_count'
                expression_values[':regen_count'] = current_regen_count + 1
            
            self.sessions_table.update_item(
                Key={'sessionId': session_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            
        except Exception as e:
            logger.error(f"Failed to save name candidates: {str(e)}")

# Lambda 핸들러
reporter_agent = ReporterAgent()

def lambda_handler(event, context):
    return reporter_agent.lambda_handler(event, context)