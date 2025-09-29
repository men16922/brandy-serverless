"""
Signboard Agent - OpenAI DALL-E 연동 간판 이미지 생성
"""

import json
import sys
import os
import time
import base64
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import aiohttp

# Add shared modules to path
sys.path.append('/opt/python')

try:
    from shared.base_agent import BaseAgent
    from shared.models import AgentType, ImageResult, SignboardImages, BusinessInfo
    from shared.utils import create_response
    from shared.env_loader import get_openai_api_key, is_local_environment
    from shared.s3_client import get_s3_client
except ImportError:
    # For testing purposes, create mock implementations
    from datetime import datetime
    from typing import Dict, Any, List
    from enum import Enum
    import time
    
    class AgentType(Enum):
        SIGNBOARD = "signboard"
    
    class ImageResult:
        def __init__(self, url: str, provider: str, style: str, prompt: str, 
                     metadata: Dict[str, Any] = None, is_fallback: bool = False):
            self.url = url
            self.provider = provider
            self.style = style
            self.prompt = prompt
            self.metadata = metadata or {}
            self.generated_at = datetime.utcnow().isoformat()
            self.is_fallback = is_fallback
        
        def validate(self) -> bool:
            return bool(self.url and self.provider and self.style and self.prompt)
    
    class SignboardImages:
        def __init__(self, images: List[ImageResult] = None, selected_image_url: str = None):
            self.images = images or []
            self.selected_image_url = selected_image_url
        
        def validate(self) -> bool:
            return len(self.images) <= 3 and all(img.validate() for img in self.images)
    
    class BusinessInfo:
        def __init__(self, industry: str, region: str, size: str, **kwargs):
            self.industry = industry
            self.region = region
            self.size = size
    
    class BaseAgent:
        def __init__(self, agent_type):
            self.agent_type = agent_type
            self.agent_name = agent_type.value
            self.logger = self._create_mock_logger()
            self.aws_clients = self._create_mock_aws_clients()
            self.config = {'s3_bucket': 'test-bucket'}
        
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
        
        def _create_mock_aws_clients(self):
            class MockS3:
                def put_object(self, **kwargs):
                    return {'ETag': 'mock-etag'}
                def generate_presigned_url(self, operation, Params, ExpiresIn):
                    return f"https://mock-s3-url/{Params['Key']}"
            
            return {'s3': MockS3()}
        
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
        
        def update_session_data(self, session_id: str, updates: Dict[str, Any]):
            return True
        
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


