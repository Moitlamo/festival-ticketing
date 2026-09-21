import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Enforces the mandatory ownership watermark and page numbering."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#666666"))
        
        # Bottom footer line
        self.setStrokeColor(colors.HexColor("#E0E0E0"))
        self.setLineWidth(0.5)
        self.line(40, 45, 555, 45)
        
        # Explicit Ownership Credit
        self.drawString(40, 32, "Owner: Moitlamo Marumo | SmartTec Ticketing Platform")
        
        # Page numbers
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(555, 32, page_text)
        self.restoreState()


def generate_promoter_dashboard_pdf(promoter_name: str, event_name: str, kpi_stats: dict, vendor_data: list) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=60
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor("#262730"), spaceAfter=6
    )
    section_style = ParagraphStyle(
        'SectionStyle', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor("#FF4B4B"), spaceBefore=15, spaceAfter=10
    )
    meta_style = ParagraphStyle(
        'MetaStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor("#555555")
    )
    
    story = []

    # 1. Header Information
    story.append(Paragraph("SmartTec — Promoter Financial Summary", title_style))
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_info = f"""
    <b>Event:</b> {event_name}<br/>
    <b>Promoter:</b> {promoter_name}<br/>
    <b>Generated:</b> {generated_at}<br/>
    """
    story.append(Paragraph(meta_info, meta_style))
    story.append(Spacer(1, 20))

    # 2. Key Performance Indicators (KPIs)
    story.append(Paragraph("Global Performance Metrics", section_style))
    
    kpi_table_data = [
        ["Total Gross Revenue", f"P{kpi_stats.get('total_revenue', 0):,.2f}"],
        ["Total Tickets Sold", str(kpi_stats.get('total_sold', 0))],
        ["VIP Tickets Sold", str(kpi_stats.get('vip_sold', 0))],
        ["Standard Tickets Sold", str(kpi_stats.get('standard_sold', 0))],
        ["Total Gate Scans", str(kpi_stats.get('total_scans', 0))]
    ]
    
    kpi_table = Table(kpi_table_data, colWidths=[200, 150], hAlign='LEFT')
    kpi_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#262730")),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 20))

    # 3. Vendor Breakdown Section
    story.append(Paragraph("Vendor Sales Breakdown", section_style))
    
    vendor_table_data = [["Vendor Name", "Tickets Sold", "Revenue Generated (BWP)"]]
    for v in vendor_data:
        vendor_table_data.append([
            v.get('name', 'Unknown'),
            str(v.get('sold', 0)),
            f"P{float(v.get('revenue', 0)):,.2f}"
        ])

    v_table = Table(vendor_table_data, colWidths=[200, 120, 180])
    v_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#262730")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9F9F9")]),
    ]))
    story.append(v_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer
