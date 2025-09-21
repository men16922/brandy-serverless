#!/usr/bin/env python3
"""
Reporter Agent 사용 예제
상호명 제안, 재생성, 선택 기능 데모
"""

import json
import sys
import os

# 경로 설정
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda'))

from agents.reporter.index import ReporterAgent


def demo_reporter_agent():
    """Reporter Agent 기능 데모"""
    print("=== Reporter Agent 데모 ===\n")
    
    # 테스트용 세션 데이터
    session_data = {
        'sessionId': 'demo-session-001',
        'business_info': {
            'industry': 'restaurant',
            'region': 'seoul',
            'size': 'small',
            'description': '한식 전문 음식점'
        },
        'business_names': {
            'suggestions': [],
            'selected_name': None,
            'regeneration_count': 0,
            'max_regenerations': 3
        },
        'ttl': 9999999999  # 만료되지 않은 세션
    }
    
    # Mock 환경 설정
    os.environ['ENVIRONMENT'] = 'demo'
    os.environ['SESSIONS_TABLE'] = 'demo-sessions'
    os.environ['S3_BUCKET'] = 'demo-bucket'
    
    try:
        # Reporter Agent 인스턴스 생성
        agent = ReporterAgent()
        
        # 1. 상호명 제안 생성
        print("1. 상호명 제안 생성")
        print("-" * 30)
        
        from shared.models import BusinessNames
        
        suggestions = agent._generate_name_suggestions(
            session_data['business_info'],
            BusinessNames()
        )
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion.name}")
            print(f"   설명: {suggestion.description}")
            print(f"   발음 점수: {suggestion.pronunciation_score:.1f}")
            print(f"   검색 점수: {suggestion.search_score:.1f}")
            print(f"   종합 점수: {suggestion.overall_score:.1f}")
            print()
        
        # 2. 중복 회피 테스트
        print("2. 중복 회피 테스트")
        print("-" * 30)
        
        # 첫 번째 제안들을 금지 단어로 추가
        for suggestion in suggestions:
            agent.forbidden_words.add(suggestion.name.lower())
        
        # 새로운 제안 생성
        new_suggestions = agent._generate_name_suggestions(
            session_data['business_info'],
            BusinessNames()
        )
        
        print("새로운 제안 (중복 회피):")
        for i, suggestion in enumerate(new_suggestions, 1):
            print(f"{i}. {suggestion.name} (점수: {suggestion.overall_score:.1f})")
        
        # 중복 확인
        original_names = {s.name.lower() for s in suggestions}
        new_names = {s.name.lower() for s in new_suggestions}
        duplicates = original_names & new_names
        
        print(f"\n중복된 이름: {len(duplicates)}개")
        if duplicates:
            print(f"중복 목록: {list(duplicates)}")
        else:
            print("중복 없음 ✓")
        
        # 3. 점수 계산 테스트
        print("\n3. 점수 계산 테스트")
        print("-" * 30)
        
        test_names = ["맛있는집", "서울키친", "A급식당", "1번가든", "ㄱㄴㄷ"]
        
        for name in test_names:
            pronunciation_score = agent._calculate_pronunciation_score(name)
            search_score = agent._calculate_search_score(name, "restaurant")
            overall_score = (pronunciation_score * agent.pronunciation_weight + 
                           search_score * agent.search_weight)
            
            print(f"{name}:")
            print(f"  발음: {pronunciation_score:.1f}, 검색: {search_score:.1f}, 종합: {overall_score:.1f}")
        
        # 4. 재생성 제한 테스트
        print("\n4. 재생성 제한 테스트")
        print("-" * 30)
        
        # 재생성 횟수별 테스트
        for count in range(5):
            business_names = BusinessNames(regeneration_count=count, max_regenerations=3)
            can_regenerate = business_names.can_regenerate()
            validation = agent._validate_regeneration_request(business_names)
            
            print(f"재생성 {count}회: {'가능' if can_regenerate else '불가능'}")
            if not validation['valid']:
                print(f"  오류: {validation['userMessage']}")
        
        print("\n=== 데모 완료 ===")
        
    except Exception as e:
        print(f"데모 실행 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    demo_reporter_agent()