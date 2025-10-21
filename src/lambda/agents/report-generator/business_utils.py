"""
Business logic utilities for branding
Handles color palettes, budget guides, and strategic recommendations
"""
from typing import Dict, Any, List
import logging


class BusinessUtils:
    """Business logic utilities for branding recommendations"""

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def generate_color_palette(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an industry-specific color palette

        Args:
            business_info: Business information including industry

        Returns:
            Dict with primary, secondary, accent, and text colors
        """
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

        palette = color_palettes.get(industry, default_palette)
        self.logger.info(f"Generated color palette for industry: {industry}")
        return palette

    def generate_budget_guide(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate estimated budgets based on business size and industry

        Args:
            business_info: Business information including size and industry

        Returns:
            Dict with budget ranges for signboard, interior, branding, marketing, and total
        """
        size = business_info.get('size', 'small')
        industry = business_info.get('industry', '')

        # Size multipliers
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
            },
            'beauty': {
                'signboard': {'min': 900000, 'recommended': 1600000, 'max': 3200000},
                'interior': {'min': 6000000, 'recommended': 15000000, 'max': 30000000},
                'branding': {'min': 700000, 'recommended': 1500000, 'max': 3000000},
                'marketing': {'min': 400000, 'recommended': 900000, 'max': 1800000}
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

        self.logger.info(f"Generated budget guide for {industry} ({size}): {total_recommended:,}₩ recommended")
        return budget_guide

    def generate_recommendations(
        self,
        business_info: Dict[str, Any],
        analysis_result: Dict[str, Any],
        bedrock_client=None
    ) -> List[str]:
        """
        Generate AI-powered business recommendations using Bedrock Claude

        Args:
            business_info: Business information including industry and region
            analysis_result: Analysis results with scores
            bedrock_client: Optional Bedrock client for AI generation

        Returns:
            List of recommendation strings (max 5)
        """
        # Try AI-powered recommendations first
        if bedrock_client:
            try:
                ai_recommendations = self._generate_ai_recommendations(
                    business_info, 
                    analysis_result, 
                    bedrock_client
                )
                if ai_recommendations:
                    self.logger.info(f"Generated {len(ai_recommendations)} AI-powered recommendations")
                    return ai_recommendations
            except Exception as e:
                self.logger.warning(f"AI recommendation generation failed, using fallback: {str(e)}")
        
        # Fallback to rule-based recommendations
        return self._generate_fallback_recommendations(business_info, analysis_result)
    
    def _generate_ai_recommendations(
        self,
        business_info: Dict[str, Any],
        analysis_result: Dict[str, Any],
        bedrock_client
    ) -> List[str]:
        """Generate recommendations using Bedrock Claude"""
        industry = business_info.get('industry', 'general business')
        region = business_info.get('region', 'unknown')
        size = business_info.get('size', 'small')
        score = analysis_result.get('overall_score', 0) if analysis_result else 0
        
        prompt = f"""You are a business branding consultant. Based on the following business information, provide 5 specific, actionable strategic recommendations.

Business Information:
- Industry: {industry}
- Region: {region}
- Size: {size}
- Market Analysis Score: {score}/100

Analysis Insights:
{analysis_result.get('summary', 'No analysis available') if analysis_result else 'No analysis available'}

Provide exactly 5 strategic recommendations that are:
1. Specific and actionable
2. Relevant to the industry and region
3. Based on the market analysis score
4. Focused on branding, marketing, and business growth
5. Concise (one sentence each)

Format: Return only the 5 recommendations as a numbered list, one per line.
Example:
1. Focus on creating an Instagram-worthy interior design to attract younger demographics
2. Implement a loyalty program to increase customer retention by 30%
3. Partner with local influencers to build brand awareness in the region
4. Develop a unique brand story that differentiates from competitors
5. Invest in professional photography for all marketing materials

Your 5 recommendations:"""

        try:
            response = bedrock_client.invoke_model(
                modelId='us.anthropic.claude-sonnet-4-20250514-v1:0',
                body={
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "temperature": 0.7,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            )
            
            # Parse response
            response_text = response.get('content', [{}])[0].get('text', '')
            
            # Extract recommendations (numbered list)
            recommendations = []
            for line in response_text.strip().split('\n'):
                line = line.strip()
                # Remove numbering (1., 2., etc.)
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Remove leading number/bullet and clean up
                    cleaned = line.lstrip('0123456789.-•) ').strip()
                    if cleaned:
                        recommendations.append(cleaned)
            
            # Return exactly 5 recommendations
            return recommendations[:5] if len(recommendations) >= 5 else None
            
        except Exception as e:
            self.logger.error(f"Bedrock recommendation generation failed: {str(e)}")
            return None
    
    def _generate_fallback_recommendations(
        self,
        business_info: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> List[str]:
        """Fallback rule-based recommendations"""
        industry = business_info.get('industry', '').lower()
        region = business_info.get('region', '')

        # Industry-specific recommendations
        industry_recommendations = {
            'cafe': [
                "Focus on creating a warm and inviting atmosphere",
                "Consider adding SNS-friendly photo zones",
                "Plan seasonal menu-based interior changes",
                "Maximize natural light in your seating layout"
            ],
            'restaurant': [
                "Design lighting to enhance the visual appeal of food",
                "Plan efficient table layouts and traffic flow",
                "Integrate your brand story into the overall space design",
                "Ensure proper sound insulation between kitchen and dining area"
            ],
            'beauty': [
                "Build a luxurious and hygienic atmosphere",
                "Design private and comfortable treatment areas",
                "Use lighting that flatters natural skin tones",
                "Emphasize cleanliness and safety in all interiors"
            ]
        }

        # Default recommendations
        default_recommendations = [
            "Identify and meet the needs of your target audience accurately",
            "Maintain brand consistency across all customer touchpoints",
            "Develop a long-term strategy for continuous brand growth",
            "Define clear differentiating factors from competitors"
        ]

        recommendations = industry_recommendations.get(industry, default_recommendations).copy()

        # Add analysis-based recommendations
        if analysis_result:
            score = analysis_result.get('overall_score', 0)
            if score < 60:
                recommendations.append("Reevaluate market positioning and brand strategy")
            elif score > 80:
                recommendations.append("Leverage strong positioning with bold marketing campaigns")

        # Add region-specific recommendations
        if 'gangnam' in region.lower():
            recommendations.append("Highlight luxury and modern sophistication to fit the Gangnam image")
        elif 'hongdae' in region.lower():
            recommendations.append("Focus on youthful and creative design concepts for Hongdae customers")

        final_recommendations = recommendations[:5]  # Limit to 5
        self.logger.info(f"Generated {len(final_recommendations)} fallback recommendations for {industry}")
        return final_recommendations