class OpenAIClient:
    """OpenAI API 클라이언트 (AWS Secrets Manager 연동)"""
    
    def __init__(self, api_key: str = None):
        self.base_url = "https://api.openai.com/v1"
        self.timeout = 30  # 30초 타임아웃
        self.max_retries = 3  # 최대 재시도 횟수
        self.retry_delay = 1  # 재시도 간격 (초)
        
        # API 키 획득 (우선순위: 파라미터 > 환경변수 > Secrets Manager)
        self.api_key = api_key or self._get_api_key()
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
    
    def _get_api_key(self) -> str:
        """API 키 획득 (환경변수 또는 AWS Secrets Manager)"""
        # 1. 환경변수에서 확인 (env_loader 사용)
        try:
            api_key = get_openai_api_key()
            if api_key:
                return api_key
        except:
            # 폴백: 직접 환경변수 확인
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                return api_key
        
        # 2. AWS Secrets Manager에서 확인
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            secret_name = os.getenv('OPENAI_SECRET_NAME', 'openai-api-key')
            region = os.getenv('AWS_REGION', 'us-east-1')
            
            # Secrets Manager 클라이언트 생성
            if os.getenv('ENVIRONMENT') == 'local':
                # 로컬 환경에서는 환경변수만 사용
                return None
            
            session = boto3.session.Session()
            client = session.client(service_name='secretsmanager', region_name=region)
            
            response = client.get_secret_value(SecretId=secret_name)
            secret = json.loads(response['SecretString'])
            
            return secret.get('api_key') or secret.get('OPENAI_API_KEY')
            
        except Exception as e:
            print(f"Failed to get API key from Secrets Manager: {e}")
            return None
    
    async def generate_image(self, prompt: str, size: str = "1024x1024", 
                           quality: str = "standard", style: str = "vivid") -> Dict[str, Any]:
        """DALL-E 이미지 생성 (재시도 메커니즘 포함)"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AI-Branding-Chatbot/1.0"
        }
        
        payload = {
            "model": "dall-e-3",
            "prompt": self._optimize_prompt(prompt),
            "n": 1,
            "size": size,
            "quality": quality,
            "style": style,
            "response_format": "url"
        }
        
        # 재시도 로직
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    connector=aiohttp.TCPConnector(limit=10)
                ) as session:
                    async with session.post(
                        f"{self.base_url}/images/generations",
                        headers=headers,
                        json=payload
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "success": True,
                                "image_url": result["data"][0]["url"],
                                "revised_prompt": result["data"][0].get("revised_prompt", prompt),
                                "attempt": attempt + 1
                            }
                        elif response.status == 429:  # Rate limit
                            error_text = await response.text()
                            if attempt < self.max_retries - 1:
                                wait_time = self.retry_delay * (2 ** attempt)  # 지수 백오프
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                return {
                                    "success": False,
                                    "error": f"Rate limit exceeded after {self.max_retries} attempts: {error_text}",
                                    "error_type": "rate_limit"
                                }
                        elif response.status == 400:  # Bad request (프롬프트 문제)
                            error_text = await response.text()
                            return {
                                "success": False,
                                "error": f"Invalid prompt: {error_text}",
                                "error_type": "invalid_prompt"
                            }
                        elif response.status >= 500:  # Server error
                            error_text = await response.text()
                            if attempt < self.max_retries - 1:
                                wait_time = self.retry_delay * (2 ** attempt)
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                return {
                                    "success": False,
                                    "error": f"Server error after {self.max_retries} attempts: {error_text}",
                                    "error_type": "server_error"
                                }
                        else:
                            error_text = await response.text()
                            return {
                                "success": False,
                                "error": f"OpenAI API error: {response.status} - {error_text}",
                                "error_type": "api_error"
                            }
                            
            except asyncio.TimeoutError:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    return {
                        "success": False,
                        "error": f"Request timeout after {self.max_retries} attempts",
                        "error_type": "timeout"
                    }
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    return {
                        "success": False,
                        "error": f"Network error after {self.max_retries} attempts: {str(e)}",
                        "error_type": "network_error"
                    }
        
        return {
            "success": False,
            "error": "Max retries exceeded",
            "error_type": "max_retries"
        }
    
    def _optimize_prompt(self, prompt: str) -> str:
        """프롬프트 최적화 (DALL-E 3 제약사항 고려)"""
        # 1. 길이 제한 (4000자)
        if len(prompt) > 3500:  # 여유분 고려
            prompt = prompt[:3500] + "..."
        
        # 2. 금지된 키워드 필터링
        forbidden_keywords = [
            "realistic person", "celebrity", "politician", "copyrighted character",
            "brand logo", "trademark", "specific company name"
        ]
        
        for keyword in forbidden_keywords:
            if keyword.lower() in prompt.lower():
                prompt = prompt.replace(keyword, "generic design")
        
        # 3. 안전성 키워드 추가
        safety_keywords = [
            "professional", "appropriate", "business-suitable", "family-friendly"
        ]
        
        # 이미 포함되지 않은 경우에만 추가
        if not any(keyword in prompt.lower() for keyword in safety_keywords):
            prompt += ", professional and appropriate design"
        
        return prompt


class SignboardAgent(BaseAgent):
    """Signboard Agent - 간판 이미지 생성"""
    
    def __init__(self):
        super().__init__(AgentType.SIGNBOARD)
        
        # OpenAI 클라이언트 초기화
        try:
            self.openai_client = OpenAIClient()
        except ValueError as e:
            self.logger.warning(f"OpenAI client initialization failed: {e}")
            self.openai_client = None
        
        # S3/MinIO 클라이언트 초기화
        try:
            self.s3_client = get_s3_client()
        except Exception as e:
            self.logger.warning(f"S3 client initialization failed: {e}")
            self.s3_client = None
        
        # 간판 스타일 정의
        self.signboard_styles = {
            "modern": {
                "description": "모던하고 세련된 스타일",
                "keywords": ["modern", "sleek", "minimalist", "contemporary", "clean lines"],
                "colors": ["white", "black", "gray", "blue", "silver"]
            },
            "classic": {
                "description": "전통적이고 클래식한 스타일",
                "keywords": ["classic", "traditional", "elegant", "vintage", "timeless"],
                "colors": ["gold", "brown", "cream", "burgundy", "forest green"]
            },
            "vibrant": {
                "description": "활기차고 눈에 띄는 스타일",
                "keywords": ["vibrant", "colorful", "energetic", "bold", "eye-catching"],
                "colors": ["red", "orange", "yellow", "bright blue", "purple"]
            }
        }
        
        # 업종별 간판 특성
        self.industry_characteristics = {
            "restaurant": {
                "elements": ["food", "dining", "kitchen", "chef hat", "utensils"],
                "mood": "welcoming and appetizing",
                "preferred_styles": ["classic", "vibrant"]
            },
            "retail": {
                "elements": ["shopping bag", "storefront", "display", "products"],
                "mood": "inviting and trustworthy",
                "preferred_styles": ["modern", "classic"]
            },
            "service": {
                "elements": ["professional", "office", "consultation", "expertise"],
                "mood": "professional and reliable",
                "preferred_styles": ["modern", "classic"]
            },
            "healthcare": {
                "elements": ["medical cross", "health", "care", "wellness"],
                "mood": "clean and trustworthy",
                "preferred_styles": ["modern"]
            },
            "education": {
                "elements": ["books", "learning", "graduation cap", "knowledge"],
                "mood": "inspiring and academic",
                "preferred_styles": ["classic", "modern"]
            },
            "technology": {
                "elements": ["digital", "innovation", "circuits", "future"],
                "mood": "cutting-edge and innovative",
                "preferred_styles": ["modern"]
            }
        }
        
        # 폴백 이미지 설정
        self.fallback_images = self._initialize_fallback_images()
    
    def _initialize_fallback_images(self) -> Dict[str, str]:
        """폴백 이미지 URL 초기화"""
        # 환경별 폴백 이미지 URL 설정
        base_url = os.getenv('FALLBACK_IMAGES_BASE_URL', 'https://example.com/fallback')
        
        return {
            "modern": f"{base_url}/modern-signboard.png",
            "classic": f"{base_url}/classic-signboard.png",
            "vibrant": f"{base_url}/vibrant-signboard.png"
        }
    
    def execute(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Signboard Agent 실행 로직"""
        try:
            # 요청 파싱
            if isinstance(event.get('body'), str):
                body = json.loads(event['body'])
            else:
                body = event.get('body', event)
            
            session_id = body.get('sessionId')
            selected_name = body.get('selectedName')
            business_info_data = body.get('businessInfo', {})
            action = body.get('action', 'generate')
            
            if not all([session_id, selected_name]):
                return self.create_lambda_response(400, {
                    "error": "sessionId and selectedName are required"
                })
            
            # 실행 시작
            self.start_execution(session_id, "signboard.generate")
            
            # 비즈니스 정보 파싱
            if isinstance(business_info_data, str):
                business_info_data = json.loads(business_info_data)
            
            business_info = BusinessInfo(**business_info_data)
            
            # 간판 이미지 생성
            if action == 'generate':
                result = self._generate_signboard_images(session_id, selected_name, business_info)
            elif action == 'select':
                selected_image_url = body.get('selectedImageUrl')
                result = self._handle_image_selection(session_id, selected_image_url)
            else:
                raise ValueError(f"Unknown action: {action}")
            
            # 실행 완료
            self.end_execution("success", result=result)
            
            return self.create_lambda_response(200, result)
            
        except Exception as e:
            error_message = f"Signboard Agent execution failed: {str(e)}"
            self.end_execution("error", error_message)
            
            error_response = self.handle_error(e, "execute")
            return self.create_lambda_response(500, error_response)
    
    def _generate_signboard_images(self, session_id: str, selected_name: str, 
                                 business_info: BusinessInfo) -> Dict[str, Any]:
        """간판 이미지 생성"""
        try:
            # 업종별 선호 스타일 결정
            industry = business_info.industry.lower()
            industry_info = self.industry_characteristics.get(industry, self.industry_characteristics["retail"])
            preferred_styles = industry_info["preferred_styles"]
            
            # 3가지 스타일로 생성 (선호 스타일 우선)
            styles_to_generate = []
            for style in preferred_styles:
                if style not in styles_to_generate:
                    styles_to_generate.append(style)
            
            # 부족한 경우 다른 스타일 추가
            all_styles = list(self.signboard_styles.keys())
            for style in all_styles:
                if len(styles_to_generate) >= 3:
                    break
                if style not in styles_to_generate:
                    styles_to_generate.append(style)
            
            # 최대 3개 스타일
            styles_to_generate = styles_to_generate[:3]
            
            # 비동기로 이미지 생성
            try:
                # 현재 이벤트 루프가 있는지 확인
                try:
                    loop = asyncio.get_running_loop()
                    # 이미 실행 중인 루프가 있으면 태스크로 실행
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self._generate_images_async(session_id, selected_name, business_info, styles_to_generate)
                        )
                        images = future.result(timeout=60)  # 60초 타임아웃
                except RuntimeError:
                    # 실행 중인 루프가 없으면 새로 생성
                    images = asyncio.run(
                        self._generate_images_async(session_id, selected_name, business_info, styles_to_generate)
                    )
            except Exception as async_error:
                self.logger.error(f"Async image generation failed: {str(async_error)}")
                raise async_error
            
            # SignboardImages 객체 생성
            signboard_images = SignboardImages(images=images)
            
            # 세션에 저장
            self._save_signboard_images(session_id, signboard_images)
            
            return {
                "sessionId": session_id,
                "signboards": [self._image_result_to_dict(img) for img in images],
                "totalGenerated": len(images),
                "canProceed": len(images) > 0,
                "message": f"{len(images)}개의 간판 디자인이 생성되었습니다."
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate signboard images: {str(e)}")
            
            # 폴백 이미지 사용
            fallback_images = self._create_fallback_images(session_id, selected_name, business_info)
            
            return {
                "sessionId": session_id,
                "signboards": [self._image_result_to_dict(img) for img in fallback_images],
                "totalGenerated": len(fallback_images),
                "canProceed": True,
                "isFallback": True,
                "message": "AI 이미지 생성에 실패하여 기본 템플릿을 제공합니다."
            }
    
    async def _generate_images_async(self, session_id: str, selected_name: str, 
                                   business_info: BusinessInfo, styles: List[str]) -> List[ImageResult]:
        """비동기 이미지 생성"""
        tasks = []
        
        for style in styles:
            task = self._generate_single_image(session_id, selected_name, business_info, style)
            tasks.append(task)
        
        # 모든 이미지를 병렬로 생성 (최대 30초 타임아웃)
        try:
            results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=30.0)
        except asyncio.TimeoutError:
            self.logger.warning("Image generation timed out after 30 seconds")
            results = [None] * len(tasks)
        
        # 성공한 결과만 반환
        images = []
        for i, result in enumerate(results):
            if isinstance(result, ImageResult):
                images.append(result)
            else:
                # 실패한 경우 폴백 이미지 생성
                style = styles[i]
                fallback_image = self._create_single_fallback_image(session_id, selected_name, business_info, style)
                images.append(fallback_image)
        
        return images
    
    async def _generate_single_image(self, session_id: str, selected_name: str, 
                                   business_info: BusinessInfo, style: str) -> ImageResult:
        """단일 이미지 생성"""
        try:
            # 프롬프트 생성
            prompt = self._create_image_prompt(selected_name, business_info, style)
            
            # OpenAI API 호출
            if self.openai_client:
                result = await self.openai_client.generate_image(
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    style="vivid"
                )
                
                if result["success"]:
                    # 이미지 다운로드 및 S3 업로드
                    s3_url = await self._download_and_upload_image(
                        result["image_url"], session_id, style
                    )
                    
                    return ImageResult(
                        url=s3_url,
                        provider="dalle",
                        style=style,
                        prompt=result.get("revised_prompt", prompt),
                        metadata={
                            "original_prompt": prompt,
                            "generation_time": datetime.utcnow().isoformat(),
                            "business_name": selected_name,
                            "industry": business_info.industry
                        }
                    )
                else:
                    raise Exception(result["error"])
            else:
                raise Exception("OpenAI client not available")
                
        except Exception as e:
            self.logger.error(f"Failed to generate {style} image: {str(e)}")
            # 폴백 이미지 반환
            return self._create_single_fallback_image(session_id, selected_name, business_info, style)
    
    def _create_image_prompt(self, business_name: str, business_info: BusinessInfo, style: str) -> str:
        """이미지 생성 프롬프트 생성"""
        industry = business_info.industry.lower()
        region = business_info.region
        
        # 기본 프롬프트 구조
        base_prompt = f"A professional business signboard for '{business_name}'"
        
        # 업종별 특성 추가
        industry_info = self.industry_characteristics.get(industry, self.industry_characteristics["retail"])
        industry_elements = ", ".join(industry_info["elements"][:2])  # 처음 2개 요소만
        mood = industry_info["mood"]
        
        # 스타일별 특성 추가
        style_info = self.signboard_styles[style]
        style_keywords = ", ".join(style_info["keywords"][:3])  # 처음 3개 키워드만
        style_colors = ", ".join(style_info["colors"][:2])  # 처음 2개 색상만
        
        # 영어 번역 추가로 텍스트 표시 개선
        english_name = self._translate_to_english(business_name)
        
        # 최종 프롬프트 조합 (텍스트 표시 강조)
        prompt = (
            f"Restaurant storefront with a large signboard that clearly shows the text '{english_name}' "
            f"in bold, readable letters. {style_keywords} design style, "
            f"incorporating {industry_elements}, {mood} atmosphere, "
            f"using {style_colors} color scheme. "
            f"The signboard must prominently display '{english_name}' as the main text. "
            f"High quality typography, professional restaurant signage, "
            f"storefront exterior view, realistic lighting, commercial signage, "
            f"the business name '{english_name}' should be the focal point of the sign"
        )
        
        # 프롬프트 로깅 (디버깅용)
        self.logger.info(f"Generated prompt for {business_name}: {prompt[:200]}...")
        
        # 프롬프트 길이 제한 (DALL-E 3 제한: 4000자)
        if len(prompt) > 1000:
            prompt = prompt[:1000] + "..."
        
        return prompt
    
    def _translate_to_english(self, korean_name: str) -> str:
        """한국어 상호명을 영어로 간단 번역"""
        # 간단한 번역 매핑 (실제로는 더 정교한 번역 서비스 사용 가능)
        translations = {
            '좋은키친': 'Good Kitchen',
            '서울집': 'Seoul House',
            '명동하우스': 'Myeongdong House',
            '365테이블': '365 Table',
            '1번키친': 'Number 1 Kitchen',
            'Royal원': 'Royal Garden',
            'Neo키친': 'Neo Kitchen',
            '루비집': 'Ruby House',
            '예쁜향': 'Pretty Scent',
            '유니크맛': 'Unique Taste',
            '더 플레이스': 'The Place',
            '어반 스페이스': 'Urban Space',
            '코지 코너': 'Cozy Corner',
            '모던 키친': 'Modern Kitchen',
            '모던 테이블': 'Modern Table',
            '클래식향': 'Classic Scent',
            '좋은맛': 'Good Taste',
            '24시테이블': '24H Table'
        }
        
        # 매핑에 있으면 사용, 없으면 간단한 변환
        if korean_name in translations:
            return translations[korean_name]
        
        # 기본 변환 로직
        if '키친' in korean_name:
            base = korean_name.replace('키친', '').strip()
            return f"{base} Kitchen"
        elif '하우스' in korean_name or '집' in korean_name:
            base = korean_name.replace('하우스', '').replace('집', '').strip()
            return f"{base} House"
        elif '테이블' in korean_name:
            base = korean_name.replace('테이블', '').strip()
            return f"{base} Table"
        elif '가든' in korean_name:
            base = korean_name.replace('가든', '').strip()
            return f"{base} Garden"
        elif '원' in korean_name:
            base = korean_name.replace('원', '').strip()
            return f"{base} Garden"
        else:
            # 간단한 음성 변환
            simple_translations = {
                '위너': 'Winner',
                '다이아': 'Diamond', 
                '빠른': 'Quick',
                '좋은': 'Good',
                '예쁜': 'Pretty',
                '클래식': 'Classic',
                '모던': 'Modern'
            }
            
            for korean, english in simple_translations.items():
                if korean in korean_name:
                    return korean_name.replace(korean, english)
            
            # 그냥 로마자 표기
            return korean_name
    
    async def _download_and_upload_image(self, image_url: str, session_id: str, style: str) -> str:
        """이미지 다운로드 및 S3/MinIO 업로드"""
        try:
            if not self.s3_client:
                self.logger.warning("S3 client not available, returning original URL")
                return image_url
            
            # 이미지 다운로드
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        content_type = response.headers.get('content-type', 'image/png')
                    else:
                        self.logger.error(f"Failed to download image: HTTP {response.status}")
                        return image_url
            
            # S3 키 생성
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            s3_key = f"signboards/{session_id}/{style}_{timestamp}_{unique_id}.png"
            
            # 메타데이터 준비
            metadata = {
                'session_id': session_id,
                'style': style,
                'generated_by': 'openai-dalle3',
                'original_url': image_url
            }
            
            # S3/MinIO에 업로드
            upload_result = self.s3_client.upload_file(
                file_content=image_data,
                key=s3_key,
                content_type=content_type,
                metadata=metadata
            )
            
            if upload_result.get('success'):
                stored_url = upload_result.get('url')
                self.logger.info(f"Successfully stored image: {s3_key}")
                return stored_url
            else:
                self.logger.error(f"Failed to store image: {upload_result.get('error')}")
                return image_url
                
        except Exception as e:
            self.logger.error(f"Error downloading and storing image: {str(e)}")
            return image_url
    

    
    def _create_fallback_images(self, session_id: str, selected_name: str, 
                              business_info: BusinessInfo) -> List[ImageResult]:
        """폴백 이미지 생성"""
        fallback_images = []
        
        for style in ["modern", "classic", "vibrant"]:
            fallback_image = self._create_single_fallback_image(session_id, selected_name, business_info, style)
            fallback_images.append(fallback_image)
        
        return fallback_images
    
    def _create_single_fallback_image(self, session_id: str, selected_name: str, 
                                    business_info: BusinessInfo, style: str) -> ImageResult:
        """단일 폴백 이미지 생성"""
        fallback_url = self.fallback_images.get(style, "https://example.com/fallback.png")
        
        return ImageResult(
            url=fallback_url,
            provider="fallback",
            style=style,
            prompt=f"Fallback signboard for {selected_name} in {style} style",
            metadata={
                "is_fallback": True,
                "business_name": selected_name,
                "industry": business_info.industry,
                "generated_at": datetime.utcnow().isoformat()
            },
            is_fallback=True
        )
    
    def _handle_image_selection(self, session_id: str, selected_image_url: str) -> Dict[str, Any]:
        """이미지 선택 처리"""
        if not selected_image_url:
            raise ValueError("Selected image URL is required")
        
        # 세션 데이터 업데이트
        updates = {
            "signboard_images": json.dumps({
                "selected_image_url": selected_image_url
            }),
            "currentStep": 4  # Interior step으로 진행
        }
        
        success = self.update_session_data(session_id, updates)
        if not success:
            raise Exception("Failed to update session data")
        
        return {
            "sessionId": session_id,
            "selectedImageUrl": selected_image_url,
            "message": "간판 이미지가 선택되었습니다.",
            "nextStep": "interior",
            "canProceed": True
        }
    
    def _save_signboard_images(self, session_id: str, signboard_images: SignboardImages) -> None:
        """SignboardImages를 세션에 저장"""
        try:
            signboard_data = {
                "images": [self._image_result_to_dict(img) for img in signboard_images.images],
                "selected_image_url": signboard_images.selected_image_url
            }
            
            updates = {
                "signboard_images": json.dumps(signboard_data)
            }
            
            success = self.update_session_data(session_id, updates)
            if not success:
                raise Exception("Failed to update session data")
                
        except Exception as e:
            self.logger.error(f"Failed to save signboard images: {str(e)}")
            raise
    
    def _image_result_to_dict(self, image_result: ImageResult) -> Dict[str, Any]:
        """ImageResult를 딕셔너리로 변환"""
        return {
            "url": image_result.url,
            "provider": image_result.provider,
            "style": image_result.style,
            "prompt": image_result.prompt,
            "metadata": image_result.metadata,
            "generatedAt": image_result.generated_at,
            "isFallback": image_result.is_fallback
        }


# Lambda 핸들러
def lambda_handler(event, context):
    """Lambda 핸들러 함수"""
    agent = SignboardAgent()
    return agent.lambda_handler(event, context)