# Reporter Agent Lambda Function
# 3개 상호명 후보 생성, 중복 회피 알고리즘, 발음/검색 점수 산출, 재생성 제한

import json
import re
import random
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import sys

# 공통 유틸리티 import
sys.path.append('/opt/python')
from shared.base_agent import BaseAgent
from shared.models import AgentType, NameSuggestion, BusinessNames, WorkflowStep
from shared.utils import create_response


class ReporterAgent(BaseAgent):
    """Reporter Agent - 상호명 제안 및 재생성 관리"""
    
    def __init__(self):
        super().__init__(AgentType.REPORTER)
        
        # 상호명 생성 관련 설정
        self.max_regenerations = 3
        self.target_suggestions = 3
        
        # 발음/검색 점수 가중치
        self.pronunciation_weight = 0.4
        self.search_weight = 0.6
        
        # 업종별 키워드 매핑
        self.industry_keywords = {
            "restaurant": ["맛", "향", "집", "원", "가든", "하우스", "키친", "테이블"],
            "retail": ["샵", "스토어", "마켓", "플레이스", "코너", "갤러리"],
            "service": ["센터", "스튜디오", "랩", "클리닉", "오피스", "룸"],
            "healthcare": ["클리닉", "케어", "메디", "헬스", "웰", "라이프"],
            "education": ["아카데미", "스쿨", "센터", "랩", "스튜디오", "클래스"],
            "technology": ["테크", "랩", "시스템", "솔루션", "이노베이션"],
            "manufacturing": ["팩토리", "웍스", "인더스트리", "메이커"],
            "construction": ["빌드", "컨스트럭션", "하우징", "데벨롭"],
            "finance": ["파이낸스", "캐피탈", "인베스트", "펀드"],
            "other": ["컴퍼니", "그룹", "파트너스", "솔루션"]
        }
        
        # 지역별 특성 키워드
        self.region_keywords = {
            "seoul": ["서울", "한강", "남산", "강남", "홍대", "명동"],
            "busan": ["부산", "해운대", "광안", "태종대", "감천"],
            "daegu": ["대구", "팔공산", "수성", "중앙로"],
            "incheon": ["인천", "송도", "월미도", "차이나타운"],
            "gwangju": ["광주", "무등산", "충장로"],
            "daejeon": ["대전", "유성", "둔산", "엑스포"],
            "ulsan": ["울산", "태화강", "간절곶"],
            "gyeonggi": ["경기", "수원", "성남", "고양", "용인"],
            "gangwon": ["강원", "설악", "평창", "춘천", "강릉"],
            "chungbuk": ["충북", "청주", "제천", "단양"],
            "chungnam": ["충남", "천안", "아산", "공주"],
            "jeonbuk": ["전북", "전주", "군산", "익산"],
            "jeonnam": ["전남", "목포", "여수", "순천"],
            "gyeongbuk": ["경북", "경주", "안동", "포항"],
            "gyeongnam": ["경남", "창원", "진주", "통영"],
            "jeju": ["제주", "한라산", "성산", "우도"]
        }
        
        # 금지 단어 목록 (중복 회피용)
        self.forbidden_words = set()
        
    def execute(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Reporter Agent 실행 로직"""
        try:
            # 요청 파싱
            if isinstance(event.get('body'), str):
                body = json.loads(event['body'])
            else:
                body = event.get('body', event)
            
            session_id = body.get('sessionId')
            action = body.get('action', 'suggest')  # suggest, regenerate, select
            
            if not session_id:
                return self.create_lambda_response(400, {"error": "sessionId is required"})
            
            # 실행 시작
            tool_name = "name.select" if action == 'select' else "name.generate"
            self.start_execution(session_id, tool_name)
            
            # 세션 데이터 조회
            session_data = self.get_session_data(session_id)
            if not session_data:
                self.end_execution("error", "Session not found")
                return self.create_lambda_response(404, {"error": "Session not found"})
            
            # 세션 만료 확인
            if self._is_session_expired(session_data):
                self.end_execution("error", "Session expired")
                return self.create_lambda_response(410, {"error": "Session expired"})
            
            # 비즈니스 정보 확인
            business_info = session_data.get('business_info')
            if isinstance(business_info, str):
                business_info = json.loads(business_info)
            
            if not business_info:
                self.end_execution("error", "Business info not found")
                return self.create_lambda_response(400, {"error": "Business info required"})
            
            # 기존 상호명 데이터 조회
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
    
    def _generate_name_suggestions(self, business_info: Dict[str, Any], 
                                 business_names: BusinessNames) -> List[NameSuggestion]:
        """상호명 제안 생성"""
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
            overall_score = (pronunciation_score * self.pronunciation_weight + 
                           search_score * self.search_weight)
            
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
        
        # 점수 순으로 정렬
        suggestions.sort(key=lambda x: x.overall_score, reverse=True)
        
        return suggestions[:self.target_suggestions]
    
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
        """중복 이름 확인"""
        name_lower = name.lower()
        
        # 금지 단어 목록 확인
        if name_lower in self.forbidden_words:
            return True
        
        # 기존 제안과 중복 확인
        for suggestion in existing_suggestions:
            if suggestion.name.lower() == name_lower:
                return True
        
        # 유사도 확인 (편집 거리 기반)
        for suggestion in existing_suggestions:
            if self._calculate_similarity(name, suggestion.name) > 0.8:
                return True
        
        return False
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """두 이름의 유사도 계산 (간단한 편집 거리 기반)"""
        if len(name1) == 0 or len(name2) == 0:
            return 0.0
        
        # 공통 문자 비율 계산
        common_chars = set(name1) & set(name2)
        total_chars = set(name1) | set(name2)
        
        if len(total_chars) == 0:
            return 0.0
        
        return len(common_chars) / len(total_chars)
    
    def _calculate_pronunciation_score(self, name: str) -> float:
        """발음 점수 계산"""
        score = 100.0
        
        # 길이 점수 (3-6자가 최적)
        length = len(name)
        if length < 2:
            score -= 30
        elif length > 8:
            score -= 20
        elif 3 <= length <= 6:
            score += 10
        
        # 발음 용이성 (자음/모음 비율)
        consonants = 0
        vowels = 0
        
        for char in name:
            if char in "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ":
                consonants += 1
            elif char in "ㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣ":
                vowels += 1
        
        # 자음/모음 균형 점수
        if consonants > 0 and vowels > 0:
            ratio = min(consonants, vowels) / max(consonants, vowels)
            score += ratio * 10
        
        # 반복 문자 패널티
        for i in range(len(name) - 1):
            if name[i] == name[i + 1]:
                score -= 5
        
        # 특수문자/숫자 보너스 (적절한 사용)
        special_count = sum(1 for char in name if not char.isalnum())
        if special_count == 1:
            score += 5
        elif special_count > 2:
            score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_search_score(self, name: str, industry: str) -> float:
        """검색 점수 계산"""
        score = 100.0
        
        # 업종 관련성 점수
        industry_words = self.industry_keywords.get(industry, [])
        for word in industry_words:
            if word in name:
                score += 15
                break
        
        # 고유성 점수 (일반적인 단어 사용 시 감점)
        common_words = ["좋은", "새로운", "최고", "1등", "베스트"]
        for word in common_words:
            if word in name:
                score -= 10
        
        # 기억하기 쉬운 정도
        if len(name) <= 4:
            score += 10
        elif len(name) > 7:
            score -= 5
        
        # 브랜딩 가능성 (영문 포함 시 보너스)
        if any(char.isalpha() and ord(char) < 128 for char in name):
            score += 10
        
        # 도메인 가능성 (특수문자 없으면 보너스)
        if name.replace(" ", "").isalnum():
            score += 5
        
        return max(0, min(100, score))
    
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
        """NameSuggestion을 딕셔너리로 변환"""
        return {
            "name": suggestion.name,
            "description": suggestion.description,
            "pronunciationScore": suggestion.pronunciation_score,
            "searchScore": suggestion.search_score,
            "overallScore": suggestion.overall_score
        }
    
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
        """재생성 요청 검증"""
        if not business_names.can_regenerate():
            return {
                "valid": False,
                "error": "Maximum regeneration limit reached",
                "userMessage": f"재생성은 최대 {business_names.max_regenerations}회까지만 가능합니다. 현재 제안 중에서 선택해주세요.",
                "regenerationCount": business_names.regeneration_count,
                "maxRegenerations": business_names.max_regenerations
            }
        
        return {"valid": True}
    
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
            # BusinessNames를 딕셔너리로 변환
            business_names_dict = {
                "suggestions": [self._suggestion_to_dict(s) for s in business_names.suggestions],
                "selected_name": business_names.selected_name,
                "regeneration_count": business_names.regeneration_count,
                "max_regenerations": business_names.max_regenerations
            }
            
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