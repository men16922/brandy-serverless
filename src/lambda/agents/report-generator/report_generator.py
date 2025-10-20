"""
Report generation module
Handles creation of reports in multiple formats (PDF, HTML, JSON, Text)
"""
from typing import Dict, Any
import logging
import time
import json
from datetime import datetime


class ReportGenerator:
    """Generates reports in various formats with optional AI-based enhancement"""

    def __init__(
        self,
        logger=None,
        bedrock_integration=None,
        business_utils=None,
        data_sanitizer=None
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.bedrock = bedrock_integration
        self.business_utils = business_utils
        self.data_sanitizer = data_sanitizer

    def generate_report(
        self,
        session_data: Dict[str, Any],
        format_type: str = "html"
    ) -> Dict[str, Any]:
        """
        Generate a report in the specified format.

        Args:
            session_data: Complete session data.
            format_type: Desired report format (html, json, text, pdf).

        Returns:
            A dictionary containing content, format, content_type, file_extension, and bedrock_enhanced.
        """
        try:
            # Sanitize session data (remove DynamoDB format, etc.)
            if self.data_sanitizer:
                session_data = self.data_sanitizer.sanitize_session_data(session_data)
                self.logger.info("Session data sanitized successfully.")

            # Try to enhance report using Bedrock if enabled
            bedrock_enhanced = False
            if self.bedrock and self.bedrock.is_enabled():
                insights = self.bedrock.synthesize_insights(session_data)
                if insights:
                    session_data['synthesized_insights'] = insights
                    bedrock_enhanced = True
                    self.logger.info("Added Bedrock-synthesized insights to the report.")

            # Generate report by format type
            if format_type.lower() == "html":
                return self._generate_html_report(session_data, bedrock_enhanced)
            elif format_type.lower() == "json":
                return self._generate_json_report(session_data, bedrock_enhanced)
            elif format_type.lower() == "text":
                return self._generate_text_report(session_data, bedrock_enhanced)
            elif format_type.lower() == "pdf":
                return self._generate_pdf_report(session_data, bedrock_enhanced)
            else:
                raise ValueError(f"Unsupported format: {format_type}")

        except Exception as e:
            self.logger.error(f"Error generating {format_type} report: {str(e)}")
            raise

    def _generate_html_report(
        self,
        session_data: Dict[str, Any],
        bedrock_enhanced: bool
    ) -> Dict[str, Any]:
        """Generate an HTML report."""
        try:
            import importlib.util
            import os

            alt_gen_path = os.path.join(os.path.dirname(__file__), 'alternative_report_generator.py')
            spec = importlib.util.spec_from_file_location("alternative_report_generator", alt_gen_path)
            alt_gen_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(alt_gen_module)
            AlternativeReportGenerator = alt_gen_module.AlternativeReportGenerator

            alt_generator = AlternativeReportGenerator(self.logger)
            html_content = alt_generator.generate_html_report(session_data)

            self.logger.info("Successfully generated HTML report.")
            return {
                "content": html_content,
                "format": "html",
                "content_type": "text/html",
                "file_extension": "html",
                "bedrock_enhanced": bedrock_enhanced
            }

        except Exception as e:
            self.logger.warning(f"HTML report generation failed: {str(e)}. Falling back to JSON.")
            return self._generate_json_report(session_data, bedrock_enhanced)

    def _generate_json_report(
        self,
        session_data: Dict[str, Any],
        bedrock_enhanced: bool
    ) -> Dict[str, Any]:
        """Generate a JSON report."""
        try:
            import importlib.util
            import os

            alt_gen_path = os.path.join(os.path.dirname(__file__), 'alternative_report_generator.py')
            spec = importlib.util.spec_from_file_location("alternative_report_generator", alt_gen_path)
            alt_gen_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(alt_gen_module)
            AlternativeReportGenerator = alt_gen_module.AlternativeReportGenerator

            alt_generator = AlternativeReportGenerator(self.logger)
            json_content = alt_generator.generate_json_report(session_data)

            self.logger.info("Successfully generated JSON report.")
            return {
                "content": json.dumps(json_content, ensure_ascii=False, indent=2),
                "format": "json",
                "content_type": "application/json",
                "file_extension": "json",
                "bedrock_enhanced": bedrock_enhanced
            }

        except Exception as e:
            self.logger.warning(f"JSON report generation failed: {str(e)}. Falling back to text.")
            return self._generate_text_report(session_data, bedrock_enhanced)

    def _generate_text_report(
        self,
        session_data: Dict[str, Any],
        bedrock_enhanced: bool
    ) -> Dict[str, Any]:
        """Generate a plain text report."""
        try:
            import importlib.util
            import os

            alt_gen_path = os.path.join(os.path.dirname(__file__), 'alternative_report_generator.py')
            spec = importlib.util.spec_from_file_location("alternative_report_generator", alt_gen_path)
            alt_gen_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(alt_gen_module)
            AlternativeReportGenerator = alt_gen_module.AlternativeReportGenerator

            alt_generator = AlternativeReportGenerator(self.logger)
            text_content = alt_generator.generate_text_report(session_data)

            self.logger.info("Successfully generated text report.")
            return {
                "content": text_content,
                "format": "text",
                "content_type": "text/plain",
                "file_extension": "txt",
                "bedrock_enhanced": bedrock_enhanced
            }

        except Exception as e:
            self.logger.error(f"Text report generation failed: {str(e)}")
            return self._generate_simple_text_report(session_data, bedrock_enhanced)

    def _generate_pdf_report(
        self,
        session_data: Dict[str, Any],
        bedrock_enhanced: bool
    ) -> Dict[str, Any]:
        """Generate a PDF report."""
        try:
            from pdf_template import create_branding_report_pdf
            import io

            self.logger.info("Creating PDF using enhanced template.")
            pdf_buffer = create_branding_report_pdf(session_data)

            self.logger.info(f"PDF created successfully. Size: {len(pdf_buffer.getvalue())} bytes.")
            return {
                "content": pdf_buffer.getvalue(),
                "format": "pdf",
                "content_type": "application/pdf",
                "file_extension": "pdf",
                "bedrock_enhanced": bedrock_enhanced
            }

        except Exception as e:
            self.logger.warning(f"PDF generation failed: {str(e)}. Falling back to HTML.")
            return self._generate_html_report(session_data, bedrock_enhanced)

    def _generate_simple_text_report(
        self,
        session_data: Dict[str, Any],
        bedrock_enhanced: bool
    ) -> Dict[str, Any]:
        """Generate a minimal text report as the final fallback."""
        try:
            business_info = session_data.get('business_info', {})
            business_names = session_data.get('business_names', [])
            signboard_images = session_data.get('signboard_images', [])
            interior_images = session_data.get('interior_images', [])

            text_content = f"""
AI Branding Report
==================

Business Information:
- Industry: {business_info.get('industry', 'N/A')}
- Region: {business_info.get('region', 'N/A')}
- Size: {business_info.get('size', 'N/A')}

Suggested Business Names:
{chr(10).join([f"- {name}" for name in business_names[:5]])}

Generated Assets:
- Signboard Designs: {len(signboard_images)}
- Interior Designs: {len(interior_images)}

Generated At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

This report was generated by the AI Branding System.
            """.strip()

            self.logger.info("Generated simple text report as fallback.")
            return {
                "content": text_content,
                "format": "text",
                "content_type": "text/plain",
                "file_extension": "txt",
                "bedrock_enhanced": bedrock_enhanced
            }

        except Exception as e:
            self.logger.error(f"Even simple text report failed: {str(e)}")
            return {
                "content": f"Report generation failed: {str(e)}",
                "format": "text",
                "content_type": "text/plain",
                "file_extension": "txt",
                "bedrock_enhanced": False
            }

    def generate_comprehensive_report(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        format_type: str = "html"
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive report including timing and metadata.

        Args:
            session_id: Unique session identifier.
            session_data: Complete session data.
            format_type: Report format.

        Returns:
            Complete report dictionary including metadata.
        """
        start_time = time.time()

        try:
            self.logger.info(f"Starting comprehensive report generation for session {session_id}.")

            report_start = time.time()
            report_result = self.generate_report(session_data, format_type)
            report_time = time.time() - report_start
            self.logger.info(f"Report generation completed in {report_time:.2f}s.")

            total_time = time.time() - start_time

            report_result['session_id'] = session_id
            report_result['processing_time'] = f"{total_time:.2f}s"
            report_result['generated_at'] = datetime.utcnow().isoformat()

            return report_result

        except Exception as e:
            error_time = time.time() - start_time
            self.logger.error(f"Failed to generate report after {error_time:.2f}s: {str(e)}")
            raise
