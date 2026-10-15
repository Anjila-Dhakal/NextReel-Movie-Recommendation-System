"""
Generate NextReel_Developer_Documentation.pdf from the markdown file.
Run: python generate_doc_pdf.py
"""
import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Preformatted
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Color palette ───────────────────────────────────────────────
C_DARK      = colors.HexColor('#1a1a2e')
C_ACCENT    = colors.HexColor('#e8a020')
C_ACCENT2   = colors.HexColor('#c0763a')
C_LIGHT_BG  = colors.HexColor('#f5f0ea')
C_CODE_BG   = colors.HexColor('#1e1e2e')
C_CODE_TEXT = colors.HexColor('#cdd6f4')
C_MUTED     = colors.HexColor('#666666')
C_WHITE     = colors.white
C_TABLE_HDR = colors.HexColor('#2d2d44')
C_TABLE_ROW = colors.HexColor('#f9f6f1')
C_TABLE_ALT = colors.HexColor('#ede8e0')
C_HR        = colors.HexColor('#d4a056')

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm

# ── Styles ───────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()

    styles = {}

    styles['title'] = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=28,
        textColor=C_DARK,
        spaceAfter=6,
        alignment=TA_CENTER,
        leading=34,
    )
    styles['subtitle'] = ParagraphStyle(
        'DocSubtitle',
        fontName='Helvetica',
        fontSize=13,
        textColor=C_MUTED,
        spaceAfter=20,
        alignment=TA_CENTER,
    )
    styles['h1'] = ParagraphStyle(
        'H1',
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=C_WHITE,
        spaceBefore=20,
        spaceAfter=8,
        leftIndent=0,
        leading=22,
    )
    styles['h2'] = ParagraphStyle(
        'H2',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=C_ACCENT,
        spaceBefore=16,
        spaceAfter=5,
        leading=18,
    )
    styles['h3'] = ParagraphStyle(
        'H3',
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=C_ACCENT2,
        spaceBefore=10,
        spaceAfter=3,
        leading=14,
    )
    styles['body'] = ParagraphStyle(
        'Body',
        fontName='Helvetica',
        fontSize=9.5,
        textColor=C_DARK,
        spaceAfter=5,
        leading=14,
    )
    styles['bullet'] = ParagraphStyle(
        'Bullet',
        fontName='Helvetica',
        fontSize=9.5,
        textColor=C_DARK,
        spaceAfter=3,
        leftIndent=16,
        bulletIndent=6,
        leading=13,
    )
    styles['code'] = ParagraphStyle(
        'Code',
        fontName='Courier',
        fontSize=8.5,
        textColor=C_CODE_TEXT,
        backColor=C_CODE_BG,
        spaceBefore=4,
        spaceAfter=4,
        leftIndent=8,
        rightIndent=8,
        leading=12,
        borderPadding=(5, 8, 5, 8),
    )
    styles['table_hdr'] = ParagraphStyle(
        'TableHdr',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=C_WHITE,
        alignment=TA_LEFT,
        leading=12,
    )
    styles['table_cell'] = ParagraphStyle(
        'TableCell',
        fontName='Helvetica',
        fontSize=9,
        textColor=C_DARK,
        leading=12,
    )
    styles['table_code'] = ParagraphStyle(
        'TableCode',
        fontName='Courier',
        fontSize=8.5,
        textColor=colors.HexColor('#1a1a2e'),
        leading=12,
    )
    return styles


def h1_block(text, styles, story):
    """Render H1 as a dark banner."""
    story.append(Spacer(1, 8))
    data = [[Paragraph(text, styles['h1'])]]
    t = Table(data, colWidths=[PAGE_W - 2 * MARGIN])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_DARK),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))
    story.append(t)
    story.append(Spacer(1, 4))


def make_table(rows, styles, col_widths=None):
    """Build a styled table from list of row-lists. First row = header."""
    avail = PAGE_W - 2 * MARGIN
    if col_widths is None:
        n = len(rows[0])
        col_widths = [avail / n] * n

    table_data = []
    for i, row in enumerate(rows):
        if i == 0:
            table_data.append([Paragraph(str(c), styles['table_hdr']) for c in row])
        else:
            table_data.append([Paragraph(str(c), styles['table_cell']) for c in row])

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), C_TABLE_HDR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_TABLE_ROW, C_TABLE_ALT]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cccccc')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t


