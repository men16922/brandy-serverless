# Reporter Agent Lambda Function
# 3개 상호명 후보 생성, 중복 회피 알고리즘, 발음/검색 점수 산출, 재생성 제한

import json
import re
import random
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import sys

# 공통 유틸리티 import - Lambda Layer 사용
# SAM builds Layer with python/python/shared structure
sys.path.insert(0, '/opt/python/python')

from shared.base_agent import BaseAgent
from shared.models import AgentType, NameSuggestion, BusinessNames, WorkflowStep
from shared.utils import create_response
from shared.bedrock_client import BedrockClient, BedrockException
from shared.reasoning_engine import ReasoningEngine


class ReporterAgent(BaseAgent):
    """Reporter Agent - 상호명 제안 및 재생성 관리"""
    
    def __init__(self):
        super().__init__(AgentType.REPORTER)
        
        # Bedrock 통합 (Requirement 1.2, 3.3)
        self.enable_bedrock = os.getenv('ENABLE_FALLBACK', 'false').lower() != 'true'
        self.bedrock_client = None
        self.reasoning_engine = None
        
        if self.enable_bedrock:
            try:
                self.bedrock_client = BedrockClient(logger=self.logger)
                self.reasoning_engine = ReasoningEngine(
                    bedrock_client=self.bedrock_client,
                    logger=self.logger
                )
                self.logger.info("Bedrock integration enabled for Reporter Agent")
            except Exception as e:
                self.logger.warning(f"Bedrock initialization failed, using fallback: {str(e)}")
                self.enable_bedrock = False
        
        # 상호명 생성 관련 설정
        self.max_regenerations = 3
        self.target_suggestions = 3
        
        # 점수 가중치 시스템
        self.pronunciation_weight = 0.35  # 발음 용이성
        self.search_weight = 0.45         # SEO 친화성
        self.uniqueness_weight = 0.20     # 고유성 보너스
        
        # 업종별 키워드 매핑 - English only
        self.industry_keywords = {
            "restaurant": ["Taste", "Flavor", "House", "Garden", "Kitchen", "Table", "Dining", "Bistro"],
            "retail": ["Shop", "Store", "Market", "Place", "Corner", "Gallery", "Boutique", "Emporium"],
            "service": ["Center", "Studio", "Lab", "Clinic", "Office", "Room", "Hub", "Space"],
            "healthcare": ["Clinic", "Care", "Medi", "Health", "Well", "Life", "Wellness", "Medical"],
            "education": ["Academy", "School", "Center", "Lab", "Studio", "Class", "Institute", "Learning"],
            "technology": ["Tech", "Lab", "System", "Solution", "Innovation", "Digital", "Smart", "Cyber"],
            "manufacturing": ["Factory", "Works", "Industry", "Maker", "Craft", "Production", "Forge", "Mill"],
            "construction": ["Build", "Construction", "Housing", "Develop", "Structure", "Foundation", "Architect", "Design"],
            "finance": ["Finance", "Capital", "Invest", "Fund", "Wealth", "Asset", "Trust", "Equity"],
            "other": ["Company", "Group", "Partners", "Solution", "Enterprise", "Ventures", "Associates", "Collective"]
        }
        
        # 지역별 특성 키워드 - English only
        self.region_keywords = {
            "seoul": ["Seoul", "Han", "Namsan", "Gangnam", "Hongdae", "Myeongdong", "Capital", "Metro"],
            "busan": ["Busan", "Haeundae", "Gwangan", "Beach", "Port", "Coastal", "Marine", "Harbor"],
            "daegu": ["Daegu", "Palgong", "Suseong", "Central", "Valley", "Historic", "Traditional", "Heritage"],
            "incheon": ["Incheon", "Songdo", "Wolmi", "Gateway", "Port", "International", "Bridge", "Coast"],
            "gwangju": ["Gwangju", "Mudeung", "Culture", "Art", "Heritage", "Traditional", "Historic", "Valley"],
            "daejeon": ["Daejeon", "Yuseong", "Science", "Tech", "Innovation", "Research", "Expo", "Modern"],
            "ulsan": ["Ulsan", "Taehwa", "Industrial", "Modern", "Coastal", "River", "Harbor", "Bay"],
            "gyeonggi": ["Gyeonggi", "Suwon", "Metro", "Modern", "Urban", "Central", "Gateway", "Hub"],
            "gangwon": ["Gangwon", "Seorak", "Mountain", "Alpine", "Nature", "Highland", "Peak", "Valley"],
            "chungbuk": ["Chungbuk", "Cheongju", "Central", "Valley", "Heritage", "Traditional", "Historic", "Lake"],
            "chungnam": ["Chungnam", "Cheonan", "Asan", "Central", "Heritage", "Traditional", "Valley", "Bay"],
            "jeonbuk": ["Jeonbuk", "Jeonju", "Heritage", "Traditional", "Historic", "Culture", "Valley", "Classic"],
            "jeonnam": ["Jeonnam", "Mokpo", "Yeosu", "Coastal", "Bay", "Harbor", "Marine", "Island"],
            "gyeongbuk": ["Gyeongbuk", "Gyeongju", "Heritage", "Historic", "Ancient", "Traditional", "Culture", "Temple"],
            "gyeongnam": ["Gyeongnam", "Changwon", "Coastal", "Industrial", "Modern", "Bay", "Harbor", "Marine"],
            "jeju": ["Jeju", "Island", "Hallasan", "Volcanic", "Coastal", "Paradise", "Nature", "Ocean"]
        }
        
        # 금지 단어 목록 (중복 회피용)
        self.forbidden_words = set()
        
        # Fallback names (업종별 기본 상호명) - English only
        self.fallback_names = {
            "restaurant": ["TasteHouse", "DeliciousTable", "HappyDining"],
            "retail": ["GoodStore", "HappyShopping", "TrustShop"],
            "service": ["KindService", "TrustPlace", "HappySpace"],
            "healthcare": ["HealthyLife", "CarePlus", "WellbeingClinic"],
            "education": ["LearningPlace", "KnowledgeShare", "GrowthAcademy"],
            "technology": ["TechSolution", "InnovationLab", "SmartSystem"],
            "manufacturing": ["QualityFactory", "PrecisionWorks", "PremiumMaker"],
            "construction": ["StrongBuild", "SafeConstruction", "TrustBuild"],
            "finance": ["TrustFinance", "StableInvest", "GrowthCapital"],
            "other": ["GoodCompany", "TrustPartners", "HappyGroup"]
        }
        
    def execute(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Reporter Agent 실행 로직"""
        try:
            # 비동기 모드 확인
            headers = event.get('headers', {})
            async_mode = headers.get('x-async-mode', 'false').lower() == 'true'
            
            # 요청 파싱
            if isinstance(event.get('body'), str):
                body = json.loads(event['body'])
            else:
                body = event.get('body', event)
            
            session_id = body.get('sessionId')
            action = body.get('action', 'suggest')  # suggest, regenerate, select
            
            if not session_id:
                return self.create_lambda_response(400, {"error": "sessionId is required"})
            
            # 비동기 모드 처리
            if async_mode and action in ['suggest', 'regenerate']:
                return self._handle_async_request(session_id, body, context)
            
            # 실행 시작
            tool_name = "name.select" if action == 'select' else "name.generate"
            self.start_execution(session_id, tool_name)
            
            # 요청 body에서 직접 데이터 가져오기 (DynamoDB 조회 불필요)
            business_info = body.get('businessInfo')
            analysis_result = body.get('analysisResult')
            
            self.logger.info(f"Business info from body: {business_info is not None}")
            self.logger.info(f"Analysis result from body: {analysis_result is not None}")
            
            if not business_info:
                self.logger.error(f"Business info not found in request body. Available keys: {list(body.keys())}")
                self.end_execution("error", "Business info not found")
                return self.create_lambda_response(400, {"error": "Business info required"})
            
            # 기존 상호명 데이터 조회 (body 또는 DynamoDB)
            existing_names = body.get('business_names', {})
            if not existing_names:
                # body에 없으면 DynamoDB에서 조회 (재생성 케이스)
                session_data = self.get_session_data(session_id)
                if session_data:
                    existing_names = session_data.get('business_names', {})
            
            if isinstance(existing_names, str):
                existing_names = json.loads(existing_names)
            
            # NameSuggestion 객체들로 변환
            suggestions = []
            for s in existing_names.get('suggestions', []):
                if isinstance(s, dict):
                    suggestions.append(NameSuggestion(
                        name=s.get('name', ''),
                        description=s.get('description', ''),
                        pronunciation_score=s.get('pronunciationScore', s.get('pronunciation_score', 0.0)),
                        memorability_score=s.get('memorabilityScore', s.get('memorability_score', 0.0)),
                        relevance_score=s.get('relevanceScore', s.get('relevance_score', 0.0)),
                        search_score=s.get('searchScore', s.get('search_score', 0.0)),
                        overall_score=s.get('overallScore', s.get('overall_score', 0.0))
                    ))
                else:
                    suggestions.append(s)
            
            business_names = BusinessNames(
                suggestions=suggestions,
                selected_name=existing_names.get('selected_name'),
                regeneration_count=existing_names.get('regeneration_count', 0),
                max_regenerations=self.max_regenerations
            )
            
            # 액션에 따른 처리
            if action == 'regenerate':
                result = self._handle_regeneration(session_id, business_info, business_names)
            elif action == 'select':
                selected_name = body.get('selectedName')
                result = self._handle_selection(session_id, selected_name, business_names)
            else:
                result = self._handle_suggestion(session_id, business_info, business_names)
            
            # Supervisor Agent와 상태 동기화
            self._sync_with_supervisor(session_id, action, result)
            
            # 실행 완료
            self.end_execution("success", result=result)
            
            return self.create_lambda_response(200, result)
            
        except Exception as e:
            error_message = f"Reporter Agent execution failed: {str(e)}"
            self.end_execution("error", error_message)
            
            # 오류 시 사용자 메시지 포함
            error_response = {
                "error": error_message,
                "userMessage": self._get_user_error_message(str(e)),
                "canRetry": True
            }
            
            return self.create_lambda_response(500, error_response)
    
    def _handle_suggestion(self, session_id: str, business_info: Dict[str, Any], 
                          business_names: BusinessNames) -> Dict[str, Any]:
        """상호명 제안 처리"""
        # 기존 제안이 있으면 반환
        if business_names.suggestions:
            return {
                "sessionId": session_id,
                "suggestions": [self._suggestion_to_dict(s) for s in business_names.suggestions],
                "canRegenerate": business_names.can_regenerate(),
                "regenerationCount": business_names.regeneration_count,
                "maxRegenerations": business_names.max_regenerations
            }
        
        # 새로운 제안 생성
        suggestions = self._generate_name_suggestions(business_info, business_names)
        
        # BusinessNames 객체 업데이트
        business_names.suggestions = suggestions
        
        # 세션에 저장
        self._save_business_names(session_id, business_names)
        
        return {
            "sessionId": session_id,
            "suggestions": [self._suggestion_to_dict(s) for s in suggestions],
            "canRegenerate": business_names.can_regenerate(),
            "regenerationCount": business_names.regeneration_count,
            "maxRegenerations": business_names.max_regenerations
        }
    
    def _handle_regeneration(self, session_id: str, business_info: Dict[str, Any], 
                           business_names: BusinessNames) -> Dict[str, Any]:
        """재생성 처리"""
        # 재생성 요청 검증
        validation_result = self._validate_regeneration_request(business_names)
        if not validation_result["valid"]:
            raise ValueError(validation_result["error"])
        
        # 재생성 시도 로깅
        self._log_regeneration_attempt(session_id, business_names.regeneration_count + 1)
        
        # 기존 제안들을 금지 단어로 추가 (중복 회피)
        for suggestion in business_names.suggestions:
            self.forbidden_words.add(suggestion.name.lower())
        
        # 재생성 카운트 증가
        business_names.add_regeneration()
        
        # 새로운 제안 생성
        new_suggestions = self._generate_name_suggestions(business_info, business_names)
        
        # 생성 실패 시 처리
        if not new_suggestions:
            # 재생성 카운트 롤백
            business_names.regeneration_count -= 1
            raise Exception("Failed to generate new name suggestions")
        
        # BusinessNames 객체 업데이트
        business_names.suggestions = new_suggestions
        
        # 세션에 저장
        self._save_business_names(session_id, business_names)
        
        # 성공 로깅
        self.logger.info(
            f"Name regeneration completed: session={session_id}, count={business_names.regeneration_count}",
            extra={
                "agent": "reporter",
                "tool": "name.regenerate",
                "session_id": session_id,
                "regeneration_count": business_names.regeneration_count,
                "suggestions_count": len(new_suggestions),
                "action": "regeneration_completed"
            }
        )
        
        return {
            "sessionId": session_id,
            "suggestions": [self._suggestion_to_dict(s) for s in new_suggestions],
            "canRegenerate": business_names.can_regenerate(),
            "regenerationCount": business_names.regeneration_count,
            "maxRegenerations": business_names.max_regenerations,
            "regenerated": True,
            "message": f"새로운 상호명을 생성했습니다. (재생성 {business_names.regeneration_count}/{business_names.max_regenerations}회)"
        }
    
    def get_fallback_names(self, industry: str) -> List[Dict[str, Any]]:
        """
        Get fallback names when Bedrock is unavailable or throttled.
        
        Returns baseline names with default scores for the given industry.
        
        Args:
            industry: Business industry
        
        Returns:
            List of name dictionaries with default scores (as float for JSON serialization)
        """
        names = self.fallback_names.get(industry, self.fallback_names["other"])
        
        return [
            {
                "name": name,
                "description": f"{industry} 업종에 적합한 기본 상호명입니다.",
                "pronunciation_score": 75.0,
                "memorability_score": 70.0,
                "relevance_score": 80.0,
                "search_score": 70.0,
                "overall_score": 73.75,
                "reasoning": "Fallback name due to API throttling or unavailability",
                "is_fallback": True
            }
            for name in names
        ]
    
    def _generate_name_suggestions(self, business_info: Dict[str, Any], 
                                 business_names: BusinessNames) -> List[NameSuggestion]:
        """상호명 제안 생성 (Bedrock 우선, 기존 로직 fallback)"""
        # Bedrock을 사용한 상호명 생성 시도 (Requirement 1.2, 3.3)
        if self.enable_bedrock and self.bedrock_client and self.reasoning_engine:
            try:
                return self._generate_names_with_bedrock(business_info, business_names)
            except Exception as e:
                self.logger.warning(
                    f"Bedrock name generation failed, using fallback: {str(e)}",
                    extra={
                        "agent": "reporter",
                        "tool": "name.generate",
                        "bedrock_error": str(e),
                        "fallback": "traditional_algorithm"
                    }
                )
        
        # 기존 알고리즘 사용 (Fallback)
        return self._generate_names_with_traditional_algorithm(business_info, business_names)
    
    def _sanitize_description(self, description: str) -> Optional[str]:
        """
        Sanitize business description for AI prompts.
        
        Implements Requirements 3.1, 3.4:
        - Limit length to 500 characters
        - Remove potentially problematic characters
        - Log warnings for truncation
        
        Args:
            description: Raw business description
        
        Returns:
            Sanitized description or None if invalid
        """
        if not description:
            return None
        
        # Trim whitespace
        description = description.strip()
        
        if not description:
            return None
        
        # Limit length (max 500 characters)
        if len(description) > 500:
            description = description[:500]
            self.logger.warning(
                "Description truncated to 500 characters",
                extra={
                    "agent": "reporter",
                    "tool": "name.generate",
                    "original_length": len(description),
                    "truncated_length": 500
                }
            )
        
        # Remove potentially problematic characters (keep alphanumeric, spaces, basic punctuation)
        description = re.sub(r'[^\w\s\-,.\'\"]', '', description)
        
        return description
    
    def _generate_names_with_bedrock(self, business_info: Dict[str, Any], 
                                    business_names: BusinessNames) -> List[NameSuggestion]:
        """
        Bedrock Claude를 사용한 상호명 생성 및 평가
        
        60초 이상 걸리면 fallback names 사용
        
        Implements Requirements 1.2, 2.1, 2.3, 3.2:
        - Extract and include business description in prompts
        - Emphasize description theme in name generation
        - Add structured logging for description usage
        """
        import time
        from decimal import Decimal
        
        industry = business_info.get('industry', '').lower()
        region = business_info.get('region', '').lower()
        size = business_info.get('size', '').lower()
        
        # Extract and sanitize description (Requirement 1.2, 3.1)
        raw_description = business_info.get('description')
        description = self._sanitize_description(raw_description)
        
        # Log description usage (Requirement 3.2)
        self.logger.info(
            f"Generating names with description: '{description[:50] if description else 'None'}...'",
            extra={
                "agent": "reporter",
                "tool": "name.generate",
                "has_description": bool(description),
                "description_length": len(description) if description else 0,
                "industry": industry,
                "region": region
            }
        )
        
        start_time = time.time()
        max_bedrock_time = 60.0  # 60초 제한
        
        # 기존 제안들을 제외 목록으로 전달
        existing_names = [s.name for s in business_names.suggestions]
        existing_names.extend(list(self.forbidden_words))
        
        # Claude에게 상호명 생성 요청
        system_prompt = """You are an expert business naming consultant.
Generate creative, memorable, and market-appropriate business names IN ENGLISH ONLY.

Requirements:
1. Names MUST be in English only (no Korean characters)
2. Names should be 2-4 words, easy to pronounce and remember
3. Reflect the industry and regional characteristics
4. SEO-friendly and unique
5. Avoid common or generic names
6. Can combine words creatively (e.g., "TasteAlley", "SeoulBites", "FreshCorner")

Respond in JSON format with exactly 3 name suggestions:
{
    "suggestions": [
        {
            "name": "BusinessName",
            "description": "Description of the name in English",
            "reasoning": "Reasoning for selection and brand fit analysis"
        }
    ]
}"""
        
        # Build prompt with description emphasis (Requirement 2.1, 2.3)
        prompt = f"""Business Context:
- Industry: {industry}
- Region: {region}
- Size: {size}
- Description: {description or 'Not provided'}

{f"IMPORTANT: This business has a unique concept: '{description}'. Generate names that reflect this theme and create strong brand association with this concept." if description else ""}

Existing names to avoid:
{json.dumps(existing_names, ensure_ascii=False)}

Please generate 3 unique, creative business names that fit this context perfectly."""
        
        self.logger.info(
            f"Generating names with Bedrock Claude: industry={industry}, region={region}",
            extra={
                "agent": "reporter",
                "tool": "name.generate",
                "provider": "bedrock_claude",
                "model": self.bedrock_client.claude_model_id
            }
        )
        
        try:
            # Claude 호출
            response = self.bedrock_client.invoke_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=1024,
                temperature=0.8  # 창의성을 위해 높은 temperature
            )
            
            # 시간 체크 - 60초 초과 시 fallback 사용
            elapsed_time = time.time() - start_time
            if elapsed_time > max_bedrock_time:
                self.logger.warning(
                    f"Bedrock name generation exceeded {max_bedrock_time}s ({elapsed_time:.2f}s), using fallback",
                    extra={
                        "agent": "reporter",
                        "tool": "name.generate",
                        "elapsed_time": elapsed_time,
                        "max_time": max_bedrock_time,
                        "fallback_used": True
                    }
                )
                # Fallback names 사용
                fallback_data = self.get_fallback_names(industry)
                return [
                    NameSuggestion(
                        name=item['name'],
                        description=item['description'],
                        pronunciation_score=float(item['pronunciation_score']),
                        search_score=float(item['search_score']),
                        overall_score=float(item['overall_score'])
                    )
                    for item in fallback_data
                ]
            
            # JSON 응답 파싱
            response_text = response['text']
            suggestions_data = self._extract_json_from_response(response_text)
            
            if not suggestions_data or 'suggestions' not in suggestions_data:
                raise BedrockException("Invalid response format from Claude")
            
            # NameSuggestion 객체 생성 및 평가
            suggestions = []
            names_to_evaluate = []
            name_descriptions = {}
            
            # 먼저 모든 이름 수집 (중복 제거)
            for item in suggestions_data['suggestions'][:3]:  # 최대 3개
                name = item.get('name', '')
                description = item.get('description', '')
                
                # 중복 확인
                if not self._is_duplicate_name(name, []):
                    names_to_evaluate.append(name)
                    name_descriptions[name] = description
            
            # Rate limiting: 이름 생성과 평가 사이에 2초 대기 (throttling 방지)
            self.logger.info("Adding rate limit delay before batch evaluation")
            self.bedrock_client.add_rate_limit_delay(2.0)
            
            # Batch evaluation으로 모든 이름을 한 번에 평가 (4 API calls → 2 API calls)
            try:
                self.logger.info(f"Batch evaluating {len(names_to_evaluate)} names")
                
                # analysis_result 가져오기 (있으면)
                analysis_result = {}
                if hasattr(self, 'session_data') and self.session_data:
                    analysis_result = self.session_data.get('results', {}).get('analysis', {})
                
                evaluations = self.bedrock_client.batch_evaluate_names(
                    names=names_to_evaluate,
                    business_info=business_info,
                    analysis_result=analysis_result
                )
                
                # 평가 결과를 NameSuggestion으로 변환
                for evaluation in evaluations:
                    name = evaluation.get('name', '')
                    description = name_descriptions.get(name, '')
                    
                    # 점수를 float로 가져오기 (나중에 Decimal로 변환)
                    pronunciation_score = float(evaluation.get('pronunciation_score', 75.0))
                    memorability_score = float(evaluation.get('memorability_score', 75.0))
                    relevance_score = float(evaluation.get('relevance_score', 75.0))
                    search_score = float(evaluation.get('search_score', 75.0))
                    overall_score = float(evaluation.get('overall_score', 75.0))
                    
                    suggestion = NameSuggestion(
                        name=name,
                        description=description,
                        pronunciation_score=pronunciation_score,
                        memorability_score=memorability_score,
                        relevance_score=relevance_score,
                        search_score=search_score,
                        overall_score=overall_score
                    )
                    
                    suggestions.append(suggestion)
                    
                    self.logger.info(
                        f"Name evaluated: '{name}' scored {overall_score:.1f}/100",
                        extra={
                            "agent": "reporter",
                            "tool": "name.batch_evaluate",
                            "business_name": name,
                            "score": overall_score,
                            "reasoning": evaluation.get('reasoning', '')[:200]
                        }
                    )
                    
            except Exception as e:
                self.logger.warning(f"Batch evaluation failed: {str(e)}, using fallback scores")
                # Fallback: 기본 점수 사용
                for name in names_to_evaluate:
                    description = name_descriptions.get(name, '')
                    suggestion = NameSuggestion(
                        name=name,
                        description=description,
                        pronunciation_score=75.0,
                        memorability_score=75.0,
                        relevance_score=75.0,
                        search_score=75.0,
                        overall_score=75.0
                    )
                    suggestions.append(suggestion)
            
            # 최소 3개 보장 (부족하면 기존 알고리즘으로 보충)
            if len(suggestions) < self.target_suggestions:
                self.logger.warning(
                    f"Bedrock generated only {len(suggestions)} names, "
                    f"supplementing with traditional algorithm"
                )
                traditional_suggestions = self._generate_names_with_traditional_algorithm(
                    business_info, business_names
                )
                # 중복 제거하면서 추가
                for trad_sugg in traditional_suggestions:
                    if len(suggestions) >= self.target_suggestions:
                        break
                    if not self._is_duplicate_name(trad_sugg.name, suggestions):
                        suggestions.append(trad_sugg)
            
            # 점수 정규화 및 순위 매기기
            suggestions = self._normalize_and_rank_suggestions(suggestions, industry, region, size)
            
            # 총 실행 시간 로깅
            total_time = time.time() - start_time
            self.logger.info(
                f"Bedrock name generation completed in {total_time:.2f}s",
                extra={
                    "agent": "reporter",
                    "tool": "name.generate",
                    "total_time": total_time,
                    "suggestions_count": len(suggestions)
                }
            )
            
            return suggestions[:self.target_suggestions]
            
        except Exception as e:
            # Bedrock 전체 실패 시 fallback names 사용
            elapsed_time = time.time() - start_time
            self.logger.error(
                f"Bedrock name generation failed after {elapsed_time:.2f}s: {str(e)}",
                extra={
                    "agent": "reporter",
                    "tool": "name.generate",
                    "error": str(e),
                    "elapsed_time": elapsed_time,
                    "fallback_used": True
                }
            )
            
            # Fallback names 반환
            fallback_data = self.get_fallback_names(industry)
            return [
                NameSuggestion(
                    name=item['name'],
                    description=item['description'],
                    pronunciation_score=float(item['pronunciation_score']),
                    search_score=float(item['search_score']),
                    overall_score=float(item['overall_score'])
                )
                for item in fallback_data
            ]
    
    def _generate_names_with_traditional_algorithm(self, business_info: Dict[str, Any], 
                                                  business_names: BusinessNames) -> List[NameSuggestion]:
        """기존 알고리즘을 사용한 상호명 생성 (Fallback)"""
        industry = business_info.get('industry', '').lower()
        region = business_info.get('region', '').lower()
        size = business_info.get('size', '').lower()
        
        suggestions = []
        attempts = 0
        max_attempts = 50  # 무한 루프 방지
        
        while len(suggestions) < self.target_suggestions and attempts < max_attempts:
            attempts += 1
            
            # 상호명 생성
            name = self._create_business_name(industry, region, size)
            
            # 중복 확인
            if self._is_duplicate_name(name, suggestions):
                continue
            
            # 점수 계산
            pronunciation_score = self._calculate_pronunciation_score(name)
            search_score = self._calculate_search_score(name, industry)
            uniqueness_score = self._calculate_uniqueness_bonus(name, industry, region)
            
            # 종합 점수 계산 (가중 평균 + 보너스)
            base_score = (pronunciation_score * self.pronunciation_weight + 
                         search_score * self.search_weight)
            overall_score = base_score + (uniqueness_score * self.uniqueness_weight)
            
            # 설명 생성
            description = self._generate_name_description(name, industry, region)
            
            suggestion = NameSuggestion(
                name=name,
                description=description,
                pronunciation_score=pronunciation_score,
                search_score=search_score,
                overall_score=overall_score
            )
            
            suggestions.append(suggestion)
        
        # 점수 정규화 및 순위 매기기
        suggestions = self._normalize_and_rank_suggestions(suggestions, industry, region, size)
        
        return suggestions[:self.target_suggestions]
    
    def _extract_json_from_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Claude 응답에서 JSON 추출 (마크다운 래핑 처리)"""
        try:
            # JSON 찾기 (마크다운 코드 블록 안에 있을 수 있음)
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = text[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON parsing failed: {str(e)}")
        
        return None
    
    def _calculate_uniqueness_bonus(self, name: str, industry: str, region: str) -> float:
        """고유성 보너스 점수 계산"""
        bonus = 0.0
        
        # 1. 창의적 조합 보너스
        creativity_bonus = self._assess_creativity(name)
        bonus += creativity_bonus
        
        # 2. 지역 특색 반영 보너스
        regional_bonus = self._assess_regional_uniqueness(name, region)
        bonus += regional_bonus
        
        # 3. 업종 혁신성 보너스
        innovation_bonus = self._assess_industry_innovation(name, industry)
        bonus += innovation_bonus
        
        # 4. 트렌드 반영 보너스
        trend_bonus = self._assess_trend_alignment(name)
        bonus += trend_bonus
        
        return min(20.0, bonus)  # 최대 20점 보너스
    
    def _assess_creativity(self, name: str) -> float:
        """창의성 평가"""
        creativity = 0.0
        
        # 독특한 문자 조합
        char_types = {
            'korean': any('가' <= char <= '힣' for char in name),
            'english': any(char.isalpha() and ord(char) < 128 for char in name),
            'number': any(char.isdigit() for char in name),
            'special': any(not char.isalnum() and char != ' ' for char in name)
        }
        
        active_types = sum(char_types.values())
        if active_types >= 3:
            creativity += 8  # 3가지 이상 문자 타입 사용
        elif active_types == 2:
            creativity += 5  # 2가지 문자 타입 사용
        
        # 신조어 가능성
        if self._is_potential_neologism(name):
            creativity += 6
        
        # 언어유희 요소
        if self._has_wordplay_elements(name):
            creativity += 4
        
        return creativity
    
    def _assess_regional_uniqueness(self, name: str, region: str) -> float:
        """지역 특색 반영도 평가"""
        regional_bonus = 0.0
        
        # 지역 키워드 직접 사용
        region_words = self.region_keywords.get(region, [])
        for word in region_words:
            if word in name:
                regional_bonus += 5
                break
        
        # 지역 특성 간접 반영
        regional_characteristics = {
            "seoul": ["모던", "트렌디", "글로벌", "혁신"],
            "busan": ["바다", "항구", "신선", "활력"],
            "jeju": ["자연", "힐링", "순수", "특별"],
            "gyeonggi": ["신도시", "젊은", "역동", "미래"]
        }
        
        characteristics = regional_characteristics.get(region, [])
        for char in characteristics:
            if char in name:
                regional_bonus += 3
                break
        
        return regional_bonus
    
    def _assess_industry_innovation(self, name: str, industry: str) -> float:
        """업종 혁신성 평가"""
        innovation = 0.0
        
        # 업종별 혁신 키워드
        innovation_keywords = {
            "technology": ["AI", "스마트", "디지털", "이노", "테크"],
            "healthcare": ["웰니스", "케어", "힐링", "바이오"],
            "education": ["러닝", "아카데미", "스마트", "에듀"],
            "restaurant": ["퓨전", "크래프트", "아티산", "가든"],
            "retail": ["큐레이션", "편집", "셀렉트", "라이프"],
            "service": ["솔루션", "컨설팅", "프리미엄", "전문"]
        }
        
        keywords = innovation_keywords.get(industry, [])
        for keyword in keywords:
            if keyword.lower() in name.lower():
                innovation += 4
                break
        
        # 미래지향적 요소
        future_elements = ["2.0", "넥스트", "뉴", "프로", "플러스", "+"]
        for element in future_elements:
            if element in name:
                innovation += 3
                break
        
        return innovation
    
    def _assess_trend_alignment(self, name: str) -> float:
        """트렌드 반영도 평가"""
        trend_score = 0.0
        
        # 2024-2025 트렌드 키워드
        current_trends = [
            "친환경", "지속가능", "ESG", "그린", "에코",
            "개인화", "맞춤", "커스텀", "퍼스널",
            "경험", "체험", "라이프", "스타일",
            "공유", "커뮤니티", "소셜", "네트워크"
        ]
        
        for trend in current_trends:
            if trend in name:
                trend_score += 5
                break
        
        # MZ세대 친화적 요소
        mz_elements = ["24", "365", "올인원", "원스톱", "스마트"]
        for element in mz_elements:
            if element in name:
                trend_score += 3
                break
        
        return trend_score
    
    def _is_potential_neologism(self, name: str) -> bool:
        """신조어 가능성 판단"""
        # 기존 단어의 변형이나 조합인지 확인
        if len(name) >= 4:
            # 영문+한글 조합
            has_english = any(char.isalpha() and ord(char) < 128 for char in name)
            has_korean = any('가' <= char <= '힣' for char in name)
            if has_english and has_korean:
                return True
            
            # 숫자+문자 조합
            has_number = any(char.isdigit() for char in name)
            if has_number and (has_english or has_korean):
                return True
        
        return False
    
    def _has_wordplay_elements(self, name: str) -> bool:
        """언어유희 요소 확인"""
        # 의성어/의태어 패턴
        onomatopoeia_patterns = ["팡", "쿵", "짱", "쫄", "촉", "톡", "팝"]
        for pattern in onomatopoeia_patterns:
            if pattern in name:
                return True
        
        # 반복 패턴
        if len(name) >= 4:
            for i in range(len(name) - 1):
                if name[i] == name[i + 1]:
                    return True
        
        return False
    
    def _normalize_and_rank_suggestions(self, suggestions: List[NameSuggestion], 
                                      industry: str, region: str, size: str) -> List[NameSuggestion]:
        """점수 정규화 및 순위 매기기"""
        if not suggestions:
            return suggestions
        
        # 1. 점수 정규화 (0-100 범위로 조정)
        max_score = max(s.overall_score for s in suggestions)
        min_score = min(s.overall_score for s in suggestions)
        
        if max_score > min_score:
            for suggestion in suggestions:
                # 정규화된 점수 계산
                normalized = ((suggestion.overall_score - min_score) / (max_score - min_score)) * 100
                suggestion.overall_score = round(normalized, 1)
        
        # 2. 비즈니스 규모별 가중치 적용
        size_weights = {
            "small": {"pronunciation": 1.2, "search": 0.9},    # 발음 중시
            "medium": {"pronunciation": 1.0, "search": 1.0},   # 균형
            "large": {"pronunciation": 0.9, "search": 1.2}     # 검색 중시
        }
        
        weights = size_weights.get(size, size_weights["medium"])
        
        for suggestion in suggestions:
            # 규모별 가중치 재적용
            adjusted_score = (
                suggestion.pronunciation_score * weights["pronunciation"] * self.pronunciation_weight +
                suggestion.search_score * weights["search"] * self.search_weight
            )
            suggestion.overall_score = round(adjusted_score, 1)
        
        # 3. 최종 순위 매기기 (종합 점수 기준)
        suggestions.sort(key=lambda x: x.overall_score, reverse=True)
        
        # 4. 점수 범위 최종 조정 (60-95 범위)
        for i, suggestion in enumerate(suggestions):
            # 1등: 85-95, 2등: 75-85, 3등: 65-75 범위로 조정
            if i == 0:
                suggestion.overall_score = max(85, min(95, suggestion.overall_score))
            elif i == 1:
                suggestion.overall_score = max(75, min(85, suggestion.overall_score))
            else:
                suggestion.overall_score = max(65, min(75, suggestion.overall_score))
        
        return suggestions
    
    def _create_business_name(self, industry: str, region: str, size: str) -> str:
        """비즈니스 상호명 생성"""
        # 업종별 키워드 선택
        industry_words = self.industry_keywords.get(industry, self.industry_keywords["other"])
        
        # 지역별 키워드 선택 (선택적)
        region_words = self.region_keywords.get(region, [])
        
        # 이름 생성 패턴들
        patterns = [
            # 패턴 1: [형용사] + [업종키워드]
            lambda: f"{self._get_adjective()}{random.choice(industry_words)}",
            
            # 패턴 2: [지역특성] + [업종키워드] (지역 키워드가 있을 때)
            lambda: f"{random.choice(region_words)}{random.choice(industry_words)}" if region_words else f"{self._get_adjective()}{random.choice(industry_words)}",
            
            # 패턴 3: [고유명사] + [업종키워드]
            lambda: f"{self._get_unique_name()}{random.choice(industry_words)}",
            
            # 패턴 4: [영문] + [업종키워드]
            lambda: f"{self._get_english_word()}{random.choice(industry_words)}",
            
            # 패턴 5: [숫자/기호] + [업종키워드]
            lambda: f"{self._get_number_prefix()}{random.choice(industry_words)}"
        ]
        
        # 랜덤 패턴 선택하여 이름 생성
        pattern = random.choice(patterns)
        name = pattern()
        
        # 길이 조정 (2-8자)
        if len(name) > 8:
            name = name[:8]
        elif len(name) < 2:
            name = name + random.choice(industry_words)[:2]
        
        return name
    
    def _get_adjective(self) -> str:
        """형용사 반환"""
        adjectives = [
            "좋은", "새로운", "빠른", "편한", "맛있는", "예쁜", "멋진", "특별한",
            "프리미엄", "스마트", "모던", "클래식", "트렌디", "유니크"
        ]
        return random.choice(adjectives)
    
    def _get_unique_name(self) -> str:
        """고유명사 반환"""
        names = [
            "골든", "실버", "다이아", "플래티넘", "크리스탈", "펄", "루비", "사파이어",
            "선샤인", "문라이트", "스타", "드림", "해피", "럭키", "위너", "챔피언"
        ]
        return random.choice(names)
    
    def _get_english_word(self) -> str:
        """영문 단어 반환"""
        words = [
            "Best", "Top", "Prime", "Elite", "Royal", "Grand", "Super", "Ultra",
            "Neo", "New", "Fresh", "Pure", "True", "Real", "Fine", "Nice"
        ]
        return random.choice(words)
    
    def _get_number_prefix(self) -> str:
        """숫자/기호 접두사 반환"""
        prefixes = [
            "1번", "24시", "365", "7번가", "1등", "A급", "S급", "프로"
        ]
        return random.choice(prefixes)
    
    def _is_duplicate_name(self, name: str, existing_suggestions: List[NameSuggestion]) -> bool:
        """고도화된 중복 이름 확인"""
        name_lower = name.lower().strip()
        
        # 금지 단어 목록 확인
        if name_lower in self.forbidden_words:
            return True
        
        # 기존 제안과 정확한 중복 확인
        for suggestion in existing_suggestions:
            if suggestion.name.lower().strip() == name_lower:
                return True
        
        # 다양한 유사도 검사
        for suggestion in existing_suggestions:
            existing_name = suggestion.name.lower().strip()
            
            # 1. 편집 거리 기반 유사도
            edit_similarity = self._calculate_edit_distance_similarity(name_lower, existing_name)
            if edit_similarity > 0.85:
                return True
            
            # 2. 음성학적 유사도 (발음이 비슷한 경우)
            phonetic_similarity = self._calculate_phonetic_similarity(name_lower, existing_name)
            if phonetic_similarity > 0.9:
                return True
            
            # 3. 구조적 유사도 (단어 구성이 비슷한 경우)
            structural_similarity = self._calculate_structural_similarity(name_lower, existing_name)
            if structural_similarity > 0.8:
                return True
            
            # 4. 의미적 유사도 (키워드가 겹치는 경우)
            semantic_similarity = self._calculate_semantic_similarity(name_lower, existing_name)
            if semantic_similarity > 0.7:
                return True
        
        # 5. 일반적인 상호명과의 중복 확인
        if self._is_common_business_name(name_lower):
            return True
        
        return False
    
    def _calculate_edit_distance_similarity(self, name1: str, name2: str) -> float:
        """편집 거리 기반 유사도 계산 (Levenshtein Distance)"""
        if len(name1) == 0 and len(name2) == 0:
            return 1.0
        if len(name1) == 0 or len(name2) == 0:
            return 0.0
        
        # 동적 프로그래밍으로 편집 거리 계산
        dp = [[0] * (len(name2) + 1) for _ in range(len(name1) + 1)]
        
        # 초기화
        for i in range(len(name1) + 1):
            dp[i][0] = i
        for j in range(len(name2) + 1):
            dp[0][j] = j
        
        # 편집 거리 계산
        for i in range(1, len(name1) + 1):
            for j in range(1, len(name2) + 1):
                if name1[i-1] == name2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = min(
                        dp[i-1][j] + 1,    # 삭제
                        dp[i][j-1] + 1,    # 삽입
                        dp[i-1][j-1] + 1   # 치환
                    )
        
        # 유사도 계산 (0~1 범위)
        max_len = max(len(name1), len(name2))
        edit_distance = dp[len(name1)][len(name2)]
        similarity = 1 - (edit_distance / max_len)
        
        return max(0.0, similarity)
    
    def _calculate_phonetic_similarity(self, name1: str, name2: str) -> float:
        """음성학적 유사도 계산"""
        # 한글 자음/모음 분리하여 비교
        phonemes1 = self._extract_phonemes(name1)
        phonemes2 = self._extract_phonemes(name2)
        
        if not phonemes1 and not phonemes2:
            return 1.0
        if not phonemes1 or not phonemes2:
            return 0.0
        
        # 자카드 유사도 계산
        common_phonemes = set(phonemes1) & set(phonemes2)
        total_phonemes = set(phonemes1) | set(phonemes2)
        
        if len(total_phonemes) == 0:
            return 0.0
        
        return len(common_phonemes) / len(total_phonemes)
    
    def _extract_phonemes(self, name: str) -> list:
        """한글에서 음소 추출"""
        phonemes = []
        
        for char in name:
            if '가' <= char <= '힣':
                # 한글 음절 분해
                code = ord(char) - ord('가')
                initial = code // (21 * 28)  # 초성
                medial = (code % (21 * 28)) // 28  # 중성
                final = code % 28  # 종성
                
                # 초성, 중성, 종성을 음소로 변환
                initials = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
                medials = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
                finals = " ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"
                
                phonemes.append(initials[initial])
                phonemes.append(medials[medial])
                if final > 0:
                    phonemes.append(finals[final])
            else:
                phonemes.append(char.lower())
        
        return phonemes
    
    def _calculate_structural_similarity(self, name1: str, name2: str) -> float:
        """구조적 유사도 계산 (길이, 패턴 등)"""
        similarity = 0.0
        
        # 길이 유사도
        len1, len2 = len(name1), len(name2)
        if len1 == len2:
            similarity += 0.3
        elif abs(len1 - len2) == 1:
            similarity += 0.2
        elif abs(len1 - len2) <= 2:
            similarity += 0.1
        
        # 문자 타입 패턴 유사도
        pattern1 = self._get_character_pattern(name1)
        pattern2 = self._get_character_pattern(name2)
        
        if pattern1 == pattern2:
            similarity += 0.4
        
        # 시작/끝 문자 유사도
        if len1 > 0 and len2 > 0:
            if name1[0] == name2[0]:
                similarity += 0.15
            if name1[-1] == name2[-1]:
                similarity += 0.15
        
        return min(1.0, similarity)
    
    def _get_character_pattern(self, name: str) -> str:
        """문자 패턴 추출 (K=한글, E=영문, N=숫자, S=특수문자)"""
        pattern = ""
        for char in name:
            if '가' <= char <= '힣':
                pattern += 'K'
            elif char.isalpha():
                pattern += 'E'
            elif char.isdigit():
                pattern += 'N'
            elif char != ' ':
                pattern += 'S'
        return pattern
    
    def _calculate_semantic_similarity(self, name1: str, name2: str) -> float:
        """의미적 유사도 계산 (공통 키워드 기반)"""
        # 모든 업종 키워드 수집
        all_keywords = set()
        for keywords in self.industry_keywords.values():
            all_keywords.update(keywords)
        
        # 각 이름에서 키워드 추출
        keywords1 = set()
        keywords2 = set()
        
        for keyword in all_keywords:
            if keyword in name1:
                keywords1.add(keyword)
            if keyword in name2:
                keywords2.add(keyword)
        
        # 공통 키워드가 없으면 0
        if not keywords1 and not keywords2:
            return 0.0
        
        # 자카드 유사도
        common_keywords = keywords1 & keywords2
        total_keywords = keywords1 | keywords2
        
        if len(total_keywords) == 0:
            return 0.0
        
        return len(common_keywords) / len(total_keywords)
    
    def _is_common_business_name(self, name: str) -> bool:
        """일반적인 상호명인지 확인"""
        # 너무 일반적인 상호명들
        common_names = {
            "좋은가게", "새로운집", "맛있는집", "예쁜가게", "멋진집",
            "베스트", "최고", "1등", "프리미엄", "스페셜",
            "골든", "실버", "다이아", "플래티넘", "크리스탈"
        }
        
        return name in common_names
    
    def _calculate_pronunciation_score(self, name: str) -> float:
        """음성학 기반 발음 점수 계산"""
        score = 100.0
        
        # 길이 점수 (3-6자가 최적)
        length = len(name)
        if length < 2:
            score -= 30
        elif length > 8:
            score -= 20
        elif 3 <= length <= 6:
            score += 10
        
        # 한글 음성학적 분석
        korean_score = self._analyze_korean_phonetics(name)
        score = (score + korean_score) / 2
        
        # 발음 용이성 (자음/모음 비율)
        consonants, vowels = self._count_korean_phonemes(name)
        
        # 자음/모음 균형 점수
        if consonants > 0 and vowels > 0:
            ratio = min(consonants, vowels) / max(consonants, vowels)
            score += ratio * 10
        
        # 반복 문자 패널티
        for i in range(len(name) - 1):
            if name[i] == name[i + 1]:
                score -= 5
        
        # 발음 난이도 분석
        difficulty_penalty = self._calculate_pronunciation_difficulty(name)
        score -= difficulty_penalty
        
        # 리듬감 분석 (음절 패턴)
        rhythm_bonus = self._analyze_syllable_rhythm(name)
        score += rhythm_bonus
        
        # 특수문자/숫자 보너스 (적절한 사용)
        special_count = sum(1 for char in name if not char.isalnum())
        if special_count == 1:
            score += 5
        elif special_count > 2:
            score -= 10
        
        return max(0, min(100, score))
    
    def _analyze_korean_phonetics(self, name: str) -> float:
        """한글 음성학적 분석"""
        score = 100.0
        
        # 발음하기 어려운 자음 조합 패널티
        difficult_combinations = [
            'ㅃㅍ', 'ㅉㅊ', 'ㄲㅋ', 'ㅆㅅ', 'ㄸㅌ',  # 된소리 + 거센소리
            'ㅂㅍ', 'ㄷㅌ', 'ㄱㅋ', 'ㅈㅊ',  # 예사소리 + 거센소리
            'ㄹㄹ', 'ㄴㄴ', 'ㅁㅁ'  # 같은 자음 연속
        ]
        
        for combo in difficult_combinations:
            if combo in name:
                score -= 15
        
        # 발음하기 쉬운 자음 조합 보너스
        easy_combinations = [
            'ㄴㅁ', 'ㅁㄴ', 'ㄹㄴ', 'ㄴㄹ',  # 비음 조합
            'ㅅㄴ', 'ㄴㅅ', 'ㅅㅁ', 'ㅁㅅ'   # 마찰음 + 비음
        ]
        
        for combo in easy_combinations:
            if combo in name:
                score += 10
        
        return score
    
    def _count_korean_phonemes(self, name: str) -> tuple:
        """한글 자음/모음 개수 계산"""
        consonants = 0
        vowels = 0
        
        # 한글 자음 (초성, 중성, 종성 포함)
        consonant_chars = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
        vowel_chars = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
        
        for char in name:
            # 한글 음절 분해
            if '가' <= char <= '힣':
                # 유니코드 한글 음절 분해
                code = ord(char) - ord('가')
                initial = code // (21 * 28)  # 초성
                medial = (code % (21 * 28)) // 28  # 중성
                final = code % 28  # 종성
                
                consonants += 1  # 초성
                vowels += 1      # 중성
                if final > 0:    # 종성이 있으면
                    consonants += 1
            elif char in consonant_chars:
                consonants += 1
            elif char in vowel_chars:
                vowels += 1
        
        return consonants, vowels
    
    def _calculate_pronunciation_difficulty(self, name: str) -> float:
        """발음 난이도 계산"""
        difficulty = 0.0
        
        # 어려운 발음 패턴들
        difficult_patterns = {
            'ㅢ': 10,  # 의
            'ㅟ': 8,   # 위
            'ㅚ': 8,   # 외
            'ㅝ': 6,   # 워
            'ㅞ': 8,   # 웨
            'ㅙ': 8,   # 왜
            'ㅘ': 4,   # 와
        }
        
        for pattern, penalty in difficult_patterns.items():
            if pattern in name:
                difficulty += penalty
        
        # 자음군 복잡도
        complex_finals = ['ㄳ', 'ㄵ', 'ㄶ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅄ']
        for final in complex_finals:
            if final in name:
                difficulty += 12
        
        return difficulty
    
    def _analyze_syllable_rhythm(self, name: str) -> float:
        """음절 리듬감 분석"""
        rhythm_score = 0.0
        
        # 음절 수 계산
        syllable_count = len([char for char in name if '가' <= char <= '힣'])
        
        # 2-4음절이 리듬감이 좋음
        if 2 <= syllable_count <= 4:
            rhythm_score += 10
        elif syllable_count == 1:
            rhythm_score -= 5
        elif syllable_count > 5:
            rhythm_score -= 8
        
        # 음성학적 리듬 패턴 (강세 패턴)
        if syllable_count == 2:
            rhythm_score += 5  # 2음절은 기본적으로 리듬감이 좋음
        elif syllable_count == 3:
            rhythm_score += 8  # 3음절은 가장 리듬감이 좋음
        elif syllable_count == 4:
            rhythm_score += 3  # 4음절도 괜찮음
        
        return rhythm_score
    
    def _calculate_search_score(self, name: str, industry: str) -> float:
        """SEO 친화성 기반 검색 점수 계산"""
        score = 100.0
        
        # 1. 업종 관련성 점수 (키워드 매칭)
        industry_relevance = self._calculate_industry_relevance(name, industry)
        score += industry_relevance
        
        # 2. 검색 고유성 점수 (경쟁 키워드 분석)
        uniqueness_score = self._calculate_search_uniqueness(name)
        score += uniqueness_score
        
        # 3. 브랜딩 가능성 점수
        branding_score = self._calculate_branding_potential(name)
        score += branding_score
        
        # 4. 도메인 친화성 점수
        domain_score = self._calculate_domain_friendliness(name)
        score += domain_score
        
        # 5. 검색 엔진 최적화 점수
        seo_score = self._calculate_seo_factors(name)
        score += seo_score
        
        # 6. 소셜 미디어 친화성
        social_score = self._calculate_social_media_friendliness(name)
        score += social_score
        
        return max(0, min(100, score))
    
    def _calculate_industry_relevance(self, name: str, industry: str) -> float:
        """업종 관련성 점수 계산"""
        relevance_score = 0.0
        
        # 직접적인 업종 키워드 매칭
        industry_words = self.industry_keywords.get(industry, [])
        direct_match = False
        
        for word in industry_words:
            if word in name:
                relevance_score += 15
                direct_match = True
                break
        
        # 간접적인 업종 연관성 (의미적 유사성)
        semantic_keywords = {
            "restaurant": ["맛", "향", "요리", "음식", "식당", "밥", "국", "찌개"],
            "retail": ["판매", "구매", "쇼핑", "상품", "물건", "가게"],
            "service": ["서비스", "도움", "지원", "상담", "관리"],
            "healthcare": ["건강", "치료", "의료", "병원", "약", "케어"],
            "education": ["교육", "학습", "공부", "배움", "지식", "스쿨"],
            "technology": ["기술", "IT", "컴퓨터", "소프트", "시스템"],
            "manufacturing": ["제조", "생산", "공장", "만들기"],
            "construction": ["건설", "건축", "집", "빌딩", "공사"],
            "finance": ["돈", "금융", "투자", "은행", "자금"],
            "other": []
        }
        
        if not direct_match:
            semantic_words = semantic_keywords.get(industry, [])
            for word in semantic_words:
                if word in name:
                    relevance_score += 8
                    break
        
        return relevance_score
    
    def _calculate_search_uniqueness(self, name: str) -> float:
        """검색 고유성 점수 계산"""
        uniqueness_score = 0.0
        
        # 일반적인 단어 사용 시 감점 (검색 경쟁 심화)
        common_words = [
            "좋은", "새로운", "최고", "1등", "베스트", "프리미엄", "스페셜",
            "골든", "실버", "다이아", "킹", "퀸", "로얄", "그랜드"
        ]
        
        common_count = sum(1 for word in common_words if word in name)
        uniqueness_score -= common_count * 12
        
        # 독특한 조합 보너스
        if len(name) >= 3:
            # 숫자 + 한글 조합
            has_number = any(char.isdigit() for char in name)
            has_korean = any('가' <= char <= '힣' for char in name)
            if has_number and has_korean:
                uniqueness_score += 8
            
            # 영문 + 한글 조합
            has_english = any(char.isalpha() and ord(char) < 128 for char in name)
            if has_english and has_korean:
                uniqueness_score += 10
        
        # 길이별 고유성 (너무 짧으면 중복 가능성 높음)
        length = len(name)
        if length <= 2:
            uniqueness_score -= 15
        elif length >= 6:
            uniqueness_score += 5
        
        return uniqueness_score
    
    def _calculate_branding_potential(self, name: str) -> float:
        """브랜딩 가능성 점수 계산"""
        branding_score = 0.0
        
        # 기억하기 쉬운 정도
        length = len(name)
        if 3 <= length <= 5:
            branding_score += 12  # 최적 길이
        elif length <= 2:
            branding_score += 5   # 짧아서 기억하기 쉬움
        elif length > 7:
            branding_score -= 8   # 너무 길어서 기억하기 어려움
        
        # 발음 용이성 (브랜딩에 중요)
        pronunciation_ease = self._assess_pronunciation_ease(name)
        branding_score += pronunciation_ease
        
        # 시각적 임팩트 (특수문자, 숫자 사용)
        visual_impact = self._assess_visual_impact(name)
        branding_score += visual_impact
        
        # 확장성 (다양한 매체에서 사용 가능성)
        scalability = self._assess_brand_scalability(name)
        branding_score += scalability
        
        return branding_score
    
    def _calculate_domain_friendliness(self, name: str) -> float:
        """도메인 친화성 점수 계산"""
        domain_score = 0.0
        
        # 도메인으로 사용 가능한 문자만 포함
        domain_safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-')
        korean_chars = set()
        
        for char in name:
            if '가' <= char <= '힣':
                korean_chars.add(char)
            elif char not in domain_safe_chars and char != ' ':
                domain_score -= 5  # 도메인 불가능 문자
        
        # 한글 도메인 가능성 (한글.kr 등)
        if korean_chars:
            domain_score += 3
        
        # 영문 도메인 가능성
        english_chars = sum(1 for char in name if char.isalpha() and ord(char) < 128)
        if english_chars > 0:
            domain_score += 8
        
        # 하이픈 사용 (SEO에 좋음)
        if '-' in name:
            domain_score += 2
        
        # 숫자 사용 (기억하기 쉬움)
        if any(char.isdigit() for char in name):
            domain_score += 3
        
        return domain_score
    
    def _calculate_seo_factors(self, name: str) -> float:
        """검색 엔진 최적화 요소 점수"""
        seo_score = 0.0
        
        # 키워드 밀도 (너무 많은 키워드는 스팸으로 간주)
        keyword_density = self._calculate_keyword_density(name)
        if 0.3 <= keyword_density <= 0.7:
            seo_score += 10
        elif keyword_density > 0.8:
            seo_score -= 5
        
        # 검색 친화적 길이
        length = len(name)
        if 3 <= length <= 6:
            seo_score += 8  # 검색하기 좋은 길이
        
        # 특수문자 최소화 (검색 엔진이 선호)
        special_char_count = sum(1 for char in name if not char.isalnum() and char != ' ')
        if special_char_count == 0:
            seo_score += 5
        elif special_char_count > 2:
            seo_score -= 8
        
        # 공백 처리 (검색 쿼리 친화성)
        if ' ' in name:
            word_count = len(name.split())
            if word_count == 2:
                seo_score += 6  # 2단어 조합이 검색에 좋음
            elif word_count > 3:
                seo_score -= 4  # 너무 많은 단어
        
        return seo_score
    
    def _calculate_social_media_friendliness(self, name: str) -> float:
        """소셜 미디어 친화성 점수"""
        social_score = 0.0
        
        # 해시태그 친화성
        if len(name) <= 6 and ' ' not in name:
            social_score += 8  # 해시태그로 사용하기 좋음
        
        # 멘션 친화성 (@username 형태)
        if name.replace(' ', '').isalnum():
            social_score += 5
        
        # 트렌디한 요소 (숫자, 영문 조합)
        has_trendy_elements = (
            any(char.isdigit() for char in name) or
            any(char.isalpha() and ord(char) < 128 for char in name)
        )
        if has_trendy_elements:
            social_score += 6
        
        # 이모지 친화성 (특수문자 적절 사용)
        special_chars = sum(1 for char in name if not char.isalnum() and char != ' ')
        if special_chars == 1:
            social_score += 3
        
        return social_score
    
    def _assess_pronunciation_ease(self, name: str) -> float:
        """발음 용이성 평가 (브랜딩 관점)"""
        ease_score = 0.0
        
        # 음절 수 (2-3음절이 브랜딩에 최적)
        syllable_count = len([char for char in name if '가' <= char <= '힣'])
        if syllable_count == 2:
            ease_score += 8
        elif syllable_count == 3:
            ease_score += 10
        elif syllable_count == 1:
            ease_score += 5
        elif syllable_count > 4:
            ease_score -= 5
        
        return ease_score
    
    def _assess_visual_impact(self, name: str) -> float:
        """시각적 임팩트 평가"""
        visual_score = 0.0
        
        # 대문자 사용 (브랜드 임팩트)
        uppercase_count = sum(1 for char in name if char.isupper())
        if 1 <= uppercase_count <= 2:
            visual_score += 5
        
        # 숫자 사용 (시각적 구분)
        if any(char.isdigit() for char in name):
            visual_score += 4
        
        # 균형잡힌 구성
        if len(name) >= 3:
            char_types = {
                'korean': sum(1 for char in name if '가' <= char <= '힣'),
                'english': sum(1 for char in name if char.isalpha() and ord(char) < 128),
                'number': sum(1 for char in name if char.isdigit())
            }
            
            # 2가지 이상 문자 타입 사용 시 보너스
            used_types = sum(1 for count in char_types.values() if count > 0)
            if used_types >= 2:
                visual_score += 6
        
        return visual_score
    
    def _assess_brand_scalability(self, name: str) -> float:
        """브랜드 확장성 평가"""
        scalability_score = 0.0
        
        # 다양한 매체 적용 가능성
        if name.replace(' ', '').isalnum():
            scalability_score += 5  # 모든 매체에서 사용 가능
        
        # 국제화 가능성
        has_english = any(char.isalpha() and ord(char) < 128 for char in name)
        if has_english:
            scalability_score += 6  # 해외 진출 시 유리
        
        # 축약 가능성 (긴 이름의 경우)
        if len(name) >= 4:
            scalability_score += 3  # 줄임말 생성 가능
        
        return scalability_score
    
    def _calculate_keyword_density(self, name: str) -> float:
        """키워드 밀도 계산"""
        if len(name) == 0:
            return 0.0
        
        # 의미있는 키워드 개수 계산
        meaningful_chars = sum(1 for char in name if char.isalnum())
        total_chars = len(name)
        
        return meaningful_chars / total_chars if total_chars > 0 else 0.0
    
    def _generate_name_description(self, name: str, industry: str, region: str) -> str:
        """상호명 설명 생성"""
        descriptions = {
            "restaurant": f"'{name}'은 {region} 지역의 특색을 살린 음식점 이름으로, 기억하기 쉽고 친근한 느낌을 줍니다.",
            "retail": f"'{name}'은 고객들이 쉽게 찾을 수 있는 상점명으로, 브랜드 인지도를 높이는 데 효과적입니다.",
            "service": f"'{name}'은 전문성과 신뢰감을 전달하는 서비스업 상호명으로, 고객 신뢰도 향상에 도움이 됩니다.",
            "healthcare": f"'{name}'은 건강과 치료에 대한 전문성을 나타내는 의료업 상호명입니다.",
            "education": f"'{name}'은 학습과 성장을 상징하는 교육업 상호명으로, 학습자들에게 긍정적인 인상을 줍니다.",
            "technology": f"'{name}'은 혁신과 기술력을 강조하는 IT업 상호명으로, 현대적이고 전문적인 이미지를 전달합니다.",
            "manufacturing": f"'{name}'은 제조업의 신뢰성과 품질을 나타내는 상호명입니다.",
            "construction": f"'{name}'은 건설업의 견고함과 전문성을 표현하는 상호명입니다.",
            "finance": f"'{name}'은 금융업의 안정성과 신뢰성을 강조하는 상호명입니다.",
            "other": f"'{name}'은 해당 업종의 특성을 잘 반영한 상호명으로, 고객들에게 좋은 인상을 줄 것입니다."
        }
        
        return descriptions.get(industry, descriptions["other"])
    
    def _suggestion_to_dict(self, suggestion: NameSuggestion) -> Dict[str, Any]:
        """
        NameSuggestion을 딕셔너리로 변환 (DynamoDB 호환)
        
        Float 값을 Decimal로 변환하여 DynamoDB 저장 시 오류 방지
        """
        from decimal import Decimal
        
        # Float를 Decimal로 변환
        result = {
            "name": suggestion.name,
            "description": suggestion.description,
            "pronunciationScore": self.convert_floats_to_decimal(suggestion.pronunciation_score),
            "memorabilityScore": self.convert_floats_to_decimal(suggestion.memorability_score),
            "relevanceScore": self.convert_floats_to_decimal(suggestion.relevance_score),
            "searchScore": self.convert_floats_to_decimal(suggestion.search_score),
            "overallScore": self.convert_floats_to_decimal(suggestion.overall_score)
        }
        
        return result
    
    def _handle_selection(self, session_id: str, selected_name: str, 
                        business_names: BusinessNames) -> Dict[str, Any]:
        """상호명 선택 처리"""
        if not selected_name:
            raise ValueError("Selected name is required")
        
        # 선택된 이름이 제안 목록에 있는지 확인
        valid_names = [s.name for s in business_names.suggestions]
        if selected_name not in valid_names:
            raise ValueError(f"Selected name '{selected_name}' is not in the suggestion list")
        
        # 선택된 이름 저장
        business_names.selected_name = selected_name
        
        # 세션에 저장 (다음 단계로 진행)
        self._save_business_names(session_id, business_names, advance_step=True)
        
        return {
            "sessionId": session_id,
            "selectedName": selected_name,
            "message": f"'{selected_name}' 상호명이 선택되었습니다.",
            "nextStep": "signboard",
            "canProceed": True
        }
    
    def _handle_async_request(self, session_id: str, body: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """비동기 요청 처리 - 즉시 202 반환하고 백그라운드에서 실행"""
        try:
            self.logger.info(f"Starting async name generation for session: {session_id}")
            
            # 상태를 'processing'으로 설정
            self.update_session_data(session_id, {
                'nameGenerationStatus': 'processing',
                'nameGenerationStartedAt': datetime.utcnow().isoformat()
            })
            
            # 즉시 202 Accepted 반환
            response = self.create_lambda_response(202, {
                "sessionId": session_id,
                "status": "processing",
                "message": "Name generation started. Poll /names/status/{sessionId} for results.",
                "pollUrl": f"/names/status/{session_id}",
                "estimatedTime": "60-90 seconds"
            })
            
            # 백그라운드에서 실행 (Lambda는 계속 실행)
            # context.get_remaining_time_in_millis()로 남은 시간 확인
            try:
                business_info = body.get('businessInfo')
                analysis_result = body.get('analysisResult')
                
                # 기존 상호명 데이터 조회
                existing_names = body.get('business_names', {})
                if not existing_names:
                    session_data = self.get_session_data(session_id)
                    if session_data:
                        existing_names = session_data.get('business_names', {})
                
                if isinstance(existing_names, str):
                    existing_names = json.loads(existing_names)
                
                # NameSuggestion 객체들로 변환
                suggestions = []
                for s in existing_names.get('suggestions', []):
                    if isinstance(s, dict):
                        suggestions.append(NameSuggestion(
                            name=s.get('name', ''),
                            description=s.get('description', ''),
                            pronunciation_score=s.get('pronunciationScore', 0.0),
                            search_score=s.get('searchScore', 0.0),
                            overall_score=s.get('overallScore', 0.0)
                        ))
                    else:
                        suggestions.append(s)
                
                business_names = BusinessNames(
                    suggestions=suggestions,
                    selected_name=existing_names.get('selected_name'),
                    regeneration_count=existing_names.get('regeneration_count', 0),
                    max_regenerations=self.max_regenerations
                )
                
                # 상호명 생성 실행
                result = self._handle_suggestion(session_id, business_info, business_names)
                
                # 완료 상태 저장 (Float를 Decimal로 변환)
                converted_result = self.convert_floats_to_decimal(result)
                
                self.update_session_data(session_id, {
                    'nameGenerationStatus': 'completed',
                    'business_names': converted_result,
                    'nameGenerationCompletedAt': datetime.utcnow().isoformat()
                })
                
                self.logger.info(
                    f"Name generation result converted to Decimal for DynamoDB",
                    extra={
                        "agent": "reporter",
                        "session_id": session_id,
                        "suggestions_count": len(result.get('suggestions', []))
                    }
                )
                
                self.logger.info(f"Async name generation completed for session: {session_id}")
                
            except Exception as e:
                # 오류 상태 저장
                error_message = str(e)
                self.logger.error(f"Async name generation failed: {error_message}")
                
                self.update_session_data(session_id, {
                    'nameGenerationStatus': 'failed',
                    'nameGenerationError': error_message,
                    'nameGenerationFailedAt': datetime.utcnow().isoformat()
                })
            
            return response
            
        except Exception as e:
            error_message = f"Failed to start async generation: {str(e)}"
            self.logger.error(error_message)
            return self.create_lambda_response(500, {"error": error_message})
    
    def _is_session_expired(self, session_data: Dict[str, Any]) -> bool:
        """세션 만료 확인"""
        ttl = session_data.get('ttl', 0)
        current_timestamp = datetime.utcnow().timestamp()
        return current_timestamp > ttl
    
    def _sync_with_supervisor(self, session_id: str, action: str, result: Dict[str, Any]) -> None:
        """Supervisor Agent와 상태 동기화"""
        try:
            # Supervisor에게 상태 전송
            status_data = {
                "agent": "reporter",
                "action": action,
                "session_id": session_id,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 재생성 제한 도달 시 특별 처리
            if action == 'regenerate' and not result.get('canRegenerate', True):
                status_data["warning"] = "Maximum regeneration limit reached"
            
            # 선택 완료 시 다음 단계 진행 신호
            if action == 'select':
                status_data["next_step"] = "signboard"
                status_data["ready_for_next"] = True
            
            # Supervisor에게 전송 (communication 인터페이스 사용)
            self.communication.send_to_supervisor(
                agent_id="reporter",
                status="completed" if result.get('canProceed') else "waiting",
                result=status_data,
                session_id=session_id
            )
            
        except Exception as e:
            self.logger.error(f"Failed to sync with supervisor: {str(e)}")
            # 동기화 실패는 치명적이지 않으므로 예외를 다시 발생시키지 않음
    
    def _get_user_error_message(self, error: str) -> str:
        """사용자 친화적 오류 메시지 생성"""
        error_messages = {
            "Session not found": "세션을 찾을 수 없습니다. 새로운 세션을 시작해주세요.",
            "Session expired": "세션이 만료되었습니다. 새로운 세션을 시작해주세요.",
            "Business info not found": "비즈니스 정보가 필요합니다. 분석 단계를 먼저 완료해주세요.",
            "Maximum regeneration limit reached": "재생성 횟수가 한계에 도달했습니다. 현재 제안 중에서 선택해주세요.",
            "Selected name": "선택하신 상호명에 문제가 있습니다. 다시 선택해주세요."
        }
        
        for key, message in error_messages.items():
            if key in error:
                return message
        
        return "상호명 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    
    def _validate_regeneration_request(self, business_names: BusinessNames) -> Dict[str, Any]:
        """재생성 요청 검증 (고도화)"""
        # 기본 재생성 한도 확인
        if not business_names.can_regenerate():
            return {
                "valid": False,
                "error": "Maximum regeneration limit reached",
                "userMessage": f"재생성은 최대 {business_names.max_regenerations}회까지만 가능합니다. 현재 제안 중에서 선택해주세요.",
                "regenerationCount": business_names.regeneration_count,
                "maxRegenerations": business_names.max_regenerations,
                "suggestions": {
                    "action": "select_from_current",
                    "message": "현재 제안된 상호명들을 다시 검토해보시거나, 새로운 세션을 시작해주세요."
                }
            }
        
        # 재생성 품질 경고 (2회차부터)
        warning_message = None
        if business_names.regeneration_count == 1:
            warning_message = "두 번째 재생성입니다. 더 나은 결과를 위해 비즈니스 정보를 구체적으로 검토해보세요."
        elif business_names.regeneration_count == 2:
            warning_message = "마지막 재생성 기회입니다. 신중하게 선택해주세요."
        
        return {
            "valid": True,
            "warning": warning_message,
            "remainingAttempts": business_names.max_regenerations - business_names.regeneration_count,
            "qualityTips": self._get_regeneration_quality_tips(business_names.regeneration_count)
        }
    
    def _get_regeneration_quality_tips(self, regeneration_count: int) -> List[str]:
        """재생성 품질 향상 팁 제공"""
        tips = []
        
        if regeneration_count == 0:
            tips = [
                "첫 번째 제안이 마음에 들지 않으시나요?",
                "재생성하면 완전히 새로운 스타일의 상호명을 제안해드립니다.",
                "발음과 검색 최적화를 고려한 새로운 조합을 생성합니다."
            ]
        elif regeneration_count == 1:
            tips = [
                "두 번째 재생성에서는 더 창의적인 조합을 시도합니다.",
                "지역 특색과 업종 특성을 더 강하게 반영합니다.",
                "트렌드를 반영한 현대적인 네이밍을 우선시합니다."
            ]
        elif regeneration_count == 2:
            tips = [
                "마지막 재생성에서는 가장 독창적인 아이디어를 제안합니다.",
                "기존 제안과 완전히 다른 접근 방식을 사용합니다.",
                "브랜딩 잠재력이 높은 이름들을 우선 선별합니다."
            ]
        
        return tips
    
    def _log_regeneration_attempt(self, session_id: str, regeneration_count: int) -> None:
        """재생성 시도 로깅"""
        self.logger.info(
            f"Name regeneration attempt: session={session_id}, count={regeneration_count}",
            extra={
                "agent": "reporter",
                "tool": "name.regenerate",
                "session_id": session_id,
                "regeneration_count": regeneration_count,
                "action": "regeneration_attempt"
            }
        )
    
    def _save_business_names(self, session_id: str, business_names: BusinessNames, 
                           advance_step: bool = False) -> None:
        """BusinessNames를 세션에 저장"""
        try:
            from decimal import Decimal
            
            # Decimal을 float로 변환하는 helper
            def decimal_to_float(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                elif isinstance(obj, dict):
                    return {k: decimal_to_float(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [decimal_to_float(item) for item in obj]
                return obj
            
            # BusinessNames를 딕셔너리로 변환
            business_names_dict = {
                "suggestions": [self._suggestion_to_dict(s) for s in business_names.suggestions],
                "selected_name": business_names.selected_name,
                "regeneration_count": business_names.regeneration_count,
                "max_regenerations": business_names.max_regenerations
            }
            
            # Decimal을 float로 변환 (JSON serialization을 위해)
            business_names_dict = decimal_to_float(business_names_dict)
            
            # 세션 업데이트
            updates = {
                "business_names": json.dumps(business_names_dict)
            }
            
            # 선택 완료 시 다음 단계로 진행
            if advance_step and business_names.selected_name:
                updates["currentStep"] = WorkflowStep.SIGNBOARD.value
            
            success = self.update_session_data(session_id, updates)
            if not success:
                raise Exception("Failed to update session data")
                
        except Exception as e:
            self.logger.error(f"Failed to save business names: {str(e)}")
            raise


# Lambda 핸들러
def lambda_handler(event, context):
    """Lambda 핸들러 함수"""
    agent = ReporterAgent()
    return agent.lambda_handler(event, context)