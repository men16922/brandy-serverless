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

    def generate_budget_guide(self, business_info: Dict[str, Any], bedrock_client=None) -> Dict[str, Any]:
        """
        Generate estimated budgets based on business size, industry, and region
        Uses Bedrock Claude to calculate budgets in local currency

        Args:
            business_info: Business information including size, industry, region, and country
            bedrock_client: Optional Bedrock client for AI-powered budget calculation

        Returns:
            Dict with budget ranges for signboard, interior, branding, marketing, and total
            Includes currency symbol and region-specific pricing
        """
        size = business_info.get('size', 'small')
        industry = business_info.get('industry', '')
        region = business_info.get('region', 'Seoul').lower()
        country = business_info.get('country', 'South Korea')
        
        # Try AI-powered budget calculation first
        if bedrock_client:
            try:
                ai_budget = self._generate_ai_budget_guide(
                    business_info,
                    bedrock_client
                )
                if ai_budget:
                    self.logger.info(f"Generated AI-powered budget guide for {region}, {country}")
                    return ai_budget
            except Exception as e:
                self.logger.warning(f"AI budget generation failed, using fallback: {str(e)}")
        
        # Fallback to rule-based calculation
        return self._generate_fallback_budget_guide(business_info)
    
    def _generate_fallback_budget_guide(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based budget calculation"""
        size = business_info.get('size', 'small')
        industry = business_info.get('industry', '')
        region = business_info.get('region', 'Seoul')
        country = business_info.get('country', 'South Korea')
        
        # Extract city from "City, Country" format if needed
        if ',' in region:
            city = region.split(',')[0].strip().lower()
        else:
            city = region.lower()

        # Size multipliers
        multipliers = {'small': 1.0, 'medium': 1.8, 'large': 3.0}
        multiplier = multipliers.get(size, 1.0)

        # Region/Country configuration (base: South Korea KRW)
        region_config = {
            # South Korea
            'seoul': {'currency': '₩', 'rate': 1.0, 'country': 'South Korea'},
            'busan': {'currency': '₩', 'rate': 0.85, 'country': 'South Korea'},
            'incheon': {'currency': '₩', 'rate': 0.9, 'country': 'South Korea'},
            'daegu': {'currency': '₩', 'rate': 0.8, 'country': 'South Korea'},
            'gwangju': {'currency': '₩', 'rate': 0.75, 'country': 'South Korea'},
            'daejeon': {'currency': '₩', 'rate': 0.8, 'country': 'South Korea'},
            'ulsan': {'currency': '₩', 'rate': 0.85, 'country': 'South Korea'},
            'jeju': {'currency': '₩', 'rate': 0.95, 'country': 'South Korea'},
            
            # USA
            'new york': {'currency': '$', 'rate': 0.00075, 'country': 'USA'},
            'los angeles': {'currency': '$', 'rate': 0.00070, 'country': 'USA'},
            'chicago': {'currency': '$', 'rate': 0.00065, 'country': 'USA'},
            'san francisco': {'currency': '$', 'rate': 0.00080, 'country': 'USA'},
            
            # Japan
            'tokyo': {'currency': '¥', 'rate': 0.11, 'country': 'Japan'},
            'osaka': {'currency': '¥', 'rate': 0.10, 'country': 'Japan'},
            'kyoto': {'currency': '¥', 'rate': 0.09, 'country': 'Japan'},
            
            # China
            'beijing': {'currency': '¥', 'rate': 0.0052, 'country': 'China'},
            'shanghai': {'currency': '¥', 'rate': 0.0055, 'country': 'China'},
            'guangzhou': {'currency': '¥', 'rate': 0.0050, 'country': 'China'},
            
            # Europe
            'london': {'currency': '£', 'rate': 0.00060, 'country': 'UK'},
            'paris': {'currency': '€', 'rate': 0.00070, 'country': 'France'},
            'berlin': {'currency': '€', 'rate': 0.00065, 'country': 'Germany'},
            
            # Southeast Asia
            'singapore': {'currency': 'S$', 'rate': 0.0010, 'country': 'Singapore'},
            'bangkok': {'currency': '฿', 'rate': 0.025, 'country': 'Thailand'},
            'hanoi': {'currency': '₫', 'rate': 18.5, 'country': 'Vietnam'},
            'manila': {'currency': '₱', 'rate': 0.042, 'country': 'Philippines'},
            
            # India
            'mumbai': {'currency': '₹', 'rate': 0.063, 'country': 'India'},
            'delhi': {'currency': '₹', 'rate': 0.062, 'country': 'India'},
            'bangalore': {'currency': '₹', 'rate': 0.065, 'country': 'India'},
            'kolkata': {'currency': '₹', 'rate': 0.058, 'country': 'India'},
            'chennai': {'currency': '₹', 'rate': 0.060, 'country': 'India'},
            'hyderabad': {'currency': '₹', 'rate': 0.061, 'country': 'India'},
            'pune': {'currency': '₹', 'rate': 0.064, 'country': 'India'},
        }

        # Get region configuration (try city first, then fallback to country-based defaults)
        config = region_config.get(city, None)
        
        # If city not found, try to match by country
        if not config:
            country_defaults = {
                'France': {'currency': '€', 'rate': 0.00070, 'country': 'France'},
                'United States': {'currency': '$', 'rate': 0.00075, 'country': 'United States'},
                'UK': {'currency': '£', 'rate': 0.00060, 'country': 'UK'},
                'Japan': {'currency': '¥', 'rate': 0.11, 'country': 'Japan'},
                'China': {'currency': '¥', 'rate': 0.0052, 'country': 'China'},
                'Germany': {'currency': '€', 'rate': 0.00065, 'country': 'Germany'},
                'Singapore': {'currency': 'S$', 'rate': 0.0010, 'country': 'Singapore'},
                'Thailand': {'currency': '฿', 'rate': 0.025, 'country': 'Thailand'},
                'Vietnam': {'currency': '₫', 'rate': 18.5, 'country': 'Vietnam'},
                'Philippines': {'currency': '₱', 'rate': 0.042, 'country': 'Philippines'},
                'India': {'currency': '₹', 'rate': 0.063, 'country': 'India'},
                'South Korea': {'currency': '₩', 'rate': 1.0, 'country': 'South Korea'},
            }
            config = country_defaults.get(country, region_config['seoul'])
        
        currency = config['currency']
        rate = config['rate']
        country = config['country']

        # Industry-specific base costs (in KRW)
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

        # Apply size multiplier and currency conversion
        budget_guide = {}
        for category, costs in base_costs.items():
            budget_guide[category] = {
                'min': int(costs['min'] * multiplier * rate),
                'recommended': int(costs['recommended'] * multiplier * rate),
                'max': int(costs['max'] * multiplier * rate)
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

        # Add currency and region info
        budget_guide['currency'] = currency
        budget_guide['region'] = region.title()
        budget_guide['country'] = country

        self.logger.info(f"Generated budget guide for {industry} ({size}) in {region}: {currency}{total_recommended:,} recommended")
        return budget_guide
    
    def _generate_ai_budget_guide(self, business_info: Dict[str, Any], bedrock_client) -> Dict[str, Any]:
        """
        Generate budget guide using Bedrock Claude with local currency calculation
        
        Args:
            business_info: Business information
            bedrock_client: Bedrock client instance
            
        Returns:
            Budget guide dict with local currency amounts
        """
        size = business_info.get('size', 'small')
        industry = business_info.get('industry', 'restaurant')
        region = business_info.get('region', 'Seoul')
        country = business_info.get('country', 'South Korea')
        description = business_info.get('description', '')
        
        # Get currency for the country
        currency_map = {
            'United States': '$',
            'South Korea': '₩',
            'India': '₹',
            'France': '€',
            'UK': '£',
            'Japan': '¥',
            'China': '¥',
            'Singapore': 'S$',
            'Thailand': '฿',
            'Vietnam': '₫',
            'Philippines': '₱',
        }
        currency = currency_map.get(country, '$')
        
        system_prompt = """You are a business budget consultant with expertise in local market pricing across different countries and cities.

Your task is to provide realistic budget estimates in the LOCAL CURRENCY for the given location.

IMPORTANT RULES:
1. Calculate budgets in the LOCAL CURRENCY of the country/city (not converted from another currency)
2. Consider local market conditions, labor costs, and material prices
3. Account for city-specific cost variations (e.g., New York is more expensive than other US cities)
4. Provide min, recommended, and max ranges for each category
5. All amounts must be realistic for the local market

Return ONLY a valid JSON object with this exact structure:
{
    "signboard": {"min": 1000, "recommended": 2000, "max": 4000},
    "interior": {"min": 10000, "recommended": 25000, "max": 50000},
    "branding": {"min": 800, "recommended": 1800, "max": 3500},
    "marketing": {"min": 500, "recommended": 1200, "max": 2500}
}

Do not include currency symbols in the numbers. Only return the JSON object."""

        prompt = f"""Calculate realistic budget estimates for a {size} {industry} business in {region}, {country}.

Business Details:
- Industry: {industry}
- Size: {size}
- Location: {region}, {country}
- Currency: {currency}
{f"- Description: {description}" if description else ""}

Provide budget ranges (min, recommended, max) in LOCAL {currency} for:
1. Signboard (exterior signage, lighting, installation)
2. Interior (furniture, fixtures, decoration, renovation)
3. Branding (logo design, business cards, packaging, brand guidelines)
4. Marketing (initial marketing campaigns, social media, advertising)

Consider:
- Local labor and material costs in {region}, {country}
- {size.capitalize()} business scale
- {industry.capitalize()} industry standards
- City-specific cost variations

Return the budget estimates as a JSON object."""

        try:
            response = bedrock_client.invoke_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=1024,
                temperature=0.3  # Lower temperature for more consistent numbers
            )
            
            # Parse response
            response_text = response.get('content', [{}])[0].get('text', '')
            
            # Extract JSON from response
            import json
            import re
            
            # Find JSON object in response
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                budget_data = json.loads(json_match.group())
                
                # Validate structure
                required_categories = ['signboard', 'interior', 'branding', 'marketing']
                if all(cat in budget_data for cat in required_categories):
                    # Calculate totals
                    total_min = sum(budget_data[cat]['min'] for cat in required_categories)
                    total_recommended = sum(budget_data[cat]['recommended'] for cat in required_categories)
                    total_max = sum(budget_data[cat]['max'] for cat in required_categories)
                    
                    budget_data['total'] = {
                        'min': total_min,
                        'recommended': total_recommended,
                        'max': total_max
                    }
                    
                    # Add metadata
                    budget_data['currency'] = currency
                    budget_data['region'] = region.title()
                    budget_data['country'] = country
                    
                    self.logger.info(
                        f"AI-generated budget for {region}, {country}: {currency}{total_recommended:,}",
                        extra={
                            "agent": "report_generator",
                            "tool": "budget.generate",
                            "provider": "bedrock_claude",
                            "currency": currency,
                            "country": country,
                            "region": region
                        }
                    )
                    
                    return budget_data
            
            self.logger.warning("Failed to parse AI budget response, using fallback")
            return None
            
        except Exception as e:
            self.logger.error(f"AI budget generation failed: {str(e)}")
            return None

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
            response = bedrock_client.invoke_claude(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7
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
