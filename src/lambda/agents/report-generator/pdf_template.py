#!/usr/bin/env python3
"""
PDF Template for AI Branding Report
"""

import json
import io
from datetime import datetime
from typing import Dict, Any, List
import logging

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class BrandingReportTemplate:
    """AI 브랜딩 보고서 PDF 템플릿"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if not PDF_AVAILABLE:
            return
            
        self.page_width, self.page_height = A4
        self.margin = 2*cm
        self.primary_color = colors.Color(0.2, 0.3, 0.6)
        self.accent_color = colors.Color(0.9, 0.6, 0.2)
        self._setup_styles()
    
    def _setup_styles(self):
        """PDF 스타일 설정"""
        if not PDF_AVAILABLE:
            return
            
        self.styles = getSampleStyleSheet()
        
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=self.primary_color,
            fontName='Helvetica-Bold'
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=15,
            textColor=self.primary_color,
            fontName='Helvetica-Bold'
        )
    
    def create_report(self, data: Dict[str, Any]) -> io.BytesIO:
        """브랜딩 보고서 PDF 생성"""
        if not PDF_AVAILABLE:
            raise ImportError("ReportLab not available")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=self.margin, bottomMargin=self.margin, leftMargin=self.margin, rightMargin=self.margin)
        
        story = []
        
        # 제목
        story.append(Paragraph("AI 브랜딩 보고서", self.title_style))
        story.append(Spacer(1, 2*cm))
        
        # 비즈니스 정보
        business_info = self._extract_business_info(data)
        subtitle = f"{business_info.get('industry', 'N/A')} • {business_info.get('region', 'N/A')} • {business_info.get('size', 'N/A')}"
        story.append(Paragraph(subtitle, self.heading_style))
        story.append(Spacer(1, 1*cm))
        
        # 기본 정보 테이블
        info_data = [
            ["항목", "내용"],
            ["업종", business_info.get('industry', 'N/A')],
            ["지역", business_info.get('region', 'N/A')],
            ["규모", business_info.get('size', 'N/A')],
            ["생성일", datetime.now().strftime("%Y년 %m월 %d일")],
            ["세션 ID", data.get("session_id", "N/A")]
        ]
        
        info_table = Table(info_data, colWidths=[4*cm, 8*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, self.primary_color)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 1*cm))
        
        # 분석 결과
        story.append(Paragraph("AI 비즈니스 분석", self.heading_style))
        analysis = data.get('session', {}).get('analysis_result', {})
        if isinstance(analysis, str):
            try:
                analysis = json.loads(analysis)
            except:
                analysis = {}
        
        score = analysis.get('overall_score', 75)
        story.append(Paragraph(f"종합 비즈니스 점수: {score}/100", self.styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
        
        insights = analysis.get('key_insights', [])
        if insights:
            story.append(Paragraph("핵심 인사이트:", self.styles['Normal']))
            for insight in insights[:3]:
                story.append(Paragraph(f"• {insight}", self.styles['Normal']))
        
        story.append(Spacer(1, 1*cm))
        
        # 상호명 추천
        story.append(Paragraph("추천 상호명", self.heading_style))
        names = data.get('session', {}).get('business_names', [])
        if isinstance(names, str):
            try:
                names = json.loads(names)
            except:
                names = []
        
        if names:
            name_data = [["순위", "상호명", "점수", "설명"]]
            for i, name_info in enumerate(names[:3], 1):
                description = name_info.get('description', '')
                if len(description) > 50:
                    description = description[:50] + "..."
                name_data.append([
                    str(i),
                    name_info.get('name', 'N/A'),
                    f"{name_info.get('score', 0)}/100",
                    description
                ])
            
            names_table = Table(name_data, colWidths=[1*cm, 4*cm, 2*cm, 6*cm])
            names_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, self.primary_color)
            ]))
            story.append(names_table)
        
        selected = data.get('session', {}).get('selected_name', '')
        if selected:
            story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph(f"최종 선택된 상호명: {selected}", self.styles['Normal']))
        
        story.append(PageBreak())
        
        # 간판 디자인
        story.append(Paragraph("간판 디자인", self.heading_style))
        signboard_images = data.get("signboard_images", [])
        story.append(Paragraph(f"총 {len(signboard_images)}개의 간판 디자인이 생성되었습니다.", self.styles['Normal']))
        
        if signboard_images:
            image_data = [["번호", "파일명", "크기", "AI 모델"]]
            for i, img in enumerate(signboard_images[:3], 1):
                filename = img.get('key', '').split('/')[-1]
                size_mb = img.get('size', 0) / (1024 * 1024)
                ai_model = 'DALL-E' if 'dalle' in filename.lower() else 'SDXL' if 'sdxl' in filename.lower() else 'Gemini' if 'gemini' in filename.lower() else 'AI Generated'
                
                if len(filename) > 25:
                    filename = filename[:25] + "..."
                
                image_data.append([str(i), filename, f"{size_mb:.1f}MB", ai_model])
            
            images_table = Table(image_data, colWidths=[1*cm, 5*cm, 2*cm, 3*cm])
            images_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, self.primary_color)
            ]))
            story.append(images_table)
        
        story.append(Spacer(1, 1*cm))
        
        # 인테리어 디자인
        story.append(Paragraph("인테리어 디자인", self.heading_style))
        interior_images = data.get("interior_images", [])
        story.append(Paragraph(f"총 {len(interior_images)}개의 인테리어 디자인이 생성되었습니다.", self.styles['Normal']))
        
        if interior_images:
            interior_data = [["번호", "파일명", "크기", "스타일"]]
            for i, img in enumerate(interior_images[:3], 1):
                filename = img.get('key', '').split('/')[-1]
                size_mb = img.get('size', 0) / (1024 * 1024)
                style = '모던' if 'modern' in filename.lower() else '스칸디나비안' if 'scandinavian' in filename.lower() else '코지' if 'cozy' in filename.lower() else '컨템포러리'
                
                if len(filename) > 25:
                    filename = filename[:25] + "..."
                
                interior_data.append([str(i), filename, f"{size_mb:.1f}MB", style])
            
            interior_table = Table(interior_data, colWidths=[1*cm, 5*cm, 2*cm, 3*cm])
            interior_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, self.primary_color)
            ]))
            story.append(interior_table)
        
        story.append(PageBreak())
        
        # 색상 팔레트
        story.append(Paragraph("추천 색상 팔레트", self.heading_style))
        industry = business_info.get('industry', '')
        
        # 업종별 색상 추천
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
        
        colors_data = color_schemes.get(industry, [
            {'type': '주 색상', 'name': '다크 블루', 'usage': '로고, 간판'},
            {'type': '보조 색상', 'name': '라이트 그레이', 'usage': '배경'},
            {'type': '강조 색상', 'name': '그린', 'usage': '포인트'}
        ])
        
        color_table_data = [["색상 유형", "색상명", "용도"]]
        for color_info in colors_data:
            color_table_data.append([color_info['type'], color_info['name'], color_info['usage']])
        
        color_table = Table(color_table_data, colWidths=[3*cm, 4*cm, 5*cm])
        color_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, self.primary_color)
        ]))
        story.append(color_table)
        story.append(Spacer(1, 1*cm))
        
        # 예산 가이드
        story.append(Paragraph("예산 가이드", self.heading_style))
        size = business_info.get('size', '소규모')
        multiplier = {'소규모': 1.0, '중규모': 1.5, '대규모': 2.5}.get(size, 1.0)
        
        base_costs = [
            {'category': '간판 제작', 'min': 500000, 'recommended': 1000000, 'max': 2000000},
            {'category': '인테리어', 'min': 2000000, 'recommended': 5000000, 'max': 10000000},
            {'category': '브랜딩 디자인', 'min': 300000, 'recommended': 800000, 'max': 1500000},
            {'category': '마케팅', 'min': 200000, 'recommended': 500000, 'max': 1000000}
        ]
        
        budget_table_data = [["항목", "최소 예산", "권장 예산", "최대 예산"]]
        total_min = total_recommended = total_max = 0
        
        for cost in base_costs:
            min_cost = int(cost['min'] * multiplier)
            rec_cost = int(cost['recommended'] * multiplier)
            max_cost = int(cost['max'] * multiplier)
            
            budget_table_data.append([
                cost['category'],
                f"{min_cost:,}원",
                f"{rec_cost:,}원",
                f"{max_cost:,}원"
            ])
            
            total_min += min_cost
            total_recommended += rec_cost
            total_max += max_cost
        
        budget_table = Table(budget_table_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        budget_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, self.primary_color)
        ]))
        story.append(budget_table)
        story.append(Spacer(1, 0.5*cm))
        
        # 총 예산 요약
        total_summary = f"총 예상 비용 - 최소: {total_min:,}원, 권장: {total_recommended:,}원, 최대: {total_max:,}원"
        story.append(Paragraph(total_summary, self.styles['Normal']))
        story.append(Spacer(1, 1*cm))
        
        # 요약 및 권장사항
        story.append(Paragraph("요약 및 권장사항", self.heading_style))
        
        summary = f"""
        본 보고서는 AI 브랜딩 시스템을 통해 생성된 {business_info.get('industry', 'N/A')} 업종의 
        종합적인 브랜딩 솔루션입니다.
        
        생성된 자산:
        • 상호명 후보: 3개
        • 간판 디자인: {len(signboard_images)}개
        • 인테리어 디자인: {len(interior_images)}개
        • 색상 팔레트: 업종 맞춤형
        • 예산 가이드: 규모별 상세 분석
        
        모든 디자인은 AI 시스템을 통해 생성되었으며, 
        비즈니스의 특성과 목표 고객층을 고려하여 최적화되었습니다.
        """
        
        story.append(Paragraph(summary, self.styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
        
        # 권장사항
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
        
        recommendations = recommendations_map.get(industry, [
            "타겟 고객층의 니즈를 정확히 파악하여 반영하세요",
            "브랜드 일관성을 모든 접점에서 유지하세요",
            "지속적인 브랜드 발전을 위한 장기 계획을 수립하세요"
        ])
        
        story.append(Paragraph("핵심 권장사항:", self.styles['Normal']))
        for i, rec in enumerate(recommendations, 1):
            story.append(Paragraph(f"{i}. {rec}", self.styles['Normal']))
        
        story.append(Spacer(1, 1*cm))
        
        # 생성 정보
        gen_info = f"본 보고서는 {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}에 AI 브랜딩 챗봇 시스템에 의해 자동 생성되었습니다."
        story.append(Paragraph(gen_info, self.styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
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
            }),
            "analysis_result": json.dumps({
                "overall_score": 85,
                "key_insights": [
                    "강남 지역 특성상 고급스러운 브랜딩 필요",
                    "직장인 타겟으로 빠른 서비스 중요",
                    "SNS 마케팅 활용도 높은 지역"
                ]
            }),
            "business_names": json.dumps([
                {"name": "카페 모멘트", "score": 88, "description": "특별한 순간을 만드는 카페"},
                {"name": "브루잉 스테이션", "score": 85, "description": "커피 전문성을 강조한 이름"},
                {"name": "어반 빈즈", "score": 82, "description": "도시적 감각의 커피 전문점"}
            ]),
            "selected_name": "카페 모멘트"
        },
        "signboard_images": [
            {"key": "signboards/test/dalle_classic_signboard.jpg", "size": 1024000},
            {"key": "signboards/test/sdxl_modern_signboard.jpg", "size": 1536000},
            {"key": "signboards/test/gemini_vibrant_signboard.jpg", "size": 1280000}
        ],
        "interior_images": [
            {"key": "interiors/test/modern_interior.jpg", "size": 2048000},
            {"key": "interiors/test/scandinavian_interior.jpg", "size": 1792000},
            {"key": "interiors/test/cozy_interior.jpg", "size": 1920000}
        ]
    }
    
    try:
        pdf_buffer = create_branding_report_pdf(test_data)
        print(f"PDF generated successfully: {len(pdf_buffer.getvalue())} bytes")
        
        with open("test_branding_report.pdf", "wb") as f:
            f.write(pdf_buffer.getvalue())
        print("Test PDF saved as 'test_branding_report.pdf'")
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()