def md_to_story(md_text, styles):
    """Parse markdown and return a list of ReportLab flowables."""
    story = []
    lines = md_text.split('\n')
    i = 0
    in_code = False
    code_buf = []
    table_buf = []
    in_table = False

    def flush_table():
        if not table_buf:
            return []
        rows = []
        for tl in table_buf:
            cells = [c.strip() for c in tl.strip('|').split('|')]
            rows.append(cells)
        # Remove separator row (---|---)
        rows = [r for r in rows if not all(re.match(r'^-+$', c.strip('-').strip()) for c in r)]
        if not rows:
            return []
        n = len(rows[0])
        avail = PAGE_W - 2 * MARGIN
        w = avail / n
        return [make_table(rows, styles, [w] * n), Spacer(1, 6)]

    while i < len(lines):
        line = lines[i]

        # Code block
        if line.strip().startswith('```'):
            if in_code:
                in_code = False
                code_text = '\n'.join(code_buf)
                # Split long code blocks into lines and render each as Paragraph
                # to allow page-breaking within code blocks
                for cline in code_text.split('\n'):
                    escaped = cline.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    if not escaped:
                        escaped = ' '  # blank line spacer
                    story.append(Paragraph(escaped, styles['code']))
                story.append(Spacer(1, 6))
                code_buf = []
            else:
                if in_table:
                    story.extend(flush_table())
                    table_buf = []
                    in_table = False
                in_code = True
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # Table rows
        if line.strip().startswith('|'):
            in_table = True
            table_buf.append(line)
            i += 1
            continue
        else:
            if in_table:
                story.extend(flush_table())
                table_buf = []
                in_table = False

        # Skip document-level metadata lines
        if line.strip().startswith('> '):
            story.append(Paragraph(line.strip()[2:], styles['subtitle']))
            story.append(Spacer(1, 4))
            i += 1
            continue

        # Headings
        if line.startswith('# ') and not line.startswith('## '):
            title = line[2:].strip()
            story.append(Paragraph(title, styles['title']))
            story.append(HRFlowable(width='100%', thickness=2, color=C_ACCENT, spaceAfter=8))
            i += 1
            continue

        if line.startswith('## '):
            h1_block(line[3:].strip(), styles, story)
            i += 1
            continue

        if line.startswith('### '):
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width='60%', thickness=1, color=C_HR, spaceAfter=2))
            story.append(Paragraph(line[4:].strip(), styles['h2']))
            i += 1
            continue

        if line.startswith('#### '):
            story.append(Paragraph(line[5:].strip(), styles['h3']))
            i += 1
            continue

        # HR
        if line.strip().startswith('---'):
            story.append(HRFlowable(width='100%', thickness=0.5, color=C_HR, spaceBefore=6, spaceAfter=6))
            i += 1
            continue

        # Bullet lists
        if re.match(r'^[\-\*] ', line):
            text = line[2:].strip()
            text = clean_inline(text)
            story.append(Paragraph(f'• {text}', styles['bullet']))
            i += 1
            continue

        if re.match(r'^\d+\. ', line):
            text = re.sub(r'^\d+\. ', '', line).strip()
            text = clean_inline(text)
            story.append(Paragraph(f'  {text}', styles['bullet']))
            i += 1
            continue

        # Blank line
        if not line.strip():
            story.append(Spacer(1, 4))
            i += 1
            continue

        # Normal paragraph
        text = clean_inline(line.strip())
        if text:
            story.append(Paragraph(text, styles['body']))

        i += 1

    if in_table:
        story.extend(flush_table())

    return story


def xml_escape(text):
    """Escape plain text for ReportLab XML paragraphs."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def clean_inline(text):
    """
    Convert basic markdown inline formatting to ReportLab XML.
    Processes the text token by token to avoid escaping inserted tags.
    """
    # Split on markdown tokens: **text**, `code`
    # Pattern captures the delimiters as separate groups
    parts = re.split(r'(\*\*\*.*?\*\*\*|\*\*.*?\*\*|`[^`]+`)', text)
    result = []
    for part in parts:
        if part.startswith('***') and part.endswith('***') and len(part) > 6:
            inner = xml_escape(part[3:-3])
            result.append(f'<b><i>{inner}</i></b>')
        elif part.startswith('**') and part.endswith('**') and len(part) > 4:
            inner = xml_escape(part[2:-2])
            result.append(f'<b>{inner}</b>')
        elif part.startswith('`') and part.endswith('`') and len(part) > 2:
            inner = xml_escape(part[1:-1])
            result.append(f'<font name="Courier" size="9">{inner}</font>')
        else:
            result.append(xml_escape(part))
    return ''.join(result)


def add_page_number(canvas, doc):
    """Footer with page number and project name."""
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(C_MUTED)
    canvas.drawString(MARGIN, 1.2 * cm, 'NextReel — Developer Documentation')
    canvas.drawRightString(PAGE_W - MARGIN, 1.2 * cm, f'Page {doc.page}')
    canvas.setStrokeColor(C_HR)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 1.5 * cm, PAGE_W - MARGIN, 1.5 * cm)
    canvas.restoreState()


def main():
    md_path = Path('NextReel_Developer_Documentation.md')
    pdf_path = Path('NextReel_Developer_Documentation.pdf')

    print(f'Reading {md_path}...')
    md_text = md_path.read_text(encoding='utf-8')

    styles = make_styles()
    story = md_to_story(md_text, styles)

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=2.5 * cm,
        title='NextReel Developer Documentation',
        author='NextReel Team',
        subject='Complete Developer Documentation for the NextReel Movie Recommendation System',
    )

    print('Building PDF...')
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f'Done! PDF saved to: {pdf_path.resolve()}')


if __name__ == '__main__':
    main()
