"""
Product Insight Agent - Business Analysis Implementation
Provides comprehensive business analysis based on industry, region, and size
"""

import json
import sys
import os
import time
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

# Add shared modules to path - Lambda Layer structure
sys.path.insert(0, '/opt/python/python')

# Product Insight specific models (always defined)
class AnalysisResult:
    def __init__(self, summary: str, score: float, insights: List[str], 
                 market_trends: List[str], recommendations: List[str]):
        self.summary = summary
        self.score = score
        self.insights = insights
        self.market_trends = market_trends
        self.recommendations = recommendations
        self.generated_at = datetime.utcnow().isoformat()
    
    def to_dict(self):
        return {
            'summary': self.summary,
            'score': self.score,
            'insights': self.insights,
            'market_trends': self.market_trends,
            'recommendations': self.recommendations,
            'generated_at': self.generated_at
        }

class BusinessInfo:
    def __init__(self, industry: str, region: str, size: str, **kwargs):
        self.industry = industry
        self.region = region
        self.size = size
    
    def validate(self):
        return bool(self.industry and self.region and self.size)

try:
    from shared.base_agent import BaseAgent
    from shared.models import AgentType
    from shared.knowledge_base import get_knowledge_base
except ImportError:
    # For testing purposes, create mock implementations
    from enum import Enum
    
    class AgentType(Enum):
        PRODUCT_INSIGHT = "product_insight"
    
    class BaseAgent:
        def __init__(self, agent_type):
            self.agent_type = agent_type
            self.agent_name = agent_type.value
            self.logger = self._create_mock_logger()
            # Mock Bedrock client and Reasoning Engine (not available in test environment)
            self.bedrock_client = None
            self.reasoning_engine = None
        
        def _create_mock_logger(self):
            import logging
            logger = logging.getLogger(self.agent_name)
            logger.setLevel(logging.INFO)
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                logger.addHandler(handler)
            return logger
        
        def start_execution(self, session_id: str, tool: str):
            self.current_session_id = session_id
            self.current_tool = tool
            self.execution_start_time = time.time()
        
        def end_execution(self, status: str = "success", error_message: str = None, result: Any = None):
            if hasattr(self, 'execution_start_time'):
                latency_ms = int((time.time() - self.execution_start_time) * 1000)
                return latency_ms
            return 0
        
        # Removed mock update_session_data - using BaseAgent's implementation
        
        def create_lambda_response(self, status_code: int, body: Any, headers=None):
            return {
                'statusCode': status_code,
                'headers': headers or {'Content-Type': 'application/json'},
                'body': json.dumps(body, ensure_ascii=False)
            }
        
        def handle_error(self, error: Exception, context: str = ""):
            return {
                'error': True,
                'message': str(error),
                'agent': self.agent_name,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        def lambda_handler(self, event: Dict[str, Any], context: Any):
            return self.execute(event, context)
    
    def get_knowledge_base():
        class MockKnowledgeBase:
            def search(self, query: str, top_k: int = 5):
                return []
        return MockKnowledgeBase()


class ProductInsightAgent(BaseAgent):
    """Product Insight Agent for business analysis"""
    
    def __init__(self):
        super().__init__(AgentType.PRODUCT_INSIGHT)
        self.knowledge_base = get_knowledge_base()
        
        # Load analysis data from JSON files
        self.industry_data = self._load_industry_analysis_data()
        self.region_data = self._load_region_analysis_data()
        self.size_data = self._load_size_analysis_data()
    
    def _load_json_data(self, filename: str, fallback_method: callable) -> Dict[str, Any]:
        """
        Load data from JSON file with fallback to hardcoded data.
        
        Args:
            filename: JSON filename (e.g., 'industry_data.json')
            fallback_method: Method to call if JSON loading fails
        
        Returns:
            Data dictionary
        """
        try:
            # Try to load from JSON file
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
            file_path = os.path.join(data_dir, filename)
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.logger.info(f"Loaded {filename} from JSON file")
                    return data
            else:
                self.logger.warning(f"{filename} not found, using fallback data")
                return fallback_method()
                
        except Exception as e:
            self.logger.error(f"Failed to load {filename}: {str(e)}, using fallback data")
            return fallback_method()
    
    def _load_industry_analysis_data(self) -> Dict[str, Dict[str, Any]]:
        """Load 16 industry-specific analysis data from JSON file"""
        return self._load_json_data('industry_data.json', self._get_fallback_industry_data)
    
    def _get_fallback_industry_data(self) -> Dict[str, Dict[str, Any]]:
        """Fallback industry data (used if JSON file not available)"""
        return {
            "restaurant": {
                "characteristics": [
                    "High customer turnover and community-anchored business",
                    "Food ingredient costs and labor are the main operating expenses",
                    "Sensitive to seasonality and trends"
                ],
                "success_factors": [
                    "Consistency in taste and service quality",
                    "Efficient inventory control and cost reduction",
                    "Strategies to increase repeat visits"
                ],
                "market_trends": [
                    "Growing demand for healthy and vegan menus",
                    "Rising dependency on delivery platforms",
                    "Emphasis on personalized customer experience"
                ],
                "risk_factors": [
                    "High failure rate of new restaurants (70% within 3 years)",
                    "Volatility in ingredient prices",
                    "Vulnerability to external shocks such as pandemics"
                ],
                "base_score": 75,
                "growth_potential": "MEDIUM",
                "competition_level": "HIGH"
            },
            "retail": {
                "characteristics": [
                    "Merchandising and customer touchpoints are key",
                    "Inventory management and sales forecasting matter",
                    "Need to integrate online and offline channels"
                ],
                "success_factors": [
                    "Product curation and display strategy",
                    "Customer-data-driven personalization",
                    "Efficient supply chain management"
                ],
                "market_trends": [
                    "Expansion of O2O (Online to Offline) services",
                    "Personalized product recommendation systems",
                    "Rising interest in eco-friendly products"
                ],
                "risk_factors": [
                    "Intensifying competition with online malls",
                    "Upward pressure on rent",
                    "Need to adapt to changing consumption patterns"
                ],
                "base_score": 70,
                "growth_potential": "MEDIUM",
                "competition_level": "HIGH"
            },
            "service": {
                "characteristics": [
                    "Intangible service delivery makes standardization difficult",
                    "Customer satisfaction directly impacts revenue",
                    "Expertise and trust are core competitiveness"
                ],
                "success_factors": [
                    "Standardization and consistency of service quality",
                    "Building a customer relationship management system",
                    "Securing and training skilled professionals"
                ],
                "market_trends": [
                    "Service delivery via digital platforms",
                    "Expansion of subscription-based models",
                    "Adoption of AI and automation"
                ],
                "risk_factors": [
                    "Reputation risk from inconsistent service quality",
                    "Difficulty securing experienced personnel",
                    "Demand drops with economic cycles"
                ],
                "base_score": 78,
                "growth_potential": "HIGH",
                "competition_level": "MEDIUM"
            },
            "healthcare": {
                "characteristics": [
                    "High level of expertise and qualifications required",
                    "Strict regulation with safety as the top priority",
                    "Continuous education and tech updates are essential"
                ],
                "success_factors": [
                    "Expertise and experience of medical staff",
                    "Modern medical equipment and facilities",
                    "Patient-centered services"
                ],
                "market_trends": [
                    "Adoption of digital healthcare technologies",
                    "Shift toward preventive care",
                    "Personalized treatment services"
                ],
                "risk_factors": [
                    "Legal liability from medical incidents",
                    "High initial capital expenditure",
                    "Imbalance in supply of medical personnel"
                ],
                "base_score": 85,
                "growth_potential": "HIGH",
                "competition_level": "LOW"
            },
            "education": {
                "characteristics": [
                    "Performance measurement over a long horizon",
                    "Need to consider individual learner characteristics",
                    "Content and methodology are critical"
                ],
                "success_factors": [
                    "Differentiated educational programs",
                    "Securing excellent teaching staff",
                    "Systems to track learning outcomes"
                ],
                "market_trends": [
                    "Proliferation of online education platforms",
                    "Personalized learning experiences",
                    "Practical, work-oriented curricula"
                ],
                "risk_factors": [
                    "Declining school-age population",
                    "Competition from online learning",
                    "Impact from changes in education policy"
                ],
                "base_score": 72,
                "growth_potential": "MEDIUM",
                "competition_level": "MEDIUM"
            },
            "technology": {
                "characteristics": [
                    "Rapid technological change requiring constant innovation",
                    "High growth potential and scalability",
                    "Skilled talent and R&D investment are crucial"
                ],
                "success_factors": [
                    "Technological innovation and IP/patents",
                    "Securing top engineering talent",
                    "Timing of market entry"
                ],
                "market_trends": [
                    "Widespread adoption of AI and ML",
                    "Migration to cloud services",
                    "Increased importance of cybersecurity"
                ],
                "risk_factors": [
                    "Obsolescence risk due to rapid tech shifts",
                    "High upfront development costs",
                    "Intense competition for talent"
                ],
                "base_score": 82,
                "growth_potential": "HIGH",
                "competition_level": "HIGH"
            },
            "manufacturing": {
                "characteristics": [
                    "Operational efficiency and quality management are key",
                    "High initial capex for facilities",
                    "Supply chain management and raw material sourcing matter"
                ],
                "success_factors": [
                    "Optimized production processes",
                    "Robust quality management systems",
                    "Stable supply chains"
                ],
                "market_trends": [
                    "Smart factories and automation",
                    "Eco-friendly production processes",
                    "Mass customization"
                ],
                "risk_factors": [
                    "Volatility in raw material prices",
                    "Stronger environmental regulations",
                    "Labor shortages and aging workforce"
                ],
                "base_score": 76,
                "growth_potential": "MEDIUM",
                "competition_level": "MEDIUM"
            },
            "construction": {
                "characteristics": [
                    "Project-based, one-off engagements",
                    "Safety management and quality assurance are critical",
                    "Sensitive to seasons and macro cycles"
                ],
                "success_factors": [
                    "Project management capability",
                    "Systems to prevent safety incidents",
                    "Network of reliable subcontractors"
                ],
                "market_trends": [
                    "Green building technologies",
                    "Modular and prefab construction",
                    "BIM and digital design"
                ],
                "risk_factors": [
                    "Risk of safety incidents",
                    "Cyclical construction market",
                    "Labor market instability"
                ],
                "base_score": 68,
                "growth_potential": "LOW",
                "competition_level": "HIGH"
            },
            "finance": {
                "characteristics": [
                    "Requires high trust and security",
                    "Complex regulations and compliance",
                    "Acceleration of digital transformation"
                ],
                "success_factors": [
                    "Robust risk management",
                    "Building customer trust",
                    "Digital service innovation"
                ],
                "market_trends": [
                    "Fintech and digital banking",
                    "Blockchain and cryptocurrencies",
                    "Personalized financial services"
                ],
                "risk_factors": [
                    "Regulatory changes",
                    "Cybersecurity threats",
                    "Competition from fintechs"
                ],
                "base_score": 80,
                "growth_potential": "MEDIUM",
                "competition_level": "HIGH"
            },
            "beauty": {
                "characteristics": [
                    "Highly sensitive to trends and personal tastes",
                    "Brand image and marketing are crucial",
                    "Customer experience and service quality are key"
                ],
                "success_factors": [
                    "Trend responsiveness and product planning",
                    "Providing personalized services",
                    "Brand differentiation strategy"
                ],
                "market_trends": [
                    "Global growth of K-beauty",
                    "Personalized cosmetics",
                    "Eco-friendly beauty products"
                ],
                "risk_factors": [
                    "Fast-changing trends",
                    "Competition with online channels",
                    "Rising raw material costs"
                ],
                "base_score": 74,
                "growth_potential": "HIGH",
                "competition_level": "HIGH"
            },
            "fitness": {
                "characteristics": [
                    "Riding the health and wellbeing trend",
                    "Importance of personalized services",
                    "Requires investment in facilities and equipment"
                ],
                "success_factors": [
                    "Securing professional trainers",
                    "Differentiated programs",
                    "Membership management systems"
                ],
                "market_trends": [
                    "Home training and online fitness",
                    "Integration with wearables",
                    "Functional training and rehabilitation"
                ],
                "risk_factors": [
                    "Impacts from infectious diseases",
                    "Competition with online services",
                    "Managing member churn"
                ],
                "base_score": 77,
                "growth_potential": "HIGH",
                "competition_level": "MEDIUM"
            },
            "entertainment": {
                "characteristics": [
                    "Creativity and content are core",
                    "Highly sensitive to trends and mass taste",
                    "High returns and high risks coexist"
                ],
                "success_factors": [
                    "Original content planning",
                    "Target audience analysis",
                    "Marketing and promotion strategies"
                ],
                "market_trends": [
                    "Expansion of OTT platforms",
                    "Metaverse and VR content",
                    "Independent creators and livestreaming"
                ],
                "risk_factors": [
                    "Uncertainty of content success",
                    "Copyright and legal issues",
                    "Platform dependency"
                ],
                "base_score": 71,
                "growth_potential": "HIGH",
                "competition_level": "HIGH"
            },
            "automotive": {
                "characteristics": [
                    "Technology-intensive industry",
                    "High initial investments and long payback",
                    "Safety and quality take precedence"
                ],
                "success_factors": [
                    "Technological innovation and R&D",
                    "Quality management systems",
                    "Customer service networks"
                ],
                "market_trends": [
                    "EVs and autonomous driving",
                    "Mobility-as-a-service",
                    "Eco-friendly technologies"
                ],
                "risk_factors": [
                    "Pace of technological change",
                    "High entry barriers",
                    "Strengthening environmental regulation"
                ],
                "base_score": 79,
                "growth_potential": "MEDIUM",
                "competition_level": "HIGH"
            },
            "agriculture": {
                "characteristics": [
                    "High dependence on seasons and climate",
                    "Traditional methods coexist with innovation",
                    "Food safety and quality are important"
                ],
                "success_factors": [
                    "Productivity-improving technologies",
                    "Quality control and branding",
                    "Diversified distribution channels"
                ],
                "market_trends": [
                    "Smart farming and precision agriculture",
                    "Eco-friendly organic farming",
                    "Direct sales and online channels"
                ],
                "risk_factors": [
                    "Impact of climate change",
                    "Fluctuating crop prices",
                    "Aging farmers and labor shortages"
                ],
                "base_score": 65,
                "growth_potential": "MEDIUM",
                "competition_level": "LOW"
            },
            "logistics": {
                "characteristics": [
                    "Efficiency and on-time delivery are critical",
                    "Networks and infrastructure matter",
                    "Tech innovation is a competitiveness lever"
                ],
                "success_factors": [
                    "Optimized delivery networks",
                    "IT systems and automation",
                    "High-quality customer service"
                ],
                "market_trends": [
                    "Growth in e-commerce deliveries",
                    "Drones and autonomous delivery",
                    "Green logistics"
                ],
                "risk_factors": [
                    "Fuel price volatility and transport costs",
                    "Labor shortages",
                    "Traffic congestion and infrastructure constraints"
                ],
                "base_score": 73,
                "growth_potential": "HIGH",
                "competition_level": "MEDIUM"
            },
            "other": {
                "characteristics": [
                    "General characteristics spanning many industries",
                    "Volatility depending on market conditions",
                    "Need for differentiation strategy"
                ],
                "success_factors": [
                    "Market analysis and positioning",
                    "Understanding customer needs",
                    "Operational efficiency improvements"
                ],
                "market_trends": [
                    "Digital transformation",
                    "Focus on customer experience",
                    "Sustainability"
                ],
                "risk_factors": [
                    "Intensifying competition",
                    "Macroeconomic fluctuations",
                    "Regulatory changes"
                ],
                "base_score": 70,
                "growth_potential": "MEDIUM",
                "competition_level": "MEDIUM"
            }
        }
    
    def _load_region_analysis_data(self) -> Dict[str, Dict[str, Any]]:
        """Load region-specific market environment analysis data from JSON file"""
        return self._load_json_data('region_data.json', self._get_fallback_region_data)
    
    def _get_fallback_region_data(self) -> Dict[str, Dict[str, Any]]:
        """Fallback region data (used if JSON file not available)"""
        return {
            "seoul": {
                "market_size": "LARGE",
                "competition_level": "VERY_HIGH",
                "consumer_power": "HIGH",
                "rent_cost": "VERY_HIGH",
                "characteristics": [
                    "The largest consumer market in Korea with high purchasing power",
                    "Fierce competition and high rents",
                    "Trend-leading region that requires innovation"
                ],
                "advantages": [
                    "Large customer base and high accessibility",
                    "Diverse business opportunities",
                    "Excellent infrastructure and transportation networks"
                ],
                "challenges": [
                    "High operating costs and rent",
                    "Highly competitive environment",
                    "Need to respond quickly to fast-changing trends"
                ],
                "score_modifier": 10
            },
            "busan": {
                "market_size": "LARGE",
                "competition_level": "HIGH",
                "consumer_power": "MEDIUM_HIGH",
                "rent_cost": "MEDIUM",
                "characteristics": [
                    "Second-largest city with a stable market size",
                    "Port-city characteristics and developed tourism",
                    "Lower entry costs compared to Seoul"
                ],
                "advantages": [
                    "Reasonable rents and operating costs",
                    "Demand fueled by tourist inflows",
                    "Potential for differentiation using regional traits"
                ],
                "challenges": [
                    "Smaller market than Seoul",
                    "Dependence on the local economy",
                    "Outflow of younger population"
                ],
                "score_modifier": 5
            },
            "daegu": {
                "market_size": "MEDIUM",
                "competition_level": "MEDIUM",
                "consumer_power": "MEDIUM",
                "rent_cost": "LOW_MEDIUM",
                "characteristics": [
                    "Traditional commercial city centered on the textile industry",
                    "Conservative consumption and a stable market",
                    "Growth in medical industry and educational institutions"
                ],
                "advantages": [
                    "Stable regional economy",
                    "Reasonable operating costs",
                    "High customer loyalty"
                ],
                "challenges": [
                    "Conservative spending patterns",
                    "Slow adoption of new trends",
                    "Declining young population"
                ],
                "score_modifier": 0
            },
            "incheon": {
                "market_size": "MEDIUM_LARGE",
                "competition_level": "MEDIUM_HIGH",
                "consumer_power": "MEDIUM_HIGH",
                "rent_cost": "MEDIUM_HIGH",
                "characteristics": [
                    "Logistics city centered on Incheon Airport and Port",
                    "Bedroom community role due to proximity to Seoul",
                    "Population growth driven by new city developments"
                ],
                "advantages": [
                    "Continuous population inflow",
                    "Hub for logistics and transportation",
                    "Opportunities from new commercial district development"
                ],
                "challenges": [
                    "Consumption patterns dependent on Seoul",
                    "Dispersed commercial districts make customer attraction difficult",
                    "Burden of transportation costs"
                ],
                "score_modifier": 3
            },
            "gwangju": {
                "market_size": "MEDIUM",
                "competition_level": "MEDIUM",
                "consumer_power": "MEDIUM",
                "rent_cost": "LOW_MEDIUM",
                "characteristics": [
                    "Cultural and artistic hub of the Honam region",
                    "University areas with a young consumer base",
                    "Coexistence of traditional markets and modern commercial zones"
                ],
                "advantages": [
                    "Ability to leverage culture and arts content",
                    "Solid base of university students",
                    "Opportunities linked to regional specialties"
                ],
                "challenges": [
                    "Relatively small market size",
                    "Limits to regional economic growth",
                    "Lower purchasing power vs. the Seoul metro area"
                ],
                "score_modifier": -2
            },
            "daejeon": {
                "market_size": "MEDIUM",
                "competition_level": "MEDIUM",
                "consumer_power": "MEDIUM_HIGH",
                "rent_cost": "MEDIUM",
                "characteristics": [
                    "Science-and-technology city with highly educated residents",
                    "Dense concentration of research institutes and universities",
                    "High openness to innovation and technology"
                ],
                "advantages": [
                    "High-income, highly educated customer base",
                    " receptive to technological innovation",
                    "Stable demand due to many government agencies"
                ],
                "challenges": [
                    "Specialized customer base limits market size",
                    "Conservative bureaucratic culture",
                    "Weekend population declines"
                ],
                "score_modifier": 2
            },
            "ulsan": {
                "market_size": "MEDIUM",
                "competition_level": "LOW_MEDIUM",
                "consumer_power": "HIGH",
                "rent_cost": "MEDIUM",
                "characteristics": [
                    "Industrial city centered on heavy chemicals",
                    "High income levels and purchasing power",
                    "Male-dominated consumption pattern"
                ],
                "advantages": [
                    "High average income and purchasing power",
                    "Relatively low competition",
                    "Market targeting industrial complex workers"
                ],
                "challenges": [
                    "Homogeneous customer composition",
                    "Sensitive to macroeconomic fluctuations",
                    "Lack of cultural content"
                ],
                "score_modifier": 1
            },
            "gyeonggi": {
                "market_size": "VERY_LARGE",
                "competition_level": "HIGH",
                "consumer_power": "HIGH",
                "rent_cost": "HIGH",
                "characteristics": [
                    "Largest population in the metro area with diverse new towns",
                    "Strong accessibility to Seoul with independent commercial districts",
                    "Consumption market centered on young families"
                ],
                "advantages": [
                    "Large and continuously inflowing population",
                    "Diverse age and income distributions",
                    "Growth potential from ongoing new town developments"
                ],
                "challenges": [
                    "Significant regional variance within the province",
                    "Competition with Seoul commercial districts",
                    "Differences in transportation accessibility"
                ],
                "score_modifier": 8
            },
            "gangwon": {
                "market_size": "SMALL_MEDIUM",
                "competition_level": "LOW",
                "consumer_power": "LOW_MEDIUM",
                "rent_cost": "LOW",
                "characteristics": [
                    "Regional economy based on tourism and leisure",
                    "Strong seasonality in consumption",
                    "Opportunities linked to the natural environment"
                ],
                "advantages": [
                    "Low entry costs and rents",
                    "Tourist-targeted market",
                    "Ability to utilize natural resources"
                ],
                "challenges": [
                    "Seasonal demand fluctuations",
                    "Limited resident population",
                    "Constraints in accessibility and logistics"
                ],
                "score_modifier": -5
            },
            "chungbuk": {
                "market_size": "SMALL_MEDIUM",
                "competition_level": "LOW_MEDIUM",
                "consumer_power": "MEDIUM",
                "rent_cost": "LOW",
                "characteristics": [
                    "Stable economy centered on agriculture and manufacturing",
                    "Conservative and practical consumption tendencies",
                    "Good accessibility to the metro area"
                ],
                "advantages": [
                    "Stable regional economy",
                    "Low operating costs",
                    "Logistics access to the metro area"
                ],
                "challenges": [
                    "Conservative consumption patterns",
                    "Aging population",
                    "Limited market size"
                ],
                "score_modifier": -3
            },
            "chungnam": {
                "market_size": "MEDIUM",
                "competition_level": "MEDIUM",
                "consumer_power": "MEDIUM",
                "rent_cost": "LOW_MEDIUM",
                "characteristics": [
                    "Industrial cities like Cheonan and Asan are developed",
                    "Proximity to the metro area and transport hubs",
                    "Manufacturing and logistics-centered economy"
                ],
                "advantages": [
                    "Market of industrial complex workers",
                    "Excellent transportation accessibility",
                    "Reasonable operating costs"
                ],
                "challenges": [
                    "Development gaps between regions",
                    "Economic dependence on the metro area",
                    "Population decline in rural areas"
                ],
                "score_modifier": -1
            },
            "jeonbuk": {
                "market_size": "SMALL_MEDIUM",
                "competition_level": "LOW_MEDIUM",
                "consumer_power": "LOW_MEDIUM",
                "rent_cost": "LOW",
                "characteristics": [
                    "Traditional regional economy centered on agriculture",
                    "Tourism assets including Jeonju Hanok Village",
                    "Conservative and traditional consumption culture"
                ],
                "advantages": [
                    "Linkage of traditional culture and tourism",
                    "Low entry costs",
                    "Utilization of regional specialties"
                ],
                "challenges": [
                    "Population decline and aging",
                    "Slowing economic growth",
                    "Outflow of young people"
                ],
                "score_modifier": -4
            },
            "jeonnam": {
                "market_size": "SMALL_MEDIUM",
                "competition_level": "LOW",
                "consumer_power": "LOW_MEDIUM",
                "rent_cost": "LOW",
                "characteristics": [
                    "Economy based on agriculture, fisheries, and tourism",
                    "Tourist destinations such as Suncheon Bay and Yeosu",
                    "Slow-paced lifestyle aligned with wellbeing trends"
                ],
                "advantages": [
                    "Natural environment and tourism resources",
                    "Very low operating costs",
                    "Demand for wellbeing lifestyle products"
                ],
                "challenges": [
                    "Rapid population decline",
                    "Limited consumption market",
                    "Accessibility and logistics constraints"
                ],
                "score_modifier": -6
            },
            "gyeongbuk": {
                "market_size": "MEDIUM",
                "competition_level": "LOW_MEDIUM",
                "consumer_power": "MEDIUM",
                "rent_cost": "LOW",
                "characteristics": [
                    "Coexistence of heavy industry (e.g., POSCO) and agriculture",
                    "Historic and cultural tourism in Gyeongju",
                    "Conservative and stable market"
                ],
                "advantages": [
                    "High-income areas in industrial cities",
                    "Linkage with cultural/historical tourism",
                    "Stable regional economy"
                ],
                "challenges": [
                    "Large disparities across regions",
                    "Progressive aging",
                    "Slow acceptance of new trends"
                ],
                "score_modifier": -2
            },
            "gyeongnam": {
                "market_size": "MEDIUM_LARGE",
                "competition_level": "MEDIUM",
                "consumer_power": "MEDIUM_HIGH",
                "rent_cost": "MEDIUM",
                "characteristics": [
                    "Manufacturing hubs like Changwon and Gimhae",
                    "Commercial linkage with adjacent Busan",
                    "Concentration of young workers"
                ],
                "advantages": [
                    "Manufacturing worker market",
                    "Synergy with the Busan area",
                    "Relatively high income levels"
                ],
                "challenges": [
                    "Dependence on Busan’s commercial area",
                    "Sensitivity to manufacturing cycles",
                    "Intensifying internal regional competition"
                ],
                "score_modifier": 1
            },
            "jeju": {
                "market_size": "SMALL",
                "competition_level": "MEDIUM_HIGH",
                "consumer_power": "MEDIUM_HIGH",
                "rent_cost": "HIGH",
                "characteristics": [
                    "Tourism-centered special economic structure",
                    "High tourist inflow and strong seasonality",
                    "Distinct local culture and specialties"
                ],
                "advantages": [
                    "15 million annual tourists",
                    "High acceptance of premium products",
                    "Ability to leverage unique regional traits"
                ],
                "challenges": [
                    "Extreme seasonal fluctuations",
                    "High rent and labor costs",
                    "Logistics cost burden"
                ],
                "score_modifier": -1
            }
        }
    
    def _load_size_analysis_data(self) -> Dict[str, Dict[str, Any]]:
        """Load business size-specific strategy data from JSON file"""
        return self._load_json_data('size_data.json', self._get_fallback_size_data)
    
    def _get_fallback_size_data(self) -> Dict[str, Dict[str, Any]]:
        """Fallback size data (used if JSON file not available)"""
        return {
            "small": {
                "characteristics": [
                    "Possible to start with small capital",
                    "Fast decision-making and flexible operations",
                    "Personal relationships and service-centric approach"
                ],
                "advantages": [
                    "Low initial investment cost",
                    "Rapid market responsiveness",
                    "Personalized customer service"
                ],
                "challenges": [
                    "Limited resources and personnel",
                    "Insufficient marketing budget",
                    "Lack of economies of scale"
                ],
                "strategies": [
                    "Target niche markets and differentiate",
                    "Leverage digital marketing",
                    "Maximize customer loyalty"
                ],
                "investment_range": "10M KRW - 50M KRW",
                "employee_range": "1-5",
                "score_modifier": -5,
                "risk_level": "MEDIUM_HIGH"
            },
            "medium": {
                "characteristics": [
                    "Stable operations at moderate scale",
                    "Structured management and specialization",
                    "Recognizable presence in regional markets"
                ],
                "advantages": [
                    "Stable cash flow",
                    "Ability to secure skilled personnel",
                    "Opportunity to build brand"
                ],
                "challenges": [
                    "Risk of growth stagnation",
                    "Competition with large enterprises",
                    "Increasing management complexity"
                ],
                "strategies": [
                    "Strengthen core competencies",
                    "Systematize and standardize",
                    "Pursue strategic partnerships"
                ],
                "investment_range": "50M KRW - 300M KRW",
                "employee_range": "6-30",
                "score_modifier": 0,
                "risk_level": "MEDIUM"
            },
            "large": {
                "characteristics": [
                    "Large capital and infrastructure",
                    "Market dominance and strong brand power",
                    "Diversified business portfolio"
                ],
                "advantages": [
                    "Realization of economies of scale",
                    "Powerful brand influence",
                    "Access to diverse opportunities"
                ],
                "challenges": [
                    "High fixed costs",
                    "Complex organizational management",
                    "Slower response speed to market change"
                ],
                "strategies": [
                    "Expand market share",
                    "Invest in innovation and R&D",
                    "Pursue global expansion"
                ],
                "investment_range": "300M KRW or more",
                "employee_range": "30+",
                "score_modifier": 5,
                "risk_level": "LOW_MEDIUM"
            }
        }
    
    def _calculate_comprehensive_score(self, industry: str, region: str, size: str) -> float:
        """Calculate comprehensive business score (0-100)"""
        # Base score from industry
        industry_data = self.industry_data.get(industry, self.industry_data["other"])
        base_score = industry_data["base_score"]
        
        # Region modifier
        region_data = self.region_data.get(region, self.region_data["seoul"])
        region_modifier = region_data["score_modifier"]
        
        # Size modifier
        size_data = self.size_data.get(size, self.size_data["medium"])
        size_modifier = size_data["score_modifier"]
        
        # Calculate final score
        final_score = base_score + region_modifier + size_modifier
        
        # Ensure score is within 0-100 range
        final_score = max(0, min(100, final_score))
        
        return round(final_score, 1)
    
    def _generate_key_insights(self, industry: str, region: str, size: str) -> List[str]:
        """Generate 3 key business insights"""
        industry_data = self.industry_data.get(industry, self.industry_data["other"])
        region_data = self.region_data.get(region, self.region_data["seoul"])
        size_data = self.size_data.get(size, self.size_data["medium"])
        
        insights = []
        
        # Industry insight
        growth_potential = industry_data["growth_potential"]
        competition = industry_data["competition_level"]
        
        if growth_potential == "HIGH" and competition == "HIGH":
            insights.append(f"The {industry} sector has strong growth potential, but differentiation is essential in a highly competitive landscape.")
        elif growth_potential == "HIGH" and competition in ["MEDIUM", "LOW"]:
            insights.append(f"The {industry} sector offers high growth potential with relatively lower competition, making this a favorable entry period.")
        elif growth_potential == "MEDIUM":
            insights.append(f"The {industry} sector is expected to grow steadily; sustained and disciplined operations will matter.")
        else:
            insights.append(f"The {industry} sector is a mature market; innovative approaches will be required to unlock growth.")
        
        # Region insight
        market_size = region_data["market_size"]
        consumer_power = region_data["consumer_power"]
        
        if market_size in ["LARGE", "VERY_LARGE"] and consumer_power == "HIGH":
            insights.append(f"The {region} region offers an optimal business environment with a large market and strong purchasing power.")
        elif market_size in ["MEDIUM", "MEDIUM_LARGE"]:
            insights.append(f"The {region} region is a stable market of moderate size; strategies leveraging local characteristics will be effective.")
        else:
            insights.append(f"In the {region} region, focus on niche market penetration and community-anchored services to build competitiveness.")
        
        # Size insight
        risk_level = size_data["risk_level"]
        investment_range = size_data["investment_range"]
        
        if size == "small":
            insights.append(f"The {size} size can launch with an investment of {investment_range}; fast market entry and close customer engagement are key.")
        elif size == "medium":
            insights.append(f"The {size} size can operate stably with an investment of {investment_range}; structured management and brand building are important.")
        else:
            insights.append(f"The {size} size requires a large investment of {investment_range}; focus on achieving economies of scale and market leadership.")
        
        return insights
    
    def _perform_bedrock_analysis(
        self,
        industry: str,
        region: str,
        size: str,
        industry_data: Dict[str, Any],
        region_data: Dict[str, Any],
        size_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform enhanced business analysis using Bedrock Claude.
        
        This method implements Requirement 1.2 and 3.1:
        - Uses Bedrock Claude for industry/region/size analysis
        - Provides Chain-of-Thought reasoning
        - Generates enhanced insights beyond static data
        
        Args:
            industry: Industry type
            region: Region name
            size: Business size
            industry_data: Static industry data
            region_data: Static region data
            size_data: Static size data
        
        Returns:
            Dict with enhanced analysis including reasoning
        """
        try:
            # Build comprehensive context for Claude
            analysis_context = {
                'industry': industry,
                'region': region,
                'size': size,
                'industry_characteristics': industry_data['characteristics'],
                'industry_trends': industry_data['market_trends'],
                'region_market': {
                    'size': region_data['market_size'],
                    'competition': region_data['competition_level'],
                    'consumer_power': region_data['consumer_power']
                },
                'size_investment': size_data['investment_range'],
                'size_risk': size_data['risk_level']
            }
            
            system_prompt = """You are an expert business consultant specializing in market analysis and business viability assessment.

Your task is to analyze a business opportunity based on industry, region, and size factors.

Provide:
1. Comprehensive viability assessment
2. Strategic insights beyond obvious factors
3. Specific actionable recommendations
4. Risk mitigation strategies
5. Growth opportunities

Respond in English with a professional, insightful tone."""
            
            prompt = f"""Business Analysis Request:

Industry: {industry}
Region: {region}
Size: {size}

Industry Characteristics:
{json.dumps(industry_data['characteristics'], ensure_ascii=False, indent=2)}

Market Trends:
{json.dumps(industry_data['market_trends'], ensure_ascii=False, indent=2)}

Regional Market Environment:
- Market size: {region_data['market_size']}
- Competition level: {region_data['competition_level']}
- Consumer power: {region_data['consumer_power']}
- Rent level: {region_data.get('rent_cost', 'N/A')}

Size-specific Traits:
- Investment range: {size_data['investment_range']}
- Risk level: {size_data['risk_level']}

Based on the above, analyze and respond in JSON with:

{{
    "score": 0-100,
    "reasoning": "Basis for the score",
    "insights": ["Insight 1", "Insight 2", "Insight 3"],
    "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"],
    "risk_factors": ["Risk 1", "Risk 2"],
    "growth_opportunities": ["Opportunity 1", "Opportunity 2"],
    "confidence": 0.0-1.0
}}"""
            
            self.logger.info(
                f"Invoking Bedrock Claude for business analysis: "
                f"industry={industry}, region={region}, size={size}"
            )
            
            # Invoke Claude for enhanced analysis
            response = self.bedrock_client.invoke_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.5  # Balanced creativity and consistency
            )
            
            # Parse Claude's response
            analysis_text = response['text']
            
            # Try to extract JSON from response
            bedrock_analysis = self._extract_json_from_response(analysis_text)
            
            if bedrock_analysis:
                self.logger.info(
                    f"Bedrock analysis complete: score={bedrock_analysis.get('score', 'N/A')}, "
                    f"confidence={bedrock_analysis.get('confidence', 'N/A')}, "
                    f"latency={response['latency_ms']}ms"
                )
                
                return {
                    'success': True,
                    'analysis': bedrock_analysis,
                    'reasoning_text': analysis_text,
                    'latency_ms': response['latency_ms'],
                    'model_id': response['model_id']
                }
            else:
                # Fallback: use text response
                self.logger.warning("Could not parse JSON from Bedrock response, using text")
                return {
                    'success': True,
                    'analysis': {
                        'score': None,
                        'reasoning': analysis_text,
                        'insights': [],
                        'recommendations': [],
                        'confidence': 0.7
                    },
                    'reasoning_text': analysis_text,
                    'latency_ms': response['latency_ms']
                }
                
        except Exception as e:
            self.logger.error(f"Bedrock analysis failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_json_from_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from Claude response (may be wrapped in markdown)"""
        try:
            # Find JSON in response
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = text[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return None
    
    def execute(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Execute Product Insight Agent business analysis with Bedrock integration.
        
        This method implements:
        - Requirement 1.2: Bedrock Claude for industry/region/size analysis
        - Requirement 3.1: Reasoning LLM for autonomous decision-making
        - Fallback: Uses existing logic when ENABLE_FALLBACK=true
        """
        try:
            # Extract request data
            body = event.get('body', '{}')
            if isinstance(body, str):
                try:
                    body_data = json.loads(body)
                except:
                    body_data = {}
            else:
                body_data = body or {}
            
            session_id = body_data.get('sessionId')
            business_info_data = body_data.get('businessInfo', {})
            
            if not session_id:
                return self.create_lambda_response(400, {
                    'error': 'Session ID is required'
                })
            
            # Start execution tracking
            self.start_execution(session_id, "business_analysis")
            
            # Validate business info
            try:
                business_info = BusinessInfo(**business_info_data)
                if not business_info.validate():
                    raise ValueError("Invalid business information")
            except Exception as e:
                self.end_execution("error", f"Invalid business info: {str(e)}")
                return self.create_lambda_response(400, {
                    'error': 'Invalid business information',
                    'details': str(e)
                })
            
            # Perform business analysis
            industry = business_info.industry.lower()
            region = business_info.region.lower()
            size = business_info.size.lower()
            
            # Get industry, region, and size data
            industry_data = self.industry_data.get(industry, self.industry_data["other"])
            region_data = self.region_data.get(region, self.region_data["seoul"])
            size_data = self.size_data.get(size, self.size_data["medium"])
            
            # Calculate baseline score (always calculate for fallback)
            baseline_score = self._calculate_comprehensive_score(industry, region, size)
            baseline_insights = self._generate_key_insights(industry, region, size)
            
            # Check if Bedrock is available and fallback is disabled
            enable_fallback = os.getenv('ENABLE_FALLBACK', 'true').lower() == 'true'
            use_bedrock = self.bedrock_client is not None and not enable_fallback
            
            # Initialize analysis variables
            final_score = baseline_score
            final_insights = baseline_insights
            final_recommendations = industry_data["success_factors"][:3]
            bedrock_reasoning = None
            bedrock_confidence = None
            analysis_provider = "baseline"
            
            # Try Bedrock analysis if available
            if use_bedrock:
                self.logger.info("Using Bedrock Claude for enhanced analysis")
                bedrock_result = self._perform_bedrock_analysis(
                    industry, region, size,
                    industry_data, region_data, size_data
                )
                
                if bedrock_result['success']:
                    bedrock_analysis = bedrock_result['analysis']
                    
                    # Use Bedrock results if available
                    if bedrock_analysis.get('score') is not None:
                        final_score = bedrock_analysis['score']
                    
                    if bedrock_analysis.get('insights'):
                        final_insights = bedrock_analysis['insights']
                    
                    if bedrock_analysis.get('recommendations'):
                        final_recommendations = bedrock_analysis['recommendations']
                    
                    bedrock_reasoning = bedrock_analysis.get('reasoning', bedrock_result.get('reasoning_text'))
                    bedrock_confidence = bedrock_analysis.get('confidence')
                    analysis_provider = "bedrock"
                    
                    self.logger.info(
                        f"Bedrock analysis applied: score={final_score}, "
                        f"confidence={bedrock_confidence}"
                    )
                else:
                    self.logger.warning(
                        f"Bedrock analysis failed, using baseline: {bedrock_result.get('error')}"
                    )
                    analysis_provider = "baseline_fallback"
            else:
                if enable_fallback:
                    self.logger.info("Fallback enabled, using baseline analysis")
                    analysis_provider = "baseline_fallback"
                else:
                    self.logger.warning("Bedrock not available, using baseline analysis")
                    analysis_provider = "baseline_no_bedrock"
            
            # Create analysis result
            analysis_result = AnalysisResult(
                summary=f"Business analysis for {industry} in {region} at {size} scale: Overall score evaluated at {final_score}.",
                score=final_score,
                insights=final_insights,
                market_trends=industry_data["market_trends"],
                recommendations=final_recommendations
            )
            
            # Update session with analysis result
            session_updates = {
                'analysisResult': analysis_result.to_dict() if hasattr(analysis_result, 'to_dict') else analysis_result.__dict__,
                'currentStep': 2  # Move to naming step
            }
            
            if not self.update_session_data(session_id, session_updates):
                self.logger.warning("Failed to update session data")
            
            # Prepare response
            response_data = {
                'sessionId': session_id,
                'analysis': {
                    'summary': analysis_result.summary,
                    'score': analysis_result.score,
                    'insights': analysis_result.insights,
                    'market_trends': analysis_result.market_trends,
                    'recommendations': analysis_result.recommendations,
                    'industry_characteristics': industry_data["characteristics"],
                    'region_advantages': self.region_data.get(region, self.region_data["seoul"]).get("advantages", []),
                    'size_strategies': size_data["strategies"],
                    'investment_range': size_data["investment_range"],
                    'risk_level': size_data["risk_level"]
                },
                'metadata': {
                    'analyzed_at': datetime.utcnow().isoformat(),
                    'agent': self.agent_name,
                    'version': '2.1.0',  # Updated version for Bedrock integration
                    'analysis_provider': analysis_provider,
                    'bedrock_enabled': use_bedrock
                }
            }
            
            # Add Bedrock-specific metadata if available
            if bedrock_reasoning:
                response_data['analysis']['bedrock_reasoning'] = bedrock_reasoning
            
            if bedrock_confidence is not None:
                response_data['analysis']['confidence'] = bedrock_confidence
            
            # End execution tracking
            latency_ms = self.end_execution("success", result=response_data)
            
            self.logger.info(
                f"Business analysis completed for {industry} in {region} "
                f"(provider: {analysis_provider}, latency: {latency_ms}ms)"
            )
            
            return self.create_lambda_response(200, response_data)
            
        except Exception as e:
            self.end_execution("error", str(e))
            error_response = self.handle_error(e, "execute")
            return self.create_lambda_response(500, error_response)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for Product Insight Agent"""
    agent = ProductInsightAgent()
    return agent.lambda_handler(event, context)
