import re
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('STHeiti', '/System/Library/Fonts/STHeiti Medium.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('Hiragino', '/System/Library/Fonts/Hiragino Sans GB.ttc', subfontIndex=0))

md_file = 'workbench/DESIGN.md'
pdf_file = 'workbench/DESIGN.pdf'

with open(md_file, 'r', encoding='utf-8') as f:
    content = f.read()

doc = SimpleDocTemplate(
    pdf_file,
    pagesize=A4,
    rightMargin=2*cm,
    leftMargin=2*cm,
    topMargin=2*cm,
    bottomMargin=2*cm
)

styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    name='ChineseTitle',
    fontName='Hiragino',
    fontSize=22,
    leading=30,
    textColor=HexColor('#1a1a1a'),
    spaceAfter=20,
    spaceBefore=0
))

styles.add(ParagraphStyle(
    name='ChineseH2',
    fontName='Hiragino',
    fontSize=15,
    leading=22,
    textColor=HexColor('#2c3e50'),
    spaceBefore=25,
    spaceAfter=12
))

styles.add(ParagraphStyle(
    name='ChineseH3',
    fontName='Hiragino',
    fontSize=12,
    leading=18,
    textColor=HexColor('#34495e'),
    spaceBefore=18,
    spaceAfter=8
))

styles.add(ParagraphStyle(
    name='ChineseH4',
    fontName='Hiragino',
    fontSize=11,
    leading=15,
    textColor=HexColor('#4a5568'),
    spaceBefore=12,
    spaceAfter=6
))

styles.add(ParagraphStyle(
    name='ChineseBody',
    fontName='Hiragino',
    fontSize=10,
    leading=16,
    textColor=HexColor('#333333'),
    alignment=TA_JUSTIFY,
    spaceBefore=6,
    spaceAfter=6
))

styles.add(ParagraphStyle(
    name='CodeBlock',
    fontName='Courier',
    fontSize=7,
    leading=10,
    textColor=HexColor('#333333'),
    backColor=HexColor('#f8f8f8'),
    spaceBefore=8,
    spaceAfter=8,
    leftIndent=10,
    rightIndent=10
))

styles.add(ParagraphStyle(
    name='InlineCode',
    fontName='Courier',
    fontSize=9,
    textColor=HexColor('#c7254e'),
    backColor=HexColor('#f4f4f4')
))

styles.add(ParagraphStyle(
    name='ListItem',
    fontName='Hiragino',
    fontSize=10,
    leading=15,
    textColor=HexColor('#333333'),
    leftIndent=20,
    spaceBefore=3,
    spaceAfter=3
))

def escape_html(text):
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

def process_inline_formatting(text):
    text = escape_html(text)
    text = re.sub(r'`([^`]+)`', r'<font face="Courier" size="9" color="#c7254e">\1</font>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
    return text

story = []

lines = content.split('\n')
i = 0
in_code_block = False
code_content = []
in_table = False
table_rows = []
list_items = []

def flush_list_items():
    global list_items
    if list_items:
        for item in list_items:
            story.append(Paragraph(f"• {process_inline_formatting(item)}", styles['ListItem']))
        list_items = []

def parse_table_row(line):
    cells = [cell.strip() for cell in line.split('|')]
    cells = [c for c in cells if c]
    return cells

while i < len(lines):
    line = lines[i]
    
    if line.startswith('```'):
        if in_code_block:
            code_text = '\n'.join(code_content)
            story.append(Preformatted(code_text, styles['CodeBlock']))
            code_content = []
            in_code_block = False
        else:
            flush_list_items()
            in_code_block = True
        i += 1
        continue
    
    if in_code_block:
        code_content.append(line)
        i += 1
        continue
    
    if line.startswith('|') and '|' in line[1:]:
        flush_list_items()
        if not in_table:
            in_table = True
            table_rows = []
        
        if re.match(r'^\|[\s\-:|]+\|$', line):
            i += 1
            continue
        
        table_rows.append(parse_table_row(line))
        i += 1
        continue
    elif in_table:
        if table_rows:
            col_count = max(len(row) for row in table_rows)
            normalized_rows = []
            for row in table_rows:
                while len(row) < col_count:
                    row.append('')
                normalized_rows.append(row)
            
            table_data = []
            for row in normalized_rows:
                table_data.append([Paragraph(process_inline_formatting(cell), styles['ChineseBody']) for cell in row])
            
            if table_data:
                t = Table(table_data, colWidths=[(doc.width) / col_count] * col_count)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#4c97ff')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Hiragino'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('TOPPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ffffff')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f9f9f9')]),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e0e0e0')),
                    ('FONTNAME', (0, 1), (-1, -1), 'Hiragino'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                    ('TOPPADDING', (0, 1), (-1, -1), 6),
                ]))
                story.append(t)
                story.append(Spacer(1, 10))
        table_rows = []
        in_table = False
    
    if line.startswith('# '):
        flush_list_items()
        title = line[2:].strip()
        story.append(Paragraph(title, styles['ChineseTitle']))
        story.append(Spacer(1, 5))
    elif line.startswith('## '):
        flush_list_items()
        title = line[3:].strip()
        story.append(Paragraph(title, styles['ChineseH2']))
    elif line.startswith('### '):
        flush_list_items()
        title = line[4:].strip()
        story.append(Paragraph(title, styles['ChineseH3']))
    elif line.startswith('#### '):
        flush_list_items()
        title = line[5:].strip()
        story.append(Paragraph(title, styles['ChineseH4']))
    elif line.startswith('- ') or line.startswith('* '):
        item = line[2:].strip()
        list_items.append(item)
    elif line.startswith('---'):
        flush_list_items()
        story.append(Spacer(1, 10))
    elif line.strip() == '':
        flush_list_items()
        story.append(Spacer(1, 6))
    else:
        flush_list_items()
        if line.strip():
            story.append(Paragraph(process_inline_formatting(line), styles['ChineseBody']))
    
    i += 1

flush_list_items()

if in_table and table_rows:
    col_count = max(len(row) for row in table_rows)
    normalized_rows = []
    for row in table_rows:
        while len(row) < col_count:
            row.append('')
        normalized_rows.append(row)
    
    table_data = []
    for row in normalized_rows:
        table_data.append([Paragraph(process_inline_formatting(cell), styles['ChineseBody']) for cell in row])
    
    if table_data:
        t = Table(table_data, colWidths=[(doc.width) / col_count] * col_count)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#4c97ff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Hiragino'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ffffff')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f9f9f9')]),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e0e0e0')),
            ('FONTNAME', (0, 1), (-1, -1), 'Hiragino'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
        ]))
        story.append(t)

def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    text = f"{page_num}"
    canvas.saveState()
    canvas.setFont('Hiragino', 10)
    canvas.setFillColor(HexColor('#666666'))
    canvas.drawCentredString(A4[0]/2, 1.5*cm, text)
    canvas.restoreState()

doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

print(f'PDF generated: {pdf_file}')
print(f'File size: {os.path.getsize(pdf_file) / 1024:.1f} KB')
