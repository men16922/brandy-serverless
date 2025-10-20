#!/usr/bin/env python3
"""
Report Generator Agent - Refactored
Generates comprehensive branding reports in various formats
"""

import json
import sys
import os
import time
from datetime import datetime
from typing import Dict, Any

# Add shared modules to path - Lambda Layer structure
sys.path.insert(0, '/opt/python/python')

# Import local modules
from data_sanitizer import DataSanitizer
from data_collector import DataCollector
from utils import ReportUtils
from business_utils import BusinessUtils
from storage_manager import StorageManager
from bedrock_integration import BedrockIntegration
from report_generator import ReportGenerator

# Import shared modules
try:
    from shared.base_agent import BaseAgent
    from shared.models import BusinessInfo, WorkflowSession, AgentType
    HAS_SHARED_MODULES = True
    print("✓ Successfully imported shared modules")
except ImportError as e:
    print(f"Failed to import shared modules: {e}")
    HAS_SHARED_MODULES = False
    # Fallback: try relative import
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
    from base_agent import BaseAgent
    from models import BusinessInfo, WorkflowSession, AgentType


class ReportGeneratorAgent(BaseAgent):
    """Report Generator Agent - Orchestrates report generation workflow"""
    
    def __init__(self):
        super().__init__(AgentType.REPORT_GENERATOR)
        self.agent_name = "report-generator"
        
        # Initialize utility modules
        self.sanitizer = DataSanitizer(logger=self.logger)
        self.collector = DataCollector(base_agent=self, logger=self.logger)
        self.utils = ReportUtils()
        self.business_utils = BusinessUtils(logger=self.logger)
        self.storage_manager = StorageManager(logger=self.logger)
        
        # Initialize Bedrock integration
        enable_bedrock = os.getenv('ENABLE_FALLBACK', 'false').lower() != 'true'
        self.bedrock_integration = BedrockIntegration(
            logger=self.logger,
            enable_bedrock=enable_bedrock
        )
        
        # Initialize report generator
        self.report_generator = ReportGenerator(
            logger=self.logger,
            bedrock_integration=self.bedrock_integration,
            business_utils=self.business_utils,
            data_sanitizer=self.sanitizer
        )
        
        self.logger.info("ReportGeneratorAgent initialized successfully")
    
    def execute(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Report Generator Agent execution logic"""
        try:
            # Parse request - support both GET and POST
            query_params = event.get('queryStringParameters', {}) or {}
            
            if isinstance(event.get('body'), str):
                body = json.loads(event['body'])
            else:
                body = event.get('body', {})
            
            # Get sessionId from query parameter or body
            session_id = (
                query_params.get('session_id') or 
                query_params.get('sessionId') or 
                body.get('sessionId')
            )
            action = body.get('action', 'download' if query_params else 'generate')
            
            if not session_id:
                return self.create_lambda_response(400, {
                    "error": "sessionId is required"
                })
            
            # Start execution
            self.start_execution(session_id, "report.generate")
            
            # Execute action
            if action == 'generate':
                result = self._generate_report(session_id)
            elif action == 'download':
                result = self._get_download_url(session_id)
            else:
                raise ValueError(f"Unknown action: {action}")
            
            # End execution
            self.end_execution("success", result=result)
            
            return self.create_lambda_response(200, result)
            
        except Exception as e:
            error_message = f"Report Generator Agent execution failed: {str(e)}"
            self.end_execution("error", error_message)
            
            error_response = self.handle_error(e, "execute")
            return self.create_lambda_response(500, error_response)
    
    def _generate_report(self, session_id: str) -> Dict[str, Any]:
        """Generate comprehensive report"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting report generation for session {session_id}")
            
            # 1. Collect session data
            session_data = self._collect_comprehensive_session_data(session_id)
            if not session_data:
                raise ValueError(f"No data found for session {session_id}")
            
            collection_time = time.time() - start_time
            self.logger.info(f"Data collection completed in {collection_time:.2f}s")
            
            # 2. Generate report (HTML format by default)
            report_start = time.time()
            report_result = self.report_generator.generate_report(
                session_data=session_data,
                format_type="html"
            )
            report_time = time.time() - report_start
            self.logger.info(f"Report generation completed in {report_time:.2f}s")
            
            # 3. Store report to S3
            storage_start = time.time()
            storage_info = self.storage_manager.store_report(
                content=report_result.get("content"),
                session_id=session_id,
                format_type=report_result.get("format"),
                content_type=report_result.get("content_type"),
                file_extension=report_result.get("file_extension")
            )
            storage_time = time.time() - storage_start
            self.logger.info(f"Storage completed in {storage_time:.2f}s")
            
            total_time = time.time() - start_time
            self.logger.info(f"Total report generation time: {total_time:.2f}s")
            
            # 4. Update session with report info
            self.storage_manager.update_session_with_report_info(
                session_id=session_id,
                storage_info=storage_info,
                update_session_callback=self.update_session_data
            )
            
            # 5. Return result
            return {
                "sessionId": session_id,
                "reportUrl": storage_info.get("presigned_url"),
                "directUrl": storage_info.get("direct_url"),
                "reportType": storage_info.get("report_type", "html"),
                "reportContent": report_result.get("content") if storage_info.get("report_type") == "json" else None,
                "generatedAt": datetime.utcnow().isoformat(),
                "fileSize": storage_info.get("file_size", 0),
                "fileName": storage_info.get("file_name"),
                "downloadExpiry": "10 minutes",
                "processingTime": f"{total_time:.2f}s",
                "success": True,
                "bedrockEnhanced": report_result.get("bedrock_enhanced", False),
                "components": {
                    "businessAnalysis": session_data.get("analysis_included", False),
                    "businessNames": len(session_data.get("business_names", [])),
                    "signboardImages": len(session_data.get("signboard_images", [])),
                    "interiorImages": len(session_data.get("interior_images", [])),
                    "colorPalette": session_data.get("color_palette_included", False),
                    "budgetGuide": session_data.get("budget_guide_included", False),
                    "bedrockInsights": report_result.get("bedrock_enhanced", False)
                }
            }
            
        except Exception as e:
            error_time = time.time() - start_time
            self.logger.error(f"Failed to generate report after {error_time:.2f}s: {str(e)}")
            raise
    
    def _collect_comprehensive_session_data(self, session_id: str) -> Dict[str, Any]:
        """Collect comprehensive session data with all assets"""
        try:
            # Verify dependencies are available
            if not self.storage_manager.s3_client:
                self.logger.warning("S3 client not available, images will not be collected")
            
            if not self.sanitizer:
                self.logger.warning("Data sanitizer not available, data may not be properly formatted")
            
            # Use DataCollector to get session data with all required parameters
            session_data = self.collector.collect_comprehensive_session_data(
                session_id=session_id,
                s3_client=self.storage_manager.s3_client,
                sanitizer=self.sanitizer
            )
            
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            self.logger.info(f"Successfully collected comprehensive session data for {session_id}")
            
            # Add business logic utilities
            business_info = session_data.get("business_info", {})
            
            # Generate color palette
            color_palette = self.business_utils.generate_color_palette(business_info)
            session_data['color_palette'] = color_palette
            session_data['color_palette_included'] = True
            
            # Generate budget guide
            budget_guide = self.business_utils.generate_budget_guide(business_info)
            session_data['budget_guide'] = budget_guide
            session_data['budget_guide_included'] = True
            
            # Generate recommendations
            analysis_result = session_data.get("analysis_result", {})
            recommendations = self.business_utils.generate_recommendations(
                business_info,
                analysis_result
            )
            session_data['recommendations'] = recommendations
            
            # Mark analysis included
            session_data['analysis_included'] = bool(analysis_result)
            
            self.logger.info(
                f"Comprehensive session data collected for {session_id}",
                extra={
                    "session_id": session_id,
                    "has_business_info": bool(business_info),
                    "has_analysis": bool(analysis_result),
                    "business_names_count": len(session_data.get("business_names", [])),
                    "signboard_images_count": len(session_data.get("signboard_images", [])),
                    "interior_images_count": len(session_data.get("interior_images", []))
                }
            )
            return session_data
            
        except Exception as e:
            self.logger.error(
                f"Failed to collect comprehensive session data: {str(e)}",
                extra={
                    "session_id": session_id,
                    "agent": "report-generator",
                    "operation": "collect_session_data",
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise
    
    def _get_download_url(self, session_id: str) -> Dict[str, Any]:
        """Get download URL for existing report"""
        try:
            return self.storage_manager.get_download_url(session_id)
        except Exception as e:
            self.logger.error(f"Failed to get download URL: {str(e)}")
            raise


def lambda_handler(event, context):
    """AWS Lambda handler"""
    agent = ReportGeneratorAgent()
    return agent.execute(event, context)
