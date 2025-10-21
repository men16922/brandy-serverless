"""
Utility Functions Module
Generates color palettes, budget guides, and business recommendations
"""

from typing import Dict, Any, List


class ReportUtils:
    """Utility class for generating report content"""
    
    @staticmethod
    def generate_color_palette(business_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate color palette by industry"""
        industry = business_info.get('industry', '').lower()
        
        color_palettes = {
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
            'primary': {'name': 'Dark Blue', 'hex': '#1E3A8A', 'usage': 'Logo, Signboard'},
            'secondary': {'name': 'Light Gray', 'hex': '#F3F4F6', 'usage': 'Background'},
            'accent': {'name': 'Green', 'hex': '#10B981', 'usage': 'Accent'},
            'text': {'name': 'Dark Gray', 'hex': '#374151', 'usage': 'Text'}
        }
        
        return color_palettes.get(industry, default_palette)

    @staticmethod
    def generate_budget_guide(business_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate budget guide based on business size"""
        size = business_info.get('size', 'small')
        industry = business_info.get('industry', '')
        
        # Multipliers by business size
        multipliers = {'small': 1.0, 'medium': 1.8, 'large': 3.0}
        multiplier = multipliers.get(size, 1.0)
        
        # Industry-specific base costs
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
        
        # Default costs
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
        
        return budget_guide

    @staticmethod
    def generate_recommendations(business_info: Dict[str, Any], analysis_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on industry and analysis results"""
        industry = business_info.get('industry', '').lower()
        region = business_info.get('region', '')
        
        # Industry-specific recommendations
        industry_recommendations = {
            'cafe': [
                "Focus on creating a comfortable and cozy atmosphere.",
                "Consider installing SNS-friendly photo zones.",
                "Plan seasonal interior updates linked to menu changes.",
                "Maximize natural light for seating arrangements."
            ],
            'restaurant': [
                "Design lighting to highlight the visual appeal of dishes.",
                "Optimize table layout and movement flow for efficiency.",
                "Incorporate your brand story into the overall space design.",
                "Pay attention to sound insulation between the kitchen and dining area."
            ],
            'beauty': [
                "Prioritize a luxurious and clean image.",
                "Design spaces that ensure customer privacy.",
                "Adjust lighting to make skin tones look natural.",
                "Choose interiors that emphasize hygiene and safety."
            ]
        }
        
        # Default recommendations
        default_recommendations = [
            "Identify and reflect your target customers' needs accurately.",
            "Maintain brand consistency across all touchpoints.",
            "Develop a long-term plan for continuous brand growth.",
            "Clearly define your differentiation points against competitors."
        ]
        
        recommendations = industry_recommendations.get(industry, default_recommendations)
        
        # Add recommendations based on analysis results
        if analysis_result:
            score = analysis_result.get('overall_score', 0)
            if score < 60:
                recommendations.append("Reevaluate your market positioning through detailed analysis.")
            elif score > 80:
                recommendations.append("Leverage strong brand potential with active marketing strategies.")
        
        return recommendations[:5]  # Maximum 5 recommendations
