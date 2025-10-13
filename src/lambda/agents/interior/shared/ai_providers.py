"""
AI Provider 추상화 계층
다양한 AI 모델을 통일된 인터페이스로 관리
"""

import json
import asyncio
import aiohttp
import boto3
import base64
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import uuid

from .models import ImageResult


class AIProvider(ABC):
    """AI Provider 추상 인터페이스"""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 1
    
    @abstractmethod
    async def generate_image(self, prompt: str, style: str = "default", **kwargs) -> ImageResult:
        """이미지 생성 추상 메서드"""
        pass
    
    def _create_image_result(self, url: str, style: str, prompt: str, 
                           metadata: Dict[str, Any] = None, is_fallback: bool = False) -> ImageResult:
        """ImageResult 객체 생성 헬퍼"""
        return ImageResult(
            url=url,
            provider=self.provider_name,
            style=style,
            prompt=prompt,
            metadata=metadata or {},
            is_fallback=is_fallback
        )


class DALLEProvider(AIProvider):
    """OpenAI DALL-E Provider"""
    
    def __init__(self, api_key: str = None):
        super().__init__("dalle")
        self.base_url = "https://api.openai.com/v1"
        self.api_key = api_key or self._get_api_key()
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
    
    def _get_api_key(self) -> str:
        """API 키 획득"""
        # 환경변수에서 확인
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            return api_key
        
        # AWS Secrets Manager에서 확인 (프로덕션 환경)
        if os.getenv('ENVIRONMENT') != 'local':
            try:
                secret_name = os.getenv('OPENAI_SECRET_NAME', 'openai-api-key')
                region = os.getenv('AWS_REGION', 'us-east-1')
                
                session = boto3.session.Session()
                client = session.client(service_name='secretsmanager', region_name=region)
                
                response = client.get_secret_value(SecretId=secret_name)
                secret = json.loads(response['SecretString'])
                
                return secret.get('api_key') or secret.get('OPENAI_API_KEY')
            except Exception:
                pass
        
        return None
    
    async def generate_image(self, prompt: str, style: str = "default", **kwargs) -> ImageResult:
        """DALL-E 이미지 생성"""
        
        # 로컬 환경에서는 Mock 이미지 생성
        if os.getenv('ENVIRONMENT') == 'local':
            return await self._generate_mock_image(prompt, style, **kwargs)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AI-Branding-Chatbot/1.0"
        }
        
        payload = {
            "model": "dall-e-3",
            "prompt": self._optimize_prompt(prompt),
            "n": 1,
            "size": kwargs.get("size", "1024x1024"),
            "quality": kwargs.get("quality", "standard"),
            "style": kwargs.get("dalle_style", "vivid"),
            "response_format": "url"
        }
        
        # 재시도 로직
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as session:
                    async with session.post(
                        f"{self.base_url}/images/generations",
                        headers=headers,
                        json=payload
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            return self._create_image_result(
                                url=result["data"][0]["url"],
                                style=style,
                                prompt=result["data"][0].get("revised_prompt", prompt),
                                metadata={
                                    "original_prompt": prompt,
                                    "generation_time": datetime.utcnow().isoformat(),
                                    "attempt": attempt + 1,
                                    "model": "dall-e-3"
                                }
                            )
                        elif response.status == 429:  # Rate limit
                            if attempt < self.max_retries - 1:
                                wait_time = self.retry_delay * (2 ** attempt)
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                raise Exception(f"Rate limit exceeded after {self.max_retries} attempts")
                        elif response.status >= 500:  # Server error
                            if attempt < self.max_retries - 1:
                                wait_time = self.retry_delay * (2 ** attempt)
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                error_text = await response.text()
                                raise Exception(f"Server error: {error_text}")
                        else:
                            error_text = await response.text()
                            raise Exception(f"API error: {response.status} - {error_text}")
                            
            except asyncio.TimeoutError:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise Exception(f"Request timeout after {self.max_retries} attempts")
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise e
    
    def _optimize_prompt(self, prompt: str) -> str:
        """DALL-E 프롬프트 최적화"""
        # 길이 제한 (4000자)
        if len(prompt) > 3500:
            prompt = prompt[:3500] + "..."
        
        # 금지된 키워드 필터링
        forbidden_keywords = [
            "realistic person", "celebrity", "politician", "copyrighted character",
            "brand logo", "trademark", "specific company name"
        ]
        
        for keyword in forbidden_keywords:
            if keyword.lower() in prompt.lower():
                prompt = prompt.replace(keyword, "generic design")
        
        # 안전성 키워드 추가
        if not any(keyword in prompt.lower() for keyword in ["professional", "appropriate", "business-suitable"]):
            prompt += ", professional and appropriate design"
        
        return prompt
    
    async def _generate_mock_image(self, prompt: str, style: str = "default", **kwargs) -> ImageResult:
        """Mock DALL-E 이미지 생성 (개발/테스트용)"""
        # 시뮬레이션 지연
        await asyncio.sleep(0.3)
        
        # 간단한 1x1 PNG 이미지 (Base64)
        simple_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77zgAAAABJRU5ErkJggg=="
        
        # Base64 데이터 URL 생성
        mock_image_url = f"data:image/png;base64,{simple_png_base64}"
        
        return self._create_image_result(
            url=mock_image_url,
            style=style,
            prompt=prompt,
            metadata={
                "original_prompt": prompt,
                "generation_time": datetime.utcnow().isoformat(),
                "model": "dall-e-3-mock",
                "is_mock": True
            }
        )


class SDXLProvider(AIProvider):
    """AWS Bedrock Stability AI SDXL Provider"""
    
    def __init__(self, region: str = None):
        super().__init__("sdxl")
        self.region = region or os.getenv('AWS_REGION', 'us-east-1')
        self.model_id = "stability.stable-diffusion-xl-v1"
        
        # Bedrock 클라이언트 초기화
        try:
            if os.getenv('ENVIRONMENT') == 'local':
                # 로컬 환경에서는 Mock 클라이언트 사용
                self.bedrock_client = None
            else:
                self.bedrock_client = boto3.client('bedrock-runtime', region_name=self.region)
        except Exception as e:
            print(f"Failed to initialize Bedrock client: {e}")
            self.bedrock_client = None
    
    async def generate_image(self, prompt: str, style: str = "default", **kwargs) -> ImageResult:
        """SDXL 이미지 생성"""
        
        # 로컬 환경에서는 Mock 이미지 생성
        if os.getenv('ENVIRONMENT') == 'local' or not self.bedrock_client:
            return await self._generate_mock_image(prompt, style, **kwargs)
        
        if not self.bedrock_client:
            raise Exception("Bedrock client not available")
        
        # SDXL 요청 페이로드 구성
        payload = {
            "text_prompts": [
                {
                    "text": self._optimize_prompt_for_sdxl(prompt),
                    "weight": 1.0
                }
            ],
            "cfg_scale": kwargs.get("cfg_scale", 7.0),
            "steps": kwargs.get("steps", 30),
            "seed": kwargs.get("seed", 0),
            "width": kwargs.get("width", 1024),
            "height": kwargs.get("height", 1024),
            "samples": 1,
            "style_preset": self._map_style_to_sdxl(style)
        }
        
        # 재시도 로직
        for attempt in range(self.max_retries):
            try:
                # Bedrock API 호출
                response = self.bedrock_client.invoke_model(
                    modelId=self.model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(payload)
                )
                
                # 응답 파싱
                response_body = json.loads(response['body'].read())
                
                if 'artifacts' in response_body and len(response_body['artifacts']) > 0:
                    # Base64 이미지 데이터 추출
                    image_data = response_body['artifacts'][0]['base64']
                    
                    # 임시 URL 생성 (실제로는 S3에 업로드 후 URL 반환)
                    image_url = f"data:image/png;base64,{image_data}"
                    
                    return self._create_image_result(
                        url=image_url,
                        style=style,
                        prompt=prompt,
                        metadata={
                            "original_prompt": prompt,
                            "generation_time": datetime.utcnow().isoformat(),
                            "attempt": attempt + 1,
                            "model": "sdxl-v1",
                            "cfg_scale": payload["cfg_scale"],
                            "steps": payload["steps"],
                            "style_preset": payload["style_preset"]
                        }
                    )
                else:
                    raise Exception("No image generated in response")
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    raise Exception(f"SDXL generation failed after {self.max_retries} attempts: {str(e)}")
    
    def _optimize_prompt_for_sdxl(self, prompt: str) -> str:
        """SDXL 특화 프롬프트 최적화"""
        # SDXL은 더 상세한 프롬프트를 선호
        sdxl_enhancements = [
            "high quality", "detailed", "professional photography",
            "sharp focus", "8k resolution", "masterpiece"
        ]
        
        # 기존 프롬프트에 SDXL 최적화 키워드 추가
        enhanced_prompt = prompt
        
        # 이미 포함되지 않은 키워드만 추가
        for enhancement in sdxl_enhancements:
            if enhancement not in enhanced_prompt.lower():
                enhanced_prompt += f", {enhancement}"
        
        # 길이 제한
        if len(enhanced_prompt) > 1000:
            enhanced_prompt = enhanced_prompt[:1000] + "..."
        
        return enhanced_prompt
    
    def _map_style_to_sdxl(self, style: str) -> str:
        """스타일을 SDXL style_preset으로 매핑"""
        style_mapping = {
            "modern": "photographic",
            "classic": "enhance", 
            "vibrant": "comic-book",
            "default": "photographic"
        }
        
        return style_mapping.get(style, "photographic")
    
    async def _generate_mock_image(self, prompt: str, style: str = "default", **kwargs) -> ImageResult:
        """Mock SDXL 이미지 생성 (개발/테스트용)"""
        # 시뮬레이션 지연
        await asyncio.sleep(0.4)
        
        # 간단한 1x1 PNG 이미지 (Base64)
        simple_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77zgAAAABJRU5ErkJggg=="
        
        # Base64 데이터 URL 생성
        mock_image_url = f"data:image/png;base64,{simple_png_base64}"
        
        return self._create_image_result(
            url=mock_image_url,
            style=style,
            prompt=prompt,
            metadata={
                "original_prompt": prompt,
                "generation_time": datetime.utcnow().isoformat(),
                "model": "sdxl-v1-mock",
                "cfg_scale": kwargs.get("cfg_scale", 7.0),
                "steps": kwargs.get("steps", 30),
                "is_mock": True
            }
        )


class GeminiProvider(AIProvider):
    """Google Gemini Provider"""
    
    def __init__(self, api_key: str = None):
        super().__init__("gemini")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.api_key = api_key or self._get_api_key()
        
        if not self.api_key:
            raise ValueError("Google Gemini API key is required")
    
    def _get_api_key(self) -> str:
        """API 키 획득"""
        # 환경변수에서 확인
        api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        if api_key:
            return api_key
        
        # AWS Secrets Manager에서 확인 (프로덕션 환경)
        if os.getenv('ENVIRONMENT') != 'local':
            try:
                secret_name = os.getenv('GEMINI_SECRET_NAME', 'gemini-api-key')
                region = os.getenv('AWS_REGION', 'us-east-1')
                
                session = boto3.session.Session()
                client = session.client(service_name='secretsmanager', region_name=region)
                
                response = client.get_secret_value(SecretId=secret_name)
                secret = json.loads(response['SecretString'])
                
                return secret.get('api_key') or secret.get('GOOGLE_API_KEY')
            except Exception:
                pass
        
        return None
    
    async def generate_image(self, prompt: str, style: str = "default", **kwargs) -> ImageResult:
        """Gemini 이미지 생성 (Vertex AI Imagen API 사용)"""
        
        # 환경 확인 - 로컬 환경에서는 Mock 사용
        if os.getenv('ENVIRONMENT') == 'local':
            return await self._generate_mock_image(prompt, style, **kwargs)
        
        # 실제 Vertex AI Imagen API 호출
        try:
            # Google Cloud Vertex AI 클라이언트 초기화
            from google.cloud import aiplatform
            from google.cloud.aiplatform.gapic.schema import predict
            
            # 프로젝트 설정
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
            location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
            
            if not project_id:
                raise Exception("GOOGLE_CLOUD_PROJECT_ID environment variable is required")
            
            # Vertex AI 초기화
            aiplatform.init(project=project_id, location=location)
            
            # Imagen 모델 엔드포인트
            endpoint = aiplatform.Endpoint(
                endpoint_name=f"projects/{project_id}/locations/{location}/endpoints/imagen-endpoint"
            )
            
            # 요청 페이로드 구성
            instances = [
                {
                    "prompt": self._optimize_prompt_for_gemini(prompt)
                }
            ]
            
            parameters = {
                "sampleCount": 1,
                "aspectRatio": kwargs.get("aspect_ratio", "1:1"),
                "safetyFilterLevel": "block_some",
                "personGeneration": "dont_allow"
            }
            
            # 재시도 로직
            for attempt in range(self.max_retries):
                try:
                    # Vertex AI 예측 호출
                    response = endpoint.predict(
                        instances=instances,
                        parameters=parameters
                    )
                    
                    if response.predictions and len(response.predictions) > 0:
                        prediction = response.predictions[0]
                        
                        # 이미지 데이터 추출 (Base64 또는 GCS URL)
                        if 'bytesBase64Encoded' in prediction:
                            image_data = prediction['bytesBase64Encoded']
                            image_url = f"data:image/png;base64,{image_data}"
                        elif 'gcsUri' in prediction:
                            image_url = prediction['gcsUri']
                        else:
                            raise Exception("No image data found in response")
                        
                        return self._create_image_result(
                            url=image_url,
                            style=style,
                            prompt=prompt,
                            metadata={
                                "original_prompt": prompt,
                                "generation_time": datetime.utcnow().isoformat(),
                                "attempt": attempt + 1,
                                "model": "imagen-2",
                                "aspect_ratio": parameters["aspectRatio"],
                                "safety_filter": parameters["safetyFilterLevel"]
                            }
                        )
                    else:
                        raise Exception("No predictions returned from Vertex AI")
                        
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    else:
                        raise Exception(f"Vertex AI Imagen failed after {self.max_retries} attempts: {str(e)}")
                        
        except ImportError:
            # Google Cloud 라이브러리가 없는 경우 Mock 사용
            return await self._generate_mock_image(prompt, style, **kwargs)
        except Exception as e:
            # 기타 오류 시 Mock 사용
            print(f"Vertex AI Imagen failed, using mock: {e}")
            return await self._generate_mock_image(prompt, style, **kwargs)
    
    async def _generate_mock_image(self, prompt: str, style: str = "default", **kwargs) -> ImageResult:
        """Mock 이미지 생성 (개발/테스트용)"""
        # 시뮬레이션 지연
        await asyncio.sleep(0.5)
        
        # 실제 placeholder 이미지 생성 (1024x1024 PNG)
        import base64
        
        # 간단한 1x1 PNG 이미지 (Base64)
        # 실제로는 더 복잡한 이미지를 생성할 수 있지만, 테스트용으로는 충분
        simple_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77zgAAAABJRU5ErkJggg=="
        
        # Base64 데이터 URL 생성
        mock_image_url = f"data:image/png;base64,{simple_png_base64}"
        
        return self._create_image_result(
            url=mock_image_url,
            style=style,
            prompt=prompt,
            metadata={
                "original_prompt": prompt,
                "generation_time": datetime.utcnow().isoformat(),
                "model": "imagen-2-mock",
                "aspect_ratio": kwargs.get("aspect_ratio", "1:1"),
                "is_mock": True
            }
        )
    
    def _optimize_prompt_for_gemini(self, prompt: str) -> str:
        """Gemini 특화 프롬프트 최적화"""
        # Gemini/Imagen은 자연스러운 언어를 선호
        gemini_enhancements = [
            "realistic", "high quality", "professional", "detailed"
        ]
        
        enhanced_prompt = prompt
        
        # 자연스러운 문장 구조로 변환
        if not enhanced_prompt.endswith('.'):
            enhanced_prompt += "."
        
        # 품질 키워드 추가
        for enhancement in gemini_enhancements:
            if enhancement not in enhanced_prompt.lower():
                enhanced_prompt += f" The image should be {enhancement}."
        
        # 길이 제한
        if len(enhanced_prompt) > 1000:
            enhanced_prompt = enhanced_prompt[:1000] + "..."
        
        return enhanced_prompt


class AIProviderFactory:
    """AI Provider 팩토리 클래스"""
    
    @staticmethod
    def create_provider(provider_type: str, **kwargs) -> AIProvider:
        """Provider 타입에 따라 적절한 Provider 인스턴스 생성"""
        if provider_type.lower() == "dalle":
            return DALLEProvider(api_key=kwargs.get("api_key"))
        elif provider_type.lower() == "sdxl":
            return SDXLProvider(region=kwargs.get("region"))
        elif provider_type.lower() == "gemini":
            return GeminiProvider(api_key=kwargs.get("api_key"))
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
    
    @staticmethod
    def get_available_providers() -> List[str]:
        """사용 가능한 Provider 목록 반환"""
        return ["dalle", "sdxl", "gemini"]
    
    @staticmethod
    def create_all_providers(**kwargs) -> Dict[str, AIProvider]:
        """모든 사용 가능한 Provider 인스턴스 생성"""
        providers = {}
        
        for provider_type in AIProviderFactory.get_available_providers():
            try:
                provider = AIProviderFactory.create_provider(provider_type, **kwargs)
                providers[provider_type] = provider
            except Exception as e:
                print(f"Failed to create {provider_type} provider: {e}")
                # 실패한 Provider는 제외하고 계속 진행
                continue
        
        return providers