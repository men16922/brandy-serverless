"""
Interior Agent – Recommend interior styles & provide design guides
Bedrock Integration: Uses Claude 4 Sonnet for reasoning-based interior recommendations
"""

import json
import sys
import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add shared modules to path - Lambda Layer structure
sys.path.insert(0, '/opt/python/python')

# Interior-specific models (always defined)
class InteriorRecommendation:
    def __init__(self, style: str, description: str, color_scheme: List[str],
                 materials: List[str], furniture: List[str], estimated_cost: str,
                 suitability_score: float = 0.0, pros: List[str] = None, cons: List[str] = None):
        self.style = style
        self.description = description
        self.color_scheme = color_scheme
        self.materials = materials
        self.furniture = furniture
        self.estimated_cost = estimated_cost
        self.suitability_score = suitability_score
        self.pros = pros or []
        self.cons = cons or []
        self.generated_at = datetime.utcnow().isoformat()
    
    def validate(self) -> bool:
        return bool(self.style and self.description and self.color_scheme and 
                    self.materials and self.furniture and self.estimated_cost)

class InteriorRecommendations:
    def __init__(self, recommendations: List[InteriorRecommendation] = None):
        self.recommendations = recommendations or []
    
    def validate(self) -> bool:
        return len(self.recommendations) <= 3 and all(rec.validate() for rec in self.recommendations)

try:
    from shared.base_agent import BaseAgent
    from shared.models import AgentType, BusinessInfo
    from shared.utils import create_response
    from shared.data_loader import get_data_loader
    HAS_SHARED_MODULES = True
    print("✓ Successfully imported shared modules")
except ImportError as e:
    print(f"Failed to import shared modules: {e}")
    HAS_SHARED_MODULES = False
    # Mock implementations for testing
    from datetime import datetime
    from typing import Dict, Any, List
    from enum import Enum
    import time
    
    class AgentType(Enum):
        INTERIOR = "interior"
    
    class InteriorRecommendation:
        def __init__(self, style: str, description: str, color_scheme: List[str],
                     materials: List[str], furniture: List[str], estimated_cost: str,
                     suitability_score: float = 0.0, pros: List[str] = None, cons: List[str] = None):
            self.style = style
            self.description = description
            self.color_scheme = color_scheme
            self.materials = materials
            self.furniture = furniture
            self.estimated_cost = estimated_cost
            self.suitability_score = suitability_score
            self.pros = pros or []
            self.cons = cons or []
            self.generated_at = datetime.utcnow().isoformat()
        
        def validate(self) -> bool:
            return bool(self.style and self.description and self.color_scheme and 
                        self.materials and self.furniture and self.estimated_cost)
    
    class InteriorRecommendations:
        def __init__(self, recommendations: List[InteriorRecommendation] = None):
            self.recommendations = recommendations or []
        
        def validate(self) -> bool:
            return len(self.recommendations) <= 3 and all(rec.validate() for rec in self.recommendations)
    
    class BusinessInfo:
        def __init__(self, industry: str, region: str, size: str, country: str = None, city: str = None, **kwargs):
            self.industry = industry
            self.region = region
            self.size = size
            self.country = country
            self.city = city
    
    class BaseAgent:
        def __init__(self, agent_type):
            self.agent_type = agent_type
            self.agent_name = agent_type.value
            self.logger = self._create_mock_logger()
        
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
        
        def get_session_data(self, session_id: str):
            return None
        
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


