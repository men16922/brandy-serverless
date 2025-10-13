"""
Market Analyst Agent - Static Data Loader
JSON 파일에서 정적 참조 데이터를 로드하는 유틸리티
"""

import json
import os
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class MarketDataLoader:
    """Market Analyst Agent의 정적 데이터 로더"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self._cache = {}
    
    def _load_json(self, filename: str) -> Any:
        """JSON 파일 로드 (캐싱 지원)"""
        if filename in self._cache:
            return self._cache[filename]
        
        try:
            file_path = os.path.join(self.data_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cache[filename] = data
                logger.info(f"Loaded {filename} from JSON file")
                return data
        except FileNotFoundError:
            logger.error(f"JSON file not found: {filename}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {filename}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error loading {filename}: {str(e)}")
            return None
    
    def get_generational_preferences(self) -> Dict[str, Any]:
        """세대별 선호도 데이터 로드"""
        data = self._load_json('generational_preferences.json')
        return data if data else {}
    
    def get_regional_preferences(self) -> Dict[str, List[str]]:
        """지역별 선호도 데이터 로드"""
        data = self._load_json('regional_preferences.json')
        return data if data else {}
    
    def get_entry_barriers(self) -> Dict[str, List[Dict[str, str]]]:
        """진입 장벽 데이터 로드"""
        data = self._load_json('entry_barriers.json')
        return data if data else {}
    
    def get_differentiation_factors(self) -> Dict[str, List[str]]:
        """차별화 요소 데이터 로드"""
        data = self._load_json('differentiation_factors.json')
        return data if data else {}
    
    def get_partnership_opportunities(self) -> List[Dict[str, str]]:
        """파트너십 기회 데이터 로드"""
        data = self._load_json('partnership_opportunities.json')
        return data if data else []
    
    def get_expansion_opportunities(self) -> List[Dict[str, str]]:
        """확장 기회 데이터 로드"""
        data = self._load_json('expansion_opportunities.json')
        return data if data else []
    
    def get_trend_risks(self) -> List[Dict[str, str]]:
        """트렌드 변화 위험 데이터 로드"""
        data = self._load_json('trend_risks.json')
        return data if data else []
    
    def get_positioning_strategies(self) -> Dict[str, str]:
        """포지셔닝 전략 데이터 로드"""
        data = self._load_json('positioning_strategies.json')
        return data if data else {}
    
    def get_target_segments(self) -> Dict[str, str]:
        """타겟 세그먼트 데이터 로드"""
        data = self._load_json('target_segments.json')
        return data if data else {}
    
    def get_value_propositions(self) -> Dict[str, str]:
        """가치 제안 데이터 로드"""
        data = self._load_json('value_propositions.json')
        return data if data else {}
    
    def get_tech_impacts(self) -> Dict[str, Dict[str, Any]]:
        """기술 트렌드 영향 데이터 로드"""
        data = self._load_json('tech_impacts.json')
        return data if data else {}
    
    def get_industry_competition(self) -> Dict[str, str]:
        """업종별 경쟁 강도 데이터 로드"""
        data = self._load_json('industry_competition.json')
        return data if data else {}
    
    def get_competitor_adoption(self) -> Dict[str, str]:
        """경쟁사 트렌드 도입 현황 데이터 로드"""
        data = self._load_json('competitor_adoption.json')
        return data if data else {}
    
    def get_regional_adaptation_rates(self) -> Dict[str, Dict[str, str]]:
        """지역별 트렌드 적응도 데이터 로드"""
        data = self._load_json('regional_adaptation_rates.json')
        return data if data else {}
    
    def get_mega_trends(self) -> List[Dict[str, str]]:
        """메가 트렌드 데이터 로드"""
        data = self._load_json('mega_trends.json')
        return data if data else []
    
    def get_consumer_trends(self) -> List[Dict[str, str]]:
        """소비자 행동 변화 트렌드 데이터 로드"""
        data = self._load_json('consumer_trends.json')
        return data if data else []
    
    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        logger.info("Data loader cache cleared")


# Singleton instance
_data_loader_instance = None


def get_data_loader() -> MarketDataLoader:
    """MarketDataLoader 싱글톤 인스턴스 반환"""
    global _data_loader_instance
    if _data_loader_instance is None:
        _data_loader_instance = MarketDataLoader()
    return _data_loader_instance
