#!/usr/bin/env python3
"""
Report Generator Agent
전체 브랜딩 결과를 PDF 보고서로 생성하는 Agent
"""

import json
import sys
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid
import io

# 프로젝트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

try:
    from base_agent import BaseAgent
    from models import BusinessInfo, WorkflowSession, AgentType
except ImportError:
    # 상대 경로로 시도
    import sys
    import os
    shared_path = os.path.join(os.path.dirname(__file__), '..', '..', 'shared')
    sys.path.insert(0, shared_path)
    from base_agent import BaseAgent
    from models import BusinessInfo, WorkflowSession, AgentType


class ReportGeneratorAgent(BaseAgent):
    """PDF 보고서 생성 Agent"""
    
    def __init__(self):
        super().__init__(AgentType.REPORT_GENERATOR)
        self.agent_name = "report-generator"
        
        # PDF 생성 라이브러리 import
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.pdfgen import canvas
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
            
            self.pdf_available = True
            self.logger.info("PDF generation libraries loaded successfully")
        except ImportError as e:
            self.pdf_available = False
            self.logger.warning(f"PDF libraries not available: {str(e)}")
    
    def execute(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Report Generator Agent 실행 로직"""
        try:
            # 요청 파싱
            if isinstance(event.get('body'), str):
                body = json.loads(event['body'])
            else:
                body = event.get('body', event)
            
            session_id = body.get('sessionId')
            action = body.get('action', 'generate')
            
            if not session_id:
                return self.create_lambda_response(400, {
                    "error": "sessionId is required"
                })
            
            # 실행 시작
            self.start_execution(session_id, "report.generate")
            
            # PDF 보고서 생성
            if action == 'generate':
                result = self._generate_pdf_report(session_id)
            elif action == 'download':
                result = self._get_download_url(session_id)
            else:
                raise ValueError(f"Unknown action: {action}")
            
            # 실행 완료
            self.end_execution("success", result=result)
            
            return self.create_lambda_response(200, result)
            
        except Exception as e:
            error_message = f"Report Generator Agent execution failed: {str(e)}"
            self.end_execution("error", error_message)
            
            error_response = self.handle_error(e, "execute")
            return self.create_lambda_response(500, error_response)
    
    def _generate_pdf_report(self, session_id: str) -> Dict[str, Any]:
        """보고서 생성 - PDF 대신 HTML/JSON/텍스트 형식 지원"""
        start_time = time.time()
        
        try:
            # 1. 세션 데이터 수집
            self.logger.info(f"Starting comprehensive report generation for session {session_id}")
            session_data = self._collect_comprehensive_session_data(session_id)
            
            if not session_data:
                raise ValueError(f"No data found for session {session_id}")
            
            collection_time = time.time() - start_time
            self.logger.info(f"Data collection completed in {collection_time:.2f}s")
            
            # 2. 대안 보고서 생성 (HTML 우선, 폴백으로 JSON/텍스트)
            report_start = time.time()
            report_result = self._generate_alternative_report(session_data)
            report_time = time.time() - report_start
            self.logger.info(f"Report generation completed in {report_time:.2f}s")
            
            # 3. S3/MinIO에 저장 및 presigned URL 생성
            storage_start = time.time()
            storage_info = self._store_alternative_report(report_result, session_id)
            storage_time = time.time() - storage_start
            self.logger.info(f"Storage and URL generation completed in {storage_time:.2f}s")
            
            total_time = time.time() - start_time
            self.logger.info(f"Total report generation time: {total_time:.2f}s")
            
            # 4. 세션 상태 업데이트
            self._update_session_with_report_info(session_id, storage_info)
            
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
                "components": {
                    "businessAnalysis": session_data.get("analysis_included", False),
                    "businessNames": len(session_data.get("business_names", [])),
                    "signboardImages": len(session_data.get("signboard_images", [])),
                    "interiorImages": len(session_data.get("interior_images", [])),
                    "colorPalette": session_data.get("color_palette_included", False),
                    "budgetGuide": session_data.get("budget_guide_included", False)
                }
            }
            
        except Exception as e:
            error_time = time.time() - start_time
            self.logger.error(f"Failed to generate report after {error_time:.2f}s: {str(e)}")
            # 최종 폴백으로 간단한 텍스트 보고서 생성
            return self._generate_simple_text_report(session_id)
    
    def _collect_session_data(self, session_id: str) -> Dict[str, Any]:
        """세션 데이터 수집"""
        try:
            # DynamoDB에서 세션 데이터 조회
            session_data = self.get_session_data(session_id)
            
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            # S3에서 이미지 파일들 조회
            try:
                from shared.s3_client import get_s3_client
            except ImportError:
                from s3_client import get_s3_client
            s3_client = get_s3_client()
            
            # 간판 이미지들
            signboard_images = s3_client.list_objects(prefix=f"signboards/{session_id}/")
            
            # 인테리어 이미지들
            interior_images = s3_client.list_objects(prefix=f"interiors/{session_id}/")
            
            return {
                "session": session_data,
                "signboard_images": signboard_images,
                "interior_images": interior_images,
                "session_id": session_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect session data: {str(e)}")
            return None
    
    def _collect_comprehensive_session_data(self, session_id: str) -> Dict[str, Any]:
        """종합 세션 데이터 수집 - 모든 선택 사항 통합"""
        try:
            # DynamoDB에서 세션 데이터 조회
            session_data = self.get_session_data(session_id)
            
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            # S3에서 모든 관련 파일들 조회
            try:
                from shared.s3_client import get_s3_client
            except ImportError:
                from s3_client import get_s3_client
            s3_client = get_s3_client()
            
            # 병렬로 이미지 데이터 수집
            signboard_images = s3_client.list_objects(prefix=f"signboards/{session_id}/")
            interior_images = s3_client.list_objects(prefix=f"interiors/{session_id}/")
            uploaded_images = s3_client.list_objects(prefix=f"uploads/{session_id}/")
            
            # 비즈니스 정보 파싱
            business_info = session_data.get("business_info", {})
            if isinstance(business_info, str):
                try:
                    business_info = json.loads(business_info)
                except:
                    business_info = {}
            elif hasattr(business_info, 'get') and 'S' in business_info:
                try:
                    business_info = json.loads(business_info.get('S', '{}'))
                except:
                    business_info = {}
            
            # 분석 결과 파싱
            analysis_result = session_data.get("analysis_result", {})
            if isinstance(analysis_result, str):
                try:
                    analysis_result = json.loads(analysis_result)
                except:
                    analysis_result = {}
            
            # 상호명 후보들 파싱
            business_names = session_data.get("business_names", [])
            if isinstance(business_names, str):
                try:
                    business_names = json.loads(business_names)
                except:
                    business_names = []
            
            # 선택된 항목들
            selected_name = session_data.get("selected_name", "")
            selected_signboard = session_data.get("selected_signboard", "")
            selected_interior = session_data.get("selected_interior", "")
            
            # 색상 팔레트 생성
            color_palette = self._generate_color_palette(business_info)
            
            # 예산 가이드 생성
            budget_guide = self._generate_budget_guide(business_info)
            
            # 권장사항 생성
            recommendations = self._generate_recommendations(business_info, analysis_result)
            
            return {
                "session": session_data,
                "session_id": session_id,
                "business_info": business_info,
                "analysis_result": analysis_result,
                "business_names": business_names,
                "selected_name": selected_name,
                "selected_signboard": selected_signboard,
                "selected_interior": selected_interior,
                "signboard_images": signboard_images,
                "interior_images": interior_images,
                "uploaded_images": uploaded_images,
                "color_palette": color_palette,
                "budget_guide": budget_guide,
                "recommendations": recommendations,
                "analysis_included": bool(analysis_result),
                "color_palette_included": True,
                "budget_guide_included": True,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect comprehensive session data: {str(e)}")
            return None
    
    def _create_pdf_document(self, data: Dict[str, Any]) -> io.BytesIO:
        """PDF 문서 생성 - 새로운 템플릿 사용"""
        try:
            # 새로운 PDF 템플릿 사용
            from pdf_template import create_branding_report_pdf
            
            self.logger.info("Creating PDF using enhanced template")
            pdf_buffer = create_branding_report_pdf(data)
            
            self.logger.info(f"PDF created successfully. Size: {len(pdf_buffer.getvalue())} bytes")
            return pdf_buffer
            
        except ImportError as e:
            self.logger.warning(f"Enhanced PDF template not available: {str(e)}, falling back to simple template")
            return self._create_simple_pdf_document(data)
        except Exception as e:
            self.logger.error(f"Failed to create PDF with enhanced template: {str(e)}, falling back to simple template")
            return self._create_simple_pdf_document(data)
    
    def _create_simple_pdf_document(self, data: Dict[str, Any]) -> io.BytesIO:
        """간단한 PDF 문서 생성 (폴백용)"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
            
            # 스타일 설정
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.darkblue
            )
            
            # 문서 내용 구성
            story = []
            
            # 제목
            story.append(Paragraph("AI 브랜딩 보고서", title_style))
            story.append(Spacer(1, 20))
            
            # 기본 정보
            session = data.get("session", {})
            business_info = session.get("business_info", {})
            
            if isinstance(business_info, str):
                business_info = json.loads(business_info)
            
            story.append(Paragraph("비즈니스 정보", heading_style))
            
            business_table_data = [
                ["업종", business_info.get("industry", "N/A")],
                ["지역", business_info.get("region", "N/A")],
                ["규모", business_info.get("size", "N/A")],
                ["생성일", datetime.now().strftime("%Y년 %m월 %d일")],
                ["세션 ID", data.get("session_id", "N/A")]
            ]
            
            business_table = Table(business_table_data, colWidths=[2*inch, 3*inch])
            business_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(business_table)
            story.append(Spacer(1, 20))
            
            # 상호명 추천
            story.append(Paragraph("추천 상호명", heading_style))
            story.append(Paragraph("AI가 분석한 최적의 상호명 후보들입니다.", styles['Normal']))
            story.append(Spacer(1, 10))
            
            # 간판 디자인 섹션
            signboard_images = data.get("signboard_images", [])
            if signboard_images:
                story.append(Paragraph("간판 디자인", heading_style))
                story.append(Paragraph(f"총 {len(signboard_images)}개의 간판 디자인이 생성되었습니다.", styles['Normal']))
                story.append(Spacer(1, 10))
                
                # 이미지 정보 테이블
                image_table_data = [["파일명", "크기", "스타일"]]
                for img in signboard_images:
                    filename = img.get('key', '').split('/')[-1]
                    size_mb = img.get('size', 0) / (1024 * 1024)
                    style = "Classic" if "classic" in filename else "Modern" if "modern" in filename else "Vibrant"
                    image_table_data.append([filename, f"{size_mb:.1f}MB", style])
                
                image_table = Table(image_table_data, colWidths=[3*inch, 1*inch, 1*inch])
                image_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(image_table)
                story.append(Spacer(1, 20))
            
            # 인테리어 디자인 섹션
            interior_images = data.get("interior_images", [])
            if interior_images:
                story.append(Paragraph("인테리어 디자인", heading_style))
                story.append(Paragraph(f"총 {len(interior_images)}개의 인테리어 디자인이 생성되었습니다.", styles['Normal']))
                story.append(Spacer(1, 10))
                
                # 인테리어 이미지 정보 테이블
                interior_table_data = [["파일명", "크기", "스타일"]]
                for img in interior_images:
                    filename = img.get('key', '').split('/')[-1]
                    size_mb = img.get('size', 0) / (1024 * 1024)
                    style = "모던" if "모던" in filename else "스칸디나비안" if "스칸디나비안" in filename else "코지"
                    interior_table_data.append([filename, f"{size_mb:.1f}MB", style])
                
                interior_table = Table(interior_table_data, colWidths=[3*inch, 1*inch, 1*inch])
                interior_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(interior_table)
                story.append(Spacer(1, 20))
            
            # 요약 및 권장사항
            story.append(Paragraph("요약 및 권장사항", heading_style))
            
            summary_text = f"""
            이 보고서는 AI 브랜딩 시스템을 통해 생성된 종합적인 브랜딩 솔루션입니다.
            
            • 업종: {business_info.get('industry', 'N/A')}에 최적화된 디자인
            • 지역: {business_info.get('region', 'N/A')} 지역 특성 반영
            • 규모: {business_info.get('size', 'N/A')} 규모에 적합한 솔루션
            
            생성된 자산:
            • 간판 디자인: {len(signboard_images)}개
            • 인테리어 디자인: {len(interior_images)}개
            
            모든 디자인은 OpenAI DALL-E 3를 통해 생성되었으며, 
            비즈니스의 특성과 목표 고객층을 고려하여 최적화되었습니다.
            """
            
            story.append(Paragraph(summary_text, styles['Normal']))
            
            # PDF 생성
            doc.build(story)
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            self.logger.error(f"Failed to create simple PDF document: {str(e)}")
            raise
    
    def _store_pdf_report(self, pdf_buffer: io.BytesIO, session_id: str) -> str:
        """PDF 보고서를 S3/MinIO에 저장"""
        try:
            try:
                from shared.s3_client import get_s3_client
            except ImportError:
                from s3_client import get_s3_client
            
            s3_client = get_s3_client()
            if not s3_client:
                raise ValueError("S3 client not available")
            
            # S3 키 생성
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            s3_key = f"reports/{session_id}/branding_report_{timestamp}.pdf"
            
            # 메타데이터
            metadata = {
                'session_id': session_id,
                'report_type': 'branding_report',
                'generated_by': 'report-generator-agent',
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # 업로드
            upload_result = s3_client.upload_file(
                file_content=pdf_buffer.getvalue(),
                key=s3_key,
                content_type='application/pdf',
                metadata=metadata
            )
            
            if upload_result.get('success'):
                self.logger.info(f"Successfully stored PDF report: {s3_key}")
                return upload_result.get('url')
            else:
                raise ValueError(f"Failed to upload PDF: {upload_result}")
                
        except Exception as e:
            self.logger.error(f"Error storing PDF report: {str(e)}")
            raise
    
    def _generate_alternative_report(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """대안 보고서 생성 - HTML, JSON, 텍스트 형식 지원"""
        try:
            from alternative_report_generator import AlternativeReportGenerator
            
            alt_generator = AlternativeReportGenerator(self.logger)
            
            # HTML 보고서 우선 시도
            try:
                html_content = alt_generator.generate_html_report(session_data)
                self.logger.info("Successfully generated HTML report")
                return {
                    "content": html_content,
                    "format": "html",
                    "content_type": "text/html",
                    "file_extension": "html"
                }
            except Exception as e:
                self.logger.warning(f"HTML report generation failed: {str(e)}, trying JSON")
            
            # JSON 보고서 폴백
            try:
                json_content = alt_generator.generate_json_report(session_data)
                self.logger.info("Successfully generated JSON report")
                return {
                    "content": json.dumps(json_content, ensure_ascii=False, indent=2),
                    "format": "json",
                    "content_type": "application/json",
                    "file_extension": "json"
                }
            except Exception as e:
                self.logger.warning(f"JSON report generation failed: {str(e)}, trying text")
            
            # 텍스트 보고서 최종 폴백
            text_content = alt_generator.generate_text_report(session_data)
            self.logger.info("Successfully generated text report")
            return {
                "content": text_content,
                "format": "text",
                "content_type": "text/plain",
                "file_extension": "txt"
            }
            
        except ImportError:
            self.logger.warning("Alternative report generator not available, using simple text")
            return self._generate_simple_text_fallback(session_data)
        except Exception as e:
            self.logger.error(f"All alternative report formats failed: {str(e)}")
            return self._generate_simple_text_fallback(session_data)
    
    def _generate_simple_text_fallback(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """최종 폴백용 간단한 텍스트 보고서"""
        business_info = session_data.get("business_info", {})
        signboard_images = session_data.get("signboard_images", [])
        interior_images = session_data.get("interior_images", [])
        
        content = f"""
AI 브랜딩 보고서
================

비즈니스 정보:
- 업종: {business_info.get('industry', 'N/A')}
- 지역: {business_info.get('region', 'N/A')}
- 규모: {business_info.get('size', 'N/A')}
- 생성일: {datetime.now().strftime('%Y년 %m월 %d일')}

생성된 자산:
- 간판 디자인: {len(signboard_images)}개
- 인테리어 디자인: {len(interior_images)}개

세션 ID: {session_data.get('session_id', 'N/A')}
생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        return {
            "content": content,
            "format": "text",
            "content_type": "text/plain",
            "file_extension": "txt"
        }
    
    def _store_alternative_report(self, report_result: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """대안 보고서를 S3/MinIO에 저장"""
        try:
            try:
                from shared.s3_client import get_s3_client
            except ImportError:
                from s3_client import get_s3_client
            
            s3_client = get_s3_client()
            if not s3_client:
                raise ValueError("S3 client not available")
            
            # 파일 정보 생성
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            format_type = report_result.get("format", "txt")
            file_extension = report_result.get("file_extension", "txt")
            content_type = report_result.get("content_type", "text/plain")
            
            file_name = f"branding_report_{timestamp}.{file_extension}"
            s3_key = f"reports/{session_id}/{file_name}"
            
            # 메타데이터
            metadata = {
                'session_id': session_id,
                'report_type': 'branding_report',
                'report_format': format_type,
                'generated_by': 'report-generator-agent',
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # 콘텐츠 인코딩
            content = report_result.get("content", "")
            if isinstance(content, str):
                content_bytes = content.encode('utf-8')
            else:
                content_bytes = str(content).encode('utf-8')
            
            # 업로드
            upload_result = s3_client.upload_file(
                file_content=content_bytes,
                key=s3_key,
                content_type=content_type,
                metadata=metadata
            )
            
            if upload_result.get('success'):
                self.logger.info(f"Successfully stored {format_type} report: {s3_key}")
                
                # presigned URL 생성
                presigned_url = s3_client.generate_presigned_url(s3_key, expiration=600)  # 10분
                
                return {
                    "presigned_url": presigned_url,
                    "direct_url": upload_result.get('url'),
                    "file_name": file_name,
                    "file_size": len(content_bytes),
                    "report_type": format_type,
                    "s3_key": s3_key
                }
            else:
                raise ValueError(f"Failed to upload {format_type} report: {upload_result}")
                
        except Exception as e:
            self.logger.error(f"Error storing alternative report: {str(e)}")
            raise
    
    def _generate_simple_text_report(self, session_id: str) -> Dict[str, Any]:
        """최종 폴백용 간단한 텍스트 보고서 생성"""
        try:
            session_data = self._collect_session_data(session_id)
            
            if not session_data:
                raise ValueError(f"No data found for session {session_id}")
            
            # 간단한 텍스트 보고서 생성
            report_text = self._create_simple_text_report(session_data)
            
            return {
                "sessionId": session_id,
                "reportContent": report_text,
                "reportType": "text",
                "generatedAt": datetime.utcnow().isoformat(),
                "success": True,
                "note": "Fallback text report - other formats not available"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate simple text report: {str(e)}")
            # 최종 최종 폴백
            return {
                "sessionId": session_id,
                "reportContent": f"보고서 생성 실패: {str(e)}",
                "reportType": "error",
                "generatedAt": datetime.utcnow().isoformat(),
                "success": False,
                "error": str(e)
            }
    
    def _create_simple_text_report(self, data: Dict[str, Any]) -> str:
        """간단한 텍스트 보고서 생성"""
        session = data.get("session", {})
        business_info = session.get("business_info", {})
        
        if isinstance(business_info, str):
            try:
                business_info = json.loads(business_info)
            except:
                business_info = {}
        
        signboard_images = data.get("signboard_images", [])
        interior_images = data.get("interior_images", [])
        
        report = f"""
AI 브랜딩 보고서
================

비즈니스 정보:
- 업종: {business_info.get('industry', 'N/A')}
- 지역: {business_info.get('region', 'N/A')}
- 규모: {business_info.get('size', 'N/A')}
- 생성일: {datetime.now().strftime('%Y년 %m월 %d일')}
- 세션 ID: {data.get('session_id', 'N/A')}

생성된 자산:
- 간판 디자인: {len(signboard_images)}개
- 인테리어 디자인: {len(interior_images)}개

간판 이미지:
{chr(10).join([f"- {img.get('key', '').split('/')[-1]} ({img.get('size', 0) / (1024*1024):.1f}MB)" for img in signboard_images])}

인테리어 이미지:
{chr(10).join([f"- {img.get('key', '').split('/')[-1]} ({img.get('size', 0) / (1024*1024):.1f}MB)" for img in interior_images])}

요약:
이 보고서는 AI 브랜딩 시스템을 통해 생성된 종합적인 브랜딩 솔루션입니다.
모든 디자인은 비즈니스의 특성과 목표를 고려하여 최적화되었습니다.

Generated by AI Branding Chatbot on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return report.strip()
    
    def _generate_color_palette(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """업종별 색상 팔레트 생성"""
        industry = business_info.get('industry', '').lower()
        
        color_palettes = {
            '카페': {
                'primary': {'name': '따뜻한 브라운', 'hex': '#8B4513', 'usage': '로고, 간판'},
                'secondary': {'name': '크림 베이지', 'hex': '#F5F5DC', 'usage': '배경, 인테리어'},
                'accent': {'name': '골드', 'hex': '#FFD700', 'usage': '포인트 요소'},
                'text': {'name': '다크 브라운', 'hex': '#3C2415', 'usage': '텍스트'}
            },
            '레스토랑': {
                'primary': {'name': '딥 레드', 'hex': '#B22222', 'usage': '로고, 간판'},
                'secondary': {'name': '웜 화이트', 'hex': '#FDF5E6', 'usage': '배경, 메뉴판'},
                'accent': {'name': '골든 옐로우', 'hex': '#DAA520', 'usage': '포인트 요소'},
                'text': {'name': '다크 레드', 'hex': '#8B0000', 'usage': '텍스트'}
            },
            '뷰티': {
                'primary': {'name': '소프트 핑크', 'hex': '#FFB6C1', 'usage': '로고, 간판'},
                'secondary': {'name': '펄 화이트', 'hex': '#F8F8FF', 'usage': '배경'},
                'accent': {'name': '로즈 골드', 'hex': '#E8B4B8', 'usage': '포인트 요소'},
                'text': {'name': '차콜 그레이', 'hex': '#36454F', 'usage': '텍스트'}
            }
        }
        
        # 기본 색상 팔레트
        default_palette = {
            'primary': {'name': '다크 블루', 'hex': '#1E3A8A', 'usage': '로고, 간판'},
            'secondary': {'name': '라이트 그레이', 'hex': '#F3F4F6', 'usage': '배경'},
            'accent': {'name': '그린', 'hex': '#10B981', 'usage': '포인트'},
            'text': {'name': '다크 그레이', 'hex': '#374151', 'usage': '텍스트'}
        }
        
        return color_palettes.get(industry, default_palette)
    
    def _generate_budget_guide(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """규모별 예산 가이드 생성"""
        size = business_info.get('size', '소규모')
        industry = business_info.get('industry', '')
        
        # 규모별 배수
        multipliers = {'소규모': 1.0, '중규모': 1.8, '대규모': 3.0}
        multiplier = multipliers.get(size, 1.0)
        
        # 업종별 기본 비용
        industry_base_costs = {
            '카페': {
                'signboard': {'min': 800000, 'recommended': 1500000, 'max': 3000000},
                'interior': {'min': 5000000, 'recommended': 12000000, 'max': 25000000},
                'branding': {'min': 500000, 'recommended': 1200000, 'max': 2500000},
                'marketing': {'min': 300000, 'recommended': 800000, 'max': 1500000}
            },
            '레스토랑': {
                'signboard': {'min': 1000000, 'recommended': 2000000, 'max': 4000000},
                'interior': {'min': 8000000, 'recommended': 20000000, 'max': 40000000},
                'branding': {'min': 800000, 'recommended': 1800000, 'max': 3500000},
                'marketing': {'min': 500000, 'recommended': 1200000, 'max': 2500000}
            }
        }
        
        # 기본 비용 (업종별 데이터가 없는 경우)
        default_costs = {
            'signboard': {'min': 600000, 'recommended': 1200000, 'max': 2500000},
            'interior': {'min': 3000000, 'recommended': 8000000, 'max': 18000000},
            'branding': {'min': 400000, 'recommended': 1000000, 'max': 2000000},
            'marketing': {'min': 250000, 'recommended': 600000, 'max': 1200000}
        }
        
        base_costs = industry_base_costs.get(industry, default_costs)
        
        # 규모별 조정
        budget_guide = {}
        for category, costs in base_costs.items():
            budget_guide[category] = {
                'min': int(costs['min'] * multiplier),
                'recommended': int(costs['recommended'] * multiplier),
                'max': int(costs['max'] * multiplier)
            }
        
        # 총 예산 계산
        total_min = sum(item['min'] for item in budget_guide.values())
        total_recommended = sum(item['recommended'] for item in budget_guide.values())
        total_max = sum(item['max'] for item in budget_guide.values())
        
        budget_guide['total'] = {
            'min': total_min,
            'recommended': total_recommended,
            'max': total_max
        }
        
        return budget_guide
    
    def _generate_recommendations(self, business_info: Dict[str, Any], analysis_result: Dict[str, Any]) -> List[str]:
        """업종 및 분석 결과 기반 권장사항 생성"""
        industry = business_info.get('industry', '').lower()
        region = business_info.get('region', '')
        size = business_info.get('size', '')
        
        # 업종별 기본 권장사항
        industry_recommendations = {
            '카페': [
                "편안하고 아늑한 분위기 조성에 집중하세요",
                "SNS 친화적인 포토존 설치를 고려하세요",
                "계절별 메뉴와 연계한 인테리어 변화를 계획하세요",
                "자연광을 최대한 활용한 좌석 배치를 권장합니다"
            ],
            '레스토랑': [
                "음식의 맛을 돋보이게 하는 조명 설계가 중요합니다",
                "테이블 배치와 동선을 효율적으로 계획하세요",
                "브랜드 스토리를 공간에 녹여내는 것이 핵심입니다",
                "주방과 홀의 소음 차단에 신경 쓰세요"
            ],
            '뷰티': [
                "고급스럽고 청결한 이미지 구축이 최우선입니다",
                "고객 프라이버시를 고려한 공간 설계를 하세요",
                "조명은 피부톤을 자연스럽게 보이도록 설정하세요",
                "위생과 안전을 강조하는 인테리어를 선택하세요"
            ]
        }
        
        # 기본 권장사항
        default_recommendations = [
            "타겟 고객층의 니즈를 정확히 파악하여 반영하세요",
            "브랜드 일관성을 모든 접점에서 유지하세요",
            "지속적인 브랜드 발전을 위한 장기 계획을 수립하세요",
            "경쟁사 대비 차별화 포인트를 명확히 하세요"
        ]
        
        recommendations = industry_recommendations.get(industry, default_recommendations)
        
        # 분석 결과 기반 추가 권장사항
        if analysis_result:
            score = analysis_result.get('overall_score', 0)
            if score < 60:
                recommendations.append("시장 분석을 통해 포지셔닝을 재검토해보세요")
            elif score > 80:
                recommendations.append("높은 잠재력을 바탕으로 적극적인 마케팅을 추진하세요")
        
        # 지역별 추가 권장사항
        if '강남' in region:
            recommendations.append("고급스러운 이미지와 트렌디한 요소를 강조하세요")
        elif '홍대' in region:
            recommendations.append("젊고 개성 있는 컨셉으로 차별화하세요")
        
        return recommendations[:5]  # 최대 5개 권장사항
    
    def _create_comprehensive_pdf_document(self, data: Dict[str, Any]) -> io.BytesIO:
        """종합 PDF 문서 생성 - 모든 선택 사항 포함"""
        try:
            # 향상된 PDF 템플릿 사용
            from pdf_template import create_branding_report_pdf
            
            self.logger.info("Creating comprehensive PDF using enhanced template")
            pdf_buffer = create_branding_report_pdf(data)
            
            self.logger.info(f"Comprehensive PDF created successfully. Size: {len(pdf_buffer.getvalue())} bytes")
            return pdf_buffer
            
        except ImportError as e:
            self.logger.warning(f"Enhanced PDF template not available: {str(e)}, falling back to simple template")
            return self._create_simple_pdf_document(data)
        except Exception as e:
            self.logger.error(f"Failed to create PDF with enhanced template: {str(e)}, falling back to simple template")
            return self._create_simple_pdf_document(data)
    
    def _store_pdf_report_with_presigned_url(self, pdf_buffer: io.BytesIO, session_id: str) -> Dict[str, Any]:
        """PDF 보고서를 S3/MinIO에 저장하고 presigned URL 생성"""
        try:
            try:
                from shared.s3_client import get_s3_client
            except ImportError:
                from s3_client import get_s3_client
            
            s3_client = get_s3_client()
            if not s3_client:
                raise ValueError("S3 client not available")
            
            # S3 키 생성
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            file_name = f"branding_report_{timestamp}.pdf"
            s3_key = f"reports/{session_id}/{file_name}"
            
            # 메타데이터
            metadata = {
                'session_id': session_id,
                'report_type': 'comprehensive_branding_report',
                'generated_by': 'report-generator-agent',
                'generated_at': datetime.utcnow().isoformat(),
                'file_size': str(len(pdf_buffer.getvalue()))
            }
            
            # 업로드
            upload_result = s3_client.upload_file(
                file_content=pdf_buffer.getvalue(),
                key=s3_key,
                content_type='application/pdf',
                metadata=metadata
            )
            
            if not upload_result.get('success'):
                raise ValueError(f"Failed to upload PDF: {upload_result}")
            
            # presigned URL 생성 (10분 유효)
            presigned_url = s3_client.generate_presigned_url(
                key=s3_key,
                expiration=600  # 10분
            )
            
            self.logger.info(f"Successfully stored PDF report with presigned URL: {s3_key}")
            
            return {
                "s3_key": s3_key,
                "file_name": file_name,
                "direct_url": upload_result.get('url'),
                "presigned_url": presigned_url,
                "file_size": len(pdf_buffer.getvalue()),
                "expires_in": 600
            }
                
        except Exception as e:
            self.logger.error(f"Error storing PDF report with presigned URL: {str(e)}")
            raise
    
    def _update_session_with_report_info(self, session_id: str, pdf_info: Dict[str, Any]) -> None:
        """세션에 보고서 정보 업데이트"""
        try:
            update_data = {
                "pdf_report_path": pdf_info["s3_key"],
                "pdf_report_url": pdf_info["presigned_url"],
                "pdf_file_name": pdf_info["file_name"],
                "pdf_file_size": pdf_info["file_size"],
                "report_generated_at": datetime.utcnow().isoformat(),
                "current_step": 5  # 보고서 생성 완료
            }
            
            self.update_session_data(session_id, update_data)
            self.logger.info(f"Updated session {session_id} with report information")
            
        except Exception as e:
            self.logger.error(f"Failed to update session with report info: {str(e)}")
            # 세션 업데이트 실패는 치명적이지 않으므로 계속 진행
    
    def _get_download_url(self, session_id: str) -> Dict[str, Any]:
        """PDF 다운로드 URL 생성"""
        try:
            try:
                from shared.s3_client import get_s3_client
            except ImportError:
                from s3_client import get_s3_client
            
            s3_client = get_s3_client()
            
            # 최신 PDF 파일 찾기
            report_objects = s3_client.list_objects(prefix=f"reports/{session_id}/")
            
            if not report_objects:
                raise ValueError(f"No report found for session {session_id}")
            
            # 가장 최신 파일 선택
            latest_report = max(report_objects, key=lambda x: x.get('last_modified', ''))
            
            # presigned URL 생성 (10분 유효)
            download_url = s3_client.generate_presigned_url(
                key=latest_report['key'],
                expiration=600  # 10분
            )
            
            return {
                "sessionId": session_id,
                "downloadUrl": download_url,
                "fileName": latest_report['key'].split('/')[-1],
                "fileSize": latest_report.get('size', 0),
                "expiresIn": "10 minutes",
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get download URL: {str(e)}")
            raise


def lambda_handler(event, context):
    """Lambda 핸들러"""
    agent = ReportGeneratorAgent()
    return agent.execute(event, context)


if __name__ == "__main__":
    # 로컬 테스트용
    test_event = {
        'body': json.dumps({
            'sessionId': 'test-session-123',
            'action': 'generate'
        })
    }
    
    class MockContext:
        function_name = "test-report-generator-agent"
        aws_request_id = "test-request-id"
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2, ensure_ascii=False))