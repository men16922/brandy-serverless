"""
Bedrock AI integration for report enhancement
Handles insight synthesis and AI-powered content generation
"""
from typing import Dict, Any, Optional, List
import logging
import os


class BedrockIntegration:
    """Manages Bedrock AI integration for report enhancement"""
    
    def __init__(self, logger=None, enable_bedrock=None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Determine if Bedrock should be enabled
        if enable_bedrock is None:
            # Check environment variable (ENABLE_FALLBACK=false means use Bedrock)
            enable_bedrock = os.getenv('ENABLE_FALLBACK', 'false').lower() != 'true'
        
        self.enable_bedrock = enable_bedrock
        self.bedrock_client = None
        self.reasoning_engine = None
        
        if self.enable_bedrock:
            self._initialize_bedrock()
    
    def _initialize_bedrock(self):
        """Initialize Bedrock client and reasoning engine"""
        try:
            # Try Lambda Layer import first
            try:
                from shared.bedrock_client import BedrockClient, BedrockException
                from shared.reasoning_engine import ReasoningEngine
            except ImportError:
                # Fallback to local import
                from bedrock_client import BedrockClient, BedrockException
                from reasoning_engine import ReasoningEngine
            
            self.bedrock_client = BedrockClient(logger=self.logger)
            self.reasoning_engine = ReasoningEngine(
                bedrock_client=self.bedrock_client,
                logger=self.logger
            )
            
            self.logger.info("Bedrock integration initialized successfully")
            
        except Exception as e:
            self.logger.warning(f"Bedrock initialization failed: {str(e)}, using fallback")
            self.enable_bedrock = False
            self.bedrock_client = None
            self.reasoning_engine = None
    
    def is_enabled(self) -> bool:
        """
        Check if Bedrock is enabled and available
        
        Returns:
            True if Bedrock is enabled and initialized
        """
        return self.enable_bedrock and self.reasoning_engine is not None
    
    def synthesize_insights(self, session_data: Dict[str, Any]) -> Optional[str]:
        """
        Use Bedrock Claude to synthesize insights from agent outputs
        
        Args:
            session_data: Session data with agent outputs
        
        Returns:
            Synthesized insights text or None if disabled/failed
        """
        if not self.is_enabled():
            self.logger.info("Bedrock is disabled, skipping insight synthesis")
            return None
        
        try:
            # Collect agent output data
            agent_outputs = {
                'business_info': session_data.get('business_info', {}),
                'analysis_result': session_data.get('analysis_result', {}),
                'business_names': session_data.get('business_names', []),
                'selected_name': session_data.get('selected_name', ''),
                'signboard_count': len(session_data.get('signboard_images', [])),
                'interior_count': len(session_data.get('interior_images', [])),
                'color_palette': session_data.get('color_palette', {}),
                'budget_guide': session_data.get('budget_guide', {}),
                'recommendations': session_data.get('recommendations', [])
            }
            
            self.logger.info("Synthesizing insights with Bedrock Claude")
            
            # Use ReasoningEngine.synthesize_insights()
            synthesized_insights = self.reasoning_engine.synthesize_insights(
                agent_outputs=agent_outputs,
                temperature=0.5  # Slightly higher temperature for creative synthesis
            )
            
            self.logger.info(
                f"Bedrock insight synthesis complete: {len(synthesized_insights)} characters"
            )
            
            return synthesized_insights
            
        except Exception as e:
            self.logger.warning(f"Bedrock insight synthesis failed: {str(e)}, using fallback")
            return None
    
    def enhance_report_content(
        self,
        base_content: str,
        session_data: Dict[str, Any]
    ) -> str:
        """
        Enhance report content with AI insights
        
        Args:
            base_content: Base report content
            session_data: Session data for context
        
        Returns:
            Enhanced content or original content if Bedrock fails
        """
        if not self.is_enabled():
            self.logger.info("Bedrock is disabled, returning base content")
            return base_content
        
        try:
            # Get synthesized insights
            insights = self.synthesize_insights(session_data)
            
            if insights:
                # Add insights section to content
                enhanced_content = base_content + "\n\n## AI 인사이트\n\n" + insights
                self.logger.info("Successfully enhanced report content with Bedrock insights")
                return enhanced_content
            else:
                return base_content
                
        except Exception as e:
            self.logger.warning(f"Failed to enhance report content: {str(e)}")
            return base_content
    
    def generate_executive_summary(self, session_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate executive summary using Bedrock
        
        Args:
            session_data: Session data
        
        Returns:
            Executive summary text or None if failed
        """
        if not self.is_enabled():
            return None
        
        try:
            business_info = session_data.get('business_info', {})
            business_names = session_data.get('business_names', [])
            
            prompt = f"""
            다음 비즈니스 브랜딩 프로젝트에 대한 간결한 요약을 작성해주세요:
            
            업종: {business_info.get('industry', 'N/A')}
            지역: {business_info.get('region', 'N/A')}
            규모: {business_info.get('size', 'N/A')}
            제안된 상호명: {', '.join(business_names[:3])}
            
            3-4문장으로 핵심 내용을 요약해주세요.
            """
            
            response = self.bedrock_client.generate_text(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3
            )
            
            summary = response.get('content', '')
            self.logger.info("Generated executive summary with Bedrock")
            return summary
            
        except Exception as e:
            self.logger.warning(f"Failed to generate executive summary: {str(e)}")
            return None
    
    def get_branding_recommendations(self, session_data: Dict[str, Any]) -> Optional[List[str]]:
        """
        Get AI-powered branding recommendations
        
        Args:
            session_data: Session data
        
        Returns:
            List of recommendations or None if failed
        """
        if not self.is_enabled():
            return None
        
        try:
            business_info = session_data.get('business_info', {})
            analysis_result = session_data.get('analysis_result', {})
            
            prompt = f"""
            다음 비즈니스에 대한 브랜딩 권장사항 5가지를 제시해주세요:
            
            업종: {business_info.get('industry', 'N/A')}
            지역: {business_info.get('region', 'N/A')}
            규모: {business_info.get('size', 'N/A')}
            분석 점수: {analysis_result.get('overall_score', 'N/A')}
            
            각 권장사항은 한 문장으로 작성하고, 실행 가능한 조언을 제공해주세요.
            """
            
            response = self.bedrock_client.generate_text(
                prompt=prompt,
                max_tokens=800,
                temperature=0.5
            )
            
            content = response.get('content', '')
            # Parse recommendations (assuming they're numbered or bulleted)
            recommendations = [
                line.strip().lstrip('0123456789.-•* ')
                for line in content.split('\n')
                if line.strip() and len(line.strip()) > 10
            ][:5]
            
            self.logger.info(f"Generated {len(recommendations)} AI recommendations")
            return recommendations
            
        except Exception as e:
            self.logger.warning(f"Failed to get branding recommendations: {str(e)}")
            return None