class InteriorAgent(BaseAgent):
    """Interior Agent – interior style recommendations"""
    
    def __init__(self):
        super().__init__(AgentType.INTERIOR)
        
        # Bedrock integration (Hackathon requirement)
        enable_fallback_env = os.getenv('ENABLE_FALLBACK', 'false')
        self.use_bedrock = enable_fallback_env.lower() != 'true'
        
        self.logger.info(f"Interior Agent initialization: ENABLE_FALLBACK={enable_fallback_env}, use_bedrock={self.use_bedrock}, HAS_SHARED_MODULES={HAS_SHARED_MODULES}")
        
        if self.use_bedrock and HAS_SHARED_MODULES:
            try:
                self.logger.info("Attempting to import Bedrock modules...")
                from shared.bedrock_client import BedrockClient
                from shared.reasoning_engine import ReasoningEngine
                
                self.logger.info("Creating BedrockClient...")
                self.bedrock_client = BedrockClient(logger=self.logger)
                
                self.logger.info("Creating ReasoningEngine...")
                self.reasoning_engine = ReasoningEngine(
                    bedrock_client=self.bedrock_client,
                    logger=self.logger
                )
                self.logger.info("✓ Bedrock integration enabled for Interior Agent")
            except Exception as e:
                self.logger.error(f"Failed to initialize Bedrock: {str(e)}", exc_info=True)
                self.bedrock_client = None
                self.reasoning_engine = None
                self.use_bedrock = False
        else:
            self.bedrock_client = None
            self.reasoning_engine = None
            if not self.use_bedrock:
                self.logger.info("Bedrock disabled (ENABLE_FALLBACK=true), using fallback")
            if not HAS_SHARED_MODULES:
                self.logger.warning("Shared modules not available, using fallback")
        
        # Data loader initialization (only if shared modules are available)
        if HAS_SHARED_MODULES:
            self.data_loader = get_data_loader()
            self._ensure_data_initialized()
            self._load_all_data()
        else:
            self.data_loader = None
            self._load_fallback_data()
    
    def _ensure_data_initialized(self) -> None:
        """Ensure data is initialized, initialize if needed"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(current_dir, '..', '..', '..')
            data_dir = os.path.join(project_root, 'data')
            self.data_loader.initialize_all_data(data_dir, force_reload=False)
        except Exception as e:
            self.logger.warning(f"Failed to initialize data from files: {str(e)}")
            self._load_fallback_data()
    
    def _load_all_data(self) -> None:
        """Load all interior data from DynamoDB"""
        try:
            if not self.data_loader:
                self._load_fallback_data()
                return
                
            all_data = self.data_loader.get_all_interior_data()
            self.interior_styles = all_data.get('interior_styles', {})
            self.industry_characteristics = all_data.get('industry_characteristics', {})
            self.regional_trends = all_data.get('regional_trends', {})
            self.size_considerations = all_data.get('size_considerations', {})
            
            if not self.interior_styles:
                self.logger.warning("No data found in DynamoDB, using fallback data")
                self._load_fallback_data()
        except Exception as e:
            self.logger.error(f"Failed to load data from DynamoDB: {str(e)}")
            self._load_fallback_data()
    
    def _load_fallback_data(self) -> None:
        """Load baseline fallback data"""
        self.interior_styles = self._get_fallback_interior_styles()
        self.industry_characteristics = self._get_fallback_industry_characteristics()
        self.regional_trends = self._get_fallback_regional_trends()
        self.size_considerations = self._get_fallback_size_considerations()
    
    def _get_fallback_interior_styles(self) -> Dict[str, Dict[str, Any]]:
        """Interior style dataset (EN)"""
        return {
            "modern": {
                "name": "Modern Style",
                "description": "Clean and refined contemporary design emphasizing simplicity and function.",
                "color_scheme": ["White", "Gray", "Black", "Silver"],
                "materials": ["Stainless steel", "Glass", "Concrete", "Engineered stone"],
                "furniture": ["Minimal table", "Modern chairs", "LED lighting", "Simple storage"],
                "estimated_cost": "Medium",
                "pros": [
                    "Sleek, professional image",
                    "Clean and hygienic impression",
                    "Easy to maintain",
                    "Timeless design"
                ],
                "cons": [
                    "Can feel cold",
                    "May lack personality",
                    "Slightly higher upfront cost"
                ]
            },
            "cozy": {
                "name": "Cozy Style",
                "description": "Warm and welcoming atmosphere that provides comfort and friendliness.",
                "color_scheme": ["Warm brown", "Cream", "Beige", "Soft orange"],
                "materials": ["Solid wood", "Fabric", "Natural stone", "Rattan"],
                "furniture": ["Comfortable sofa", "Wood table", "Warm lighting", "Cushions"],
                "estimated_cost": "Low",
                "pros": [
                    "Friendly, relaxing mood",
                    "Encourages longer stays",
                    "Relatively affordable",
                    "Appeals to a wide age range"
                ],
                "cons": [
                    "Slightly harder to maintain",
                    "May feel less trendy",
                    "Space can feel cramped"
                ]
            },
            "industrial": {
                "name": "Industrial Style",
                "description": "Urban, distinctive charm that creates a highly individual space.",
                "color_scheme": ["Dark gray", "Rust", "Black", "Bronze"],
                "materials": ["Exposed brick", "Metal", "Reclaimed wood", "Concrete"],
                "furniture": ["Industrial table", "Metal chairs", "Pendant lights", "Pipe shelving"],
                "estimated_cost": "High",
                "pros": [
                    "Unique and full of character",
                    "Very durable",
                    "Highly Instagrammable",
                    "Strong brand differentiation"
                ],
                "cons": [
                    "High initial cost",
                    "May feel heavy to some customers",
                    "Maintenance can be complex",
                    "Less seasonal warmth"
                ]
            },
            "scandinavian": {
                "name": "Scandinavian Style",
                "description": "Simple, nature-friendly design creating a comfortable yet refined space.",
                "color_scheme": ["White", "Light gray", "Natural wood", "Pastel blue"],
                "materials": ["Birch", "Linen", "Wool", "Ceramic"],
                "furniture": ["Simple wood table", "Fabric chairs", "Maximize daylight", "Greenery"],
                "estimated_cost": "Medium",
                "pros": [
                    "Bright, pleasant ambiance",
                    "Eco-friendly image",
                    "Popular with younger customers",
                    "Great for photos"
                ],
                "cons": [
                    "May feel less distinctive",
                    "Sensitive to trends",
                    "Some materials may lack durability"
                ]
            },
            "vintage": {
                "name": "Vintage Style",
                "description": "Classic charm that evokes nostalgia to provide a special experience.",
                "color_scheme": ["Antique brown", "Deep green", "Gold", "Burgundy"],
                "materials": ["Antique wood", "Leather", "Brass", "Velvet"],
                "furniture": ["Antique table", "Classic chairs", "Vintage lighting", "Display cabinet"],
                "estimated_cost": "High",
                "pros": [
                    "Luxurious and elegant",
                    "Strong storytelling potential",
                    "Ages gracefully",
                    "Distinct brand image"
                ],
                "cons": [
                    "High initial cost",
                    "Challenging maintenance",
                    "May appeal less to younger audiences",
                    "Potentially lower space efficiency"
                ]
            }
        }
    
    def _get_fallback_industry_characteristics(self) -> Dict[str, Dict[str, Any]]:
        """Fallback: industry-specific interior characteristics (EN)"""
        return {
            "restaurant": {
                "priority_factors": ["Hygiene", "Comfort", "Ambience", "Operational efficiency"],
                "recommended_styles": ["modern", "cozy", "scandinavian"],
                "avoid_styles": ["industrial"],
                "special_requirements": [
                    "Hygienic, non-porous materials",
                    "Layouts that are easy to clean",
                    "Appropriate lighting design",
                    "Sound insulation"
                ],
                "customer_considerations": [
                    "Comfortable seating for mealtime",
                    "Colors that complement food",
                    "Family-friendly options"
                ]
            },
            "retail": {
                "priority_factors": ["Merchandising", "Customer flow", "Brand image", "Lighting"],
                "recommended_styles": ["modern", "scandinavian", "industrial"],
                "avoid_styles": [],
                "special_requirements": [
                    "Lighting that highlights products",
                    "Efficient display space",
                    "Optimized customer pathways",
                    "Reflect brand colors"
                ],
                "customer_considerations": [
                    "Easy-to-shop environment",
                    "Product try-out area",
                    "Waiting/rest area"
                ]
            },
            "service": {
                "priority_factors": ["Professionalism", "Trust", "Comfort", "Privacy"],
                "recommended_styles": ["modern", "scandinavian"],
                "avoid_styles": ["industrial", "vintage"],
                "special_requirements": [
                    "Professional visual language",
                    "Separate consultation zones",
                    "Calm color palette",
                    "Noise control"
                ],
                "customer_considerations": [
                    "Privacy protection",
                    "Comfortable consultation space",
                    "Foster trust"
                ]
            }
        }
    
    def _get_fallback_regional_trends(self) -> Dict[str, Dict[str, Any]]:
        """Fallback: regional interior trends (EN)"""
        return {
            "seoul": {
                "trending_styles": ["modern", "scandinavian"],
                "characteristics": ["Trendy", "Sophisticated", "Efficient"],
                "budget_range": "High",
                "customer_preferences": ["Instagrammable", "Brand value", "Differentiation"]
            },
            "busan": {
                "trending_styles": ["cozy", "scandinavian"],
                "characteristics": ["Comfort", "Nature-friendly", "Practicality"],
                "budget_range": "Medium",
                "customer_preferences": ["Comfort", "Value for money", "Regional character"]
            }
        }
    
    def _get_fallback_size_considerations(self) -> Dict[str, Dict[str, Any]]:
        """Fallback: size-based considerations (EN)"""
        return {
            "small": {
                "budget_constraint": "High",
                "space_efficiency": "Critical",
                "cost_saving_tips": [
                    "Maximize existing structure",
                    "Use accent colors for impact",
                    "Shape ambience with lighting",
                    "Decorate with plants"
                ]
            },
            "medium": {
                "budget_constraint": "Moderate",
                "space_efficiency": "Important",
                "investment_priorities": [
                    "Focus spend on core zones",
                    "Choose durable materials",
                    "Keep structures extensible",
                    "Consider energy efficiency"
                ]
            },
            "large": {
                "budget_constraint": "Low",
                "space_efficiency": "Moderate",
                "luxury_elements": [
                    "Use premium finishes",
                    "Custom-made furniture",
                    "Introduce smart systems",
                    "Curated art and sculptures"
                ]
            }
        }
    
    def execute(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Interior Agent execution logic"""
        try:
            headers = event.get('headers', {})
            is_async = headers.get('x-async-mode') == 'true'
            
            # Parse body
            if isinstance(event.get('body'), str):
                body = json.loads(event['body'])
            else:
                body = event.get('body', event)
            
            session_id = body.get('sessionId')
            business_info_data = body.get('businessInfo', {})
            selected_signboard = body.get('selectedSignboard')
            action = body.get('action', 'recommend')
            
            if not session_id:
                return self.create_lambda_response(400, {"error": "sessionId is required"})
            
            # Asynchronous mode: invoke self and return 202
            if is_async:
                self.logger.info(f"Async mode enabled for session: {session_id}")
                try:
                    import boto3
                    lambda_client = boto3.client('lambda')
                    sync_event = event.copy()
                    if 'headers' in sync_event:
                        sync_headers = sync_event['headers'].copy()
                        sync_headers.pop('x-async-mode', None)
                        sync_event['headers'] = sync_headers
                    function_name = os.getenv('AWS_LAMBDA_FUNCTION_NAME')
                    self.logger.info(f"Invoking Lambda asynchronously: {function_name}")
                    lambda_client.invoke(
                        FunctionName=function_name,
                        InvocationType='Event',
                        Payload=json.dumps(sync_event)
                    )
                    self.logger.info(f"Async Lambda invocation successful for session: {session_id}")
                except Exception as invoke_error:
                    self.logger.error(f"Failed to invoke Lambda asynchronously: {str(invoke_error)}")
                return self.create_lambda_response(202, {
                    "message": "Interior generation started",
                    "sessionId": session_id,
                    "status": "processing"
                })
            
            # Sync flow
            self.start_execution(session_id, f"interior.{action}")
            
            if action == 'select':
                selected_style = body.get('selectedStyle')
                if not selected_style:
                    self.end_execution("error", "selectedStyle is required")
                    return self.create_lambda_response(400, {
                        "error": "selectedStyle is required for select action"
                    })
                try:
                    self.update_session_data(session_id, {
                        "selected_interior": selected_style,
                        "currentStep": 5  # Interior selection complete; next step: report generation
                    })
                    result = {
                        "message": "Interior style selected",
                        "sessionId": session_id,
                        "selectedStyle": selected_style,
                        "success": True
                    }
                    self.end_execution("success", result=result)
                    return self.create_lambda_response(200, result)
                except Exception as e:
                    error_msg = f"Failed to save selected interior: {str(e)}"
                    self.logger.error(error_msg)
                    self.end_execution("error", error_msg)
                    return self.create_lambda_response(500, {"error": error_msg, "success": False})
            
            # recommend action
            try:
                self.update_session_data(session_id, {
                    "interiorGenerationStatus": "in_progress",
                    "interiorGenerationStartedAt": datetime.utcnow().isoformat()
                })
            except Exception as status_error:
                self.logger.warning(f"Failed to set initial status: {str(status_error)}")
            
            if isinstance(business_info_data, str):
                business_info_data = json.loads(business_info_data)
            business_info = BusinessInfo(**business_info_data)
            
            if action == 'recommend':
                if self.use_bedrock and getattr(self, 'bedrock_client', None) and getattr(self, 'reasoning_engine', None):
                    result = self._generate_interior_recommendations_with_bedrock(
                        session_id, business_info, selected_signboard
                    )
                else:
                    result = self._generate_interior_recommendations_with_images_sync(
                        session_id, business_info, selected_signboard
                    )
            else:
                raise ValueError(f"Unknown action: {action}")
            
            self.end_execution("success", result=result)
            return self.create_lambda_response(200, result)
            
        except Exception as e:
            error_message = f"Interior Agent execution failed: {str(e)}"
            self.end_execution("error", error_message)
            error_response = self.handle_error(e, "execute")
            return self.create_lambda_response(500, error_response)
    
    def _generate_interior_recommendations_with_bedrock(
        self, session_id: str, business_info: BusinessInfo,
        selected_signboard: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate interior recommendations using Bedrock Claude (Reasoning LLM)"""
        try:
            self.logger.info(f"Generating interior recommendations with Bedrock for session {session_id}")
            
            # System prompt enforces ENGLISH ONLY
            system_prompt = """You are an expert interior design consultant specializing in commercial spaces.
Your task is to recommend 3 interior design styles that best match the business requirements.

IMPORTANT: ALL responses must be in ENGLISH ONLY.

Consider:
1. Industry characteristics and functional requirements
2. Regional trends and customer preferences
3. Business size and budget constraints
4. Brand identity alignment (if signboard design is provided)
5. Customer experience and atmosphere

For each recommended style, provide:
- Style name (from available options)
- Detailed description (ENGLISH)
- Color scheme (4–5 colors, ENGLISH)
- Materials (4–5 items, ENGLISH)
- Furniture recommendations (4–5 items, ENGLISH)
- Estimated cost level (Low/Medium/High)
- Suitability score (0–100)
- Pros (3–4)
- Cons (2–3)

Respond in JSON:
{
  "recommendations": [{...}],
  "reasoning": "overall reasoning (ENGLISH)",
  "confidence": 0.0-1.0
}"""
            
            prompt = f"""Business Context:
- Industry: {business_info.industry}
- Region: {business_info.region}
- Size: {business_info.size}

Available Interior Styles:
{json.dumps(list(self.interior_styles.keys()), indent=2)}

{f"Selected Signboard Design: {json.dumps(selected_signboard, indent=2)}" if selected_signboard else "No signboard design selected yet"}

Please recommend 3 interior design styles that best match this business, providing detailed reasoning for each recommendation."""
            
            response = self.bedrock_client.invoke_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.7
            )
            
            response_text = response['text']
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    bedrock_data = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.warning(f"Failed to parse Bedrock JSON response: {str(e)}, using fallback")
                return self._generate_interior_recommendations(session_id, business_info, selected_signboard)
            
            recommendations: List[InteriorRecommendation] = []
            for rec_data in bedrock_data.get('recommendations', [])[:3]:
                try:
                    recommendation = InteriorRecommendation(
                        style=rec_data.get('style', 'modern'),
                        description=rec_data.get('description', ''),
                        color_scheme=rec_data.get('color_scheme', []),
                        materials=rec_data.get('materials', []),
                        furniture=rec_data.get('furniture', []),
                        estimated_cost=rec_data.get('estimated_cost', 'Medium'),
                        suitability_score=float(rec_data.get('suitability_score', 70)),
                        pros=rec_data.get('pros', []),
                        cons=rec_data.get('cons', [])
                    )
                    recommendations.append(recommendation)
                except Exception as e:
                    self.logger.error(f"Failed to create recommendation object: {str(e)}")
                    continue
            
            if not recommendations:
                self.logger.warning("No valid recommendations from Bedrock, using fallback")
                return self._generate_interior_recommendations(session_id, business_info, selected_signboard)
            
            interior_recommendations = InteriorRecommendations(recommendations=recommendations)
            self._save_interior_recommendations(session_id, interior_recommendations)
            
            industry = business_info.industry.lower()
            region = business_info.region.lower()
            size = business_info.size.lower()
            industry_info = self.industry_characteristics.get(industry, self.industry_characteristics.get("retail", {}))
            regional_info = self.regional_trends.get(region, self.regional_trends.get("seoul", {}))
            size_info = self.size_considerations.get(size, self.size_considerations.get("medium", {}))
            
            # Try to generate images (Bedrock Titan + optional DALL·E fallback)
            self.logger.info(f"Generating interior images for {len(recommendations)} styles")
            recommendations_with_images = []
            enable_fallback = os.getenv('ENABLE_FALLBACK', 'false').lower() == 'true'
            
            for idx, rec in enumerate(recommendations):
                rec_dict = self._recommendation_to_dict(rec)
                image_url = None
                provider_used = None
                
                style_name = rec.style
                img_prompt = self._create_interior_image_prompt(
                    style_name, business_info.industry, rec.color_scheme, rec.materials
                )
                
                use_dalle_first = (idx == len(recommendations) - 1) and enable_fallback
                if use_dalle_first:
                    try:
                        self.logger.info(f"[{style_name}] Using DALL·E first (fallback enabled)")
                        from openai import OpenAI
                        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                        resp = client.images.generate(
                            model="dall-e-3",
                            prompt=img_prompt,
                            size="1024x1024",
                            quality="standard",
                            n=1
                        )
                        dalle_url = resp.data[0].url
                        image_url = self._upload_image_to_s3(
                            dalle_url,
                            f"interiors/{session_id}-{style_name}-{int(time.time())}.png"
                        )
                        if image_url:
                            provider_used = "openai-dalle3"
                    except Exception as dalle_error:
                        self.logger.error(f"[{style_name}] DALL·E failed: {str(dalle_error)}")
                        use_dalle_first = False
                
                if not use_dalle_first or not image_url:
                    try:
                        self.logger.info(f"[{style_name}] Using Bedrock Titan Image Generator")
                        import boto3, base64
                        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-west-2')
                        request_body = {
                            "taskType": "TEXT_IMAGE",
                            "textToImageParams": {
                                "text": img_prompt[:512],
                                "negativeText": "low quality, blurry, distorted"
                            },
                            "imageGenerationConfig": {
                                "numberOfImages": 1,
                                "quality": "standard",
                                "height": 1024,
                                "width": 1024,
                                "cfgScale": 8.0
                            }
                        }
                        resp = bedrock_runtime.invoke_model(
                            modelId="amazon.titan-image-generator-v2:0",
                            body=json.dumps(request_body)
                        )
                        body_json = json.loads(resp['body'].read())
                        if 'images' in body_json and body_json['images']:
                            image_data = base64.b64decode(body_json['images'][0])
                            s3 = boto3.client('s3')
                            bucket = os.getenv('S3_BUCKET_NAME', 'ai-branding-chatbot-assets-908601828278')
                            key = f"interiors/{session_id}-{style_name}-{int(time.time())}.png"
                            s3.put_object(Bucket=bucket, Key=key, Body=image_data, ContentType='image/png')
                            image_url = s3.generate_presigned_url(
                                'get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=604800
                            )
                            provider_used = "bedrock-titan"
                        else:
                            self.logger.warning(f"[{style_name}] Titan returned no images")
                    except Exception as bedrock_error:
                        self.logger.warning(f"[{style_name}] Bedrock image gen failed: {str(bedrock_error)}")
                        if not use_dalle_first and enable_fallback:
                            try:
                                from openai import OpenAI
                                client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                                resp = client.images.generate(
                                    model="dall-e-3",
                                    prompt=img_prompt,
                                    size="1024x1024",
                                    quality="standard",
                                    n=1
                                )
                                dalle_url = resp.data[0].url
                                image_url = self._upload_image_to_s3(
                                    dalle_url,
                                    f"interiors/{session_id}-{style_name}-{int(time.time())}.png"
                                )
                                if image_url:
                                    provider_used = "openai-dalle3"
                            except Exception as dalle_error:
                                self.logger.error(f"[{style_name}] DALL·E fallback failed: {str(dalle_error)}")
                
                if image_url:
                    rec_dict['imageUrl'] = image_url
                    rec_dict['isGenerated'] = True
                    rec_dict['prompt'] = img_prompt
                    rec_dict['provider'] = provider_used
                else:
                    rec_dict['imageUrl'] = None
                    rec_dict['isGenerated'] = False
                    rec_dict['provider'] = None
                
                recommendations_with_images.append(rec_dict)
            
            generated_count = sum(1 for rec in recommendations_with_images if rec.get('isGenerated'))
            providers_used = [rec.get('provider') for rec in recommendations_with_images if rec.get('provider')]
            self.logger.info(f"Generated {generated_count}/{len(recommendations)} interior images. Providers: {providers_used}")
            
            try:
                self._save_interior_to_dynamodb(session_id, recommendations_with_images)
            except Exception as save_error:
                self.logger.error(f"DynamoDB save failed but continuing: {str(save_error)}")
            
            providers_summary = "bedrock-claude"
            if providers_used:
                unique = set(providers_used)
                if "bedrock-sdxl" in unique:
                    providers_summary += "+sdxl"
                if "openai-dalle3" in unique:
                    providers_summary += "+dalle3"
            
            result = {
                "sessionId": session_id,
                "recommendations": recommendations_with_images,
                "totalRecommendations": len(recommendations),
                "generatedImages": generated_count,
                "reasoning": bedrock_data.get('reasoning', ''),
                "confidence": bedrock_data.get('confidence', 0.8),
                "generatedBy": providers_summary,
                "industryInsights": {
                    "priorityFactors": industry_info.get("priority_factors", []),
                    "specialRequirements": industry_info.get("special_requirements", []),
                    "customerConsiderations": industry_info.get("customer_considerations", [])
                },
                "regionalTrends": {
                    "trendingStyles": regional_info.get("trending_styles", []),
                    "characteristics": regional_info.get("characteristics", []),
                    "customerPreferences": regional_info.get("customer_preferences", [])
                },
                "budgetGuidance": self._generate_budget_guidance(size_info, recommendations),
                "implementationGuide": self._generate_implementation_guide(size_info, recommendations),
                "nextSteps": [
                    "Choose one of the recommended styles",
                    "Review the detailed guide for the chosen style",
                    "Build an execution plan that fits your budget"
                ],
                "canProceed": len(recommendations) > 0,
                "latency_ms": response.get('latency_ms', 0)
            }
            
            self.logger.info(
                f"Bedrock interior recommendations generated: {len(recommendations)} styles, "
                f"{generated_count} images, confidence={result['confidence']:.2f}, latency={result['latency_ms']}ms"
            )
            return result
            
        except Exception as e:
            self.logger.error(f"Bedrock interior recommendation failed: {str(e)}, using fallback")
            return self._generate_interior_recommendations(session_id, business_info, selected_signboard)
    
    def _generate_interior_recommendations(
        self, session_id: str, business_info: BusinessInfo, 
        selected_signboard: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate interior recommendations (fallback)"""
        try:
            industry = business_info.industry.lower()
            region = business_info.region.lower()
            size = business_info.size.lower()
            
            industry_info = self.industry_characteristics.get(industry, self.industry_characteristics["retail"])
            regional_info = self.regional_trends.get(region, self.regional_trends["seoul"])
            size_info = self.size_considerations.get(size, self.size_considerations["medium"])
            
            recommended_styles = self._determine_recommended_styles(
                industry_info, regional_info, selected_signboard
            )
            
            recommendations: List[InteriorRecommendation] = []
            for style_name in recommended_styles[:3]:
                recommendation = self._create_style_recommendation(
                    style_name, business_info, industry_info, size_info, selected_signboard
                )
                recommendations.append(recommendation)
            
            interior_recommendations = InteriorRecommendations(recommendations=recommendations)
            self._save_interior_recommendations(session_id, interior_recommendations)
            
            return {
                "sessionId": session_id,
                "recommendations": [self._recommendation_to_dict(rec) for rec in recommendations],
                "totalRecommendations": len(recommendations),
                "industryInsights": {
                    "priorityFactors": industry_info["priority_factors"],
                    "specialRequirements": industry_info["special_requirements"],
                    "customerConsiderations": industry_info["customer_considerations"]
                },
                "regionalTrends": {
                    "trendingStyles": regional_info["trending_styles"],
                    "characteristics": regional_info["characteristics"],
                    "customerPreferences": regional_info["customer_preferences"]
                },
                "budgetGuidance": self._generate_budget_guidance(size_info, recommendations),
                "implementationGuide": self._generate_implementation_guide(size_info, recommendations),
                "nextSteps": [
                    "Choose one of the recommended styles",
                    "Review the detailed guide for the chosen style",
                    "Build an execution plan that fits your budget"
                ],
                "canProceed": len(recommendations) > 0
            }
        except Exception as e:
            self.logger.error(f"Failed to generate interior recommendations: {str(e)}")
            raise
    
    async def _generate_interior_recommendations_with_images(
        self, session_id: str, business_info: BusinessInfo, 
        selected_signboard: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate recommendations and images (async OpenAI path)"""
        try:
            text_recs = self._generate_interior_recommendations(session_id, business_info, selected_signboard)
            from shared.env_loader import get_openai_api_key
            api_key = get_openai_api_key()
            if not api_key:
                self.logger.warning("OpenAI API key not available, returning text-only recommendations")
                return text_recs
            
            business_name = getattr(business_info, 'name', None) or "Modern Restaurant"
            recommendations = text_recs.get('recommendations', [])
            enhanced = []
            
            import openai
            client = openai.AsyncOpenAI(api_key=api_key)
            
            for rec in recommendations:
                try:
                    style_name = rec.get('styleName', rec.get('style', 'modern'))
                    description = rec.get('description', '')
                    prompt = self._create_interior_prompt(business_name, business_info, style_name, description)
                    self.logger.info(f"Generating interior image for {style_name}")
                    resp = await client.images.generate(
                        model="dall-e-3",
                        prompt=prompt,
                        size="1024x1024",
                        quality="standard",
                        n=1
                    )
                    if resp.data:
                        image_url = resp.data[0].url
                        stored_url = await self._store_interior_image(image_url, business_name, style_name, session_id)
                        rec['imageUrl'] = stored_url or image_url
                        rec['isGenerated'] = True
                        rec['prompt'] = prompt
                    else:
                        rec['imageUrl'] = None
                        rec['isGenerated'] = False
                except Exception as img_error:
                    self.logger.error(f"Failed to generate image for {style_name}: {str(img_error)}")
                    rec['imageUrl'] = None
                    rec['isGenerated'] = False
                enhanced.append(rec)
            
            text_recs['recommendations'] = enhanced
            text_recs['generatedImages'] = sum(1 for r in enhanced if r.get('isGenerated'))
            return text_recs
        except Exception as e:
            self.logger.error(f"Error in interior image generation: {str(e)}")
            return self._generate_interior_recommendations(session_id, business_info, selected_signboard)
    
    def _create_interior_prompt(self, business_name: str, business_info: BusinessInfo, 
                                style_name: str, description: str) -> str:
        """Create an English image prompt for interiors"""
        industry = business_info.industry.lower()
        size = business_info.size.lower()
        
        style_keywords = {
            'modern': 'modern minimalist interior, clean lines, neutral colors, sleek furniture',
            'cozy': 'cozy warm interior, comfortable seating, wood elements, soft lighting',
            'industrial': 'industrial interior, exposed brick, metal fixtures, urban style',
            'scandinavian': 'scandinavian interior, light wood, white walls, natural lighting',
            'vintage': 'vintage interior, antique furniture, warm colors, classic elements'
        }
        industry_keywords = {
            'restaurant': 'restaurant dining area, tables and chairs, kitchen sightline optional',
            'cafe': 'cafe interior, coffee bar, comfortable seating area',
            'retail': 'retail store interior, product displays, shopping area',
            'service': 'service office interior, reception area, professional setting'
        }
        
        style_desc = style_keywords.get(style_name.lower(), 'modern interior design')
        industry_desc = industry_keywords.get(industry, 'commercial interior')
        
        prompt = f"""
Interior design for '{business_name}', a {industry} business.
{style_desc}, {industry_desc}.
Professional interior photography, realistic lighting, high quality,
{size} space, inviting atmosphere, well-designed layout,
architectural photography, wide-angle view
""".strip()
        return prompt
    
    async def _store_interior_image(self, image_url: str, business_name: str, 
                                    style: str, session_id: str) -> str:
        """Store generated image to S3/MinIO"""
        try:
            from shared.s3_client import get_s3_client
            import aiohttp, uuid
            s3_client = get_s3_client()
            if not s3_client:
                self.logger.warning("S3 client not available, returning original URL")
                return image_url
            
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        image_data = await resp.read()
                    else:
                        self.logger.error(f"Failed to download image: HTTP {resp.status}")
                        return image_url
            
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            key = f"interiors/{session_id}/{style}_{timestamp}_{unique_id}.png"
            
            metadata = {
                'business_name': business_name,
                'style': style,
                'session_id': session_id,
                'generated_by': 'openai-dalle3',
                'original_url': image_url
            }
            
            upload_result = s3_client.upload_file(
                file_content=image_data,
                key=key,
                content_type='image/png',
                metadata=metadata
            )
            if upload_result.get('success'):
                self.logger.info(f"Stored interior image: {key}")
                return upload_result.get('url')
            else:
                self.logger.error(f"Failed to upload interior image: {upload_result}")
                return image_url
        except Exception as e:
            self.logger.error(f"Error storing interior image: {str(e)}")
            return image_url
    
    def _generate_interior_recommendations_with_images_sync(
        self, session_id: str, business_info: BusinessInfo, 
        selected_signboard: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate recommendations and images (sync OpenAI path)"""
        try:
            text_recs = self._generate_interior_recommendations(session_id, business_info, selected_signboard)
            from shared.env_loader import get_openai_api_key
            api_key = get_openai_api_key()
            if not api_key:
                self.logger.warning("OpenAI API key not available, returning text-only recommendations")
                return text_recs
            
            business_name = getattr(business_info, 'name', None) or "Modern Restaurant"
            recommendations = text_recs.get('recommendations', [])
            enhanced = []
            
            import openai, requests, uuid
            client = openai.OpenAI(api_key=api_key)
            
            for rec in recommendations:
                try:
                    style_name = rec.get('styleName', rec.get('style', 'modern'))
                    description = rec.get('description', '')
                    prompt = self._create_interior_prompt(business_name, business_info, style_name, description)
                    self.logger.info(f"Generating interior image for {style_name}")
                    resp = client.images.generate(
                        model="dall-e-3",
                        prompt=prompt,
                        size="1024x1024",
                        quality="standard",
                        n=1
                    )
                    if resp.data:
                        image_url = resp.data[0].url
                        stored_url = self._store_interior_image_sync(image_url, business_name, style_name, session_id)
                        rec['imageUrl'] = stored_url or image_url
                        rec['isGenerated'] = True
                        rec['prompt'] = prompt
                    else:
                        rec['imageUrl'] = None
                        rec['isGenerated'] = False
                except Exception as img_error:
                    self.logger.error(f"Failed to generate image for {style_name}: {str(img_error)}")
                    rec['imageUrl'] = None
                    rec['isGenerated'] = False
                enhanced.append(rec)
            
            text_recs['recommendations'] = enhanced
            text_recs['generatedImages'] = sum(1 for r in enhanced if r.get('isGenerated'))
            return text_recs
        except Exception as e:
            self.logger.error(f"Error in interior image generation: {str(e)}")
            return self._generate_interior_recommendations(session_id, business_info, selected_signboard)
    
    def _store_interior_image_sync(self, image_url: str, business_name: str, 
                                   style: str, session_id: str) -> str:
        """Store generated image to S3/MinIO (sync)"""
        try:
            from shared.s3_client import get_s3_client
            import requests, uuid
            s3_client = get_s3_client()
            if not s3_client:
                self.logger.warning("S3 client not available, returning original URL")
                return image_url
            
            resp = requests.get(image_url, timeout=30)
            if resp.status_code == 200:
                image_data = resp.content
            else:
                self.logger.error(f"Failed to download image: HTTP {resp.status_code}")
                return image_url
            
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            key = f"interiors/{session_id}/{style}_{timestamp}_{unique_id}.png"
            
            metadata = {
                'business_name': business_name,
                'style': style,
                'session_id': session_id,
                'generated_by': 'openai-dalle3',
                'original_url': image_url
            }
            
            upload_result = s3_client.upload_file(
                file_content=image_data,
                key=key,
                content_type='image/png',
                metadata=metadata
            )
            if upload_result.get('success'):
                self.logger.info(f"Stored interior image: {key}")
                return upload_result.get('url')
            else:
                self.logger.error(f"Failed to upload interior image: {upload_result}")
                return image_url
        except Exception as e:
            self.logger.error(f"Error storing interior image: {str(e)}")
            return image_url
    
    def _determine_recommended_styles(
        self, industry_info: Dict[str, Any], 
        regional_info: Dict[str, Any], 
        selected_signboard: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Choose up to 3 styles based on industry, region, and signboard alignment"""
        industry_styles = set(industry_info["recommended_styles"])
        regional_styles = set(regional_info["trending_styles"])
        
        signboard_compatible_styles = set()
        if selected_signboard:
            signboard_style = selected_signboard.get('style', '').lower()
            if signboard_style == 'modern':
                signboard_compatible_styles = {'modern', 'scandinavian'}
            elif signboard_style == 'classic':
                signboard_compatible_styles = {'vintage', 'cozy'}
            elif signboard_style == 'vibrant':
                signboard_compatible_styles = {'industrial', 'cozy'}
        
        style_scores: Dict[str, int] = {}
        for style in self.interior_styles.keys():
            score = 0
            if style in industry_styles:
                score += 40
            elif style in industry_info.get("avoid_styles", []):
                score -= 20
            if style in regional_styles:
                score += 30
            if style in signboard_compatible_styles:
                score += 20
            popularity_scores = {
                'modern': 10, 'scandinavian': 9, 'cozy': 8, 
                'industrial': 6, 'vintage': 5
            }
            score += popularity_scores.get(style, 5)
            style_scores[style] = score
        
        sorted_styles = sorted(style_scores.items(), key=lambda x: x[1], reverse=True)
        return [style for style, _ in sorted_styles[:3]]
    
    def _create_style_recommendation(
        self, style_name: str, business_info: BusinessInfo,
        industry_info: Dict[str, Any], size_info: Dict[str, Any],
        selected_signboard: Optional[Dict[str, Any]] = None
    ) -> InteriorRecommendation:
        """Create a recommendation object for a given style"""
        style_data = self.interior_styles[style_name]
        suitability_score = self._calculate_suitability_score(
            style_name, business_info, industry_info, size_info
        )
        customized_pros = style_data["pros"].copy()
        customized_cons = style_data["cons"].copy()
        
        if business_info.size == "small":
            if style_name in ["modern", "scandinavian"]:
                customized_pros.append("Makes a small space feel larger")
            if style_name in ["industrial", "vintage"]:
                customized_cons.append("Can feel heavy in a compact space")
        
        return InteriorRecommendation(
            style=style_data["name"],
            description=style_data["description"],
            color_scheme=style_data["color_scheme"],
            materials=style_data["materials"],
            furniture=style_data["furniture"],
            estimated_cost=style_data["estimated_cost"],
            suitability_score=suitability_score,
            pros=customized_pros,
            cons=customized_cons
        )
    
    def _calculate_suitability_score(
        self, style_name: str, business_info: BusinessInfo,
        industry_info: Dict[str, Any], size_info: Dict[str, Any]
    ) -> float:
        """Compute suitability score (0–100)"""
        score = 50.0
        if style_name in industry_info["recommended_styles"]:
            score += 25
        elif style_name in industry_info.get("avoid_styles", []):
            score -= 20
        
        if business_info.size == "small":
            if style_name in ["modern", "scandinavian"]:
                score += 15
            elif style_name in ["industrial", "vintage"]:
                score -= 10
        elif business_info.size == "large":
            if style_name in ["industrial", "vintage"]:
                score += 10
        
        regional_info = self.regional_trends.get(business_info.region.lower(), {})
        if style_name in regional_info.get("trending_styles", []):
            score += 10
        
        return max(0, min(100, round(score, 1)))
    
    def _generate_budget_guidance(
        self, size_info: Dict[str, Any], 
        recommendations: List[InteriorRecommendation]
    ) -> Dict[str, Any]:
        """Create budget guidance (per m²)"""
        cost_estimates = {
            "Low": {"min": 300000, "max": 500000, "description": "Basic interior scope"},
            "Medium": {"min": 500000, "max": 800000, "description": "Mid-range interior scope"},
            "High": {"min": 800000, "max": 1200000, "description": "Premium interior scope"}
        }
        
        guidance = {
            "constraint_level": size_info.get("budget_constraint"),
            "recommendations_by_cost": {},
            "cost_saving_tips": size_info.get("cost_saving_tips", []),
            "investment_priorities": size_info.get("investment_priorities", []),
            "financing_options": self._generate_financing_options()
        }
        
        for rec in recommendations:
            cost_level = rec.estimated_cost
            if cost_level in cost_estimates:
                info = cost_estimates[cost_level]
                guidance["recommendations_by_cost"][rec.style] = {
                    "cost_level": cost_level,
                    "per_sqm_range": {
                        "min": info["min"],
                        "max": info["max"],
                        "description": info["description"]
                    }
                }
        return guidance
    
    def _generate_financing_options(self) -> Dict[str, Any]:
        """Funding options guidance"""
        return {
            "payment_methods": {
                "lump_sum": {
                    "name": "Lump-sum payment",
                    "pros": ["Lower total cost", "Faster completion", "Potential vendor discounts"],
                    "cons": ["High upfront burden", "Cash-flow pressure"],
                    "recommended_for": ["Sufficient cash on hand", "Need to open quickly"]
                },
                "installment": {
                    "name": "Installments by phase",
                    "pros": ["Cash-flow friendly", "Quality checks per phase", "Risk distribution"],
                    "cons": ["Higher total cost", "More management overhead"],
                    "recommended_for": ["Limited cash", "Prefer staged progress"]
                }
            },
            "funding_sources": [
                "Government start-up grants",
                "SMB loans",
                "Interior-focused renovation loans",
                "Credit card 0% installment plans"
            ]
        }
    
    def _generate_implementation_guide(
        self, size_info: Dict[str, Any], 
        recommendations: List[InteriorRecommendation]
    ) -> Dict[str, Any]:
        """Step-by-step implementation guide"""
        return {
            "step_by_step_process": {
                "1": {
                    "title": "Select style & lock concept",
                    "duration": "1–2 days",
                    "activities": [
                        "Pick the final style",
                        "Decide detailed concept & theme",
                        "Collect reference images",
                        "Set priorities"
                    ]
                },
                "2": {
                    "title": "Plan budget & prepare funds",
                    "duration": "3–5 days",
                    "activities": [
                        "Draft a detailed budget plan",
                        "Decide funding method",
                        "Secure contingency reserve",
                        "Plan payment schedule"
                    ]
                },
                "3": {
                    "title": "Select contractor & sign",
                    "duration": "~1 week",
                    "activities": [
                        "Research interior contractors",
                        "Compare quotes & negotiate",
                        "Review portfolios",
                        "Draft & sign the contract"
                    ]
                }
            },
            "success_factors": [
                "Clear concept and goals",
                "Sufficient pre-planning",
                "Reliable contractor selection",
                "Active communication & oversight"
            ]
        }
    
    def _save_interior_recommendations(
        self, session_id: str, interior_recommendations: InteriorRecommendations
    ) -> None:
        """Persist recommendations in the session (legacy compatibility)"""
        try:
            from decimal import Decimal
            def decimal_to_float(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                if isinstance(obj, dict):
                    return {k: decimal_to_float(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [decimal_to_float(i) for i in obj]
                return obj
            
            recommendations_data = {
                "recommendations": [self._recommendation_to_dict(rec) for rec in interior_recommendations.recommendations]
            }
            recommendations_data = decimal_to_float(recommendations_data)
            updates = {"interior_recommendations": json.dumps(recommendations_data)}
            success = self.update_session_data(session_id, updates)
            if not success:
                raise Exception("Failed to update session data")
        except Exception as e:
            self.logger.error(f"Failed to save interior recommendations: {str(e)}")
            raise
    
    def _save_interior_to_dynamodb(
        self, session_id: str, recommendations: List[Dict[str, Any]]
    ) -> None:
        """Save interior recommendations to DynamoDB as Map type (not JSON string)"""
        try:
            from decimal import Decimal
            def float_to_decimal(obj):
                if isinstance(obj, float):
                    return Decimal(str(obj))
                if isinstance(obj, dict):
                    return {k: float_to_decimal(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [float_to_decimal(i) for i in obj]
                return obj
            
            recommendations_clean = float_to_decimal(recommendations)
            updates = {
                "interiors": recommendations_clean,
                "interiorGenerationStatus": "completed",
                "interiorGenerationCompletedAt": datetime.utcnow().isoformat()
            }
            self.logger.info(f"Saving interior data to DynamoDB: {len(recommendations_clean)} recommendations")
            success = self.update_session_data(session_id, updates)
            if not success:
                raise Exception("Failed to update session data in DynamoDB")
            self.logger.info(f"✅ Successfully saved {len(recommendations_clean)} interiors to DynamoDB as Map type")
        except Exception as e:
            self.logger.error(f"❌ Failed to save interior data to DynamoDB: {str(e)}")
    
    def _upload_image_to_s3(self, image_url: str, s3_key: str) -> Optional[str]:
        """Upload an image to S3 and return a presigned URL"""
        try:
            import requests, boto3
            resp = requests.get(image_url, timeout=30)
            resp.raise_for_status()
            image_data = resp.content
            
            s3 = boto3.client('s3')
            bucket = os.getenv('S3_BUCKET_NAME', 'ai-branding-chatbot-assets-908601828278')
            s3.put_object(Bucket=bucket, Key=s3_key, Body=image_data, ContentType='image/png')
            url = s3.generate_presigned_url(
                'get_object', Params={'Bucket': bucket, 'Key': s3_key}, ExpiresIn=604800
            )
            self.logger.info(f"Image uploaded to S3: {url}")
            return url
        except Exception as e:
            self.logger.error(f"Failed to upload image to S3: {str(e)}")
            return None
    
    def _create_interior_image_prompt(
        self, style: str, industry: str, colors: List[str], materials: List[str]
    ) -> str:
        """Create an English prompt for image generation"""
        style_keywords = {
            'modern': 'sleek, minimalist, contemporary',
            'cozy': 'warm, comfortable, inviting',
            'industrial': 'raw, urban, edgy',
            'classic': 'elegant, timeless, refined',
            'scandinavian': 'bright, airy, natural'
        }
        style_desc = style_keywords.get(style.lower(), 'stylish, professional')
        
        industry_keywords = {
            'restaurant': 'dining area, tables and chairs, welcoming atmosphere',
            'cafe': 'coffee shop, cozy seating, relaxed ambiance',
            'retail': 'store interior, display shelves, shopping space',
            'office': 'workspace, desks, professional environment'
        }
        industry_desc = industry_keywords.get(industry.lower(), 'commercial space')
        
        color_desc = ', '.join(colors[:3]) if colors else 'neutral tones'
        material_desc = ', '.join(materials[:3]) if materials else 'modern materials'
        
        prompt = f"""Professional interior design photograph of a {style} style {industry} space.

{style_desc}, {industry_desc}.

Color palette: {color_desc}
Materials: {material_desc}

High-quality, realistic, well-lit, architectural digest style,
wide-angle view, 8k resolution, no people, clean and organized space"""
        return prompt
    
    def _recommendation_to_dict(self, recommendation: InteriorRecommendation) -> Dict[str, Any]:
        """Convert InteriorRecommendation to dict"""
        return {
            "style": recommendation.style,
            "description": recommendation.description,
            "colorScheme": recommendation.color_scheme,
            "materials": recommendation.materials,
            "furniture": recommendation.furniture,
            "estimatedCost": recommendation.estimated_cost,
            "suitabilityScore": recommendation.suitability_score,
            "pros": recommendation.pros,
            "cons": recommendation.cons,
            "generatedAt": recommendation.generated_at
        }


# Lambda handler
def lambda_handler(event, context):
    """Lambda entrypoint"""
    agent = InteriorAgent()
    return agent.lambda_handler(event, context)
