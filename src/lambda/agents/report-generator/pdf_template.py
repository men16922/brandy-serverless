#!/usr/bin/env python3
"""
PDF Template for AI Branding Report
브랜딩 보고서 PDF 템플릿 구현
"""

import json
import io
from datetime import datetime
from typing import Dict, Any, List
import logging

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class BrandingReportTemplate:
    """AI 브랜딩 보고서 PDF 템플릿"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if not PDF_AVAILABLE:
            self.logger.warning("ReportLab not available")
            return
            
        self.page_width, self.page_height = A4
        self.margin = 2*cm
        
        # 색상 정의
        self.primary_color = colors.Color(0.2, 0.3, 0.6)
        self.accent_color = colors.Color(0.9, 0.6, 0.2)
        
        # 한글 폰트 설정
        self._setup_korean_fonts()
        
        # 스타일 설정
        self._setup_styles()
    
    def _setup_korean_fonts(self):
        """폰트 설정 - 한글 문제 해결을 위해 영어 우선 사용"""
        try:
            # 한글 폰트 문제를 완전히 피하기 위해 Helvetica 사용
            self.korean_font = 'Helvetica'
            self.use_unicode = False
            self.force_english = True  # 모든 텍스트를 영어로 변환
            
            self.logger.info("Using Helvetica font with English translation for Korean text")
            
        except Exception as e:
            self.logger.error(f"Font setup failed: {e}")
            self.korean_font = 'Helvetica'
            self.use_unicode = False
            self.force_english = True
    
    def _setup_styles(self):
        """PDF 스타일 설정"""
        if not PDF_AVAILABLE:
            return
            
        self.styles = getSampleStyleSheet()
        
        # 커스텀 스타일 (한글 폰트 적용)
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,  # 크기 줄여서 안정성 향상
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=self.primary_color,
            fontName=self.korean_font,
            wordWrap='CJK'  # 한글 줄바꿈 지원
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,  # 크기 줄여서 안정성 향상
            spaceAfter=15,
            textColor=self.primary_color,
            fontName=self.korean_font,
            wordWrap='CJK'
        )
        
        self.section_style = ParagraphStyle(
            'SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,  # 크기 줄여서 안정성 향상
            spaceAfter=12,
            textColor=self.accent_color,
            fontName=self.korean_font,
            wordWrap='CJK'
        )
        
        self.normal_style = ParagraphStyle(
            'KoreanNormal',
            parent=self.styles['Normal'],
            fontSize=9,  # 크기 줄여서 안정성 향상
            fontName=self.korean_font,
            wordWrap='CJK',
            leading=12  # 줄 간격 설정
        )
    
    def create_report(self, data: Dict[str, Any]) -> io.BytesIO:
        """브랜딩 보고서 PDF 생성"""
        if not PDF_AVAILABLE:
            raise ImportError("ReportLab not available for PDF generation")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=self.margin,
            bottomMargin=self.margin,
            leftMargin=self.margin,
            rightMargin=self.margin
        )
        
        story = []
        
        # 표지
        story.extend(self._create_cover(data))
        story.append(PageBreak())
        
        # 비즈니스 정보
        story.extend(self._create_business_info(data))
        
        # 분석 결과
        story.extend(self._create_analysis(data))
        
        # 상호명
        story.extend(self._create_names(data))
        
        # 간판 디자인
        story.extend(self._create_signboards(data))
        
        # 인테리어
        story.extend(self._create_interiors(data))
        
        # 색상 팔레트
        story.extend(self._create_colors(data))
        
        # 예산 가이드
        story.extend(self._create_budget(data))
        
        # 요약
        story.extend(self._create_summary(data))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _create_cover(self, data: Dict[str, Any]) -> List:
        """표지 페이지"""
        elements = []
        elements.append(Spacer(1, 3*cm))
        elements.append(self._create_safe_paragraph("AI 브랜딩 보고서", self.title_style))
        elements.append(Spacer(1, 2*cm))
        
        business_info = self._extract_business_info(data)
        subtitle = f"{business_info.get('industry', 'N/A')} • {business_info.get('region', 'N/A')}"
        elements.append(self._create_safe_paragraph(subtitle, self.heading_style))
        elements.append(Spacer(1, 2*cm))
        
        info_data = [
            ["생성일", datetime.now().strftime("%Y년 %m월 %d일")],
            ["세션 ID", data.get("session_id", "N/A")[:20]],  # ID 길이 제한
            ["시스템", "AI 브랜딩 챗봇"]
        ]
        
        info_table = Table(info_data, colWidths=[4*cm, 6*cm])
        info_table.setStyle(self._get_table_style())
        elements.append(info_table)
        
        return elements
    
    def _create_business_info(self, data: Dict[str, Any]) -> List:
        """비즈니스 정보 섹션"""
        elements = []
        elements.append(self._create_safe_paragraph("1. 비즈니스 정보", self.section_style))
        elements.append(Spacer(1, 0.5*cm))
        
        business_info = self._extract_business_info(data)
        
        info_data = [
            ["항목", "내용"],
            ["업종", business_info.get('industry', 'N/A')],
            ["지역", business_info.get('region', 'N/A')],
            ["규모", business_info.get('size', 'N/A')]
        ]
        
        # 설명이 있으면 추가
        description = business_info.get('description', '')
        if description:
            info_data.append(["설명", description[:50] + ('...' if len(description) > 50 else '')])
        
        table = Table(info_data, colWidths=[3*cm, 8*cm])
        table.setStyle(self._get_table_style())
        elements.append(table)
        elements.append(Spacer(1, 1*cm))
        
        return elements
    
    def _create_analysis(self, data: Dict[str, Any]) -> List:
        """분석 결과 섹션"""
        elements = []
        elements.append(Paragraph("2. AI 비즈니스 분석", self.section_style))
        elements.append(Spacer(1, 0.5*cm))
        
        analysis = data.get('session', {}).get('analysis_result', {})
        if isinstance(analysis, str):
            try:
                analysis = json.loads(analysis)
            except:
                analysis = {}
        
        score = analysis.get('overall_score', 75)
        elements.append(Paragraph(f"종합 점수: {score}/100", self.styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))
        
        insights = analysis.get('key_insights', [])
        if insights:
            elements.append(Paragraph("핵심 인사이트:", self.styles['Normal']))
            for insight in insights[:3]:
                elements.append(Paragraph(f"• {insight}", self.styles['Normal']))
        
        elements.append(Spacer(1, 1*cm))
        return elements
    
    def _create_names(self, data: Dict[str, Any]) -> List:
        """상호명 섹션"""
        elements = []
        elements.append(Paragraph("3. 추천 상호명", self.section_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # 세션 데이터와 직접 데이터 모두 확인
        names = data.get('business_names', [])
        if not names:
            session_names = data.get('session', {}).get('business_names', [])
            if isinstance(session_names, str):
                try:
                    names = json.loads(session_names)
                except:
                    names = []
            else:
                names = session_names
        
        selected = data.get('selected_name', '') or data.get('session', {}).get('selected_name', '')
        
        if names:
            # 상호명 후보 테이블
            name_data = [["순위", "상호명", "설명", "점수"]]
            for i, name_info in enumerate(names[:3], 1):
                name = name_info.get('name', 'N/A')
                description = name_info.get('description', '')[:30] + ('...' if len(name_info.get('description', '')) > 30 else '')
                score = name_info.get('score', 0)
                
                # 선택된 상호명 표시
                if name == selected:
                    name = f"✓ {name}"
                
                name_data.append([
                    str(i),
                    name,
                    description,
                    f"{score}/100"
                ])
            
            table = Table(name_data, colWidths=[1.5*cm, 3.5*cm, 5*cm, 1.5*cm])
            table.setStyle(self._get_table_style())
            elements.append(table)
            
            # 상호명 분석 기준 설명
            elements.append(Spacer(1, 0.3*cm))
            analysis_desc = """
            상호명 분석 기준:
            • 발음 용이성: 고객이 쉽게 발음하고 기억할 수 있는지
            • 검색 최적화: 온라인 검색에서 찾기 쉬운지
            • 업종 적합성: 비즈니스 특성을 잘 반영하는지
            • 브랜드 확장성: 향후 사업 확장 시 활용 가능한지
            """
            elements.append(Paragraph(analysis_desc.strip(), self.normal_style))
        
        if selected:
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph(f"최종 선택된 상호명: {selected}", self.heading_style))
            
            # 선택된 상호명의 상세 정보
            selected_info = next((name for name in names if name.get('name') == selected), None)
            if selected_info:
                elements.append(Spacer(1, 0.2*cm))
                elements.append(Paragraph(f"설명: {selected_info.get('description', '')}", self.normal_style))
                elements.append(Paragraph(f"종합 점수: {selected_info.get('score', 0)}/100", self.normal_style))
        
        elements.append(Spacer(1, 1*cm))
        return elements
    
    def _create_image_placeholder(self, width: float, height: float, text: str) -> Drawing:
        """이미지 플레이스홀더 생성"""
        try:
            drawing = Drawing(width, height)
            
            # 배경 사각형
            drawing.add(Rect(0, 0, width, height, 
                           fillColor=colors.lightgrey, 
                           strokeColor=colors.grey))
            
            # 텍스트 추가
            drawing.add(String(width/2, height/2, text, 
                              textAnchor='middle',
                              fontSize=8,
                              fillColor=colors.black))
            
            return drawing
        except Exception as e:
            self.logger.warning(f"Failed to create image placeholder: {e}")
            return None
    
    def _create_signboards(self, data: Dict[str, Any]) -> List:
        """간판 디자인 섹션"""
        elements = []
        elements.append(self._create_safe_paragraph("4. Signboard Design", self.section_style))
        elements.append(Spacer(1, 0.5*cm))
        
        images = data.get("signboard_images", [])
        selected_signboard = data.get("selected_signboard", "")
        
        elements.append(self._create_safe_paragraph(f"Generated signboard designs: {len(images)}", self.normal_style))
        
        if selected_signboard:
            elements.append(Spacer(1, 0.3*cm))
            selected_name = selected_signboard.split('/')[-1]
            elements.append(self._create_safe_paragraph(f"Selected: {selected_name[:30]}", self.normal_style))
        
        if images:
            elements.append(Spacer(1, 0.3*cm))
            
            # 이미지 플레이스홀더 추가
            for i, img in enumerate(images[:3], 1):
                filename = img.get('key', '').split('/')[-1]
                style = img.get('style', 'Modern')
                ai_model = img.get('ai_model', 'DALL-E 3')
                
                # 이미지 플레이스홀더
                placeholder = self._create_image_placeholder(
                    4*cm, 2*cm, 
                    f"Signboard {i}\n{style}\n{ai_model}"
                )
                if placeholder:
                    elements.append(placeholder)
                    elements.append(Spacer(1, 0.2*cm))
            
            # 이미지 정보 테이블
            image_data = [["No.", "Filename", "Size", "AI Model", "Status"]]
            for i, img in enumerate(images[:3], 1):
                filename = img.get('key', '').split('/')[-1]
                size_mb = img.get('size', 0) / (1024 * 1024)
                ai_model = img.get('ai_model', 'DALL-E 3')
                status = "Selected" if img.get('key') == selected_signboard else "Generated"
                
                image_data.append([
                    str(i), 
                    filename[:25] + ('...' if len(filename) > 25 else ''),
                    f"{size_mb:.1f}MB", 
                    ai_model,
                    status
                ])
            
            table = Table(image_data, colWidths=[1*cm, 4*cm, 1.5*cm, 2*cm, 1.5*cm])
            table.setStyle(self._get_table_style())
            elements.append(table)
            
            # 간판 디자인 설명
            elements.append(Spacer(1, 0.3*cm))
            signboard_desc = "Signboard designs are generated using AI considering industry characteristics and regional environment."
            elements.append(self._create_safe_paragraph(signboard_desc, self.normal_style))
        
        elements.append(Spacer(1, 1*cm))
        return elements
    
    def _create_interiors(self, data: Dict[str, Any]) -> List:
        """인테리어 섹션"""
        elements = []
        elements.append(Paragraph("5. 인테리어 디자인", self.section_style))
        elements.append(Spacer(1, 0.5*cm))
        
        images = data.get("interior_images", [])
        selected_interior = data.get("selected_interior", "")
        
        elements.append(Paragraph(f"생성된 인테리어 디자인: {len(images)}개", self.normal_style))
        
        if selected_interior:
            elements.append(Spacer(1, 0.3*cm))
            elements.append(Paragraph(f"선택된 인테리어: {selected_interior.split('/')[-1]}", self.normal_style))
        
        if images:
            elements.append(Spacer(1, 0.3*cm))
            image_data = [["번호", "파일명", "크기", "스타일", "상태"]]
            for i, img in enumerate(images[:3], 1):
                filename = img.get('key', '').split('/')[-1]
                size_mb = img.get('size', 0) / (1024 * 1024)
                
                # 파일명에서 스타일 추출
                if "cozy" in filename.lower() or "아늑" in filename:
                    style = "아늑한"
                elif "modern" in filename.lower() or "모던" in filename:
                    style = "모던"
                elif "scandinavian" in filename.lower() or "스칸디나비안" in filename:
                    style = "스칸디나비안"
                else:
                    style = "클래식"
                
                status = "✓ 선택됨" if img.get('key') == selected_interior else "생성됨"
                image_data.append([str(i), filename[:20], f"{size_mb:.1f}MB", style, status])
            
            table = Table(image_data, colWidths=[1*cm, 4*cm, 1.5*cm, 2.5*cm, 2*cm])
            table.setStyle(self._get_table_style())
            elements.append(table)
            
            # 인테리어 디자인 설명
            elements.append(Spacer(1, 0.3*cm))
            interior_desc = """
            인테리어 디자인은 선택된 간판 스타일과 조화를 이루도록 생성되었습니다. 
            각 스타일은 업종의 특성과 타겟 고객층을 고려하여 최적화되었습니다.
            """
            elements.append(Paragraph(interior_desc.strip(), self.normal_style))
        
        elements.append(Spacer(1, 1*cm))
        return elements
    
    def _create_colors(self, data: Dict[str, Any]) -> List:
        """색상 팔레트 섹션"""
        elements = []
        elements.append(Paragraph("6. 추천 색상 팔레트", self.section_style))
        elements.append(Spacer(1, 0.5*cm))
        
        business_info = self._extract_business_info(data)
        industry = business_info.get('industry', '')
        
        colors_data = self._get_industry_colors(industry)
        
        color_table_data = [["색상 유형", "색상명", "용도"]]
        for color_info in colors_data:
            color_table_data.append([
                color_info['type'],
                color_info['name'],
                color_info['usage']
            ])
        
        table = Table(color_table_data, colWidths=[3*cm, 4*cm, 5*cm])
        table.setStyle(self._get_table_style())
        elements.append(table)
        elements.append(Spacer(1, 1*cm))
        
        return elements
    
    def _create_budget(self, data: Dict[str, Any]) -> List:
        """예산 가이드 섹션"""
        elements = []
        elements.append(Paragraph("7. 예산 가이드", self.section_style))
        elements.append(Spacer(1, 0.5*cm))
        
        business_info = self._extract_business_info(data)
        size = business_info.get('size', '소규모')
        
        budget_data = self._get_budget_estimates(size)
        
        budget_table_data = [["항목", "최소", "권장", "최대"]]
        for item in budget_data:
            budget_table_data.append([
                item['category'],
                f"{item['min']:,}원",
                f"{item['recommended']:,}원",
                f"{item['max']:,}원"
            ])
        
        table = Table(budget_table_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        table.setStyle(self._get_table_style())
        elements.append(table)
        elements.append(Spacer(1, 1*cm))
        
        return elements
    
    def _create_summary(self, data: Dict[str, Any]) -> List:
        """요약 섹션"""
        elements = []
        elements.append(Paragraph("8. 요약 및 권장사항", self.section_style))
        elements.append(Spacer(1, 0.5*cm))
        
        business_info = self._extract_business_info(data)
        signboard_count = len(data.get("signboard_images", []))
        interior_count = len(data.get("interior_images", []))
        
        summary = f"""
        본 보고서는 AI 브랜딩 시스템을 통해 생성된 {business_info.get('industry', 'N/A')} 업종의 
        종합적인 브랜딩 솔루션입니다.
        
        생성된 자산:
        • 상호명 후보: 3개
        • 간판 디자인: {signboard_count}개
        • 인테리어 디자인: {interior_count}개
        • 색상 팔레트: 업종 맞춤형
        • 예산 가이드: 규모별 분석
        """
        
        elements.append(Paragraph(summary, self.styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # 권장사항
        recommendations = self._get_industry_recommendations(business_info.get('industry', ''))
        elements.append(Paragraph("핵심 권장사항:", self.styles['Normal']))
        for i, rec in enumerate(recommendations, 1):
            elements.append(Paragraph(f"{i}. {rec}", self.styles['Normal']))
        
        elements.append(Spacer(1, 1*cm))
        
        # 생성 정보
        gen_info = f"본 보고서는 {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}에 생성되었습니다."
        elements.append(Paragraph(gen_info, self.styles['Normal']))
        
        return elements
    
    # 유틸리티 메서드들
    
    def _extract_business_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """비즈니스 정보 추출"""
        session = data.get("session", {})
        business_info = session.get("business_info", {})
        
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
        
        return business_info
    
    def _get_industry_colors(self, industry: str) -> List[Dict[str, str]]:
        """업종별 추천 색상"""
        color_schemes = {
            '카페': [
                {'type': '주 색상', 'name': '따뜻한 브라운', 'usage': '로고, 간판'},
                {'type': '보조 색상', 'name': '크림 베이지', 'usage': '배경, 인테리어'},
                {'type': '강조 색상', 'name': '골드', 'usage': '포인트 요소'}
            ],
            '레스토랑': [
                {'type': '주 색상', 'name': '딥 레드', 'usage': '로고, 간판'},
                {'type': '보조 색상', 'name': '웜 화이트', 'usage': '배경, 메뉴판'},
                {'type': '강조 색상', 'name': '골든 옐로우', 'usage': '포인트 요소'}
            ]
        }
        
        return color_schemes.get(industry, [
            {'type': '주 색상', 'name': '다크 블루', 'usage': '로고, 간판'},
            {'type': '보조 색상', 'name': '라이트 그레이', 'usage': '배경'},
            {'type': '강조 색상', 'name': '그린', 'usage': '포인트'}
        ])
    
    def _get_budget_estimates(self, size: str) -> List[Dict[str, Any]]:
        """규모별 예산 추정"""
        multiplier = {'소규모': 1.0, '중규모': 1.5, '대규모': 2.5}.get(size, 1.0)
        
        base_costs = [
            {'category': '간판 제작', 'min': 500000, 'recommended': 1000000, 'max': 2000000},
            {'category': '인테리어', 'min': 2000000, 'recommended': 5000000, 'max': 10000000},
            {'category': '브랜딩 디자인', 'min': 300000, 'recommended': 800000, 'max': 1500000},
            {'category': '마케팅', 'min': 200000, 'recommended': 500000, 'max': 1000000}
        ]
        
        for cost in base_costs:
            cost['min'] = int(cost['min'] * multiplier)
            cost['recommended'] = int(cost['recommended'] * multiplier)
            cost['max'] = int(cost['max'] * multiplier)
        
        return base_costs
    
    def _get_industry_recommendations(self, industry: str) -> List[str]:
        """업종별 권장사항"""
        recommendations_map = {
            '카페': [
                "편안하고 아늑한 분위기 조성에 집중하세요",
                "SNS 친화적인 포토존 설치를 고려하세요",
                "계절별 메뉴와 연계한 인테리어 변화를 계획하세요"
            ],
            '레스토랑': [
                "음식의 맛을 돋보이게 하는 조명 설계가 중요합니다",
                "테이블 배치와 동선을 효율적으로 계획하세요",
                "브랜드 스토리를 공간에 녹여내는 것이 핵심입니다"
            ]
        }
        
        return recommendations_map.get(industry, [
            "타겟 고객층의 니즈를 정확히 파악하여 반영하세요",
            "브랜드 일관성을 모든 접점에서 유지하세요",
            "지속적인 브랜드 발전을 위한 장기 계획을 수립하세요"
        ])
    
    def _safe_korean_text(self, text: str) -> str:
        """한글 텍스트를 영어로 완전 변환"""
        if not text:
            return ""
        
        try:
            # 문자열로 변환
            text = str(text)
            
            # 포괄적인 한글-영어 변환 사전
            korean_to_english = {
                # 기본 단어들
                '카페': 'Cafe',
                '레스토랑': 'Restaurant', 
                '뷰티': 'Beauty',
                '한식당': 'Korean Restaurant',
                '소매': 'Retail',
                
                # 규모
                '소규모': 'Small Scale',
                '중규모': 'Medium Scale', 
                '대규모': 'Large Scale',
                
                # 지역
                '서울': 'Seoul',
                '서울특별시': 'Seoul',
                '강남구': 'Gangnam District',
                '역삼동': 'Yeoksam-dong',
                '부산': 'Busan',
                '대구': 'Daegu',
                '인천': 'Incheon',
                
                # 보고서 관련
                'AI 브랜딩 보고서': 'AI Branding Report',
                '브랜딩': 'Branding',
                '보고서': 'Report',
                '생성일': 'Generated Date',
                '세션': 'Session',
                '시스템': 'System',
                'AI 브랜딩 챗봇': 'AI Branding Chatbot',
                
                # 비즈니스 정보
                '비즈니스': 'Business',
                '정보': 'Information',
                '업종': 'Industry',
                '지역': 'Region',
                '규모': 'Scale',
                '설명': 'Description',
                '항목': 'Item',
                '내용': 'Content',
                
                # 분석 관련
                '분석': 'Analysis',
                '결과': 'Result',
                '점수': 'Score',
                '종합': 'Overall',
                '핵심': 'Key',
                '인사이트': 'Insights',
                '시장': 'Market',
                '잠재력': 'Potential',
                '경쟁': 'Competition',
                '수준': 'Level',
                '높음': 'High',
                '중간': 'Medium',
                '낮음': 'Low',
                
                # 상호명 관련
                '상호명': 'Business Name',
                '추천': 'Recommended',
                '후보': 'Candidates',
                '선택': 'Selected',
                '최종': 'Final',
                '순위': 'Rank',
                '번호': 'No.',
                
                # 디자인 관련
                '간판': 'Signboard',
                '디자인': 'Design',
                '인테리어': 'Interior',
                '생성된': 'Generated',
                '파일명': 'Filename',
                '크기': 'Size',
                '상태': 'Status',
                '선택됨': 'Selected',
                '생성됨': 'Generated',
                '모델': 'Model',
                '스타일': 'Style',
                
                # 색상 관련
                '색상': 'Color',
                '팔레트': 'Palette',
                '따뜻한': 'Warm',
                '브라운': 'Brown',
                '크림': 'Cream',
                '베이지': 'Beige',
                '골드': 'Gold',
                '용도': 'Usage',
                '로고': 'Logo',
                '배경': 'Background',
                '포인트': 'Point',
                '요소': 'Element',
                
                # 예산 관련
                '예산': 'Budget',
                '가이드': 'Guide',
                '최소': 'Minimum',
                '권장': 'Recommended',
                '최대': 'Maximum',
                '총': 'Total',
                '원': 'KRW',
                
                # 권장사항
                '권장사항': 'Recommendations',
                '요약': 'Summary',
                
                # 날짜/시간
                '년': 'Year',
                '월': 'Month',
                '일': 'Day',
                
                # 기타 자주 사용되는 단어들
                '특별한': 'Special',
                '순간': 'Moment',
                '커피': 'Coffee',
                '공간': 'Space',
                '아늑한': 'Cozy',
                '분위기': 'Atmosphere',
                '전문점': 'Specialty Shop',
                '고품질': 'High Quality',
                '원두': 'Coffee Beans',
                '수제': 'Handmade',
                '디저트': 'Dessert',
                '제공': 'Provide',
                '서비스': 'Service',
                '고객': 'Customer',
                '브랜드': 'Brand',
                '마케팅': 'Marketing',
                '장비': 'Equipment'
            }
            
            # 한글 문자가 포함되어 있는지 확인
            has_korean = any('\u3131' <= char <= '\uD7A3' for char in text)
            
            if has_korean or self.force_english:
                # 단어별 변환
                for korean, english in korean_to_english.items():
                    text = text.replace(korean, english)
                
                # 남은 한글 문자들을 제거하거나 대체
                import re
                # 한글 문자를 찾아서 제거
                text = re.sub(r'[\u3131-\uD7A3]', '', text)
                
                # 연속된 공백 정리
                text = re.sub(r'\s+', ' ', text).strip()
                
                # 빈 문자열이 되면 기본값 제공
                if not text or text.isspace():
                    text = "Content Available"
            
            # HTML 특수 문자 처리
            text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            # 너무 긴 텍스트는 줄바꿈
            if len(text) > 70:
                words = text.split(' ')
                lines = []
                current_line = []
                current_length = 0
                
                for word in words:
                    word_length = len(word)
                    if current_length + word_length > 70:
                        if current_line:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                            current_length = word_length
                        else:
                            lines.append(word)
                            current_length = 0
                    else:
                        current_line.append(word)
                        current_length += word_length + 1
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                return '<br/>'.join(lines)
            
            return text
            
        except Exception as e:
            self.logger.warning(f"Text processing failed: {e}")
            return "Content Processing Error"
    
    def _create_safe_paragraph(self, text: str, style) -> Paragraph:
        """안전한 Paragraph 생성"""
        try:
            safe_text = self._safe_korean_text(text)
            return Paragraph(safe_text, style)
        except Exception as e:
            self.logger.warning(f"Failed to create paragraph with Korean text: {e}")
            # 폴백: 영어로 변환하거나 간단한 텍스트 사용
            fallback_text = "Content not available"
            return Paragraph(fallback_text, style)
    
    def _get_table_style(self) -> TableStyle:
        """테이블 스타일 - 한글 폰트 적용"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.korean_font),  # 한글 폰트 사용
            ('FONTNAME', (0, 1), (-1, -1), self.korean_font),  # 한글 폰트 사용
            ('FONTSIZE', (0, 0), (-1, -1), 8),  # 크기 줄여서 안정성 향상
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, self.primary_color),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # 세로 정렬
        ])


def create_branding_report_pdf(data: Dict[str, Any]) -> io.BytesIO:
    """브랜딩 보고서 PDF 생성 함수"""
    template = BrandingReportTemplate()
    return template.create_report(data)


if __name__ == "__main__":
    # 테스트
    test_data = {
        "session_id": "test-123",
        "session": {
            "business_info": json.dumps({
                "industry": "카페",
                "region": "서울 강남구",
                "size": "소규모"
            })
        },
        "signboard_images": [{"key": "test.jpg", "size": 1024000}],
        "interior_images": [{"key": "test.jpg", "size": 2048000}]
    }
    
    try:
        pdf_buffer = create_branding_report_pdf(test_data)
        print(f"PDF generated: {len(pdf_buffer.getvalue())} bytes")
        
        with open("test_report.pdf", "wb") as f:
            f.write(pdf_buffer.getvalue())
        print("Test PDF saved as 'test_report.pdf'")
        
    except Exception as e:
        print(f"Error: {str(e)}")