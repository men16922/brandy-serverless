"""
Signboard Agent - 다중 AI 모델 연동 간판 이미지 생성
OpenAI DALL-E, Stability AI SDXL, Google Gemini 지원
"""

import json
import sys
import os
import time
import base64
import uuid
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime
import asyncio
import aiohttp

if TYPE_CHECKING:
    from shared.ai_providers import AIProvider

# Add shared modules to path - Lambda Layer structure
sys.path.insert(0, '/opt/python')

from shared.base_agent import BaseAgent
from shared.models import AgentType, ImageResult, SignboardImages, BusinessInfo
from shared.utils import create_response
from shared.env_loader import get_openai_api_key, is_local_environment
from shared.s3_client import get_s3_client
from shared.ai_providers import AIProviderFactory, AIProvider

# Mock implementations removed - using actual imports from Lambda Layer


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
    """Signboard Agent - 다중 AI 모델 간판 이미지 생성"""
    
    def __init__(self):
        super().__init__(AgentType.SIGNBOARD)
        
        # 다중 AI Provider 초기화
        self.ai_providers = self._initialize_ai_providers()
        
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
    
    def _initialize_ai_providers(self) -> Dict[str, 'AIProvider']:
        """
        AI Provider 초기화
        
        Priority order (Hackathon compliant):
        1. Bedrock SDXL (Primary - AWS Bedrock)
        2. DALL-E (Fallback - OpenAI)
        3. Gemini (Fallback - Google)
        """
        providers = {}
        
        # Check if fallback is enabled
        enable_fallback = os.getenv('ENABLE_FALLBACK', 'true').lower() == 'true'
        dev_profile = os.getenv('DEV_PROFILE', 'false').lower() == 'true'
        environment = os.getenv('ENVIRONMENT', 'prod')
        
        self.logger.info(
            f"Initializing AI providers: environment={environment}, "
            f"enable_fallback={enable_fallback}, dev_profile={dev_profile}"
        )
        
        # Log AWS credentials status (without exposing actual credentials)
        try:
            import boto3
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            self.logger.info(f"AWS credentials available: Account={identity.get('Account')}")
        except Exception as cred_error:
            self.logger.warning(f"AWS credentials check failed: {cred_error}")
        
        # Bedrock SDXL is always initialized (Primary for hackathon)
        self.logger.info("Attempting to initialize Bedrock SDXL provider (PRIMARY)...")
        try:
            # Use Bedrock SDXL Provider (AWS Bedrock)
            sdxl_provider = AIProviderFactory.create_provider("sdxl", logger=self.logger)
            providers["bedrock_sdxl"] = sdxl_provider
            self.logger.info("✓ Bedrock SDXL provider initialized successfully (PRIMARY)")
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            self.logger.error(f"✗ Failed to initialize Bedrock SDXL provider: {error_type}: {error_msg}")
            # Note: AgentLogger doesn't support exc_info parameter
            import traceback
            self.logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Bedrock SDXL failure is critical for hackathon submission
            if not enable_fallback and not dev_profile and environment != 'local':
                critical_error = f"Bedrock SDXL initialization failed (required for hackathon): {error_msg}"
                self.logger.error(f"CRITICAL: {critical_error}")
                raise Exception(critical_error)
            else:
                self.logger.warning(f"Bedrock SDXL failed but fallback is enabled, continuing...")
        
        # Additional providers for diversity (DALL-E, Gemini)
        # Always initialize for multi-provider comparison, regardless of fallback setting
        self.logger.info("Initializing additional providers (DALL-E, Gemini) for multi-provider comparison...")
        
        # DALL-E Provider
        self.logger.info("Attempting to initialize DALL-E provider...")
        try:
            dalle_provider = AIProviderFactory.create_provider("dalle", logger=self.logger)
            providers["dalle"] = dalle_provider
            self.logger.info("✓ DALL-E provider initialized successfully")
        except Exception as e:
            error_type = type(e).__name__
            self.logger.warning(f"✗ Failed to initialize DALL-E provider: {error_type}: {str(e)}")
        
        # Gemini Provider
        self.logger.info("Attempting to initialize Gemini provider...")
        try:
            gemini_provider = AIProviderFactory.create_provider("gemini", logger=self.logger)
            providers["gemini"] = gemini_provider
            self.logger.info("✓ Gemini provider initialized successfully")
        except Exception as e:
            error_type = type(e).__name__
            self.logger.warning(f"✗ Failed to initialize Gemini provider: {error_type}: {str(e)}")
        
        # Summary
        if len(providers) == 0:
            self.logger.error("CRITICAL: No AI providers initialized! Image generation will fail.")
        else:
            self.logger.info(
                f"✓ Successfully initialized {len(providers)} AI provider(s): {list(providers.keys())}"
            )
            self.logger.info(f"Provider priority: {list(providers.keys())}")
        
        return providers
    
    def _initialize_fallback_images(self) -> Dict[str, str]:
        """폴백 이미지 URL 초기화"""
        # 환경별 폴백 이미지 URL 설정
        base_url = os.getenv('FALLBACK_IMAGES_BASE_URL', 'https://example.com/fallback')
        
        return {
            "modern": f"{base_url}/modern-signboard.png",
            "classic": f"{base_url}/classic-signboard.png",
            "vibrant": f"{base_url}/vibrant-signboard.png"
        }
    
    def _validate_providers(self) -> Dict[str, bool]:
        """
        Validate all AI providers on initialization.
        
        Returns:
            Dict mapping provider names to availability status
        """
        provider_status = {}
        
        for provider_name, provider in self.ai_providers.items():
            try:
                # Check if provider is properly initialized
                if provider is None:
                    provider_status[provider_name] = False
                    self.logger.warning(f"Provider {provider_name} is None")
                else:
                    provider_status[provider_name] = True
                    self.logger.info(f"Provider {provider_name} is available")
            except Exception as e:
                provider_status[provider_name] = False
                self.logger.error(f"Provider {provider_name} validation failed: {str(e)}")
        
        return provider_status
    
    def _log_generation_attempt(
        self,
        provider_name: str,
        style: str,
        session_id: str,
        prompt: str
    ) -> None:
        """Log image generation attempt with context"""
        self.logger.info(
            f"Image generation attempt: "
            f"session_id={session_id}, "
            f"provider={provider_name}, "
            f"style={style}, "
            f"prompt_length={len(prompt)}"
        )
    
    def _log_generation_result(
        self,
        provider_name: str,
        style: str,
        success: bool,
        error: Optional[str] = None,
        latency_ms: Optional[int] = None
    ) -> None:
        """Log image generation result"""
        if success:
            self.logger.info(
                f"Image generation success: "
                f"provider={provider_name}, "
                f"style={style}, "
                f"latency_ms={latency_ms}"
            )
        else:
            self.logger.error(
                f"Image generation failed: "
                f"provider={provider_name}, "
                f"style={style}, "
                f"error={error}"
            )
    
    def _should_use_fallback(self) -> bool:
        """Determine if fallback providers should be used"""
        environment = os.getenv('ENVIRONMENT', 'prod')
        enable_fallback = os.getenv('ENABLE_FALLBACK', 'true').lower() == 'true'
        dev_profile = os.getenv('DEV_PROFILE', 'false').lower() == 'true'
        
        # Fallback enabled in local/dev or when explicitly enabled
        should_fallback = (
            environment in ['local', 'dev'] or
            enable_fallback or
            dev_profile
        )
        
        self.logger.info(
            f"Fallback decision: should_use={should_fallback}, "
            f"environment={environment}, "
            f"enable_fallback={enable_fallback}, "
            f"dev_profile={dev_profile}"
        )
        
        return should_fallback
    
    def execute(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Signboard Agent 실행 로직"""
        try:
            # 비동기 모드 확인
            headers = event.get('headers', {})
            is_async = headers.get('x-async-mode') == 'true'
            
            # 요청 파싱
            if isinstance(event.get('body'), str):
                body = json.loads(event['body'])
            else:
                body = event.get('body', event)
            
            session_id = body.get('sessionId')
            selected_name = body.get('selectedName')
            business_info_data = body.get('businessInfo', {})
            
            # Action 감지: body 또는 path에서 추출
            action = body.get('action')
            
            # Action이 body에 없으면 path에서 추론
            if not action:
                path = event.get('path', '') or event.get('rawPath', '')
                self.logger.info(f"Inferring action from path: {path}")
                
                if '/select' in path:
                    action = 'select'
                    self.logger.info("Action inferred: select")
                elif '/generate' in path:
                    action = 'generate'
                    self.logger.info("Action inferred: generate")
                else:
                    action = 'generate'  # Default action
                    self.logger.info("Action defaulted to: generate")
            else:
                self.logger.info(f"Action from body: {action}")
            
            # Validate required fields based on action
            if action == 'select':
                # For select action, only sessionId and selectedImageUrl are required
                if not session_id:
                    return self.create_lambda_response(400, {
                        "error": "sessionId is required"
                    })
                selected_image_url = body.get('selectedImageUrl')
                if not selected_image_url:
                    return self.create_lambda_response(400, {
                        "error": "selectedImageUrl is required"
                    })
            else:
                # For other actions, sessionId and selectedName are required
                if not all([session_id, selected_name]):
                    return self.create_lambda_response(400, {
                        "error": "sessionId and selectedName are required"
                    })
            
            # 비동기 모드: 즉시 202 반환하고 별도 Lambda 호출로 백그라운드 실행
            if is_async:
                self.logger.info(f"Async mode enabled for session: {session_id}")
                
                # Lambda를 비동기로 재호출 (InvocationType='Event')
                try:
                    import boto3
                    lambda_client = boto3.client('lambda')
                    
                    # 동기 모드로 재호출 (x-async-mode 헤더 제거)
                    sync_event = event.copy()
                    if 'headers' in sync_event:
                        sync_headers = sync_event['headers'].copy()
                        sync_headers.pop('x-async-mode', None)
                        sync_event['headers'] = sync_headers
                    
                    # 현재 Lambda 함수 이름 가져오기
                    function_name = os.getenv('AWS_LAMBDA_FUNCTION_NAME')
                    
                    self.logger.info(f"Invoking Lambda asynchronously: {function_name}")
                    
                    # 비동기 호출 (Event 타입)
                    lambda_client.invoke(
                        FunctionName=function_name,
                        InvocationType='Event',  # 비동기 호출
                        Payload=json.dumps(sync_event)
                    )
                    
                    self.logger.info(f"Async Lambda invocation successful for session: {session_id}")
                    
                except Exception as invoke_error:
                    self.logger.error(f"Failed to invoke Lambda asynchronously: {str(invoke_error)}")
                    # 실패해도 202 반환 (폴링으로 확인 가능)
                
                # 즉시 202 반환
                return self.create_lambda_response(202, {
                    "message": "Signboard generation started",
                    "sessionId": session_id,
                    "status": "processing"
                })
            
            # 동기 모드: 기존 로직
            # 실행 시작
            self.start_execution(session_id, f"signboard.{action}")
            
            # 간판 이미지 생성 또는 선택 처리
            if action == 'select':
                # 선택 action은 business_info 불필요
                selected_image_url = body.get('selectedImageUrl')
                result = self._handle_image_selection(session_id, selected_image_url)
            else:
                # 다른 action들은 business_info 필요
                # 비즈니스 정보 파싱
                if isinstance(business_info_data, str):
                    business_info_data = json.loads(business_info_data)
                
                business_info = BusinessInfo(**business_info_data)
                
                if action == 'generate':
                    result = self._generate_signboard_images(session_id, selected_name, business_info)
                elif action == 'generate_single':
                    # 단일 Provider로 이미지 생성 (Step Functions용)
                    provider = body.get('provider')
                    style = body.get('style')
                    
                    # 비동기 실행
                    try:
                        loop = asyncio.get_running_loop()
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(
                                asyncio.run,
                                self._generate_single_provider_image(session_id, selected_name, business_info, provider, style)
                            )
                            result = future.result(timeout=35)  # 35초 타임아웃
                    except RuntimeError:
                        result = asyncio.run(
                            self._generate_single_provider_image(session_id, selected_name, business_info, provider, style)
                        )
                elif action == 'merge_results':
                    # 병렬 생성 결과 병합 (Step Functions용)
                    dalle_result = body.get('dalleResult')
                    sdxl_result = body.get('sdxlResult')
                    gemini_result = body.get('geminiResult')
                    result = self._merge_parallel_results(session_id, dalle_result, sdxl_result, gemini_result)
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
    
    def _assign_providers_to_styles(self, styles: List[str]) -> List[tuple]:
        """
        Assign providers to styles with strict 1:1 mapping
        
        Strategy:
        - Style 0 (modern) → DALL-E
        - Style 1 (classic) → SDXL
        - Style 2 (vibrant) → SDXL
        
        Note: Using DALL-E for one style and SDXL for two styles
        
        Returns: List of (provider_name, style) tuples
        """
        # Preferred provider order for each style
        preferred_providers = {
            0: "dalle",          # modern → DALL-E
            1: "bedrock_sdxl",   # classic → SDXL
            2: "bedrock_sdxl"    # vibrant → SDXL
        }
        
        # Check availability
        available_providers = []
        for provider_name in ["dalle", "bedrock_sdxl"]:
            if provider_name in self.ai_providers:
                available_providers.append(provider_name)
                self.logger.info(f"✓ Provider {provider_name} is available")
            else:
                self.logger.warning(f"✗ Provider {provider_name} not available")
        
        if not available_providers:
            self.logger.error("No AI providers available!")
            return []
        
        # Log provider availability summary
        self.logger.info(f"Available providers: {available_providers}")
        
        # Assign providers to styles
        assignments = []
        for i, style in enumerate(styles[:3]):  # Max 3 styles
            # Get preferred provider for this index
            preferred_provider = preferred_providers.get(i, "bedrock_sdxl")
            
            if preferred_provider in self.ai_providers:
                # Use the preferred provider
                provider_name = preferred_provider
                self.logger.info(f"✓ Using preferred provider {provider_name} for {style} (index {i})")
            elif available_providers:
                # Fallback: use available provider (prefer SDXL over DALLE for fallback)
                if "bedrock_sdxl" in available_providers:
                    provider_name = "bedrock_sdxl"
                else:
                    provider_name = available_providers[0]
                self.logger.warning(f"⚠ Using fallback provider {provider_name} for {style} (index {i}) - preferred provider not available")
            else:
                # No providers available
                self.logger.error(f"No provider available for style {style}")
                continue
            
            assignments.append((provider_name, style))
            self.logger.info(f"✓ Final assignment: {provider_name} → {style} style")
        
        return assignments
    
    async def _generate_images_async(self, session_id: str, selected_name: str, 
                                   business_info: BusinessInfo, styles: List[str]) -> List[ImageResult]:
        """
        다중 AI 모델을 사용한 비동기 이미지 생성
        
        Strategy (Updated):
        - DALL-E for style 0 (modern)
        - Gemini for style 1 (classic)
        - SDXL for style 2 (vibrant)
        - Parallel generation for performance (≤30 seconds)
        """
        
        # 사용 가능한 AI Provider 확인
        available_providers = list(self.ai_providers.keys())
        if not available_providers:
            self.logger.warning("No AI providers available, using fallback images")
            return self._create_fallback_images(session_id, selected_name, business_info)
        
        # Provider-to-style 할당 (새로운 로직)
        provider_style_assignments = self._assign_providers_to_styles(styles)
        
        if not provider_style_assignments:
            self.logger.error("Failed to assign providers to styles, using fallback")
            return self._create_fallback_images(session_id, selected_name, business_info)
        
        # Log assignments
        self.logger.info(f"Provider assignments: {provider_style_assignments}")
        
        # Provider와 스타일 조합으로 태스크 생성 (새로운 로직)
        tasks = []
        provider_style_combinations = []
        
        # 할당된 (provider, style) 조합으로 태스크 생성
        for provider_name, style in provider_style_assignments:
            provider = self.ai_providers[provider_name]
            
            self.logger.info(f"Creating task: {provider_name} → {style} style")
            
            task = self._generate_single_image_with_provider(
                provider, session_id, selected_name, business_info, style
            )
            tasks.append(task)
            provider_style_combinations.append((provider_name, style))
        
        # 모든 이미지를 병렬로 생성 (최대 55초 타임아웃 - Lambda 60초 제한 고려)
        try:
            results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=55.0)
        except asyncio.TimeoutError:
            self.logger.warning("Image generation timed out after 55 seconds")
            results = [None] * len(tasks)
        
        # 성공한 결과 처리
        images = []
        for i, result in enumerate(results):
            provider_name, style = provider_style_combinations[i]
            
            if isinstance(result, ImageResult):
                # 성공한 경우
                images.append(result)
                self.logger.info(
                    f"Successfully generated {style} image with {provider_name} "
                    f"(is_bedrock={provider_name == 'bedrock_sdxl'})"
                )
            else:
                # 실패한 경우 폴백 이미지 생성
                self.logger.warning(f"Failed to generate {style} image with {provider_name}: {result}")
                fallback_image = self._create_single_fallback_image(session_id, selected_name, business_info, style)
                images.append(fallback_image)
        
        return images
    
    async def _generate_single_image_with_provider(self, provider: 'AIProvider', session_id: str, 
                                                 selected_name: str, business_info: BusinessInfo, 
                                                 style: str) -> ImageResult:
        """
        특정 AI Provider를 사용한 단일 이미지 생성
        
        Tracks Bedrock usage for hackathon compliance monitoring
        """
        start_time = time.time()
        
        try:
            # 프롬프트 생성
            prompt = self._create_image_prompt(selected_name, business_info, style)
            
            # Log generation attempt using new method
            self._log_generation_attempt(
                provider_name=provider.provider_name,
                style=style,
                session_id=session_id,
                prompt=prompt
            )
            
            # Provider별 특화 파라미터 설정
            provider_params = self._get_provider_params(provider.provider_name, style)
            self.logger.info(f"Provider params: {provider_params}")
            
            # Log Bedrock usage (Requirement 5.3)
            is_bedrock = provider.provider_name == "bedrock_sdxl" or provider.provider_name == "sdxl"
            if is_bedrock:
                self.logger.info(
                    f"🎯 Using Bedrock SDXL for image generation: "
                    f"style={style}, size=1024x1024, session={session_id}"
                )
            else:
                self.logger.info(f"Using fallback provider: {provider.provider_name}")
            
            # AI Provider를 통한 이미지 생성
            self.logger.info(f"Calling {provider.provider_name}.generate_image()...")
            image_result = await provider.generate_image(
                prompt=prompt,
                style=style,
                **provider_params
            )
            self.logger.info(f"✓ {provider.provider_name}.generate_image() returned successfully")
            
            # 이미지 다운로드 및 S3 업로드 (URL이 data: 형식이 아닌 경우)
            if image_result.url.startswith('http'):
                s3_url = await self._download_and_upload_image(
                    image_result.url, session_id, f"{provider.provider_name}_{style}"
                )
                image_result.url = s3_url
            elif image_result.url.startswith('data:image'):
                # Base64 데이터인 경우 직접 S3에 업로드
                s3_url = await self._upload_base64_image(
                    image_result.url, session_id, f"{provider.provider_name}_{style}"
                )
                image_result.url = s3_url
            
            # 메타데이터 업데이트 (번역 정보 포함)
            latency_ms = int((time.time() - start_time) * 1000)
            english_name = self._translate_to_english(selected_name)
            
            # 번역 방법 결정
            translation_method = "dictionary" if english_name != selected_name else "none"
            if selected_name.isascii():
                translation_method = "already_english"
            
            image_result.metadata.update({
                "business_name": selected_name,
                "english_name": english_name,  # NEW
                "translation_method": translation_method,  # NEW
                "industry": business_info.industry,
                "provider": provider.provider_name,
                "is_bedrock": is_bedrock,
                "latency_ms": latency_ms,
                "session_id": session_id
            })
            
            # Log generation result using new method
            self._log_generation_result(
                provider_name=provider.provider_name,
                style=style,
                success=True,
                latency_ms=latency_ms
            )
            
            return image_result
                
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Log generation result using new method
            self._log_generation_result(
                provider_name=provider.provider_name,
                style=style,
                success=False,
                error=f"{error_type}: {error_msg}"
            )
            
            # Note: AgentLogger doesn't support exc_info parameter
            import traceback
            self.logger.error(f"Stack trace: {traceback.format_exc()}")
            raise e
    
    def _get_provider_params(self, provider_name: str, style: str) -> Dict[str, Any]:
        """
        Provider별 특화 파라미터 반환
        
        Optimized for hackathon requirements:
        - Bedrock SDXL: 1024x1024, optimized cfg_scale and steps
        - DALL-E: Standard quality for cost efficiency
        - Gemini: 1:1 aspect ratio
        """
        if provider_name == "bedrock_sdxl":
            # Bedrock SDXL optimized parameters (Requirement 1.4)
            return {
                "width": 1024,
                "height": 1024,
                "cfg_scale": 7.5,  # Slightly higher for better quality
                "steps": 30,  # Balanced quality/speed
                "seed": None  # Random seed for variety
            }
        elif provider_name == "dalle":
            # DALL-E fallback parameters
            return {
                "size": "1024x1024",
                "quality": "standard",  # Cost-optimized
                "dalle_style": "vivid"
            }
        elif provider_name == "sdxl":
            # Legacy SDXL provider (same as bedrock_sdxl)
            return {
                "width": 1024,
                "height": 1024,
                "cfg_scale": 7.0,
                "steps": 30
            }
        elif provider_name == "gemini":
            # Gemini fallback parameters
            return {
                "aspect_ratio": "1:1"
            }
        else:
            return {}
    
    def _create_image_prompt(self, business_name: str, business_info: BusinessInfo, style: str) -> str:
        """
        이미지 생성 프롬프트 생성 (영어 텍스트 강조)
        
        Enhanced to emphasize English text display in generated images
        """
        industry = business_info.industry.lower()
        region = business_info.region
        
        # 영어 이름으로 변환 (한글 이름은 사용하지 않음)
        english_name = self._translate_to_english(business_name)
        
        # 번역 로깅
        self.logger.info(f"Business name translation: '{business_name}' → '{english_name}'")
        
        # 업종별 특성 추가
        industry_info = self.industry_characteristics.get(industry, self.industry_characteristics["retail"])
        mood = industry_info["mood"]
        
        # 스타일별 특성 추가
        style_info = self.signboard_styles[style]
        style_keywords = ", ".join(style_info["keywords"][:2])  # 처음 2개 키워드만
        
        # 최종 프롬프트 조합 (영어 텍스트 강조 - 이름을 여러 번 반복)
        # 텍스트 표시를 최우선으로 강조
        prompt = (
            f"Professional storefront signboard design. "
            f"Large bold text displaying '{english_name}' in English letters. "
            f"The signboard prominently shows '{english_name}' as the main focal point. "
            f"{style_keywords} style, {mood} atmosphere, business-appropriate design. "
            f"Text: '{english_name}'"
        )
        
        # 프롬프트 로깅 (디버깅용)
        original_length = len(prompt)
        self.logger.info(f"Generated prompt: length={original_length} chars")
        self.logger.info(f"Prompt preview: {prompt[:150]}...")
        
        # 프롬프트 길이 제한
        # Titan Image Generator v2: 512 characters max
        # DALL-E 3: 4000 characters max
        # Gemini: 1000 characters max
        # Use the most restrictive limit for compatibility
        MAX_PROMPT_LENGTH = 512
        
        if len(prompt) > MAX_PROMPT_LENGTH:
            # Truncate intelligently - keep the most important parts
            # Priority: business name (repeated), style, basic description
            truncated_prompt = (
                f"Signboard with '{english_name}' text in bold English letters. "
                f"{style_keywords} style, professional design. "
                f"Main text: '{english_name}'"
            )
            
            # If still too long, do hard truncation
            if len(truncated_prompt) > MAX_PROMPT_LENGTH:
                # Keep at least the business name
                truncated_prompt = f"Signboard: '{english_name}' in bold letters. {style_keywords} style."
                if len(truncated_prompt) > MAX_PROMPT_LENGTH:
                    truncated_prompt = truncated_prompt[:MAX_PROMPT_LENGTH-3] + "..."
            
            self.logger.warning(
                f"Prompt truncated: {original_length} → {len(truncated_prompt)} chars"
            )
            prompt = truncated_prompt
        
        # Final validation
        self.logger.info(f"Final prompt ({len(prompt)} chars): {prompt}")
        
        return prompt
    
    def _translate_to_english(self, korean_name: str) -> str:
        """
        한국어 상호명을 영어로 번역
        
        Enhanced with expanded dictionary and better fallback logic
        """
        # 확장된 번역 매핑
        translations = {
            # 기존 번역
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
            '24시테이블': '24H Table',
            
            # 새로운 번역 (음식점/카페 관련)
            '카페': 'Cafe',
            '레스토랑': 'Restaurant',
            '베이커리': 'Bakery',
            '치킨': 'Chicken',
            '피자': 'Pizza',
            '버거': 'Burger',
            '스시': 'Sushi',
            '바': 'Bar',
            '펍': 'Pub',
            '그릴': 'Grill',
            '비스트로': 'Bistro',
            '델리': 'Deli',
            '브런치': 'Brunch',
            '디저트': 'Dessert',
            '와인': 'Wine',
            '커피': 'Coffee',
            '티': 'Tea',
            
            # 스타일/분위기
            '모던': 'Modern',
            '클래식': 'Classic',
            '빈티지': 'Vintage',
            '럭셔리': 'Luxury',
            '프리미엄': 'Premium',
            '심플': 'Simple',
            '엘레강스': 'Elegance',
            
            # 형용사
            '좋은': 'Good',
            '예쁜': 'Pretty',
            '맛있는': 'Delicious',
            '신선한': 'Fresh',
            '건강한': 'Healthy',
            '특별한': 'Special',
            '유니크': 'Unique',
            '빠른': 'Quick',
            
            # 장소/공간
            '키친': 'Kitchen',
            '하우스': 'House',
            '집': 'House',
            '테이블': 'Table',
            '가든': 'Garden',
            '원': 'Garden',
            '플레이스': 'Place',
            '스페이스': 'Space',
            '코너': 'Corner',
            '룸': 'Room',
            '홀': 'Hall'
        }
        
        # 정확한 매칭 확인
        if korean_name in translations:
            english_name = translations[korean_name]
            self.logger.info(f"Translation (exact match): {korean_name} → {english_name}")
            return english_name
        
        # 부분 매칭 (단어 단위)
        result = korean_name
        translation_applied = False
        
        for korean, english in translations.items():
            if korean in result:
                result = result.replace(korean, english)
                translation_applied = True
                self.logger.info(f"Translation (partial): {korean} → {english}")
        
        if translation_applied:
            self.logger.info(f"Translation (final): {korean_name} → {result}")
            return result
        
        # 폴백: 로마자 표기 (간단한 음역)
        # 이미 영어인 경우 그대로 반환
        if korean_name.isascii():
            self.logger.info(f"Translation (already English): {korean_name}")
            return korean_name
        
        # 한글이 포함된 경우 간단한 로마자 변환
        # 실제 프로덕션에서는 romanization 라이브러리 사용 권장
        self.logger.warning(f"Translation (no match found): {korean_name} → using as-is")
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
    
    async def _upload_base64_image(self, base64_data: str, session_id: str, style: str) -> str:
        """Base64 이미지 데이터를 S3에 업로드"""
        try:
            if not self.s3_client:
                self.logger.warning("S3 client not available, returning base64 data")
                return base64_data
            
            # Base64 데이터 파싱
            if base64_data.startswith('data:image'):
                # data:image/png;base64,... 형식에서 실제 데이터 추출
                header, data = base64_data.split(',', 1)
                image_data = base64.b64decode(data)
                
                # Content-Type 추출
                if 'png' in header:
                    content_type = 'image/png'
                elif 'jpeg' in header or 'jpg' in header:
                    content_type = 'image/jpeg'
                else:
                    content_type = 'image/png'
            else:
                # 순수 base64 데이터
                image_data = base64.b64decode(base64_data)
                content_type = 'image/png'
            
            # S3 키 생성
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            s3_key = f"signboards/{session_id}/{style}_{timestamp}_{unique_id}.png"
            
            # 메타데이터 준비
            metadata = {
                'session_id': session_id,
                'style': style,
                'generated_by': 'ai-provider',
                'source': 'base64'
            }
            
            # S3에 업로드
            upload_result = self.s3_client.upload_file(
                file_content=image_data,
                key=s3_key,
                content_type=content_type,
                metadata=metadata
            )
            
            if upload_result.get('success'):
                stored_url = upload_result.get('url') or upload_result.get('public_url')
                self.logger.info(f"Successfully uploaded base64 image to S3: {s3_key}")
                return stored_url
            else:
                self.logger.error(f"Failed to upload base64 image: {upload_result}")
                return base64_data
                
        except Exception as e:
            self.logger.error(f"Failed to upload base64 image to S3: {str(e)}")
            return base64_data

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
            from decimal import Decimal
            
            # Decimal을 float로 변환하는 helper (JSON serialization용)
            def decimal_to_float(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                elif isinstance(obj, dict):
                    return {k: decimal_to_float(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [decimal_to_float(item) for item in obj]
                return obj
            
            signboard_data = {
                "images": [self._image_result_to_dict(img) for img in signboard_images.images],
                "selected_image_url": signboard_images.selected_image_url
            }
            
            # Decimal을 float로 변환 (JSON serialization을 위해)
            signboard_data = decimal_to_float(signboard_data)
            
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
        result_dict = {
            "url": image_result.url,
            "provider": image_result.provider,
            "style": image_result.style,
            "prompt": image_result.prompt,
            "metadata": image_result.metadata,
            "generatedAt": image_result.generated_at,
            "isFallback": image_result.is_fallback
        }
        
        # Add optional fields if present (use hasattr to avoid AttributeError)
        if hasattr(image_result, 'error_message') and image_result.error_message:
            result_dict["errorMessage"] = image_result.error_message
        if hasattr(image_result, 'generation_time_ms') and image_result.generation_time_ms is not None:
            result_dict["generationTimeMs"] = image_result.generation_time_ms
        if hasattr(image_result, 'retry_count') and image_result.retry_count is not None:
            result_dict["retryCount"] = image_result.retry_count
        
        return result_dict


    async def _generate_single_provider_image(self, session_id: str, selected_name: str, 
                                            business_info: BusinessInfo, provider_name: str, 
                                            style: str) -> Dict[str, Any]:
        """단일 AI Provider로 이미지 생성 (Step Functions용)"""
        try:
            # Provider 확인
            if provider_name not in self.ai_providers:
                raise ValueError(f"Provider {provider_name} not available")
            
            provider = self.ai_providers[provider_name]
            
            # 이미지 생성
            image_result = await self._generate_single_image_with_provider(
                provider, session_id, selected_name, business_info, style
            )
            
            return {
                "success": True,
                "provider": provider_name,
                "style": style,
                "image": self._image_result_to_dict(image_result),
                "sessionId": session_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate image with {provider_name}: {str(e)}")
            
            # 폴백 이미지 생성
            fallback_image = self._create_single_fallback_image(session_id, selected_name, business_info, style)
            
            return {
                "success": False,
                "provider": provider_name,
                "style": style,
                "image": self._image_result_to_dict(fallback_image),
                "error": str(e),
                "sessionId": session_id
            }
    
    def _merge_parallel_results(self, session_id: str, dalle_result: Dict[str, Any], 
                              sdxl_result: Dict[str, Any], gemini_result: Dict[str, Any]) -> Dict[str, Any]:
        """병렬 생성 결과 병합"""
        try:
            signboards = []
            
            # 각 Provider 결과 처리
            for result in [dalle_result, sdxl_result, gemini_result]:
                if result and 'image' in result:
                    signboards.append(result['image'])
            
            # 최소 1개 이상의 이미지가 있어야 함
            if not signboards:
                # 모든 Provider가 실패한 경우 폴백 이미지 사용
                fallback_images = self._create_fallback_images(session_id, "", BusinessInfo(industry="", region="", size=""))
                signboards = [self._image_result_to_dict(img) for img in fallback_images]
            
            return {
                "sessionId": session_id,
                "signboards": signboards,
                "totalGenerated": len(signboards),
                "canProceed": len(signboards) > 0,
                "message": f"{len(signboards)}개의 간판 디자인이 생성되었습니다.",
                "providers_used": [result.get('provider') for result in [dalle_result, sdxl_result, gemini_result] if result]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to merge parallel results: {str(e)}")
            
            # 오류 시 기본 폴백 응답
            return {
                "sessionId": session_id,
                "signboards": [],
                "totalGenerated": 0,
                "canProceed": False,
                "error": str(e),
                "message": "이미지 생성에 실패했습니다."
            }


# Lambda 핸들러
def lambda_handler(event, context):
    """Lambda 핸들러 함수"""
    agent = SignboardAgent()
    return agent.lambda_handler(event, context)