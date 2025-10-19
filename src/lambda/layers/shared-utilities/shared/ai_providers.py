"""
AI Provider 추상화 계층
다양한 AI 모델을 통일된 인터페이스로 관리
"""

import json
import asyncio
import aiohttp
import boto3
import base64
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import uuid

from .models import ImageResult
from .utils import exponential_backoff


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
                           metadata: Dict[str, Any] = None, is_fallback: bool = False,
                           error_message: Optional[str] = None,
                           generation_time_ms: Optional[int] = None,
                           retry_count: Optional[int] = None) -> ImageResult:
        """ImageResult 객체 생성 헬퍼"""
        return ImageResult(
            url=url,
            provider=self.provider_name,
            style=style,
            prompt=prompt,
            metadata=metadata or {},
            is_fallback=is_fallback,
            error_message=error_message,
            generation_time_ms=generation_time_ms,
            retry_count=retry_count
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
                                wait_time = exponential_backoff(attempt, base_delay=self.retry_delay)
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                raise Exception(f"Rate limit exceeded after {self.max_retries} attempts")
                        elif response.status >= 500:  # Server error
                            if attempt < self.max_retries - 1:
                                wait_time = exponential_backoff(attempt, base_delay=self.retry_delay)
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
                    wait_time = exponential_backoff(attempt, base_delay=self.retry_delay)
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Request timeout after {self.max_retries} attempts")
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = exponential_backoff(attempt, base_delay=self.retry_delay)
                    await asyncio.sleep(wait_time)
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
    """AWS Bedrock Image Generator Provider (Titan Image Generator v2)"""
    
    def __init__(self, region: str = None, logger = None):
        super().__init__("sdxl")
        self.region = region or os.getenv('AWS_REGION', 'us-east-1')
        # Use Titan Image Generator (SDXL is deprecated)
        # Check both IMAGE_MODEL_ID and SDXL_MODEL_ID for backward compatibility
        self.model_id = os.getenv('IMAGE_MODEL_ID') or os.getenv('SDXL_MODEL_ID', 'amazon.titan-image-generator-v2:0')
        self.logger = logger or self._create_logger()
        
        # Log initialization attempt
        self.logger.info(f"Initializing SDXLProvider: region={self.region}, model_id={self.model_id}")
        
        # Check environment
        environment = os.getenv('ENVIRONMENT', 'prod')
        self.logger.info(f"Environment: {environment}")
        
        # Bedrock 클라이언트 초기화
        try:
            if environment == 'local':
                # 로컬 환경에서는 Mock 클라이언트 사용
                self.logger.info("Using mock Bedrock client for local environment")
                self.bedrock_client = None
            else:
                # Check AWS credentials
                try:
                    import boto3
                    sts = boto3.client('sts')
                    identity = sts.get_caller_identity()
                    self.logger.info(f"AWS credentials found: Account={identity.get('Account')}, ARN={identity.get('Arn')}")
                except Exception as cred_error:
                    self.logger.error(f"AWS credentials check failed: {cred_error}")
                    raise Exception(f"AWS credentials not configured: {cred_error}")
                
                # Initialize Bedrock client
                self.logger.info(f"Creating Bedrock runtime client in region: {self.region}")
                self.bedrock_client = boto3.client('bedrock-runtime', region_name=self.region)
                self.logger.info("Bedrock runtime client created successfully")
                
                # Validate client can access Bedrock
                try:
                    # Test connection by listing models (if available)
                    self.logger.info("Validating Bedrock client access...")
                    # Note: We can't easily test without making an actual API call
                    self.logger.info("Bedrock client validation skipped (will validate on first API call)")
                except Exception as validation_error:
                    self.logger.warning(f"Bedrock client validation warning: {validation_error}")
                    
        except Exception as e:
            self.logger.error(f"Failed to initialize Bedrock client: {type(e).__name__}: {str(e)}")
            self.logger.error(f"Error details: region={self.region}, environment={environment}")
            self.bedrock_client = None
            # Re-raise to make initialization failure visible
            raise Exception(f"SDXLProvider initialization failed: {str(e)}")
    
    def _create_logger(self):
        """Create logger for SDXL provider"""
        import logging
        logger = logging.getLogger('sdxl_provider')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    async def generate_image(self, prompt: str, style: str = "default", **kwargs) -> ImageResult:
        """SDXL 이미지 생성"""
        
        start_time = time.time()
        self.logger.info(f"Starting SDXL image generation: style={style}, prompt_length={len(prompt)}")
        
        # 로컬 환경에서는 Mock 이미지 생성
        environment = os.getenv('ENVIRONMENT', 'prod')
        if environment == 'local' or not self.bedrock_client:
            self.logger.info(f"Using mock image generation: environment={environment}, bedrock_client={'None' if not self.bedrock_client else 'available'}")
            return await self._generate_mock_image(prompt, style, **kwargs)
        
        if not self.bedrock_client:
            error_msg = "Bedrock client not available"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
        # Titan Image Generator 요청 페이로드 구성
        payload = {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": self._optimize_prompt_for_titan(prompt)
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "quality": "premium",
                "height": kwargs.get("height", 1024),
                "width": kwargs.get("width", 1024),
                "cfgScale": kwargs.get("cfg_scale", 8.0),
                "seed": kwargs.get("seed", 0)
            }
        }
        
        # 재시도 로직
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"SDXL API call attempt {attempt + 1}/{self.max_retries}: model_id={self.model_id}")
                # Note: Some loggers don't have debug method
                self.logger.info(f"SDXL payload keys: {list(payload.keys())}")
                
                # Bedrock API 호출
                response = self.bedrock_client.invoke_model(
                    modelId=self.model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(payload)
                )
                
                self.logger.info(f"SDXL API call successful on attempt {attempt + 1}")
                
                # 응답 파싱 (Titan Image Generator)
                response_body = json.loads(response['body'].read())
                self.logger.info(f"Titan Image Generator response keys: {list(response_body.keys())}")
                
                if 'images' in response_body and len(response_body['images']) > 0:
                    # Base64 이미지 데이터 추출
                    image_data = response_body['images'][0]
                    image_size = len(image_data)
                    
                    latency_ms = int((time.time() - start_time) * 1000)
                    self.logger.info(f"Titan image generated successfully: size={image_size} bytes, latency={latency_ms}ms")
                    
                    # 임시 URL 생성 (실제로는 S3에 업로드 후 URL 반환)
                    image_url = f"data:image/png;base64,{image_data}"
                    
                    result = self._create_image_result(
                        url=image_url,
                        style=style,
                        prompt=prompt,
                        metadata={
                            "original_prompt": prompt,
                            "generation_time": datetime.utcnow().isoformat(),
                            "attempt": attempt + 1,
                            "model": "titan-image-generator-v2",
                            "cfg_scale": payload["imageGenerationConfig"]["cfgScale"],
                            "seed": payload["imageGenerationConfig"]["seed"],
                            "latency_ms": latency_ms
                        }
                    )
                    # Add retry_count and generation_time_ms to result
                    result.retry_count = attempt
                    result.generation_time_ms = latency_ms
                    return result
                else:
                    error_msg = "No image generated in Titan response"
                    self.logger.error(f"{error_msg}: response_body={response_body}")
                    raise Exception(error_msg)
                    
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                self.logger.error(f"SDXL generation attempt {attempt + 1} failed: {error_type}: {error_msg}")
                
                if attempt < self.max_retries - 1:
                    # Use exponential backoff with jitter
                    retry_delay = exponential_backoff(attempt, base_delay=self.retry_delay, max_delay=30.0)
                    self.logger.info(f"Retrying in {retry_delay:.2f}s (attempt {attempt + 1}/{self.max_retries})...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    final_error = f"SDXL generation failed after {self.max_retries} attempts: {error_msg}"
                    self.logger.error(final_error)
                    raise Exception(final_error)
    
    def _optimize_prompt_for_titan(self, prompt: str) -> str:
        """
        Titan Image Generator 특화 프롬프트 최적화
        
        CRITICAL: Titan Image Generator v2 has a 512 character limit for prompts.
        ValidationException will be raised if prompt exceeds this limit.
        """
        MAX_TITAN_PROMPT_LENGTH = 512
        
        # Log original prompt length
        original_length = len(prompt)
        self.logger.info(f"Optimizing prompt for Titan: original_length={original_length}")
        
        # If prompt is already within limit, return as-is
        if original_length <= MAX_TITAN_PROMPT_LENGTH:
            self.logger.info(f"Prompt within limit ({original_length}/{MAX_TITAN_PROMPT_LENGTH}), no truncation needed")
            return prompt
        
        # Prompt exceeds limit - need to truncate intelligently
        self.logger.warning(
            f"Prompt exceeds Titan limit: {original_length} > {MAX_TITAN_PROMPT_LENGTH}, "
            f"truncating..."
        )
        
        # Truncate with ellipsis, leaving room for it
        truncated_prompt = prompt[:MAX_TITAN_PROMPT_LENGTH - 3] + "..."
        
        self.logger.info(
            f"Prompt truncated: {original_length} → {len(truncated_prompt)} characters"
        )
        
        return truncated_prompt
    
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
                        wait_time = exponential_backoff(attempt, base_delay=self.retry_delay)
                        await asyncio.sleep(wait_time)
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
        import logging
        logger = logging.getLogger('ai_provider_factory')
        
        logger.info(f"Creating AI provider: type={provider_type}, kwargs={list(kwargs.keys())}")
        
        try:
            if provider_type.lower() == "dalle":
                logger.info("Initializing DALL-E provider...")
                provider = DALLEProvider(api_key=kwargs.get("api_key"))
                logger.info("DALL-E provider created successfully")
                return provider
            elif provider_type.lower() == "sdxl":
                logger.info("Initializing SDXL provider...")
                provider = SDXLProvider(region=kwargs.get("region"), logger=kwargs.get("logger"))
                logger.info("SDXL provider created successfully")
                return provider
            elif provider_type.lower() == "gemini":
                logger.info("Initializing Gemini provider...")
                provider = GeminiProvider(api_key=kwargs.get("api_key"))
                logger.info("Gemini provider created successfully")
                return provider
            else:
                error_msg = f"Unknown provider type: {provider_type}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        except Exception as e:
            logger.error(f"Failed to create {provider_type} provider: {type(e).__name__}: {str(e)}")
            raise
    
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