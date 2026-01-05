from typing import Any, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from fpdf import FPDF

from app.cache.report_cache import ReportCache
from app.services.report_service import ReportService
from app.services.billing_service import BillingService
import logging

logger = logging.getLogger(__name__)

class KundaliPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

class PDFService:
    """
    API-facing service for generating kundali PDF reports.

    This is a thin wrapper over ReportService + PDF renderer.
    """

    def __init__(self):
        self.report_service = ReportService()
        self.billing_service = BillingService()
        self.cache = ReportCache()

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    async def generate(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        kundali_core_id: UUID,
        kundali_chart,
        include_transits: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate a PDF report for a kundali.
        """
        cached_pdf = await self.cache.get_report(
        kundali_core_id=kundali_core_id,
        include_transits=include_transits,
        )

        if cached_pdf:
            return {
                "filename": f"kundali_{kundali_core_id}.pdf",
                "content_type": "application/pdf",
                "bytes": cached_pdf,
            }

        # ─────────────────────────────────────────────
        # 1. Billing check
        # ─────────────────────────────────────────────

        self.billing_service.assert_quota(
            session=session,
            user_id=user_id,
            feature="pdf_report",
        )

        # ─────────────────────────────────────────────
        # 2. Build report context
        # ─────────────────────────────────────────────

        report_context = await self.report_service.build_report_context(
            session=session,
            user_id=user_id,
            kundali_core_id=kundali_core_id,
            kundali_chart=kundali_chart,
            include_transits=include_transits,
            timestamp=datetime.now(),
        )

        # ─────────────────────────────────────────────
        # 3. Render PDF (stub for now)
        # ─────────────────────────────────────────────

        result = self.render_pdf_from_data(report_context)
        pdf_bytes = result["bytes"]

        await self.cache.set_report(
        kundali_core_id=kundali_core_id,
        include_transits=include_transits,
        pdf_bytes=pdf_bytes,
        )

        # ─────────────────────────────────────────────
        # 4. Log usage
        # ─────────────────────────────────────────────

        self.billing_service.log_usage(
            session=session,
            user_id=user_id,
            feature="pdf_report",
        )

        return {
            "filename": f"kundali_{kundali_core_id}.pdf",
            "content_type": "application/pdf",
            "bytes": pdf_bytes,
        }

    # ─────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────

    def render_pdf_from_data(
        self,
        report_context: Dict[str, Any],
    ) -> bytes:
        """
        PDF renderer that handles data structure mismatches.
        """
        pdf = KundaliPDF('P', 'mm', 'A4')
        pdf.add_page()
        
        # Log the report context structure for debugging
        logger.debug("Received report context: %s", report_context)
        
        # Validate report context structure
        if not self._validate_report_context(report_context):
            logger.error("Invalid report context structure. Expected Kundali data.")
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, "Error: Invalid report data structure", 0, 1)
            pdf.cell(0, 10, "Please check the report generation service", 0, 1)
            pdf_bytes = pdf.output(dest='S').encode('latin1')
            return {
                "filename": "error.pdf",
                "bytes": pdf_bytes
            }

        birth_details = report_context.get('birth_details', {})
        name = str(birth_details.get('name') or 'kundali').replace(' ', '_')
        kundali_id = report_context.get('persisted', {}).get('core', {}).get('id', 'report')
        filename = f"{name}-{kundali_id[:8]}.pdf"
        
        # Extract data with fallbacks
        persisted = report_context.get('persisted', {})
        core = persisted.get('core', {})
        derived = persisted.get('derived', {})
        divisionals = persisted.get('divisionals', {})
        transits_payload = report_context.get('transits', {})
        explanations = report_context.get('explanations', [])
        dashas = report_context.get('dashas', [])
        sade_sati = report_context.get('sade_sati', {})
        avakahada = report_context.get('avakahada', {})
        meta = report_context.get('meta', {})
        ai_predictions = report_context.get('ai_predictions', {})
        
        # Log the extracted data for debugging
        logger.debug("Core data: %s", core)
        logger.debug("Meta data: %s", meta)
        
        # --- Header ---
        pdf.set_font('Arial', 'B', 24)
        pdf.cell(0, 20, 'Kundali Report', 0, 1, 'C')
        
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, f"Generated on: {meta.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}", 0, 1, 'C')
        pdf.line(10, 35, 200, 35)
        pdf.ln(10)
        
        if not core:
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, "No core data found", 0, 1)
            pdf_bytes = pdf.output(dest='S').encode('latin1')
            return {
                "filename": filename,
                "bytes": pdf_bytes
            }

        # --- Astrological Particulars (Ascendant / Moon) ---
        # Use the top-level kundali object for fresher data if available
        kundali_data = report_context.get('kundali', core)
        if 'ascendant' in kundali_data and 'planets' in kundali_data:
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, "Astrological Particulars", 0, 1)
            pdf.ln(2)
            
            asc = core['ascendant']
            moon = core['planets'].get('Moon', {})
            
            asc_sign = asc.get('sign') or '-'
            asc_lord = self._get_sign_lord(asc_sign)
            asc_nak = asc.get('nakshatra') or '-'
            
            moon_sign = moon.get('sign') or '-'
            moon_lord = self._get_sign_lord(moon_sign)
            moon_nak = moon.get('nakshatra') or '-'
            
            # Table Header
            pdf.set_font('Arial', 'B', 11)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(50, 8, "Feature", 1, 0, 'L', True)
            pdf.cell(45, 8, "Sign", 1, 0, 'C', True)
            pdf.cell(45, 8, "Lord", 1, 0, 'C', True)
            pdf.cell(50, 8, "Nakshatra", 1, 1, 'C', True)
            
            pdf.set_font('Arial', '', 11)
            
            # Ascendant Row
            pdf.cell(50, 8, "Ascendant (Lagna)", 1, 0, 'L')
            pdf.cell(45, 8, asc_sign, 1, 0, 'C')
            pdf.cell(45, 8, asc_lord, 1, 0, 'C')
            pdf.cell(50, 8, asc_nak, 1, 1, 'C')
            
            # Moon Row
            pdf.cell(50, 8, "Moon (Rashi)", 1, 0, 'L')
            pdf.cell(45, 8, moon_sign, 1, 0, 'C')
            pdf.cell(45, 8, moon_lord, 1, 0, 'C')
            pdf.cell(50, 8, moon_nak, 1, 1, 'C')
            
            pdf.ln(10)

        # --- Birth Particulars ---
        if birth_details:
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, "Birth Particulars", 0, 1)
            pdf.ln(2)
            
            pdf.set_font('Arial', '', 11)
            # Row 1
            pdf.cell(40, 8, "Name:", 0, 0)
            pdf.cell(60, 8, str(birth_details.get('name') or '-'), 0, 0)
            pdf.cell(40, 8, "Place:", 0, 0)
            pdf.cell(0, 8, str(birth_details.get('birth_place') or '-'), 0, 1)
            
            # Row 2
            pdf.cell(40, 8, "Date:", 0, 0)
            pdf.cell(60, 8, str(birth_details.get('birth_date') or '-'), 0, 0)
            pdf.cell(40, 8, "Time:", 0, 0)
            pdf.cell(0, 8, str(birth_details.get('birth_time') or '-'), 0, 1)
            
            # Row 3
            pdf.cell(40, 8, "Latitude:", 0, 0)
            pdf.cell(60, 8, str(birth_details.get('latitude', '-')), 0, 0)
            pdf.cell(40, 8, "Longitude:", 0, 0)
            pdf.cell(0, 8, str(birth_details.get('longitude', '-')), 0, 1)
            pdf.ln(5)

        # --- Executive Summary (New Section) ---
        if 'Executive Summary' in ai_predictions:
            pdf.add_page()
            text = ai_predictions['Executive Summary'] or ''
            
            # Custom rendering for the structured Executive Summary
            lines = text.split('\n')
            for line in lines:
                clean_line = line.strip()
                if not clean_line:
                    pdf.ln(2)
                    continue
                
                # Title
                if "Your Kundali at a Glance" in clean_line:
                    pdf.set_font('Arial', 'B', 20)
                    pdf.cell(0, 15, "Your Kundali at a Glance", 0, 1, 'C')
                    pdf.ln(5)
                    continue
                
                # Section Headers (Check for specific keywords since emojis are removed)
                known_headers = ["Core Identity", "Key Strengths", "Key Challenges", "Career Snapshot", "Relationships & Partnerships", "Current Timing"]
                # Check if line contains one of the headers (ignoring markdown chars)
                header_match = next((h for h in known_headers if h in clean_line), None)
                
                if header_match and len(clean_line) < 40: # Simple heuristic to distinguish header from content
                    header_text = header_match
                    pdf.set_font('Arial', 'B', 14)
                    pdf.set_text_color(30, 64, 175) # Blue-800
                    pdf.cell(0, 10, header_text, 0, 1)
                    pdf.set_text_color(0, 0, 0) # Reset black
                    pdf.set_font('Arial', '', 11)
                    continue
                
                # Content
                self._write_markdown(pdf, clean_line)
                pdf.ln(5)

        # --- General Predictions ---
        # Filter out Executive Summary from the loop as it's already rendered
        remaining_topics = [t for t in ai_predictions.keys() if t != 'Executive Summary']
        
        if remaining_topics:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, "General Analysis & Predictions", 0, 1)
            pdf.ln(5)

            # Order the topics as requested
            prediction_order = ["Your Ascendant", "Your Nakshatra", "Atmakaraka", "Darakaraka", "Character", "Happiness and Fulfillment", "Lifestyle", "Career", "Occupation", "Health", "Hobbies", "Finance", "Education", "Planetary Analysis", "House Analysis", "Divisional Charts", "Dasha Analysis", "Transits & Gochar"]
            for topic in prediction_order:
                if topic in ai_predictions:
                    text = ai_predictions[topic] or ''
                    pdf.set_font('Arial', 'B', 14)
                    pdf.cell(0, 10, topic, 0, 1)
                    pdf.set_font('Arial', '', 11)
                    self._write_markdown(pdf, text)
                    pdf.ln(4)

        # --- Avakahada Chakra ---
        if avakahada:
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, "Avakahada Chakra", 0, 1)
            pdf.ln(2)
            
            pdf.set_font('Arial', '', 11)
            # Simple key-value table
            for key, value in avakahada.items():
                pdf.set_fill_color(245, 245, 245)
                pdf.cell(60, 8, key, 1, 0, 'L', True)
                pdf.cell(0, 8, str(value), 1, 1, 'L')
            pdf.ln(5)

        # --- Core Details ---
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, "Core Details", 0, 1)
        pdf.ln(2)
        
        pdf.set_font('Arial', '', 12)
        
        # Ayanamsa
        if 'ayanamsa' in core:
            pdf.cell(50, 8, "Ayanamsa:", 0, 0)
            pdf.cell(0, 8, str(core['ayanamsa']), 0, 1)
            
        # Ascendant
        if 'ascendant' in core:
            asc = core['ascendant']
            pdf.cell(50, 8, "Ascendant:", 0, 0)
            asc_text = f"{asc.get('sign', 'N/A')} {asc.get('degree', 0):.2f}°"
            if asc.get('nakshatra'):
                asc_text += f" | {asc.get('nakshatra')}"
            pdf.cell(0, 8, asc_text, 0, 1)
            
        pdf.ln(5)

        # --- Visual Chart (North Indian Style) ---
        # Draw chart centered, size 80mm
        self._draw_north_indian_chart(pdf, x=65, y=pdf.get_y() + 5, size=80, houses=core.get('houses', {}), planets=core.get('planets', {}))
        pdf.ln(90) # Move cursor past the chart

        # --- Planetary Positions (Table) ---
        if 'planets' in core:
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, "Planetary Positions", 0, 1)
            pdf.ln(2)
            
            # Headers
            pdf.set_font('Arial', 'B', 11)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(30, 10, "Planet", 1, 0, 'C', True)
            pdf.cell(30, 10, "Sign", 1, 0, 'C', True)
            pdf.cell(25, 10, "Degree", 1, 0, 'C', True)
            pdf.cell(75, 10, "Nakshatra", 1, 0, 'C', True)
            pdf.cell(20, 10, "House", 1, 1, 'C', True)
            
            # Rows
            pdf.set_font('Arial', '', 11)
            for planet, details in core['planets'].items():
                p_name = planet.title()
                if details.get('retrograde'):
                    p_name += " (R)"
                pdf.cell(30, 10, p_name, 1, 0, 'C')
                pdf.cell(30, 10, str(details.get('sign') or '-'), 1, 0, 'C')
                pdf.cell(25, 10, f"{details.get('degree', 0):.2f}°", 1, 0, 'C')
                pdf.cell(75, 10, str(details.get('nakshatra') or '-'), 1, 0, 'C')
                pdf.cell(20, 10, str(details.get('house') or '-'), 1, 1, 'C')
            
            pdf.ln(10)

        # --- House Analysis (Derived) ---
        if derived and 'house_strengths' in derived:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, "House Analysis", 0, 1)
            pdf.ln(2)
            
            # Sort by house number
            house_strengths = derived['house_strengths']
            sorted_houses = sorted(house_strengths.items(), key=lambda x: int(x[0]))
            
            pdf.set_font('Arial', '', 10)
            for h_key, h_data in sorted_houses:
                house_num = h_data.get('house', h_key)
                raw_strength = h_data.get('strength', '-').title()
                
                # Map Strength Labels & Colors
                strength_label = "Neutral"
                bar_w, r, g, b = 45, 209, 213, 219 # Gray-300
                
                # Determine Color and Width based on strength
                if 'Very Strong' in raw_strength:
                    strength_label = "Supportive (Very Strong)"
                    bar_w, r, g, b = 80, 34, 197, 94 # Green-500
                elif 'Strong' in raw_strength:
                    strength_label = "Supportive"
                    bar_w, r, g, b = 60, 74, 222, 128 # Green-400
                elif 'Weak' in raw_strength:
                    strength_label = "Challenging"
                    bar_w, r, g, b = 30, 251, 146, 60 # Orange-400
                elif 'Very Weak' in raw_strength:
                    strength_label = "Challenging (Very Weak)"
                    bar_w, r, g, b = 15, 248, 113, 113 # Red-400

                # Draw Row
                pdf.cell(25, 8, f"House {house_num}", 0, 0)
                
                # Save current position
                x, y = pdf.get_x(), pdf.get_y()
                
                # Draw Bar
                pdf.set_fill_color(r, g, b)
                pdf.rect(x, y+2, bar_w, 4, 'F')
                
                # Draw Text Label next to bar
                pdf.set_xy(x + bar_w + 2, y)
                pdf.cell(0, 8, strength_label, 0, 1)
        
        # --- Doshas & Yogas (Derived) ---
        if derived and ('doshas' in derived or 'yogas' in derived):
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, "Doshas & Yogas", 0, 1)
            pdf.ln(2)

            if 'doshas' in derived and derived['doshas']:
                for dosha in derived['doshas']:
                    name = dosha.get('name', 'Unknown')
                    present = dosha.get('present', False)
                    if present:
                        # Draw Highlight Box for present Doshas
                        title = f"{name.replace('_', ' ').title()} Dosha Detected"
                        desc = dosha.get('description', '')
                        # Light Red background
                        self._draw_highlight_box(pdf, title, desc, (254, 226, 226))
                pdf.ln(5)

            if 'yogas' in derived and derived['yogas']:
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, "Yogas", 0, 1)
                pdf.set_font('Arial', '', 11)
                for yoga in derived['yogas']:
                    name = yoga.get('name', 'Unknown')
                    # Yogas list usually contains present yogas
                    pdf.set_font('Arial', 'B', 11)
                    pdf.cell(0, 8, name, 0, 1)
                    desc = yoga.get('description')
                    if desc:
                        pdf.set_font('Arial', '', 10)
                        pdf.multi_cell(0, 6, desc, 0, 1)
                    pdf.ln(2)
            pdf.ln(5)

        # --- Divisional Charts ---
        if divisionals:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, "Divisional Charts", 0, 1)
            pdf.ln(5)
            
            for div_name, div_data in divisionals.items():
                chart_type = div_data.get('chart_type', div_name)
                asc = div_data.get('ascendant', {})
                planets = div_data.get('planets', {})
                
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, f"{chart_type} Chart", 0, 1)
                
                pdf.set_font('Arial', '', 11)
                asc_text = f"Ascendant: {asc.get('sign', 'N/A')} {asc.get('degree', 0):.2f}°"
                pdf.cell(0, 8, asc_text, 0, 1)
                pdf.ln(2)

                # Draw D9 Chart Visualization
                if chart_type == 'D9':
                    # We need to reconstruct houses for D9 based on Ascendant
                    # Assuming standard zodiac order for houses starting from Ascendant
                    signs = [
                        "Aries", "Taurus", "Gemini", "Cancer",
                        "Leo", "Virgo", "Libra", "Scorpio",
                        "Sagittarius", "Capricorn", "Aquarius", "Pisces",
                    ]
                    asc_sign = asc.get('sign')
                    if asc_sign in signs:
                        start_idx = signs.index(asc_sign)
                        d9_houses = {str(i+1): signs[(start_idx + i) % 12] for i in range(12)}
                        
                        # Calculate houses for D9 planets relative to D9 Ascendant
                        d9_planets = {}
                        for pname, pdata in planets.items():
                            p_copy = pdata.copy()
                            p_sign = pdata.get('sign')
                            if p_sign in signs:
                                p_idx = signs.index(p_sign)
                                # House = (Planet Sign Index - Ascendant Sign Index) % 12 + 1
                                p_copy['house'] = (p_idx - start_idx) % 12 + 1
                            d9_planets[pname] = p_copy

                        # Draw chart centered
                        self._draw_north_indian_chart(pdf, x=65, y=pdf.get_y() + 5, size=80, houses=d9_houses, planets=d9_planets)
                        pdf.ln(90)
                
                # Table for planets
                pdf.set_font('Arial', 'B', 10)
                pdf.set_fill_color(240, 240, 240)
                pdf.cell(40, 8, "Planet", 1, 0, 'C', True)
                pdf.cell(40, 8, "Sign", 1, 0, 'C', True)
                pdf.cell(40, 8, "Degree", 1, 1, 'C', True)
                
                pdf.set_font('Arial', '', 10)
                for p_name, p_data in planets.items():
                    name_display = p_name
                    if p_data.get('retrograde'):
                        name_display += " (R)"
                    
                    pdf.cell(40, 8, name_display, 1, 0, 'C')
                    pdf.cell(40, 8, str(p_data.get('sign') or '-'), 1, 0, 'C')
                    pdf.cell(40, 8, f"{p_data.get('degree', 0):.2f}°", 1, 1, 'C')
                
                pdf.ln(10)

        # --- Transits & Gochar ---
        if transits_payload:
            transit_chart = transits_payload.get('transit', {})
            gochar = transits_payload.get('gochar', {})
            
            if (transit_chart and 'planets' in transit_chart) or (gochar and 'planets' in gochar):
                pdf.add_page()
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, "Transits & Gochar", 0, 1)
                pdf.ln(2)
                
                # Transit Chart
                if transit_chart and 'planets' in transit_chart:
                    pdf.set_font('Arial', 'B', 14)
                    ts_str = transit_chart.get('timestamp', '')
                    if 'T' in ts_str:
                        ts_str = ts_str.split('T')[0]
                    pdf.cell(0, 10, f"Current Planetary Positions ({ts_str})", 0, 1)
                    
                    pdf.set_font('Arial', 'B', 10)
                    pdf.set_fill_color(230, 230, 230)
                    pdf.cell(40, 8, "Planet", 1, 0, 'C', True)
                    pdf.cell(40, 8, "Sign", 1, 0, 'C', True)
                    pdf.cell(40, 8, "Degree", 1, 1, 'C', True)
                    
                    pdf.set_font('Arial', '', 10)
                    for p_name, p_data in transit_chart['planets'].items():
                        name_display = p_name
                        if p_data.get('retrograde'):
                            name_display += " (R)"
                        pdf.cell(40, 8, name_display, 1, 0, 'C')
                        pdf.cell(40, 8, str(p_data.get('sign') or '-'), 1, 0, 'C')
                        pdf.cell(40, 8, f"{p_data.get('degree', 0):.2f}°", 1, 1, 'C')
                    pdf.ln(10)

                # Gochar
                if gochar and 'planets' in gochar:
                    pdf.set_font('Arial', 'B', 14)
                    pdf.cell(0, 10, "Gochar (Relative Transits)", 0, 1)
                    
                    pdf.set_font('Arial', 'B', 10)
                    pdf.set_fill_color(230, 230, 230)
                    pdf.cell(40, 8, "Planet", 1, 0, 'C', True)
                    pdf.cell(50, 8, "From Lagna (House)", 1, 0, 'C', True)
                    pdf.cell(50, 8, "From Moon (House)", 1, 1, 'C', True)
                    
                    pdf.set_font('Arial', '', 10)
                    for p_name, p_data in gochar['planets'].items():
                        pdf.cell(40, 8, p_name, 1, 0, 'C')
                        pdf.cell(50, 8, str(p_data.get('from_lagna_house', '-')), 1, 0, 'C')
                        pdf.cell(50, 8, str(p_data.get('from_moon_house', '-')), 1, 1, 'C')
                    pdf.ln(5)

        # --- Sade Sati Report ---
        if sade_sati:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, "Sade Sati Report", 0, 1)
            pdf.ln(2)
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(40, 10, "Current Status:", 0, 0)
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, sade_sati.get('status', 'Unknown'), 0, 1)
            
            pdf.set_font('Arial', '', 11)
            pdf.multi_cell(0, 8, sade_sati.get('description', ''), 0, 1)
            pdf.ln(5)

        # --- Vimshottari Dasha ---
        if dashas:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, "Vimshottari Dasha", 0, 1)
            pdf.ln(2)
            
            # Headers
            pdf.set_font('Arial', 'B', 11)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(40, 10, "Dasha Lord", 1, 0, 'C', True)
            pdf.cell(40, 10, "Start Date", 1, 0, 'C', True)
            pdf.cell(40, 10, "End Date", 1, 0, 'C', True)
            pdf.cell(40, 10, "Duration (Yrs)", 1, 1, 'C', True)
            
            # Rows
            pdf.set_font('Arial', '', 11)
            for dasha in dashas:
                start_fmt = dasha['start_date'].split('T')[0]
                end_fmt = dasha['end_date'].split('T')[0]
                pdf.cell(40, 10, dasha['lord'], 1, 0, 'C')
                pdf.cell(40, 10, start_fmt, 1, 0, 'C')
                pdf.cell(40, 10, end_fmt, 1, 0, 'C')
                pdf.cell(40, 10, str(dasha['duration_years']), 1, 1, 'C')
            pdf.ln(5)
            
            # --- Current Antardasha Detail ---
            # Find the current Mahadasha based on today's date
            now_str = datetime.utcnow().isoformat()
            current_md = None
            for d in dashas:
                if d['start_date'] <= now_str <= d['end_date']:
                    current_md = d
                    break
            
            if current_md and 'antardashas' in current_md:
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, f"Current Period: {current_md['lord']} Mahadasha", 0, 1)
                pdf.ln(2)
                
                pdf.set_font('Arial', 'B', 10)
                pdf.set_fill_color(240, 240, 240)
                pdf.cell(40, 8, "Antardasha Lord", 1, 0, 'C', True)
                pdf.cell(40, 8, "Start Date", 1, 0, 'C', True)
                pdf.cell(40, 8, "End Date", 1, 1, 'C', True)
                
                pdf.set_font('Arial', '', 10)
                for ad in current_md['antardashas']:
                    # Highlight active antardasha
                    is_active = ad['start_date'] <= now_str <= ad['end_date']
                    pdf.set_font('Arial', 'B' if is_active else '', 10)
                    pdf.cell(40, 8, ad['lord'], 1, 0, 'C')
                    pdf.cell(40, 8, ad['start_date'].split('T')[0], 1, 0, 'C')
                    pdf.cell(40, 8, ad['end_date'].split('T')[0], 1, 1, 'C')

        # --- Explanations / Insights ---
        if explanations:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, "Astrological Insights", 0, 1)
            pdf.ln(5)
            
            for exp in explanations:
                category = exp.get('category', 'General').title()
                summary = exp.get('explanation', {}).get('summary', '')
                
                # Replace unicode bullet with a latin-1 compatible character
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 8, f"- {category}", 0, 1)
                pdf.set_font('Arial', '', 11)
                self._write_markdown(pdf, summary)
                pdf.ln(4)

        # --- Additional Data ---
        if 'additional' in core and core['additional']:
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, "Additional Information", 0, 1)
            pdf.ln(2)
            
            pdf.set_font('Arial', '', 12)
            for key, value in core['additional'].items():
                pdf.cell(60, 8, f"{key.replace('_', ' ').title()}:", 0, 0)
                # Handle if value is complex
                if isinstance(value, (dict, list)):
                    pdf.multi_cell(0, 8, str(value), 0, 1)
                else:
                    pdf.cell(0, 8, str(value), 0, 1)
            pdf.ln(5)

        # --- Other Top Level Keys in Core ---
        # Check for keys we haven't processed yet
        processed_keys = {'ayanamsa', 'ascendant', 'planets', 'transits', 'additional'}
        other_keys = [k for k in core.keys() if k not in processed_keys]
        
        if other_keys:
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, "Other Details", 0, 1)
            pdf.ln(2)
            pdf.set_font('Arial', '', 12)
            
            for key in other_keys:
                value = core[key]
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, key.replace('_', ' ').title(), 0, 1)
                pdf.set_font('Arial', '', 12)
                pdf.multi_cell(0, 8, str(value), 0, 1)
                pdf.ln(2)
        
        # Return PDF as bytes
        pdf_bytes = pdf.output(dest='S').encode('latin1')

        return {
            "filename": filename,
            "bytes": pdf_bytes
        }

    def _draw_highlight_box(self, pdf, title, text, bg_color):
        """Draws a colored box with title and text for warnings/highlights."""
        pdf.set_fill_color(*bg_color)
        pdf.set_font('Arial', 'B', 11)
        
        # Calculate height needed
        # Title height (8) + Text height (approx) + Padding (4)
        # Simple approximation: 8 + (len(text)/90 * 6) + 4
        # A more robust way is to use multi_cell dry run, but for now approx is okay or just draw rect behind.
        # FPDF 1.7 doesn't support background for multi_cell easily without rect.
        
        pdf.cell(0, 8, title, 0, 1, 'L', True)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, text, 0, 1, 'L', True)
        pdf.ln(2)

    def _write_markdown(self, pdf, text: str):
        """
        Simple markdown parser for bold text (**text**), bullet points (•), and headers (#).
        Handles sanitization of unsupported characters.
        """
        # Pre-sanitize text
        text = text.replace('•', '-')  # Replace bullet with hyphen
        text = text.replace('“', '"').replace('”', '"').replace('’', "'") # Smart quotes
        text = text.replace('—', '-')  # Replace em dash with hyphen
        # Encode to latin-1 and ignore errors (drops emojis/unsupported chars) to prevent '?' artifacts
        text = text.encode('latin-1', 'ignore').decode('latin-1')

        lines = text.split('\n')
        for line in lines:
            clean_line = line.strip()
            
            # Handle Headers (###) - Convert to Bold
            if clean_line.startswith('#'):
                header_text = clean_line.lstrip('#').strip()
                pdf.set_font('Arial', 'B', 11)
                pdf.write(6, header_text)
                pdf.set_font('Arial', '', 11)
                pdf.ln()
                continue

            if clean_line.startswith('•') or clean_line.startswith('- '):
                pdf.set_x(pdf.get_x() + 5) # Indent
            
            parts = line.split('**')
            for i, part in enumerate(parts):
                if i % 2 == 1:
                    pdf.set_font('Arial', 'B', 11)
                    pdf.write(6, part)
                    pdf.set_font('Arial', '', 11)
                else:
                    pdf.write(6, part)
            pdf.ln()

    def _get_sign_lord(self, sign: str) -> str:
        lords = {
            "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
            "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
            "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
        }
        return lords.get(sign, "-")

    def _validate_report_context(self, context: Dict[str, Any]) -> bool:
        """Validate that the context contains the expected structure for a Kundali report"""
        if not isinstance(context, dict):
            return False
            
        # Check for required top-level keys
        if 'persisted' not in context or 'meta' not in context:
            return False
            
        # Check for required core fields
        core = context.get('persisted', {}).get('core', {})
        required_core_fields = ['ayanamsa', 'ascendant', 'planets']
        return all(field in core for field in required_core_fields)

    def _draw_north_indian_chart(self, pdf, x, y, size, houses, planets):
        """
        Draws a North Indian style (Diamond) chart.
        """
        # 1. Draw Geometry
        # Outer Square
        pdf.rect(x, y, size, size)
        
        # Diagonals
        pdf.line(x, y, x + size, y + size)
        pdf.line(x, y + size, x + size, y)
        
        # Midpoint connectors (Diamond)
        # Top-Mid to Left-Mid
        pdf.line(x + size/2, y, x, y + size/2)
        # Left-Mid to Bottom-Mid
        pdf.line(x, y + size/2, x + size/2, y + size)
        # Bottom-Mid to Right-Mid
        pdf.line(x + size/2, y + size, x + size, y + size/2)
        # Right-Mid to Top-Mid
        pdf.line(x + size, y + size/2, x + size/2, y)

        # 2. Prepare Data
        sign_map = {
            "Aries": 1, "Taurus": 2, "Gemini": 3, "Cancer": 4,
            "Leo": 5, "Virgo": 6, "Libra": 7, "Scorpio": 8,
            "Sagittarius": 9, "Capricorn": 10, "Aquarius": 11, "Pisces": 12
        }
        
        p_short = {
            "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
            "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"
        }

        # Group planets by house
        planets_by_house = {i: [] for i in range(1, 13)}
        for p_name, p_data in planets.items():
            h = p_data.get('house')
            if h:
                short_name = p_short.get(p_name, p_name[:2])
                if p_data.get('retrograde'):
                    short_name += "(R)"
                planets_by_house[h].append(short_name)

        # 3. Text Placement Coordinates (Relative to x, y, size)
        # House 1 is Top Center. Counter-clockwise numbering for North Indian layout positions.
        # (cx, cy) factors for 12 houses
        positions = {
            1:  (0.5, 0.20), # Top Center (Lagna)
            2:  (0.25, 0.08), # Top Left
            3:  (0.08, 0.25), # Left Top
            4:  (0.25, 0.5), # Left Center
            5:  (0.08, 0.75), # Left Bottom
            6:  (0.25, 0.92), # Bottom Left
            7:  (0.5, 0.80), # Bottom Center
            8:  (0.75, 0.92), # Bottom Right
            9:  (0.92, 0.75), # Right Bottom
            10: (0.75, 0.5), # Right Center
            11: (0.92, 0.25), # Right Top
            12: (0.75, 0.08), # Top Right
        }

        pdf.set_font('Arial', '', 8)
        
        for h_num in range(1, 13):
            # Get Sign Number
            # houses keys might be strings or ints
            sign_name = houses.get(str(h_num)) or houses.get(h_num)
            sign_num = sign_map.get(sign_name, "")
            
            # Get Planets
            p_list = planets_by_house.get(h_num, [])
            p_text = "\n".join(p_list)
            
            # Coordinates
            fx, fy = positions[h_num]
            tx = x + (size * fx)
            ty = y + (size * fy)
            
            # Draw Sign Number (Bold, centered in house)
            pdf.set_font('Arial', 'B', 10)
            pdf.text(tx - 1, ty, str(sign_num))
            
            # Draw Planets (Normal, below sign number)
            if p_list:
                pdf.set_font('Arial', '', 7)
                # Simple multiline simulation
                pdf.set_xy(tx - 5, ty + 1)
                pdf.multi_cell(10, 3, p_text, 0, 'C')