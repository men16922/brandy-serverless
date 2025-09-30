#!/usr/bin/env python3
"""
HTML to PDF Generator - WeasyPrint 사용
한글 폰트 문제 완전 해결을 위한 대안
"""

import json
import io
import os
from datetime import datetime
from typing import Dict, Any
import logging

try:
    import weasyprint
    from weasyprint import HTML, CSS
    HTML_PDF_AVAILABLE = True
except ImportError:
    HTML_PDF_AVAILABLE = False

logger = logging.getLogger(__name__)


class HTMLPDFGenerator:
    """HTML을 PDF로 변환하는 생성기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if not HTML_PDF_AVAILABLE:
            self.logger.warning("WeasyPrint not available")
            return
        
        self.logger.info("HTML PDF Generator initialized with WeasyPrint")
    
    def create_branding_report(self, data: Dict[str, Any]) -> io.BytesIO:
        """브랜딩 보고서 HTML → PDF 생성"""
        if not HTML_PDF_AVAILABLE:
            raise ImportError("WeasyPrint not available for HTML to PDF conversion")
        
        try:
            # HTML 생성
            html_content = self._generate_html_report(data)
            
            # CSS 스타일 생성
            css_content = self._generate_css_styles()
            
            # HTML을 PDF로 변환
            html_doc = HTML(string=html_content)
            css_doc = CSS(string=css_content)
            
            # PDF 생성
            pdf_buffer = io.BytesIO()
            html_doc.write_pdf(pdf_buffer, stylesheets=[css_doc])
            pdf_buffer.seek(0)
            
            self.logger.info(f"HTML PDF generated successfully. Size: {len(pdf_buffer.getvalue())} bytes")
            return pdf_buffer
            
        except Exception as e:
            self.logger.error(f"Failed to generate HTML PDF: {str(e)}")
            raise
    
    def _generate_html_report(self, data: Dict[str, Any]) -> str:
        """HTML 보고서 생성"""
        
        # 비즈니스 정보 추출
        business_info = self._extract_business_info(data)
        analysis_result = data.get('analysis_result', {})
        business_names = data.get('business_names', [])
        selected_name = data.get('selected_name', '')
        signboard_images = data.get('signboard_images', [])
        interior_images = data.get('interior_images', [])
        color_palette = data.get('color_palette', {})
        budget_guide = data.get('budget_guide', {})
        recommendations = data.get('recommendations', [])
        
        html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 브랜딩 보고서</title>
</head>
<body>
    <!-- 표지 페이지 -->
    <div class="cover-page">
        <h1 class="main-title">AI 브랜딩 보고서</h1>
        <h2 class="subtitle">{business_info.get('industry', 'N/A')} • {business_info.get('region', 'N/A')}</h2>
        
        <div class="cover-info">
            <table class="info-table">
                <tr><td>생성일</td><td>{datetime.now().strftime('%Y년 %m월 %d일')}</td></tr>
                <tr><td>세션 ID</td><td>{data.get('session_id', 'N/A')[:20]}</td></tr>
                <tr><td>시스템</td><td>AI 브랜딩 챗봇</td></tr>
            </table>
        </div>
    </div>
    
    <div class="page-break"></div>
    
    <!-- 비즈니스 정보 -->
    <div class="section">
        <h2 class="section-title">1. 비즈니스 정보</h2>
        
        <table class="data-table">
            <tr><th>항목</th><th>내용</th></tr>
            <tr><td>업종</td><td>{business_info.get('industry', 'N/A')}</td></tr>
            <tr><td>지역</td><td>{business_info.get('region', 'N/A')}</td></tr>
            <tr><td>규모</td><td>{business_info.get('size', 'N/A')}</td></tr>
            <tr><td>설명</td><td>{business_info.get('description', 'N/A')[:100]}</td></tr>
        </table>
    </div>
    
    <!-- AI 분석 결과 -->
    <div class="section">
        <h2 class="section-title">2. AI 비즈니스 분석</h2>
        
        <div class="score-box">
            <h3>종합 점수: {analysis_result.get('overall_score', 0)}/100</h3>
        </div>
        
        <h4>핵심 인사이트:</h4>
        <ul class="insights-list">
            {self._generate_insights_html(analysis_result.get('key_insights', []))}
        </ul>
        
        <div class="analysis-details">
            <p><strong>시장 잠재력:</strong> {analysis_result.get('market_potential', 'N/A')}</p>
            <p><strong>경쟁 수준:</strong> {analysis_result.get('competition_level', 'N/A')}</p>
        </div>
    </div>
    
    <!-- 추천 상호명 -->
    <div class="section">
        <h2 class="section-title">3. 추천 상호명</h2>
        
        {self._generate_business_names_html(business_names, selected_name)}
    </div>
    
    <!-- 간판 디자인 -->
    <div class="section">
        <h2 class="section-title">4. 간판 디자인</h2>
        
        <p>생성된 간판 디자인: <strong>{len(signboard_images)}개</strong></p>
        
        {self._generate_images_html(signboard_images, "간판", data.get('selected_signboard', ''))}
    </div>
    
    <!-- 인테리어 디자인 -->
    <div class="section">
        <h2 class="section-title">5. 인테리어 디자인</h2>
        
        <p>생성된 인테리어 디자인: <strong>{len(interior_images)}개</strong></p>
        
        {self._generate_images_html(interior_images, "인테리어", data.get('selected_interior', ''))}
    </div>
    
    <!-- 색상 팔레트 -->
    <div class="section">
        <h2 class="section-title">6. 추천 색상 팔레트</h2>
        
        {self._generate_color_palette_html(color_palette)}
    </div>
    
    <!-- 예산 가이드 -->
    <div class="section">
        <h2 class="section-title">7. 예산 가이드</h2>
        
        {self._generate_budget_guide_html(budget_guide)}
    </div>
    
    <!-- 요약 및 권장사항 -->
    <div class="section">
        <h2 class="section-title">8. 요약 및 권장사항</h2>
        
        <div class="summary-box">
            <p>본 보고서는 AI 브랜딩 시스템을 통해 생성된 <strong>{business_info.get('industry', 'N/A')}</strong> 업종의 
            종합적인 브랜딩 솔루션입니다.</p>
            
            <h4>생성된 자산:</h4>
            <ul>
                <li>상호명 후보: {len(business_names)}개</li>
                <li>간판 디자인: {len(signboard_images)}개</li>
                <li>인테리어 디자인: {len(interior_images)}개</li>
                <li>색상 팔레트: 업종 맞춤형</li>
                <li>예산 가이드: 규모별 분석</li>
            </ul>
        </div>
        
        <h4>핵심 권장사항:</h4>
        <ol class="recommendations-list">
            {self._generate_recommendations_html(recommendations)}
        </ol>
        
        <div class="footer">
            <p>본 보고서는 {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}에 생성되었습니다.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
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
        
        # 직접 데이터도 확인
        if not business_info:
            business_info = data.get('business_info', {})
        
        return business_info
    
    def _generate_insights_html(self, insights: list) -> str:
        """인사이트 HTML 생성"""
        if not insights:
            return "<li>분석 결과가 없습니다.</li>"
        
        html_items = []
        for insight in insights[:5]:  # 최대 5개
            html_items.append(f"<li>{insight}</li>")
        
        return '\n'.join(html_items)
    
    def _generate_business_names_html(self, business_names: list, selected_name: str) -> str:
        """상호명 HTML 생성"""
        if not business_names:
            return "<p>상호명 후보가 없습니다.</p>"
        
        html = "<table class='data-table'>"
        html += "<tr><th>순위</th><th>상호명</th><th>설명</th><th>점수</th></tr>"
        
        for i, name_info in enumerate(business_names[:3], 1):
            name = name_info.get('name', 'N/A')
            description = name_info.get('description', '')[:50] + ('...' if len(name_info.get('description', '')) > 50 else '')
            score = name_info.get('score', 0)
            
            # 선택된 상호명 표시
            name_display = f"✓ {name}" if name == selected_name else name
            row_class = "selected-row" if name == selected_name else ""
            
            html += f"<tr class='{row_class}'>"
            html += f"<td>{i}</td>"
            html += f"<td><strong>{name_display}</strong></td>"
            html += f"<td>{description}</td>"
            html += f"<td>{score}/100</td>"
            html += "</tr>"
        
        html += "</table>"
        
        if selected_name:
            html += f"<div class='selected-info'><strong>최종 선택된 상호명:</strong> {selected_name}</div>"
        
        return html
    
    def _generate_images_html(self, images: list, image_type: str, selected_image: str) -> str:
        """이미지 정보 HTML 생성"""
        if not images:
            return f"<p>{image_type} 이미지가 없습니다.</p>"
        
        html = f"<table class='data-table'>"
        html += "<tr><th>번호</th><th>파일명</th><th>크기</th><th>AI 모델</th><th>상태</th></tr>"
        
        for i, img in enumerate(images[:3], 1):
            filename = img.get('key', '').split('/')[-1]
            size_mb = img.get('size', 0) / (1024 * 1024)
            ai_model = img.get('ai_model', 'DALL-E 3')
            status = "✓ 선택됨" if img.get('key') == selected_image else "생성됨"
            
            row_class = "selected-row" if img.get('key') == selected_image else ""
            
            html += f"<tr class='{row_class}'>"
            html += f"<td>{i}</td>"
            html += f"<td>{filename[:30]}</td>"
            html += f"<td>{size_mb:.1f}MB</td>"
            html += f"<td>{ai_model}</td>"
            html += f"<td>{status}</td>"
            html += "</tr>"
        
        html += "</table>"
        
        # 이미지 플레이스홀더
        html += "<div class='image-placeholders'>"
        for i, img in enumerate(images[:3], 1):
            style = img.get('style', 'Modern')
            ai_model = img.get('ai_model', 'DALL-E 3')
            
            html += f"""
            <div class='image-placeholder'>
                <div class='placeholder-content'>
                    <h4>{image_type} {i}</h4>
                    <p>스타일: {style}</p>
                    <p>AI 모델: {ai_model}</p>
                </div>
            </div>
            """
        
        html += "</div>"
        
        return html
    
    def _generate_color_palette_html(self, color_palette: dict) -> str:
        """색상 팔레트 HTML 생성"""
        if not color_palette:
            return "<p>색상 팔레트가 없습니다.</p>"
        
        html = "<div class='color-palette'>"
        
        for color_type, color_info in color_palette.items():
            name = color_info.get('name', 'N/A')
            hex_code = color_info.get('hex', '#000000')
            usage = color_info.get('usage', 'N/A')
            
            html += f"""
            <div class='color-item'>
                <div class='color-swatch' style='background-color: {hex_code};'></div>
                <div class='color-info'>
                    <h4>{color_type.title()}: {name}</h4>
                    <p>색상 코드: {hex_code}</p>
                    <p>사용 용도: {usage}</p>
                </div>
            </div>
            """
        
        html += "</div>"
        return html
    
    def _generate_budget_guide_html(self, budget_guide: dict) -> str:
        """예산 가이드 HTML 생성"""
        if not budget_guide:
            return "<p>예산 가이드가 없습니다.</p>"
        
        html = "<table class='budget-table'>"
        html += "<tr><th>항목</th><th>최소</th><th>권장</th><th>최대</th></tr>"
        
        for category, costs in budget_guide.items():
            if category == 'total':
                html += f"<tr class='total-row'>"
                html += f"<td><strong>총 예산</strong></td>"
            else:
                html += f"<tr>"
                html += f"<td>{category.title()}</td>"
            
            html += f"<td>{costs.get('min', 0):,}원</td>"
            html += f"<td><strong>{costs.get('recommended', 0):,}원</strong></td>"
            html += f"<td>{costs.get('max', 0):,}원</td>"
            html += "</tr>"
        
        html += "</table>"
        return html
    
    def _generate_recommendations_html(self, recommendations: list) -> str:
        """권장사항 HTML 생성"""
        if not recommendations:
            return "<li>권장사항이 없습니다.</li>"
        
        html_items = []
        for rec in recommendations[:5]:  # 최대 5개
            html_items.append(f"<li>{rec}</li>")
        
        return '\n'.join(html_items)
    
    def _generate_css_styles(self) -> str:
        """CSS 스타일 생성"""
        return """
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Noto Sans KR', sans-serif;
            font-size: 12px;
            line-height: 1.6;
            color: #333;
            background: white;
        }
        
        .cover-page {
            text-align: center;
            padding: 100px 50px;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        
        .main-title {
            font-size: 36px;
            font-weight: 700;
            color: #2563eb;
            margin-bottom: 30px;
        }
        
        .subtitle {
            font-size: 20px;
            font-weight: 400;
            color: #64748b;
            margin-bottom: 50px;
        }
        
        .cover-info {
            margin-top: 50px;
        }
        
        .info-table {
            margin: 0 auto;
            border-collapse: collapse;
        }
        
        .info-table td {
            padding: 10px 20px;
            border: 1px solid #e2e8f0;
            background: #f8fafc;
        }
        
        .info-table td:first-child {
            background: #e2e8f0;
            font-weight: 500;
        }
        
        .page-break {
            page-break-before: always;
        }
        
        .section {
            margin: 30px 0;
            padding: 0 30px;
        }
        
        .section-title {
            font-size: 18px;
            font-weight: 600;
            color: #2563eb;
            margin-bottom: 20px;
            border-bottom: 2px solid #2563eb;
            padding-bottom: 10px;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        .data-table th,
        .data-table td {
            padding: 12px;
            text-align: left;
            border: 1px solid #e2e8f0;
        }
        
        .data-table th {
            background: #2563eb;
            color: white;
            font-weight: 500;
        }
        
        .data-table tr:nth-child(even) {
            background: #f8fafc;
        }
        
        .selected-row {
            background: #dbeafe !important;
            font-weight: 500;
        }
        
        .score-box {
            background: #f0f9ff;
            border: 2px solid #2563eb;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
        }
        
        .score-box h3 {
            font-size: 24px;
            color: #2563eb;
        }
        
        .insights-list {
            margin: 20px 0;
            padding-left: 20px;
        }
        
        .insights-list li {
            margin: 10px 0;
            line-height: 1.8;
        }
        
        .analysis-details {
            background: #f8fafc;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .selected-info {
            background: #dbeafe;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #2563eb;
        }
        
        .image-placeholders {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin: 20px 0;
        }
        
        .image-placeholder {
            width: 200px;
            height: 120px;
            border: 2px dashed #94a3b8;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f1f5f9;
        }
        
        .placeholder-content {
            text-align: center;
            color: #64748b;
        }
        
        .placeholder-content h4 {
            font-size: 14px;
            margin-bottom: 5px;
        }
        
        .placeholder-content p {
            font-size: 10px;
            margin: 2px 0;
        }
        
        .color-palette {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin: 20px 0;
        }
        
        .color-item {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            background: #fefefe;
        }
        
        .color-swatch {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            border: 2px solid #e2e8f0;
        }
        
        .color-info h4 {
            font-size: 14px;
            margin-bottom: 5px;
        }
        
        .color-info p {
            font-size: 11px;
            color: #64748b;
            margin: 2px 0;
        }
        
        .budget-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        .budget-table th,
        .budget-table td {
            padding: 12px;
            text-align: right;
            border: 1px solid #e2e8f0;
        }
        
        .budget-table th {
            background: #2563eb;
            color: white;
            text-align: center;
        }
        
        .budget-table td:first-child {
            text-align: left;
        }
        
        .total-row {
            background: #f0f9ff;
            font-weight: 600;
            border-top: 2px solid #2563eb;
        }
        
        .summary-box {
            background: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #10b981;
        }
        
        .recommendations-list {
            margin: 20px 0;
            padding-left: 20px;
        }
        
        .recommendations-list li {
            margin: 15px 0;
            line-height: 1.8;
        }
        
        .footer {
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            border-top: 1px solid #e2e8f0;
            color: #64748b;
            font-size: 11px;
        }
        
        @media print {
            .page-break {
                page-break-before: always;
            }
        }
        """


def create_html_branding_report_pdf(data: Dict[str, Any]) -> io.BytesIO:
    """HTML 기반 브랜딩 보고서 PDF 생성"""
    generator = HTMLPDFGenerator()
    return generator.create_branding_report(data)


if __name__ == "__main__":
    # 테스트
    test_data = {
        "session_id": "html-test-123",
        "session": {
            "business_info": json.dumps({
                "industry": "카페",
                "region": "서울 강남구",
                "size": "소규모"
            })
        },
        "business_info": {
            "industry": "카페",
            "region": "서울 강남구",
            "size": "소규모",
            "description": "아늑한 분위기의 스페셜티 커피 전문점"
        },
        "analysis_result": {
            "overall_score": 87,
            "key_insights": ["테스트 인사이트 1", "테스트 인사이트 2"]
        },
        "business_names": [
            {"name": "카페 모먼트", "description": "특별한 순간을 만드는 커피 공간", "score": 91}
        ],
        "selected_name": "카페 모먼트",
        "signboard_images": [{"key": "test.jpg", "size": 1024000, "ai_model": "DALL-E 3"}],
        "interior_images": [{"key": "test.jpg", "size": 2048000, "ai_model": "DALL-E 3"}],
        "color_palette": {
            "primary": {"name": "따뜻한 브라운", "hex": "#8B4513", "usage": "로고, 간판"}
        },
        "budget_guide": {
            "signboard": {"min": 500000, "recommended": 1000000, "max": 2000000}
        },
        "recommendations": ["테스트 권장사항 1", "테스트 권장사항 2"]
    }
    
    try:
        pdf_buffer = create_html_branding_report_pdf(test_data)
        print(f"HTML PDF generated: {len(pdf_buffer.getvalue())} bytes")
        
        with open("html_test_report.pdf", "wb") as f:
            f.write(pdf_buffer.getvalue())
        print("HTML PDF saved as 'html_test_report.pdf'")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()