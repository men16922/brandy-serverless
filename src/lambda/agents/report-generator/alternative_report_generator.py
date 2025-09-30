#!/usr/bin/env python3
"""
Alternative Report Generator - PDF 대신 HTML, JSON, 텍스트 형식 지원
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid
import io


class AlternativeReportGenerator:
    """PDF 대신 다양한 형식으로 보고서 생성"""
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def generate_html_report(self, data: Dict[str, Any]) -> str:
        """HTML 형식 보고서 생성"""
        try:
            business_info = data.get("business_info", {})
            analysis_result = data.get("analysis_result", {})
            business_names = data.get("business_names", [])
            signboard_images = data.get("signboard_images", [])
            interior_images = data.get("interior_images", [])
            color_palette = data.get("color_palette", {})
            budget_guide = data.get("budget_guide", {})
            recommendations = data.get("recommendations", [])
            
            html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 브랜딩 보고서</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-top: 30px;
        }}
        h3 {{
            color: #2c3e50;
            margin-top: 25px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}
        .info-card {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .info-label {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        .info-value {{
            color: #34495e;
        }}
        .score-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .score-circle {{
            display: inline-block;
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: linear-gradient(45deg, #3498db, #2ecc71);
            color: white;
            font-size: 24px;
            font-weight: bold;
            line-height: 100px;
            margin: 10px;
        }}
        .names-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .name-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #e9ecef;
            transition: all 0.3s ease;
        }}
        .name-card.selected {{
            border-color: #28a745;
            background: #d4edda;
        }}
        .name-title {{
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        .name-score {{
            color: #28a745;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .name-description {{
            color: #6c757d;
            font-size: 14px;
        }}
        .images-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .image-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #dee2e6;
        }}
        .image-placeholder {{
            width: 100%;
            height: 150px;
            background: linear-gradient(45deg, #e9ecef, #f8f9fa);
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #6c757d;
            margin-bottom: 10px;
        }}
        .color-palette {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .color-item {{
            display: flex;
            align-items: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .color-box {{
            width: 40px;
            height: 40px;
            border-radius: 5px;
            margin-right: 15px;
            border: 2px solid #dee2e6;
        }}
        .color-info {{
            flex: 1;
        }}
        .color-name {{
            font-weight: bold;
            color: #2c3e50;
        }}
        .color-hex {{
            color: #6c757d;
            font-size: 12px;
        }}
        .color-usage {{
            color: #495057;
            font-size: 14px;
        }}
        .budget-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .budget-table th,
        .budget-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        .budget-table th {{
            background: #f8f9fa;
            font-weight: bold;
            color: #2c3e50;
        }}
        .budget-table .total-row {{
            background: #e3f2fd;
            font-weight: bold;
        }}
        .recommendations {{
            background: #f0f8ff;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #2196f3;
        }}
        .recommendations ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .recommendations li {{
            margin-bottom: 10px;
            color: #2c3e50;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            color: #6c757d;
            font-size: 14px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .status-selected {{
            background: #d4edda;
            color: #155724;
        }}
        .status-generated {{
            background: #d1ecf1;
            color: #0c5460;
        }}
        @media print {{
            body {{ background: white; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 AI 브랜딩 보고서</h1>
        
        <h2>📋 비즈니스 정보</h2>
        <div class="info-grid">
            <div class="info-card">
                <div class="info-label">업종</div>
                <div class="info-value">{business_info.get('industry', 'N/A')}</div>
            </div>
            <div class="info-card">
                <div class="info-label">지역</div>
                <div class="info-value">{business_info.get('region', 'N/A')}</div>
            </div>
            <div class="info-card">
                <div class="info-label">규모</div>
                <div class="info-value">{business_info.get('size', 'N/A')}</div>
            </div>
            <div class="info-card">
                <div class="info-label">생성일</div>
                <div class="info-value">{datetime.now().strftime('%Y년 %m월 %d일')}</div>
            </div>
        </div>
        
        {self._generate_analysis_section_html(analysis_result)}
        
        {self._generate_business_names_section_html(business_names, data.get('selected_name', ''))}
        
        {self._generate_signboard_section_html(signboard_images, data.get('selected_signboard', ''))}
        
        {self._generate_interior_section_html(interior_images, data.get('selected_interior', ''))}
        
        {self._generate_color_palette_section_html(color_palette)}
        
        {self._generate_budget_section_html(budget_guide)}
        
        {self._generate_recommendations_section_html(recommendations)}
        
        <div class="footer">
            <p>Generated by AI Branding Chatbot on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Session ID: {data.get('session_id', 'N/A')}</p>
        </div>
    </div>
</body>
</html>
            """
            
            return html_content.strip()
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to generate HTML report: {str(e)}")
            raise
    
    def _generate_analysis_section_html(self, analysis_result: Dict[str, Any]) -> str:
        """AI 분석 결과 섹션 HTML 생성"""
        if not analysis_result:
            return ""
        
        overall_score = analysis_result.get('overall_score', 0)
        market_potential = analysis_result.get('market_potential', 'N/A')
        competition_level = analysis_result.get('competition_level', 'N/A')
        insights = analysis_result.get('insights', [])
        
        insights_html = ""
        if insights:
            insights_html = "<ul>" + "".join([f"<li>{insight}</li>" for insight in insights]) + "</ul>"
        
        return f"""
        <h2>🔍 AI 분석 결과</h2>
        <div class="score-container">
            <div class="score-circle">{overall_score}/100</div>
        </div>
        <div class="info-grid">
            <div class="info-card">
                <div class="info-label">시장 잠재력</div>
                <div class="info-value">{market_potential}</div>
            </div>
            <div class="info-card">
                <div class="info-label">경쟁 수준</div>
                <div class="info-value">{competition_level}</div>
            </div>
        </div>
        {f'<h3>핵심 인사이트</h3>{insights_html}' if insights else ''}
        """
    
    def _generate_business_names_section_html(self, business_names: List[Dict], selected_name: str) -> str:
        """상호명 섹션 HTML 생성"""
        if not business_names:
            return ""
        
        names_html = ""
        for i, name_data in enumerate(business_names[:3]):
            name = name_data.get('name', f'Name {i+1}')
            score = name_data.get('total_score', name_data.get('score', 0))
            description = name_data.get('description', '추천 상호명입니다.')
            
            selected_class = "selected" if name == selected_name else ""
            status_badge = '<span class="status-badge status-selected">✓ 선택됨</span>' if name == selected_name else '<span class="status-badge status-generated">생성됨</span>'
            
            names_html += f"""
            <div class="name-card {selected_class}">
                <div class="name-title">{i+1}. {name}{status_badge}</div>
                <div class="name-score">점수: {score}/100</div>
                <div class="name-description">{description}</div>
            </div>
            """
        
        return f"""
        <h2>🏪 추천 상호명</h2>
        <p>AI가 분석한 최적의 상호명 후보들입니다.</p>
        <div class="names-grid">
            {names_html}
        </div>
        """
    
    def _generate_signboard_section_html(self, signboard_images: List[Dict], selected_signboard: str) -> str:
        """간판 디자인 섹션 HTML 생성"""
        if not signboard_images:
            return ""
        
        images_html = ""
        for i, img in enumerate(signboard_images):
            filename = img.get('key', '').split('/')[-1]
            size_mb = img.get('size', 0) / (1024 * 1024)
            style = self._extract_style_from_filename(filename)
            
            selected_class = "selected" if filename == selected_signboard else ""
            status_badge = '<span class="status-badge status-selected">✓ 선택됨</span>' if filename == selected_signboard else '<span class="status-badge status-generated">생성됨</span>'
            
            images_html += f"""
            <div class="image-card {selected_class}">
                <div class="image-placeholder">
                    🖼️ 간판 이미지<br>{style}
                </div>
                <div><strong>{filename}</strong>{status_badge}</div>
                <div>크기: {size_mb:.1f}MB</div>
                <div>스타일: {style}</div>
            </div>
            """
        
        return f"""
        <h2>🪧 간판 디자인</h2>
        <p>총 {len(signboard_images)}개의 간판 디자인이 생성되었습니다.</p>
        <div class="images-grid">
            {images_html}
        </div>
        """
    
    def _generate_interior_section_html(self, interior_images: List[Dict], selected_interior: str) -> str:
        """인테리어 디자인 섹션 HTML 생성"""
        if not interior_images:
            return ""
        
        images_html = ""
        for i, img in enumerate(interior_images):
            filename = img.get('key', '').split('/')[-1]
            size_mb = img.get('size', 0) / (1024 * 1024)
            style = self._extract_style_from_filename(filename)
            
            selected_class = "selected" if filename == selected_interior else ""
            status_badge = '<span class="status-badge status-selected">✓ 선택됨</span>' if filename == selected_interior else '<span class="status-badge status-generated">생성됨</span>'
            
            images_html += f"""
            <div class="image-card {selected_class}">
                <div class="image-placeholder">
                    🏠 인테리어 이미지<br>{style}
                </div>
                <div><strong>{filename}</strong>{status_badge}</div>
                <div>크기: {size_mb:.1f}MB</div>
                <div>스타일: {style}</div>
            </div>
            """
        
        return f"""
        <h2>🏠 인테리어 디자인</h2>
        <p>총 {len(interior_images)}개의 인테리어 디자인이 생성되었습니다.</p>
        <div class="images-grid">
            {images_html}
        </div>
        """
    
    def _generate_color_palette_section_html(self, color_palette: Dict[str, Any]) -> str:
        """색상 팔레트 섹션 HTML 생성"""
        if not color_palette:
            return ""
        
        colors_html = ""
        for color_type, color_info in color_palette.items():
            if isinstance(color_info, dict):
                name = color_info.get('name', color_type)
                hex_code = color_info.get('hex', '#000000')
                usage = color_info.get('usage', '용도 미지정')
                
                colors_html += f"""
                <div class="color-item">
                    <div class="color-box" style="background-color: {hex_code};"></div>
                    <div class="color-info">
                        <div class="color-name">{name}</div>
                        <div class="color-hex">{hex_code}</div>
                        <div class="color-usage">{usage}</div>
                    </div>
                </div>
                """
        
        return f"""
        <h2>🎨 색상 팔레트</h2>
        <p>브랜드에 최적화된 색상 조합입니다.</p>
        <div class="color-palette">
            {colors_html}
        </div>
        """
    
    def _generate_budget_section_html(self, budget_guide: Dict[str, Any]) -> str:
        """예산 가이드 섹션 HTML 생성"""
        if not budget_guide:
            return ""
        
        budget_rows = ""
        total_data = None
        
        for category, costs in budget_guide.items():
            if category == 'total':
                total_data = costs
                continue
            
            if isinstance(costs, dict):
                category_name = {
                    'signboard': '간판',
                    'interior': '인테리어',
                    'branding': '브랜딩',
                    'marketing': '마케팅'
                }.get(category, category)
                
                min_cost = f"{costs.get('min', 0):,} 원"
                recommended_cost = f"{costs.get('recommended', 0):,} 원"
                max_cost = f"{costs.get('max', 0):,} 원"
                
                budget_rows += f"""
                <tr>
                    <td>{category_name}</td>
                    <td>{min_cost}</td>
                    <td>{recommended_cost}</td>
                    <td>{max_cost}</td>
                </tr>
                """
        
        total_row = ""
        if total_data:
            total_row = f"""
            <tr class="total-row">
                <td><strong>총 예산</strong></td>
                <td><strong>{total_data.get('min', 0):,} 원</strong></td>
                <td><strong>{total_data.get('recommended', 0):,} 원</strong></td>
                <td><strong>{total_data.get('max', 0):,} 원</strong></td>
            </tr>
            """
        
        return f"""
        <h2>💰 예산 가이드</h2>
        <p>규모와 업종을 고려한 예산 범위입니다.</p>
        <table class="budget-table">
            <thead>
                <tr>
                    <th>항목</th>
                    <th>최소</th>
                    <th>권장</th>
                    <th>최대</th>
                </tr>
            </thead>
            <tbody>
                {budget_rows}
                {total_row}
            </tbody>
        </table>
        """
    
    def _generate_recommendations_section_html(self, recommendations: List[str]) -> str:
        """권장사항 섹션 HTML 생성"""
        if not recommendations:
            return ""
        
        recommendations_html = "<ul>" + "".join([f"<li>{rec}</li>" for rec in recommendations]) + "</ul>"
        
        return f"""
        <h2>💡 권장사항</h2>
        <div class="recommendations">
            {recommendations_html}
        </div>
        """
    
    def _extract_style_from_filename(self, filename: str) -> str:
        """파일명에서 스타일 추출"""
        filename_lower = filename.lower()
        
        if 'modern' in filename_lower or '모던' in filename_lower:
            return '모던'
        elif 'classic' in filename_lower or '클래식' in filename_lower:
            return '클래식'
        elif 'minimal' in filename_lower or '미니멀' in filename_lower:
            return '미니멀'
        elif 'vibrant' in filename_lower or '활기찬' in filename_lower:
            return '활기찬'
        elif 'cozy' in filename_lower or '아늑한' in filename_lower:
            return '아늑한'
        elif 'professional' in filename_lower or '전문적' in filename_lower:
            return '전문적'
        elif 'scandinavian' in filename_lower or '스칸디나비안' in filename_lower:
            return '스칸디나비안'
        else:
            return '스타일'
    
    def generate_json_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """JSON 형식 보고서 생성"""
        try:
            report = {
                "metadata": {
                    "report_type": "branding_report",
                    "format": "json",
                    "generated_at": datetime.utcnow().isoformat(),
                    "session_id": data.get("session_id"),
                    "version": "1.0"
                },
                "business_info": data.get("business_info", {}),
                "analysis_result": data.get("analysis_result", {}),
                "business_names": data.get("business_names", []),
                "selections": {
                    "selected_name": data.get("selected_name", ""),
                    "selected_signboard": data.get("selected_signboard", ""),
                    "selected_interior": data.get("selected_interior", "")
                },
                "assets": {
                    "signboard_images": data.get("signboard_images", []),
                    "interior_images": data.get("interior_images", []),
                    "uploaded_images": data.get("uploaded_images", [])
                },
                "design_elements": {
                    "color_palette": data.get("color_palette", {}),
                    "budget_guide": data.get("budget_guide", {}),
                    "recommendations": data.get("recommendations", [])
                },
                "summary": {
                    "total_signboard_images": len(data.get("signboard_images", [])),
                    "total_interior_images": len(data.get("interior_images", [])),
                    "has_analysis": bool(data.get("analysis_result")),
                    "has_color_palette": bool(data.get("color_palette")),
                    "has_budget_guide": bool(data.get("budget_guide"))
                }
            }
            
            return report
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to generate JSON report: {str(e)}")
            raise
    
    def generate_text_report(self, data: Dict[str, Any]) -> str:
        """텍스트 형식 보고서 생성"""
        try:
            business_info = data.get("business_info", {})
            analysis_result = data.get("analysis_result", {})
            business_names = data.get("business_names", [])
            signboard_images = data.get("signboard_images", [])
            interior_images = data.get("interior_images", [])
            color_palette = data.get("color_palette", {})
            budget_guide = data.get("budget_guide", {})
            recommendations = data.get("recommendations", [])
            
            report_lines = [
                "=" * 60,
                "AI 브랜딩 보고서",
                "=" * 60,
                "",
                "📋 비즈니스 정보",
                "-" * 30,
                f"업종: {business_info.get('industry', 'N/A')}",
                f"지역: {business_info.get('region', 'N/A')}",
                f"규모: {business_info.get('size', 'N/A')}",
                f"생성일: {datetime.now().strftime('%Y년 %m월 %d일')}",
                f"세션 ID: {data.get('session_id', 'N/A')}",
                ""
            ]
            
            # AI 분석 결과
            if analysis_result:
                report_lines.extend([
                    "🔍 AI 분석 결과",
                    "-" * 30,
                    f"종합 점수: {analysis_result.get('overall_score', 0)}/100",
                    f"시장 잠재력: {analysis_result.get('market_potential', 'N/A')}",
                    f"경쟁 수준: {analysis_result.get('competition_level', 'N/A')}",
                    ""
                ])
                
                insights = analysis_result.get('insights', [])
                if insights:
                    report_lines.append("핵심 인사이트:")
                    for insight in insights:
                        report_lines.append(f"• {insight}")
                    report_lines.append("")
            
            # 상호명 추천
            if business_names:
                report_lines.extend([
                    "🏪 추천 상호명",
                    "-" * 30
                ])
                
                selected_name = data.get('selected_name', '')
                for i, name_data in enumerate(business_names[:3]):
                    name = name_data.get('name', f'Name {i+1}')
                    score = name_data.get('total_score', name_data.get('score', 0))
                    description = name_data.get('description', '추천 상호명입니다.')
                    
                    status = " ✓ 선택됨" if name == selected_name else ""
                    report_lines.append(f"{i+1}. {name} ({score}/100){status}")
                    report_lines.append(f"   {description}")
                
                report_lines.append("")
            
            # 간판 디자인
            if signboard_images:
                report_lines.extend([
                    "🪧 간판 디자인",
                    "-" * 30,
                    f"총 {len(signboard_images)}개의 간판 디자인이 생성되었습니다.",
                    ""
                ])
                
                selected_signboard = data.get('selected_signboard', '')
                for img in signboard_images:
                    filename = img.get('key', '').split('/')[-1]
                    size_mb = img.get('size', 0) / (1024 * 1024)
                    style = self._extract_style_from_filename(filename)
                    
                    status = " ✓ 선택됨" if filename == selected_signboard else ""
                    report_lines.append(f"• {filename} ({size_mb:.1f}MB, {style}){status}")
                
                report_lines.append("")
            
            # 인테리어 디자인
            if interior_images:
                report_lines.extend([
                    "🏠 인테리어 디자인",
                    "-" * 30,
                    f"총 {len(interior_images)}개의 인테리어 디자인이 생성되었습니다.",
                    ""
                ])
                
                selected_interior = data.get('selected_interior', '')
                for img in interior_images:
                    filename = img.get('key', '').split('/')[-1]
                    size_mb = img.get('size', 0) / (1024 * 1024)
                    style = self._extract_style_from_filename(filename)
                    
                    status = " ✓ 선택됨" if filename == selected_interior else ""
                    report_lines.append(f"• {filename} ({size_mb:.1f}MB, {style}){status}")
                
                report_lines.append("")
            
            # 색상 팔레트
            if color_palette:
                report_lines.extend([
                    "🎨 색상 팔레트",
                    "-" * 30
                ])
                
                for color_type, color_info in color_palette.items():
                    if isinstance(color_info, dict):
                        name = color_info.get('name', color_type)
                        hex_code = color_info.get('hex', '#000000')
                        usage = color_info.get('usage', '용도 미지정')
                        report_lines.append(f"• {name}: {hex_code} ({usage})")
                
                report_lines.append("")
            
            # 예산 가이드
            if budget_guide:
                report_lines.extend([
                    "💰 예산 가이드",
                    "-" * 30
                ])
                
                for category, costs in budget_guide.items():
                    if category == 'total':
                        continue
                    
                    if isinstance(costs, dict):
                        category_name = {
                            'signboard': '간판',
                            'interior': '인테리어',
                            'branding': '브랜딩',
                            'marketing': '마케팅'
                        }.get(category, category)
                        
                        min_cost = f"{costs.get('min', 0):,}원"
                        recommended_cost = f"{costs.get('recommended', 0):,}원"
                        max_cost = f"{costs.get('max', 0):,}원"
                        
                        report_lines.append(f"• {category_name}: {min_cost} ~ {max_cost} (권장: {recommended_cost})")
                
                # 총 예산
                total_data = budget_guide.get('total')
                if total_data:
                    total_min = f"{total_data.get('min', 0):,}원"
                    total_recommended = f"{total_data.get('recommended', 0):,}원"
                    total_max = f"{total_data.get('max', 0):,}원"
                    report_lines.append(f"• 총 예산: {total_min} ~ {total_max} (권장: {total_recommended})")
                
                report_lines.append("")
            
            # 권장사항
            if recommendations:
                report_lines.extend([
                    "💡 권장사항",
                    "-" * 30
                ])
                
                for rec in recommendations:
                    report_lines.append(f"• {rec}")
                
                report_lines.append("")
            
            # 푸터
            report_lines.extend([
                "=" * 60,
                f"Generated by AI Branding Chatbot on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "=" * 60
            ])
            
            return "\n".join(report_lines)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to generate text report: {str(e)}")
            raise