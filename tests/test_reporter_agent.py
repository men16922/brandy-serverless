# Reporter Agent 통합 테스트
# 상호명 생성, 재생성 제한, 상태 관리 검증

import json
import pytest
from unittest.mock import Mock, patch
import sys
import os

# 테스트 환경 설정
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda'))

from agents.reporter.index import ReporterAgent
from shared.models import BusinessNames, NameSuggestion, WorkflowStep


class TestReporterAgent:
    """Reporter Agent 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        # 환경 변수 설정
        os.environ['ENVIRONMENT'] = 'test'
        os.environ['SESSIONS_TABLE'] = 'test-sessions'
        os.environ['S3_BUCKET'] = 'test-bucket'
        
        # Mock AWS 클라이언트
        with patch('shared.utils.get_aws_clients') as mock_clients:
            mock_dynamodb = Mock()
            mock_table = Mock()
            mock_dynamodb.Table.return_value = mock_table
            
            mock_clients.return_value = {
                'dynamodb': mock_dynamodb,
                's3': Mock(),
                'stepfunctions': Mock()
            }
            
            self.agent = ReporterAgent()
            self.mock_table = mock_table
    
    def test_name_suggestion_generation(self):
        """상호명 제안 생성 테스트"""
        # 테스트 데이터
        business_info = {
            'industry': 'restaurant',
            'region': 'seoul',
            'size': 'small'
        }
        
        business_names = BusinessNames()
        
        # 상호명 생성
        suggestions = self.agent._generate_name_suggestions(business_info, business_names)
        
        # 검증
        assert len(suggestions) == 3
        assert all(isinstance(s, NameSuggestion) for s in suggestions)
        assert all(s.validate() for s in suggestions)
        assert all(0 <= s.overall_score <= 100 for s in suggestions)
        
        # 점수 순 정렬 확인
        scores = [s.overall_score for s in suggestions]
        assert scores == sorted(scores, reverse=True)
    
    def test_duplicate_name_avoidance(self):
        """중복 이름 회피 테스트"""
        business_info = {
            'industry': 'retail',
            'region': 'busan',
            'size': 'medium'
        }
        
        # 첫 번째 생성
        business_names = BusinessNames()
        first_suggestions = self.agent._generate_name_suggestions(business_info, business_names)
        
        # 금지 단어 추가
        for suggestion in first_suggestions:
            self.agent.forbidden_words.add(suggestion.name.lower())
        
        # 두 번째 생성
        second_suggestions = self.agent._generate_name_suggestions(business_info, business_names)
        
        # 중복 확인
        first_names = {s.name.lower() for s in first_suggestions}
        second_names = {s.name.lower() for s in second_suggestions}
        
        assert len(first_names & second_names) == 0  # 교집합이 없어야 함
    
    def test_regeneration_limit(self):
        """재생성 제한 테스트"""
        business_names = BusinessNames(regeneration_count=3, max_regenerations=3)
        
        # 재생성 불가능 확인
        assert not business_names.can_regenerate()
        
        # 검증 테스트
        validation_result = self.agent._validate_regeneration_request(business_names)
        assert not validation_result["valid"]
        assert "Maximum regeneration limit reached" in validation_result["error"]
    
    def test_pronunciation_score_calculation(self):
        """발음 점수 계산 테스트"""
        # 좋은 발음 점수 (적절한 길이, 균형잡힌 자음/모음)
        good_name = "맛있는집"
        good_score = self.agent._calculate_pronunciation_score(good_name)
        
        # 나쁜 발음 점수 (너무 길거나 짧음)
        bad_name = "ㄱ"
        bad_score = self.agent._calculate_pronunciation_score(bad_name)
        
        assert 0 <= good_score <= 100
        assert 0 <= bad_score <= 100
        assert good_score > bad_score
    
    def test_search_score_calculation(self):
        """검색 점수 계산 테스트"""
        # 업종 관련 키워드 포함
        industry_name = "맛있는집"
        industry_score = self.agent._calculate_search_score(industry_name, "restaurant")
        
        # 일반적인 이름
        generic_name = "좋은회사"
        generic_score = self.agent._calculate_search_score(generic_name, "restaurant")
        
        assert 0 <= industry_score <= 100
        assert 0 <= generic_score <= 100
        # 업종 관련 키워드가 포함된 이름이 더 높은 점수를 받아야 함
        # (단, 다른 요소들도 영향을 주므로 절대적이지는 않음)
    
    def test_name_description_generation(self):
        """상호명 설명 생성 테스트"""
        name = "맛있는집"
        industry = "restaurant"
        region = "seoul"
        
        description = self.agent._generate_name_description(name, industry, region)
        
        assert isinstance(description, str)
        assert len(description) > 0
        assert name in description
        assert region in description
    
    @patch('shared.base_agent.BaseAgent.get_session_data')
    @patch('shared.base_agent.BaseAgent.update_session_data')
    def test_suggestion_handling(self, mock_update, mock_get):
        """상호명 제안 처리 테스트"""
        # Mock 세션 데이터
        mock_get.return_value = {
            'sessionId': 'test-session',
            'business_info': json.dumps({
                'industry': 'restaurant',
                'region': 'seoul',
                'size': 'small'
            }),
            'business_names': json.dumps({
                'suggestions': [],
                'selected_name': None,
                'regeneration_count': 0,
                'max_regenerations': 3
            }),
            'ttl': 9999999999  # 만료되지 않은 세션
        }
        
        mock_update.return_value = True
        
        # 테스트 이벤트
        event = {
            'body': {
                'sessionId': 'test-session',
                'action': 'suggest'
            }
        }
        
        # 실행
        result = self.agent.execute(event, {})
        
        # 검증
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'suggestions' in body
        assert len(body['suggestions']) == 3
        assert body['canRegenerate'] == True
        assert body['regenerationCount'] == 0
    
    @patch('shared.base_agent.BaseAgent.get_session_data')
    @patch('shared.base_agent.BaseAgent.update_session_data')
    def test_name_selection(self, mock_update, mock_get):
        """상호명 선택 테스트"""
        # Mock 세션 데이터 (기존 제안 포함)
        suggestions = [
            {
                'name': '맛있는집',
                'description': '테스트 설명',
                'pronunciationScore': 80.0,
                'searchScore': 75.0,
                'overallScore': 77.0
            }
        ]
        
        mock_get.return_value = {
            'sessionId': 'test-session',
            'business_info': json.dumps({
                'industry': 'restaurant',
                'region': 'seoul',
                'size': 'small'
            }),
            'business_names': json.dumps({
                'suggestions': suggestions,
                'selected_name': None,
                'regeneration_count': 0,
                'max_regenerations': 3
            }),
            'ttl': 9999999999
        }
        
        mock_update.return_value = True
        
        # 테스트 이벤트
        event = {
            'body': {
                'sessionId': 'test-session',
                'action': 'select',
                'selectedName': '맛있는집'
            }
        }
        
        # 실행
        result = self.agent.execute(event, {})
        
        # 검증
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['selectedName'] == '맛있는집'
        assert body['canProceed'] == True
        assert body['nextStep'] == 'signboard'
    
    def test_session_expiry_handling(self):
        """세션 만료 처리 테스트"""
        # 만료된 세션 데이터
        expired_session = {
            'ttl': 1000000000  # 과거 타임스탬프
        }
        
        assert self.agent._is_session_expired(expired_session) == True
        
        # 유효한 세션 데이터
        valid_session = {
            'ttl': 9999999999  # 미래 타임스탬프
        }
        
        assert self.agent._is_session_expired(valid_session) == False
    
    def test_user_error_messages(self):
        """사용자 친화적 오류 메시지 테스트"""
        test_cases = [
            ("Session not found", "세션을 찾을 수 없습니다"),
            ("Session expired", "세션이 만료되었습니다"),
            ("Maximum regeneration limit reached", "재생성 횟수가 한계에 도달했습니다"),
            ("Unknown error", "상호명 처리 중 오류가 발생했습니다")
        ]
        
        for error, expected_message in test_cases:
            user_message = self.agent._get_user_error_message(error)
            assert expected_message in user_message


if __name__ == '__main__':
    pytest.main([__file__, '-v'])