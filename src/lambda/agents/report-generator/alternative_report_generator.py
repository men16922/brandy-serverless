#!/usr/bin/env python3
"""
Alternative Report Generator - Supports HTML, JSON, and Text formats (instead of PDF)
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid
import io


class AlternativeReportGenerator:
    """Generate reports in multiple formats instead of PDF"""

    def __init__(self, logger=None):
        self.logger = logger

    def generate_html_report(self, data: Dict[str, Any]) -> str:
        """Generate an HTML-format report"""
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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Branding Report</title>
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
        .actual-image {{
            width: 100%;
            height: 200px;
            object-fit: cover;
            border-radius: 5px;
            margin-bottom: 10px;
            border: 2px solid #dee2e6;
        }}
        .image-error {{
            width: 100%;
            height: 150px;
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #721c24;
            margin-bottom: 10px;
            font-size: 14px;
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
        <h1>🎨 AI Branding Report</h1>

        <h2>📋 Business Information</h2>
        <div class="info-grid">
            <div class="info-card">
                <div class="info-label">Industry</div>
                <div class="info-value">{business_info.get('industry', 'N/A')}</div>
            </div>
            <div class="info-card">
                <div class="info-label">Region</div>
                <div class="info-value">{business_info.get('region', 'N/A')}</div>
            </div>
            <div class="info-card">
                <div class="info-label">Size</div>
                <div class="info-value">{business_info.get('size', 'N/A')}</div>
            </div>
            <div class="info-card">
                <div class="info-label">Generated On</div>
                <div class="info-value">{datetime.now().strftime('%Y-%m-%d')}</div>
            </div>
        </div>

        {self._generate_analysis_section_html(analysis_result)}

        {self._generate_business_names_section_html(business_names, data.get('selected_name', ''))}

        {self._generate_signboard_section_html(signboard_images, data.get('selected_signboard', ''))}

        {self._generate_interior_section_html(interior_images, data.get('selected_interior', ''))}

        {self._generate_color_palette_section_html(color_palette)}

        {self._generate_budget_section_html(budget_guide)}

        {self._generate_synthesized_insights_section_html(data.get('synthesized_insights', ''))}

        {self._generate_recommendations_section_html(recommendations)}

        <div class="footer">
            <p>Generated by AI Branding Chatbot on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Session ID: {data.get('session_id', 'N/A')}</p>
            {('<p style="color: #2196f3; font-weight: bold;">✨ Enhanced with Amazon Bedrock Claude AI</p>' if data.get('synthesized_insights') else '')}
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
        """Generate HTML for the AI analysis section"""
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
        <h2>🔍 AI Analysis Results</h2>
        <div class="score-container">
            <div class="score-circle">{overall_score}/100</div>
        </div>
        <div class="info-grid">
            <div class="info-card">
                <div class="info-label">Market Potential</div>
                <div class="info-value">{market_potential}</div>
            </div>
            <div class="info-card">
                <div class="info-label">Competition Level</div>
                <div class="info-value">{competition_level}</div>
            </div>
        </div>
        {f'<h3>Key Insights</h3>{insights_html}' if insights else ''}
        """

    def _generate_business_names_section_html(self, business_names: List[Dict], selected_name: str) -> str:
        """Generate HTML for business name candidates"""
        if not business_names:
            return ""

        names_html = ""
        for i, name_data in enumerate(business_names[:3]):
            name = name_data.get('name', f'Name {i+1}')
            score = name_data.get('total_score', name_data.get('score', 0))
            description = name_data.get('description', 'Recommended business name.')

            selected_class = "selected" if name == selected_name else ""
            status_badge = '<span class="status-badge status-selected">✓ Selected</span>' if name == selected_name else '<span class="status-badge status-generated">Generated</span>'

            names_html += f"""
            <div class="name-card {selected_class}">
                <div class="name-title">{i+1}. {name}{status_badge}</div>
                <div class="name-score">Score: {score}/100</div>
                <div class="name-description">{description}</div>
            </div>
            """

        return f"""
        <h2>🏪 Recommended Business Names</h2>
        <p>Top candidates analyzed by AI.</p>
        <div class="names-grid">
            {names_html}
        </div>
        """

    def _generate_signboard_section_html(self, signboard_images: List[Dict], selected_signboard: str) -> str:
        """Generate HTML for signboard design (show selected image only)"""
        if not signboard_images:
            return ""

        # Find selected image
        selected_image = None
        for img in signboard_images:
            filename = img.get('key', '').split('/')[-1]
            if filename == selected_signboard:
                selected_image = img
                break

        # Fallback to first image if nothing selected
        if not selected_image and signboard_images:
            selected_image = signboard_images[0]

        if not selected_image:
            return ""

        # Selected image details
        filename = selected_image.get('key', '').split('/')[-1]
        size_mb = selected_image.get('size', 0) / (1024 * 1024)
        style = self._extract_style_from_filename(filename)

        # Resolve image URLs
        image_url = selected_image.get('url', '')
        presigned_url = selected_image.get('presigned_url', '')

        # Render image with graceful fallback
        if presigned_url:
            image_html = f'<img src="{presigned_url}" alt="Selected signboard design - {style}" class="actual-image" style="max-width: 100%; height: auto; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\';">'
            fallback_html = f'<div class="image-placeholder" style="display:none;">🖼️ Signboard Image<br>{style}</div>'
        elif image_url:
            image_html = f'<img src="{image_url}" alt="Selected signboard design - {style}" class="actual-image" style="max-width: 100%; height: auto; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\';">'
            fallback_html = f'<div class="image-placeholder" style="display:none;">🖼️ Signboard Image<br>{style}</div>'
        else:
            image_html = f'<div class="image-placeholder">🖼️ Signboard Image<br>{style}</div>'
            fallback_html = ''

        return f"""
        <h2>🪧 Selected Signboard Design</h2>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <div style="text-align: center; margin-bottom: 15px;">
                {image_html}
                {fallback_html}
            </div>
            <div style="text-align: center;">
                <p style="margin: 10px 0;"><strong>Filename:</strong> {filename}</p>
                <p style="margin: 10px 0;"><strong>Size:</strong> {size_mb:.1f} MB</p>
                <p style="margin: 10px 0;"><strong>Style:</strong> {style}</p>
                <span class="status-badge status-selected" style="display: inline-block; margin-top: 10px;">✓ Final Selection</span>
            </div>
        </div>
        <p style="color: #6c757d; font-size: 14px; text-align: center;">Selected from {len(signboard_images)} design(s).</p>
        """

    def _generate_interior_section_html(self, interior_images: List[Dict], selected_interior: str) -> str:
        """Generate HTML for interior design (show selected image only when available)"""
        # If no images and no selection, omit the section
        if not interior_images and not selected_interior:
            return ""

        # Try to match a selected image by style name or filename
        selected_image = None
        if interior_images:
            for img in interior_images:
                filename = img.get('key', '').split('/')[-1]
                style = self._extract_style_from_filename(filename)

                if selected_interior and (style.lower() == selected_interior.lower() or filename == selected_interior):
                    selected_image = img
                    break

            # Fallback to first image if no explicit match
            if not selected_image and interior_images:
                selected_image = interior_images[0]

        # Render either image+details or style-only placeholder
        if selected_image:
            return self._generate_interior_with_image_html(selected_image, interior_images, selected_interior)
        elif selected_interior:
            return self._generate_interior_without_image_html(selected_interior)
        else:
            return ""

    def _generate_interior_without_image_html(self, selected_style: str) -> str:
        """Render only the selected interior style when no image is available"""
        style_display = selected_style.capitalize()

        return f"""
        <h2>🏠 Selected Interior Design</h2>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <div style="text-align: center; margin-bottom: 15px;">
                <div class="image-placeholder" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 60px 20px; border-radius: 10px; font-size: 24px;">
                    🏠 {style_display} Style
                </div>
            </div>
            <div style="text-align: center;">
                <p style="margin: 10px 0;"><strong>Selected Style:</strong> {style_display}</p>
                <p style="margin: 10px 0; color: #6c757d;">The image is not generated yet or cannot be found.</p>
                <span class="status-badge status-selected" style="display: inline-block; margin-top: 10px;">✓ Final Selection</span>
            </div>
        </div>
        """

    def _generate_interior_with_image_html(self, selected_image: Dict, all_images: List[Dict], selected_interior: str) -> str:
        """Render interior section with the selected image"""
        if not selected_image:
            return ""

        filename = selected_image.get('key', '').split('/')[-1]
        size_mb = selected_image.get('size', 0) / (1024 * 1024)
        style = self._extract_style_from_filename(filename)

        image_url = selected_image.get('url', '')
        presigned_url = selected_image.get('presigned_url', '')

        if presigned_url:
            image_html = f'<img src="{presigned_url}" alt="Selected interior design - {style}" class="actual-image" style="max-width: 100%; height: auto; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\';">'
            fallback_html = f'<div class="image-placeholder" style="display:none;">🏠 Interior Image<br>{style}</div>'
        elif image_url:
            image_html = f'<img src="{image_url}" alt="Selected interior design - {style}" class="actual-image" style="max-width: 100%; height: auto; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\';">'
            fallback_html = f'<div class="image-placeholder" style="display:none;">🏠 Interior Image<br>{style}</div>'
        else:
            image_html = f'<div class="image-placeholder">🏠 Interior Image<br>{style}</div>'
            fallback_html = ''

        return f"""
        <h2>🏠 Selected Interior Design</h2>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <div style="text-align: center; margin-bottom: 15px;">
                {image_html}
                {fallback_html}
            </div>
            <div style="text-align: center;">
                <p style="margin: 10px 0;"><strong>Filename:</strong> {filename}</p>
                <p style="margin: 10px 0;"><strong>Size:</strong> {size_mb:.1f} MB</p>
                <p style="margin: 10px 0;"><strong>Style:</strong> {style}</p>
                <span class="status-badge status-selected" style="display: inline-block; margin-top: 10px;">✓ Final Selection</span>
            </div>
        </div>
        <p style="color: #6c757d; font-size: 14px; text-align: center;">Selected from {len(all_images)} design(s).</p>
        """

    def _generate_color_palette_section_html(self, color_palette: Dict[str, Any]) -> str:
        """Generate HTML for the color palette"""
        if not color_palette:
            return ""

        colors_html = ""
        for color_type, color_info in color_palette.items():
            if isinstance(color_info, dict):
                name = color_info.get('name', color_type)
                hex_code = color_info.get('hex', '#000000')
                usage = color_info.get('usage', 'Usage not specified')

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
        <h2>🎨 Color Palette</h2>
        <p>Color combinations optimized for the brand.</p>
        <div class="color-palette">
            {colors_html}
        </div>
        """

    def _generate_budget_section_html(self, budget_guide: Dict[str, Any]) -> str:
        """Generate HTML for the budget guide"""
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
                    'signboard': 'Signboard',
                    'interior': 'Interior',
                    'branding': 'Branding',
                    'marketing': 'Marketing'
                }.get(category, category)

                min_cost = f"{costs.get('min', 0):,} KRW"
                recommended_cost = f"{costs.get('recommended', 0):,} KRW"
                max_cost = f"{costs.get('max', 0):,} KRW"

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
                <td><strong>Total</strong></td>
                <td><strong>{total_data.get('min', 0):,} KRW</strong></td>
                <td><strong>{total_data.get('recommended', 0):,} KRW</strong></td>
                <td><strong>{total_data.get('max', 0):,} KRW</strong></td>
            </tr>
            """

        return f"""
        <h2>💰 Budget Guide</h2>
        <p>Budget ranges considering scale and industry.</p>
        <table class="budget-table">
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Min</th>
                    <th>Recommended</th>
                    <th>Max</th>
                </tr>
            </thead>
            <tbody>
                {budget_rows}
                {total_row}
            </tbody>
        </table>
        """

    def _convert_markdown_to_html(self, text: str) -> str:
        """Convert basic Markdown formatting to HTML"""
        import re
        
        # Convert headers (## Header -> <h3>)
        text = re.sub(r'^## (.+)$', r'<h3 style="color: #2c3e50; margin: 20px 0 10px 0; font-size: 18px; font-weight: 600;">\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^### (.+)$', r'<h4 style="color: #34495e; margin: 15px 0 8px 0; font-size: 16px; font-weight: 600;">\1</h4>', text, flags=re.MULTILINE)
        
        # Convert bold (**text** or __text__)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color: #2c3e50;">\1</strong>', text)
        text = re.sub(r'__(.+?)__', r'<strong style="color: #2c3e50;">\1</strong>', text)
        
        # Convert italic (*text* or _text_)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
        
        # Convert bullet lists (- item or * item)
        lines = text.split('\n')
        in_list = False
        result_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- ') or stripped.startswith('* '):
                if not in_list:
                    result_lines.append('<ul style="margin: 10px 0; padding-left: 25px;">')
                    in_list = True
                item_text = stripped[2:].strip()
                result_lines.append(f'<li style="margin: 5px 0; line-height: 1.6;">{item_text}</li>')
            else:
                if in_list:
                    result_lines.append('</ul>')
                    in_list = False
                if stripped:
                    result_lines.append(line)
        
        if in_list:
            result_lines.append('</ul>')
        
        return '\n'.join(result_lines)
    
    def _generate_synthesized_insights_section_html(self, synthesized_insights: str) -> str:
        """Generate the Bedrock Claude synthesized insights section (HTML)"""
        if not synthesized_insights:
            return ""

        # Convert Markdown to HTML
        html_content = self._convert_markdown_to_html(synthesized_insights)
        
        # Split into paragraphs and format
        paragraphs = [p.strip() for p in html_content.split('\n\n') if p.strip()]
        
        # Format paragraphs with proper spacing and styling
        insights_html = ""
        for i, paragraph in enumerate(paragraphs):
            # Skip if already HTML tag
            if paragraph.startswith('<h') or paragraph.startswith('<ul'):
                insights_html += paragraph + '\n'
            elif paragraph.startswith('<li'):
                insights_html += paragraph + '\n'
            else:
                # Regular paragraph with better spacing
                margin_top = "15px" if i > 0 else "0"
                insights_html += f'<p style="margin: {margin_top} 0 10px 0; line-height: 1.8; font-size: 15px; color: #2c3e50;">{paragraph}</p>'

        return f"""
        <h2>✨ AI Synthesized Insights</h2>
        <div style="background: white; padding: 30px; border-radius: 12px; border: 2px solid #667eea; margin: 20px 0; box-shadow: 0 4px 6px rgba(102, 126, 234, 0.1);">
            <div style="display: flex; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #e9ecef;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 10px 20px; border-radius: 8px; margin-right: 15px;">
                    <span style="font-size: 24px;">🤖</span>
                </div>
                <div>
                    <h3 style="margin: 0; color: #2c3e50; font-size: 20px;">Amazon Bedrock Claude</h3>
                    <p style="margin: 5px 0 0 0; color: #6c757d; font-size: 14px;">AI-Powered Analysis & Strategic Recommendations</p>
                </div>
            </div>
            <div style="color: #2c3e50;">
                {insights_html}
            </div>
            <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #e9ecef; text-align: right;">
                <span style="color: #6c757d; font-size: 13px; font-style: italic;">Powered by Amazon Bedrock</span>
            </div>
        </div>
        """

    def _generate_recommendations_section_html(self, recommendations: List[str]) -> str:
        """Generate the recommendations section (HTML)"""
        if not recommendations:
            return ""

        recommendations_html = "<ul>" + "".join([f"<li>{rec}</li>" for rec in recommendations]) + "</ul>"

        return f"""
        <h2>💡 Recommendations</h2>
        <div class="recommendations">
            {recommendations_html}
        </div>
        """

    def _extract_style_from_filename(self, filename: str) -> str:
        """Extract a style name from the filename"""
        filename_lower = filename.lower()

        if 'modern' in filename_lower or '모던' in filename_lower:
            return 'Modern'
        elif 'classic' in filename_lower or '클래식' in filename_lower:
            return 'Classic'
        elif 'minimal' in filename_lower or '미니멀' in filename_lower:
            return 'Minimal'
        elif 'vibrant' in filename_lower or '활기찬' in filename_lower:
            return 'Vibrant'
        elif 'cozy' in filename_lower or '아늑한' in filename_lower:
            return 'Cozy'
        elif 'professional' in filename_lower or '전문적' in filename_lower:
            return 'Professional'
        elif 'scandinavian' in filename_lower or '스칸디나비안' in filename_lower:
            return 'Scandinavian'
        else:
            return 'Style'

    def generate_json_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a JSON-format report"""
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
                    "interior_images": data.get("interior_images", [])
                },
                "design_elements": {
                    "color_palette": data.get("color_palette", {}),
                    "budget_guide": data.get("budget_guide", {}),
                    "recommendations": data.get("recommendations", [])
                },
                "ai_insights": {
                    "synthesized_insights": data.get("synthesized_insights", ""),
                    "bedrock_enhanced": bool(data.get("synthesized_insights"))
                },
                "summary": {
                    "total_signboard_images": len(data.get("signboard_images", [])),
                    "total_interior_images": len(data.get("interior_images", [])),
                    "has_analysis": bool(data.get("analysis_result")),
                    "has_color_palette": bool(data.get("color_palette")),
                    "has_budget_guide": bool(data.get("budget_guide")),
                    "bedrock_enhanced": bool(data.get("synthesized_insights"))
                }
            }

            return report

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to generate JSON report: {str(e)}")
            raise

    def generate_text_report(self, data: Dict[str, Any]) -> str:
        """Generate a plain-text report"""
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
                "AI Branding Report",
                "=" * 60,
                "",
                "📋 Business Information",
                "-" * 30,
                f"Industry: {business_info.get('industry', 'N/A')}",
                f"Region: {business_info.get('region', 'N/A')}",
                f"Size: {business_info.get('size', 'N/A')}",
                f"Generated On: {datetime.now().strftime('%Y-%m-%d')}",
                f"Session ID: {data.get('session_id', 'N/A')}",
                ""
            ]

            # AI analysis
            if analysis_result:
                report_lines.extend([
                    "🔍 AI Analysis",
                    "-" * 30,
                    f"Overall Score: {analysis_result.get('overall_score', 0)}/100",
                    f"Market Potential: {analysis_result.get('market_potential', 'N/A')}",
                    f"Competition Level: {analysis_result.get('competition_level', 'N/A')}",
                    ""
                ])

                insights = analysis_result.get('insights', [])
                if insights:
                    report_lines.append("Key Insights:")
                    for insight in insights:
                        report_lines.append(f"• {insight}")
                    report_lines.append("")

            # Business name candidates
            if business_names:
                report_lines.extend([
                    "🏪 Recommended Business Names",
                    "-" * 30
                ])

                selected_name = data.get('selected_name', '')
                for i, name_data in enumerate(business_names[:3]):
                    name = name_data.get('name', f'Name {i+1}')
                    score = name_data.get('total_score', name_data.get('score', 0))
                    description = name_data.get('description', 'Recommended business name.')

                    status = " ✓ Selected" if name == selected_name else ""
                    report_lines.append(f"{i+1}. {name} ({score}/100){status}")
                    report_lines.append(f"   {description}")

                report_lines.append("")

            # Signboard designs
            if signboard_images:
                report_lines.extend([
                    "🪧 Signboard Designs",
                    "-" * 30,
                    f"{len(signboard_images)} signboard design(s) generated.",
                    ""
                ])

                selected_signboard = data.get('selected_signboard', '')
                for img in signboard_images:
                    filename = img.get('key', '').split('/')[-1]
                    size_mb = img.get('size', 0) / (1024 * 1024)
                    style = self._extract_style_from_filename(filename)

                    status = " ✓ Selected" if filename == selected_signboard else ""
                    report_lines.append(f"• {filename} ({size_mb:.1f} MB, {style}){status}")

                report_lines.append("")

            # Interior designs
            if interior_images:
                report_lines.extend([
                    "🏠 Interior Designs",
                    "-" * 30,
                    f"{len(interior_images)} interior design(s) generated.",
                    ""
                ])

                selected_interior = data.get('selected_interior', '')
                for img in interior_images:
                    filename = img.get('key', '').split('/')[-1]
                    size_mb = img.get('size', 0) / (1024 * 1024)
                    style = self._extract_style_from_filename(filename)

                    status = " ✓ Selected" if filename == selected_interior else ""
                    report_lines.append(f"• {filename} ({size_mb:.1f} MB, {style}){status}")

                report_lines.append("")

            # Color palette
            if color_palette:
                report_lines.extend([
                    "🎨 Color Palette",
                    "-" * 30
                ])

                for color_type, color_info in color_palette.items():
                    if isinstance(color_info, dict):
                        name = color_info.get('name', color_type)
                        hex_code = color_info.get('hex', '#000000')
                        usage = color_info.get('usage', 'Usage not specified')
                        report_lines.append(f"• {name}: {hex_code} ({usage})")

                report_lines.append("")

            # Budget guide
            if budget_guide:
                report_lines.extend([
                    "💰 Budget Guide",
                    "-" * 30
                ])

                for category, costs in budget_guide.items():
                    if category == 'total':
                        continue

                    if isinstance(costs, dict):
                        category_name = {
                            'signboard': 'Signboard',
                            'interior': 'Interior',
                            'branding': 'Branding',
                            'marketing': 'Marketing'
                        }.get(category, category)

                        min_cost = f"{costs.get('min', 0):,} KRW"
                        recommended_cost = f"{costs.get('recommended', 0):,} KRW"
                        max_cost = f"{costs.get('max', 0):,} KRW"

                        report_lines.append(f"• {category_name}: {min_cost} ~ {max_cost} (Recommended: {recommended_cost})")

                # Totals
                total_data = budget_guide.get('total')
                if total_data:
                    total_min = f"{total_data.get('min', 0):,} KRW"
                    total_recommended = f"{total_data.get('recommended', 0):,} KRW"
                    total_max = f"{total_data.get('max', 0):,} KRW"
                    report_lines.append(f"• Total: {total_min} ~ {total_max} (Recommended: {total_recommended})")

                report_lines.append("")

            # AI synthesized insights (Bedrock Claude)
            synthesized_insights = data.get('synthesized_insights', '')
            if synthesized_insights:
                report_lines.extend([
                    "✨ AI Synthesized Insights (Amazon Bedrock Claude)",
                    "-" * 30
                ])

                paragraphs = [p.strip() for p in synthesized_insights.split('\n\n') if p.strip()]
                for paragraph in paragraphs:
                    report_lines.append(paragraph)
                    report_lines.append("")

            # Recommendations
            if recommendations:
                report_lines.extend([
                    "💡 Recommendations",
                    "-" * 30
                ])

                for rec in recommendations:
                    report_lines.append(f"• {rec}")

                report_lines.append("")

            # Footer
            report_lines.extend([
                "=" * 60,
                f"Generated by AI Branding Chatbot on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ])

            if synthesized_insights:
                report_lines.append("✨ Enhanced with Amazon Bedrock Claude AI")

            report_lines.append("=" * 60)

            return "\n".join(report_lines)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to generate text report: {str(e)}")
            raise
