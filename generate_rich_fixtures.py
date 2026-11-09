#!/usr/bin/env python3
"""Generate alternate-format ingestion fixtures from the canonical synthetic corpus.

Development-only dependencies: python-docx, reportlab, PyMuPDF, Pillow.
The macOS product itself does not require this generator or its Python libraries.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

import fitz
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfgen.canvas import Canvas


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blocks(text: str):
    raw = text.split('\n\n')
    title = raw[0].removeprefix('# ').replace(':', ' ')
    result = []
    pending = None
    for value in raw[1:]:
        value = value.strip()
        if not value:
            continue
        if value.startswith('SYNTHETIC DATA') or value.startswith('Document ID:'):
            continue
        if value.startswith('### '):
            pending = value.removeprefix('### ')
        elif value.startswith('## '):
            result.append(('heading', value.removeprefix('## ')))
        else:
            result.append(('evidence' if pending else 'body', (pending + '  ' if pending else '') + value.replace('\n', ' ')))
            pending = None
    return title, result


def metadata_table(record):
    return [['SOURCE ID', 'PUBLISHED UTC', 'TYPE'], [record['document_id'], record['published_at'], record['type']]]


def make_pdf(path: Path, record, title, content):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='FixtureTitle', fontName='Helvetica-Bold', fontSize=18, leading=21, textColor=colors.black, spaceAfter=9))
    styles.add(ParagraphStyle(name='FixtureBody', fontName='Helvetica', fontSize=10.5, leading=13.1, spaceAfter=5))
    styles.add(ParagraphStyle(name='FixtureHeading', fontName='Helvetica-Bold', fontSize=11.3, leading=14, spaceBefore=7, spaceAfter=4, keepWithNext=True))
    styles.add(ParagraphStyle(name='FixtureSmall', fontName='Helvetica', fontSize=8.6, leading=11, textColor=colors.HexColor('#4B5563'), spaceAfter=6))
    story = [Paragraph(html.escape(title), styles['FixtureTitle']), Paragraph('FICTIONAL TEST RECORD - alternate format of the canonical Markdown source', styles['FixtureSmall'])]
    table = Table(metadata_table(record), colWidths=[120, 210, 186])
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1F3652')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(0,1),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),8.4),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#D9D9D9')),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.extend([table, Spacer(1,8)])
    for kind, value in content:
        st = styles['FixtureHeading'] if kind == 'heading' else styles['FixtureBody']
        escaped = html.escape(value)
        if kind == 'evidence':
            escaped = re.sub(r'^(S\d+)  ', r'<b>\1</b>  ', escaped)
        story.append(Paragraph(escaped, st))
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica',8)
        canvas.setFillColor(colors.HexColor('#6B7280'))
        canvas.drawString(48,24,record['document_id'] + ' | SYNTHETIC DATA | no real company records')
        canvas.drawRightString(564,24,str(doc.page))
        canvas.restoreState()
    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=48, rightMargin=48, topMargin=40, bottomMargin=40, title=title, author='Synthetic corpus generator')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)


def set_borders(table):
    pr = table._tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']:
        el = OxmlElement('w:' + side)
        el.set(qn('w:val'),'single'); el.set(qn('w:sz'),'4'); el.set(qn('w:color'),'D9D9D9')
        borders.append(el)
    pr.append(borders)


def make_docx(path: Path, record, title, content):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Inches(8.5); sec.page_height = Inches(11)
    sec.top_margin = Inches(.55); sec.bottom_margin = Inches(.55)
    sec.left_margin = Inches(.67); sec.right_margin = Inches(.67)
    for style_name in ['Normal','Title','Heading 1','Heading 2']:
        st = doc.styles[style_name]
        st.font.name='Calibri'; st.font.color.rgb=RGBColor(0,0,0)
    normal=doc.styles['Normal']; normal.font.size=Pt(11)
    normal.paragraph_format.space_after=Pt(4)
    normal.paragraph_format.line_spacing=1.0
    title_style=doc.styles['Title']; title_style.font.size=Pt(19)
    title_style.paragraph_format.space_after=Pt(7)
    heading=doc.styles['Heading 1']; heading.font.size=Pt(11.5)
    heading.paragraph_format.space_before=Pt(6); heading.paragraph_format.space_after=Pt(3)
    doc.add_paragraph(title,'Title')
    p=doc.add_paragraph('FICTIONAL TEST RECORD - alternate format of the canonical Markdown source')
    for run in p.runs: run.font.size=Pt(9)
    table=doc.add_table(rows=2, cols=3); table.autofit=False
    widths=[Inches(1.5), Inches(2.8), Inches(2.86)]
    for row_idx,row in enumerate(metadata_table(record)):
        for col_idx,value in enumerate(row):
            cell=table.cell(row_idx,col_idx); cell.width=widths[col_idx]
            cell.vertical_alignment=1
            p=cell.paragraphs[0]; p.paragraph_format.space_after=Pt(4); p.paragraph_format.space_before=Pt(4)
            run=p.add_run(value); run.font.size=Pt(9)
            if row_idx==0:
                run.bold=True; run.font.color.rgb=RGBColor(255,255,255)
                shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),'1F3652'); cell._tc.get_or_add_tcPr().append(shd)
    set_borders(table)
    for kind,value in content:
        if kind=='heading':
            doc.add_paragraph(value,'Heading 1')
        elif kind=='evidence':
            p=doc.add_paragraph(); code,body=value.split('  ',1)
            p.add_run(code+'  ').bold=True; p.add_run(body)
        else:
            doc.add_paragraph(value)
    doc.core_properties.title=title
    doc.core_properties.author='Synthetic corpus generator'
    doc.core_properties.subject='Fictional ingestion fixture with source provenance'
    # The bundled Word template may supply a decorative Title paragraph rule.
    # Remove paragraph borders while preserving the intentional table grid.
    for xml_root in [doc._element, doc.styles._element]:
        for border in list(xml_root.iter(qn('w:pBdr'))):
            border.getparent().remove(border)
    doc.styles['Title'].font.underline=False
    doc.save(path)


def diagram(path: Path, record, content):
    image=Image.new('RGB',(1600,1000),'#F5F7FA'); draw=ImageDraw.Draw(image)
    font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    bold_path='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    try:
        font=ImageFont.truetype(font_path,23); large=ImageFont.truetype(bold_path,35); small=ImageFont.truetype(font_path,20)
    except OSError:
        font=ImageFont.load_default(); large=font; small=font
    draw.text((60,45),'Lumen Initiative 001 relationships',font=large,fill='#142B46')
    draw.text((60,102),'SYNTHETIC DATA | DOC-00001 | exact source statements S01-S03',font=small,fill='#475569')
    nodes=[((75,390,595,530),'Lumen Initiative 001'),((950,220,1510,330),'Lumen Document Discovery 001'),((950,430,1510,540),'Ava Cedar (001, synthetic)'),((950,640,1510,750),'Milo Cedar (002, synthetic)')]
    for (x1,y1,x2,y2),label in nodes:
        draw.rounded_rectangle((x1,y1,x2,y2),radius=18,fill='white',outline='#9AACC1',width=3)
        bbox=draw.textbbox((0,0),label,font=font)
        draw.text(((x1+x2-bbox[2])/2,(y1+y2-28)/2),label,font=font,fill='#172B43')
    for endpoint,label,yy in [((950,275),'S01 delivers',300),((950,485),'S02 owned by',470),((950,695),'S03 sponsored by',640)]:
        start=(595,460); draw.line([start,endpoint],fill='#426B9E',width=4)
        x,y=endpoint; draw.polygon([(x,y),(x-16,y-8),(x-16,y+8)],fill='#426B9E')
        draw.rectangle((620,yy-8,910,yy+33),fill='#F5F7FA')
        draw.text((634,yy),label,font=font,fill='#17426C')
    draw.text((60,855),'These arrows are source-backed relationships, not simulated outcomes.',font=font,fill='#334155')
    draw.text((60,900),'OCR can read labels; graph interpretation requires a vision-capable model or diagram parser.',font=small,fill='#475569')
    image.save(path)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--root',default=str(Path(__file__).parent)); args=parser.parse_args()
    root=Path(args.root).resolve(); out=root/'rich_fixtures'
    for folder in ['pdf','docx','images','scanned_pdf']:
        (out/folder).mkdir(parents=True,exist_ok=True)
    rows=[json.loads(line) for line in (root/'manifests/documents.jsonl').read_text().splitlines() if line.strip()][:12]
    manifest=[]
    for i,rec in enumerate(rows):
        src=root/rec['path']; text=src.read_text(); title,content=blocks(text)
        pdf=out/'pdf'/f"{rec['document_id']}.pdf"
        make_pdf(pdf,rec,title,content)
        with fitz.open(pdf) as file:
            if len(file)!=1:
                raise RuntimeError(f'Fixture expected one page but has {len(file)}: {pdf}')
            for statement in [value.split('  ',1)[1] for kind,value in content if kind=='evidence']:
                extracted=' '.join(file[0].get_text().split())
                if ' '.join(statement.split()) not in extracted:
                    raise RuntimeError('Missing PDF evidence: '+statement)
            pix=file[0].get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
            if i<11:
                png=out/'images'/f"{rec['document_id']}_scan.png"; pix.save(png)
                manifest.append({'path':str(png.relative_to(root)),'variant_of':rec['document_id'],'format':'png','purpose':'image OCR','is_excerpt':False,'sha256':sha(png),'source_sha256':sha(src)})
            if i<4:
                scan=out/'scanned_pdf'/f"{rec['document_id']}_image_only.pdf"
                image=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
                image.save(scan,'PDF',resolution=144.0)
                with fitz.open(scan) as scanned:
                    if scanned[0].get_text().strip(): raise RuntimeError('Scanned fixture unexpectedly has text layer')
                manifest.append({'path':str(scan.relative_to(root)),'variant_of':rec['document_id'],'format':'pdf','purpose':'scanned PDF OCR','is_excerpt':False,'sha256':sha(scan),'source_sha256':sha(src)})
        manifest.append({'path':str(pdf.relative_to(root)),'variant_of':rec['document_id'],'format':'pdf','purpose':'digital PDF extraction','is_excerpt':False,'sha256':sha(pdf),'source_sha256':sha(src)})
        if i<8:
            word=out/'docx'/f"{rec['document_id']}.docx"; make_docx(word,rec,title,content)
            manifest.append({'path':str(word.relative_to(root)),'variant_of':rec['document_id'],'format':'docx','purpose':'native DOCX import with table','is_excerpt':False,'sha256':sha(word),'source_sha256':sha(src)})
    chart=out/'images'/'DOC-00001_relationships.png'; diagram(chart,rows[0],None)
    manifest.append({'path':str(chart.relative_to(root)),'variant_of':'DOC-00001','format':'png','purpose':'text and relationship diagram','is_excerpt':True,'statement_ids':['DOC-00001:S01','DOC-00001:S02','DOC-00001:S03'],'sha256':sha(chart),'source_sha256':sha(root/rows[0]['path'])})
    (out/'manifest.json').write_text(json.dumps({'schema':'rich-format-fixtures/1.0','synthetic':True,'description':'Alternate representations of canonical source documents. Not 36 additional independent records.','files':manifest},indent=2)+'\n')
    (out/'README.txt').write_text('RICH INGESTION FIXTURES\n\n12 digital PDFs, 8 Word DOCX files, 11 page-scan PNGs, 1 relationship-diagram PNG, and 4 image-only scanned PDFs.\n\nAll are synthetic alternate representations of DOC-00001 through DOC-00012. Use them to test parsers/OCR/previews separately or replace a canonical source in an ingestion run. Do not count each format as independent corroborating evidence. The relationship diagram includes only statements S01-S03.\n\nmanifest.json records canonical IDs, checksums, format and purpose. Base manifests do not automatically ingest these files. No embeddings or simulation output are precomputed.\n\nRegenerate using: python3 generate_rich_fixtures.py --root .\nRequires python-docx, reportlab, PyMuPDF and Pillow in the development environment. The corpus generator itself uses only Python standard libraries.\n')
    print(json.dumps({'files':len(manifest),'formats':{'digital_pdf':12,'docx':8,'png':12,'scanned_pdf':4}},indent=2))


if __name__=='__main__': main()
