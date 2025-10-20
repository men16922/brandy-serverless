"""
Utility Functions Module
색상 팔레트, 예산 가이드, 권장사항 생성
"""

from typing import Dict, Any, List


class ReportUtils:
    """보고서 생성 유틸리티"""
    
    @staticmethod
    def generate_color_palette(business_info: Dict[str, Any]) -> Dict[str, Any]:
        """업종별 색상 팔레트 생성"""
        industry = business_info.get('industry', '').lower()
        
        color_palettes = {
            'cafe': {
                'primary': {'name': '따뜻한 브라운', 'hex': '#8B4513', 'usage': '로고, 간판'},
                'secondary': {'name': '크림 베이지', 'hex': '#F5F5DC', 'usage': '배경, 인테리어'},
                'accent': {'name': '골드', 'hex': '#FFD700', 'usage': '포인트 요소'},
                'text': {'name': '다크 브라운', 'hex': '#3C2415', 'usage': '텍스트'}
            },
            'restaurant': {
                'primary': {'name': '딥 레드', 'hex': '#B22222', 'usage': '로고, 간판'},
                'secondary': {'name': '웜 화이트', 'hex': '#FDF5E6', 'usage': '배경, 메뉴판'},
                'accent': {'name': '골든 옐로우', 'hex': '#DAA520', 'usage': '포인트 요소'},
                'text': {'name': '다크 레드', 'hex': '#8B0000', 'usage': '텍스트'}
            },
            'beauty': {
                'primary': {'name': '소프트 핑크', 'hex': '#FFB6C1', 'usage': '로고, 간판'},
                'secondary': {'name': '펄 화이트', 'hex': '#F8F8FF', 'usage': '배경'},
                'accent': {'name': '로즈 골드', 'hex': '#E8B4B8', 'usage': '포인트 요소'},
                'text': {'name': '차콜 그레이', 'hex': '#36454F', 'usage': '텍스트'}
            }
        }
        
        # 기본 색상 팔레트
        default_palette = {
            'primary': {'name': '다크 블루', 'hex': '#1E3A8A', 'usage': '로고, 간판'},
            'secondary': {'name': '라이트 그레이', 'hex': '#F3F4F6', 'usage': '배경'},
            'accent': {'name': '그린', 'hex': '#10B981', 'usage': '포인트'},
            'text': {'name': '다크 그레이', 'hex': '#374151', 'usage': '텍스트'}
        }
        
        return color_palettes.get(industry, default_palette)

    @staticmethod
    def generate_budget_guide(business_info: Dict[str, Any]) -> Dict[str, Any]:
        """규모별 예산 가이드 생성"""
        size = business_info.get('size', 'small')
        industry = business_info.get('industry', '')
        
        # 규모별 배수
        multipliers = {'small': 1.0, 'medium': 1.8, 'large': 3.0}
        multiplier = multipliers.get(size, 1.0)
        
        # 업종별 기본 비용
        industry_base_costs = {
            'cafe': {
                'signboard': {'min': 800000, 'recommended': 1500000, 'max': 3000000},
                'interior': {'min': 5000000, 'recommended': 12000000, 'max': 25000000},
                'branding': {'min': 500000, 'recommended': 1200000, 'max': 2500000},
                'marketing': {'min': 300000, 'recommended': 800000, 'max': 1500000}
            },
            'restaurant': {
                'signboard': {'min': 1000000, 'recommended': 2000000, 'max': 4000000},
                'interior': {'min': 8000000, 'recommended': 20000000, 'max': 40000000},
                'branding': {'min': 800000, 'recommended': 1800000, 'max': 3500000},
                'marketing': {'min': 500000, 'recommended': 1200000, 'max': 2500000}
            }
        }
        
        # 기본 비용
        default_costs = {
            'signboard': {'min': 600000, 'recommended': 1200000, 'max': 2500000},
            'interior': {'min': 3000000, 'recommended': 8000000, 'max': 18000000},
            'branding': {'min': 400000, 'recommended': 1000000, 'max': 2000000},
            'marketing': {'min': 250000, 'recommended': 600000, 'max': 1200000}
        }
        
        base_costs = industry_base_costs.get(industry, default_costs)
        
        # 규모별 조정
        budget_guide = {}
        for category, costs in base_costs.items():
            budget_guide[category] = {
                'min': int(costs['min'] * multiplier),
                'recommended': int(costs['recommended'] * multiplier),
                'max': int(costs['max'] * multiplier)
            }
        
        # 총 예산 계산
        total_min = sum(item['min'] for item in budget_guide.values())
        total_recommended = sum(item['recommended'] for item in budget_guide.values())
        total_max = sum(item['max'] for item in budget_guide.values())
        
        budget_guide['total'] = {
            'min': total_min,
            'recommended': total_recommended,
            'max': total_max
        }
        
        return budget_guide

    @staticmethod
    def generate_recommendations(business_info: Dict[str, Any], analysis_result: Dict[str, Any]) -> List[str]:
        """업종 및 분석 결과 기반 권장사항 생성"""
        industry = business_info.get('industry', '').lower()
        region = business_info.get('region', '')
        
        # 업종별 기본 권장사항
        industry_recommendations = {
            'cafe': [
                "편안하고 아늑한 분위기 조성에 집중하세요",
                "SNS 친화적인 포토존 설치를 고려하세요",
                "계절별 메뉴와 연계한 인테리어 변화를 계획하세요",
                "자연광을 최대한 활용한 좌석 배치를 권장합니다"
            ],
            'restaurant': [
                "음식의 맛을 돋보이게 하는 조명 설계가 중요합니다",
                "테이블 배치와 동선을 효율적으로 계획하세요",
                "브랜드 스토리를 공간에 녹여내는 것이 핵심입니다",
                "주방과 홀의 소음 차단에 신경 쓰세요"
            ],
            'beauty': [
                "고급스럽고 청결한 이미지 구축이 최우선입니다",
                "고객 프라이버시를 고려한 공간 설계를 하세요",
                "조명은 피부톤을 자연스럽게 보이도록 설정하세요",
                "위생과 안전을 강조하는 인테리어를 선택하세요"
            ]
        }
        
        # 기본 권장사항
        default_recommendations = [
            "타겟 고객층의 니즈를 정확히 파악하여 반영하세요",
            "브랜드 일관성을 모든 접점에서 유지하세요",
            "지속적인 브랜드 발전을 위한 장기 계획을 수립하세요",
            "경쟁사 대비 차별화 포인트를 명확히 하세요"
        ]
        
        recommendations = industry_recommendations.get(industry, default_recommendations)
        
        # 분석 결과 기반 추가 권장사항
        if analysis_result:
            score = analysis_result.get('overall_score', 0)
            if score < 60:
                recommendations.append("시장 분석을 통해 포지셔닝을 재검토해보세요")
            elif score > 80:
                recommendations.append("높은 잠재력을 바탕으로 적극적인 마케팅을 추진하세요")
        
        return recommendations[:5]  # 최대 5개 권장사항
