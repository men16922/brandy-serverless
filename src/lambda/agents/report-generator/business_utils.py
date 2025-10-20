"""
Business logic utilities for branding
Handles color palettes, budget guides, and recommendations
"""
from typing import Dict, Any, List
import logging


class BusinessUtils:
    """Business logic utilities for branding recommendations"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
    
    def generate_color_palette(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate industry-specific color palette
        
        Args:
            business_info: Business information including industry
        
        Returns:
            Dict with primary, secondary, accent, and text colors
        """
        industry = business_info.get('industry', '').lower()
        
        color_palettes = {
            '카페': {
                'primary': {'name': '따뜻한 브라운', 'hex': '#8B4513', 'usage': '로고, 간판'},
                'secondary': {'name': '크림 베이지', 'hex': '#F5F5DC', 'usage': '배경, 인테리어'},
                'accent': {'name': '골드', 'hex': '#FFD700', 'usage': '포인트 요소'},
                'text': {'name': '다크 브라운', 'hex': '#3C2415', 'usage': '텍스트'}
            },
            '레스토랑': {
                'primary': {'name': '딥 레드', 'hex': '#B22222', 'usage': '로고, 간판'},
                'secondary': {'name': '웜 화이트', 'hex': '#FDF5E6', 'usage': '배경, 메뉴판'},
                'accent': {'name': '골든 옐로우', 'hex': '#DAA520', 'usage': '포인트 요소'},
                'text': {'name': '다크 레드', 'hex': '#8B0000', 'usage': '텍스트'}
            },
            '뷰티': {
                'primary': {'name': '소프트 핑크', 'hex': '#FFB6C1', 'usage': '로고, 간판'},
                'secondary': {'name': '펄 화이트', 'hex': '#F8F8FF', 'usage': '배경'},
                'accent': {'name': '로즈 골드', 'hex': '#E8B4B8', 'usage': '포인트 요소'},
                'text': {'name': '차콜 그레이', 'hex': '#36454F', 'usage': '텍스트'}
            },
            'cafe': {
                'primary': {'name': 'Warm Brown', 'hex': '#8B4513', 'usage': 'Logo, Signboard'},
                'secondary': {'name': 'Cream Beige', 'hex': '#F5F5DC', 'usage': 'Background, Interior'},
                'accent': {'name': 'Gold', 'hex': '#FFD700', 'usage': 'Accent Elements'},
                'text': {'name': 'Dark Brown', 'hex': '#3C2415', 'usage': 'Text'}
            },
            'restaurant': {
                'primary': {'name': 'Deep Red', 'hex': '#B22222', 'usage': 'Logo, Signboard'},
                'secondary': {'name': 'Warm White', 'hex': '#FDF5E6', 'usage': 'Background, Menu'},
                'accent': {'name': 'Golden Yellow', 'hex': '#DAA520', 'usage': 'Accent Elements'},
                'text': {'name': 'Dark Red', 'hex': '#8B0000', 'usage': 'Text'}
            },
            'beauty': {
                'primary': {'name': 'Soft Pink', 'hex': '#FFB6C1', 'usage': 'Logo, Signboard'},
                'secondary': {'name': 'Pearl White', 'hex': '#F8F8FF', 'usage': 'Background'},
                'accent': {'name': 'Rose Gold', 'hex': '#E8B4B8', 'usage': 'Accent Elements'},
                'text': {'name': 'Charcoal Gray', 'hex': '#36454F', 'usage': 'Text'}
            }
        }
        
        # Default color palette
        default_palette = {
            'primary': {'name': '다크 블루', 'hex': '#1E3A8A', 'usage': '로고, 간판'},
            'secondary': {'name': '라이트 그레이', 'hex': '#F3F4F6', 'usage': '배경'},
            'accent': {'name': '그린', 'hex': '#10B981', 'usage': '포인트'},
            'text': {'name': '다크 그레이', 'hex': '#374151', 'usage': '텍스트'}
        }
        
        palette = color_palettes.get(industry, default_palette)
        self.logger.info(f"Generated color palette for industry: {industry}")
        return palette
    
    def generate_budget_guide(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate budget estimates based on business size and industry
        
        Args:
            business_info: Business information including size and industry
        
        Returns:
            Dict with budget ranges for signboard, interior, branding, marketing, and total
        """
        size = business_info.get('size', '소규모')
        industry = business_info.get('industry', '')
        
        # Size multipliers
        multipliers = {'소규모': 1.0, '중규모': 1.8, '대규모': 3.0}
        multiplier = multipliers.get(size, 1.0)
        
        # Industry-specific base costs
        industry_base_costs = {
            '카페': {
                'signboard': {'min': 800000, 'recommended': 1500000, 'max': 3000000},
                'interior': {'min': 5000000, 'recommended': 12000000, 'max': 25000000},
                'branding': {'min': 500000, 'recommended': 1200000, 'max': 2500000},
                'marketing': {'min': 300000, 'recommended': 800000, 'max': 1500000}
            },
            '레스토랑': {
                'signboard': {'min': 1000000, 'recommended': 2000000, 'max': 4000000},
                'interior': {'min': 8000000, 'recommended': 20000000, 'max': 40000000},
                'branding': {'min': 800000, 'recommended': 1800000, 'max': 3500000},
                'marketing': {'min': 500000, 'recommended': 1200000, 'max': 2500000}
            },
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
        
        # Default costs (if industry not found)
        default_costs = {
            'signboard': {'min': 600000, 'recommended': 1200000, 'max': 2500000},
            'interior': {'min': 3000000, 'recommended': 8000000, 'max': 18000000},
            'branding': {'min': 400000, 'recommended': 1000000, 'max': 2000000},
            'marketing': {'min': 250000, 'recommended': 600000, 'max': 1200000}
        }
        
        base_costs = industry_base_costs.get(industry, default_costs)
        
        # Apply size multiplier
        budget_guide = {}
        for category, costs in base_costs.items():
            budget_guide[category] = {
                'min': int(costs['min'] * multiplier),
                'recommended': int(costs['recommended'] * multiplier),
                'max': int(costs['max'] * multiplier)
            }
        
        # Calculate total budget
        total_min = sum(item['min'] for item in budget_guide.values())
        total_recommended = sum(item['recommended'] for item in budget_guide.values())
        total_max = sum(item['max'] for item in budget_guide.values())
        
        budget_guide['total'] = {
            'min': total_min,
            'recommended': total_recommended,
            'max': total_max
        }
        
        self.logger.info(f"Generated budget guide for {industry} ({size}): {total_recommended:,}원 recommended")
        return budget_guide
    
    def generate_recommendations(
        self, 
        business_info: Dict[str, Any], 
        analysis_result: Dict[str, Any]
    ) -> List[str]:
        """
        Generate business recommendations based on industry and analysis
        
        Args:
            business_info: Business information including industry and region
            analysis_result: Analysis results with scores
        
        Returns:
            List of recommendation strings (max 5)
        """
        industry = business_info.get('industry', '').lower()
        region = business_info.get('region', '')
        
        # Industry-specific recommendations
        industry_recommendations = {
            '카페': [
                "편안하고 아늑한 분위기 조성에 집중하세요",
                "SNS 친화적인 포토존 설치를 고려하세요",
                "계절별 메뉴와 연계한 인테리어 변화를 계획하세요",
                "자연광을 최대한 활용한 좌석 배치를 권장합니다"
            ],
            '레스토랑': [
                "음식의 맛을 돋보이게 하는 조명 설계가 중요합니다",
                "테이블 배치와 동선을 효율적으로 계획하세요",
                "브랜드 스토리를 공간에 녹여내는 것이 핵심입니다",
                "주방과 홀의 소음 차단에 신경 쓰세요"
            ],
            '뷰티': [
                "고급스럽고 청결한 이미지 구축이 최우선입니다",
                "고객 프라이버시를 고려한 공간 설계를 하세요",
                "조명은 피부톤을 자연스럽게 보이도록 설정하세요",
                "위생과 안전을 강조하는 인테리어를 선택하세요"
            ],
            'cafe': [
                "Focus on creating a comfortable and cozy atmosphere",
                "Consider installing SNS-friendly photo zones",
                "Plan interior changes linked to seasonal menus",
                "Maximize natural light in seating arrangements"
            ],
            'restaurant': [
                "Lighting design that enhances food presentation is crucial",
                "Plan efficient table layout and traffic flow",
                "Incorporate brand story into the space design",
                "Pay attention to noise isolation between kitchen and dining area"
            ],
            'beauty': [
                "Luxurious and clean image is top priority",
                "Design space with customer privacy in mind",
                "Set lighting to show natural skin tones",
                "Choose interior that emphasizes hygiene and safety"
            ]
        }
        
        # Default recommendations
        default_recommendations = [
            "타겟 고객층의 니즈를 정확히 파악하여 반영하세요",
            "브랜드 일관성을 모든 접점에서 유지하세요",
            "지속적인 브랜드 발전을 위한 장기 계획을 수립하세요",
            "경쟁사 대비 차별화 포인트를 명확히 하세요"
        ]
        
        recommendations = industry_recommendations.get(industry, default_recommendations).copy()
        
        # Add analysis-based recommendations
        if analysis_result:
            score = analysis_result.get('overall_score', 0)
            if score < 60:
                recommendations.append("시장 분석을 통해 포지셔닝을 재검토해보세요")
            elif score > 80:
                recommendations.append("높은 잠재력을 바탕으로 적극적인 마케팅을 추진하세요")
        
        # Add region-specific recommendations
        if '강남' in region:
            recommendations.append("고급스러운 이미지와 트렌디한 요소를 강조하세요")
        elif '홍대' in region:
            recommendations.append("젊고 개성 있는 컨셉으로 차별화하세요")
        
        final_recommendations = recommendations[:5]  # Max 5 recommendations
        self.logger.info(f"Generated {len(final_recommendations)} recommendations for {industry}")
        return final_recommendations
