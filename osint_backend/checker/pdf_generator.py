import os
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from django.conf import settings
from .models import User, EmailSearchResults, PhoneSearchResults, UsernameSearchResults

import re

def _clean_text(text):
    """Removes or replaces characters that might crash ReportLab."""
    if not text:
        return "N/A"
    # Remove non-printable and extreme unicode characters
    return re.sub(r'[^\x20-\x7E\n]', '', str(text))

def generate_user_report_pdf(user_id: int) -> bytes:
    """
    Generates a comprehensive OSINT PDF report for a given user.
    Returns the PDF as raw bytes.
    """
    user = User.objects.get(pk=user_id)
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'],
        fontSize=24, spaceAfter=20, textColor=colors.darkblue, alignment=1
    )
    heading_style = ParagraphStyle(
        'CustomHeading', parent=styles['Heading2'],
        fontSize=16, spaceAfter=10, textColor=colors.darkred
    )
    normal_style = styles['Normal']
    
    elements = []
    
    # Title Page
    elements.append(Paragraph("OSINT Threat Intelligence Report", title_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"<b>Prepared for:</b> {user.first_name} {user.last_name} ({user.email})", normal_style))
    elements.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}", normal_style))
    elements.append(Spacer(1, 40))
    
    elements.append(Paragraph("<b>Executive Summary</b>", heading_style))
    elements.append(Paragraph(
        "This report contains a comprehensive analysis of personal data exposures identified across the web, "
        "including known data breaches, exposed phone number information, and public social media footprint. "
        "Please review this data carefully and update passwords for any compromised accounts.",
        normal_style
    ))
    elements.append(PageBreak())
    
    # 1. Email Breaches
    elements.append(Paragraph("1. Email Exposure Analysis", heading_style))
    email_results = EmailSearchResults.objects.filter(user=user).order_by('-created_at')
    if email_results.exists():
        data = [["Email Queried", "Breach Count", "Date Scanned"]]
        for res in email_results[:10]: # Top 10 recent
            data.append([
                _clean_text(res.email), 
                _clean_text(res.breach_count), 
                res.created_at.strftime('%Y-%m-%d')
            ])
            
        table = Table(data, colWidths=[200, 100, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No email breach data found.", normal_style))
    elements.append(Spacer(1, 30))
    
    # 2. Phone Information
    elements.append(Paragraph("2. Phone Number Analysis", heading_style))
    phone_results = PhoneSearchResults.objects.filter(user=user).order_by('-created_at')
    if phone_results.exists():
        data = [["Phone Number", "Carrier", "Location", "Spam Score"]]
        for res in phone_results[:10]:
            data.append([
                _clean_text(res.phone_number), 
                _clean_text(res.carrier), 
                _clean_text(res.location), 
                _clean_text(res.spam_score)
            ])
            
        table = Table(data, colWidths=[120, 120, 130, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.lavender),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No phone analysis data found.", normal_style))
    elements.append(Spacer(1, 30))

    # 3. Username Footprint
    elements.append(Paragraph("3. Username & Social Media Footprint", heading_style))
    username_results = UsernameSearchResults.objects.filter(user=user, is_registered=True).order_by('-created_at')
    if username_results.exists():
        data = [["Username", "Platform", "Date Found"]]
        # Group by platform to avoid spamming the report with identical entries
        seen = set()
        for res in username_results:
            key = f"{res.username}-{res.platform_name}"
            if key not in seen and len(seen) < 20: # Max 20 unique
                seen.add(key)
                data.append([
                    _clean_text(res.username), 
                    _clean_text(res.platform_name), 
                    res.created_at.strftime('%Y-%m-%d')
                ])
                
        table = Table(data, colWidths=[150, 150, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No public username accounts found.", normal_style))

    # Build the PDF
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
