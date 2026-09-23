"""Create an A1 portrait poster; preserve the result plot as embedded vector PDF."""
from pathlib import Path
import io
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from pypdf import PdfReader,PdfWriter,Transformation
import matplotlib

ROOT=Path(__file__).resolve().parents[1]
fontdir=Path(matplotlib.get_data_path())/'fonts/ttf'
pdfmetrics.registerFont(TTFont('DVS',str(fontdir/'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DVS-Bold',str(fontdir/'DejaVuSans-Bold.ttf')))
pdfmetrics.registerFontFamily('DVS',normal='DVS',bold='DVS-Bold',italic='DVS',boldItalic='DVS-Bold')
W,H=594*72/25.4,841*72/25.4
NAVY=HexColor('#163d6b');TEAL=HexColor('#008b78');INK=HexColor('#172b40');MUTED=HexColor('#4b6174')
buf=io.BytesIO();c=canvas.Canvas(buf,pagesize=(W,H))
c.setTitle('Prefix-Certificate Retention - Research Poster');c.setAuthor('Shivam Gupta')
c.setFillColor(white);c.rect(0,0,W,H,fill=1,stroke=0)
c.setFillColor(NAVY);c.rect(0,H-300,W,300,fill=1,stroke=0)

def text(x,y,s,size=25,color=INK,bold=False):
    c.setFillColor(color);c.setFont('DVS-Bold' if bold else 'DVS',size);c.drawString(x,y,s)

def para(x,y,s,width,size=25,color=INK,leading=None):
    p=Paragraph(s,ParagraphStyle('p',fontName='DVS',fontSize=size,leading=leading or size*1.36,textColor=color))
    _,h=p.wrap(width,H);p.drawOn(c,x,y-h);return y-h

def box(x,y,w,h,color):
    c.setFillColor(color);c.roundRect(x,y,w,h,12,fill=1,stroke=0)

text(62,H-68,'EXACT MEMORY-TIME OPTIMIZATION',44,white,True)
text(62,H-132,'FOR PREFIX-CACHED LANGUAGE MODEL SERVING',44,white,True)
text(62,H-201,'Shivam Gupta  |  Independent Researcher, Delhi, India',27,white)
text(62,H-251,'Prefix-Certificate Retention (PCR)  •  September 2026',26,HexColor('#bcefe4'))

box(62,H-485,W-124,143,HexColor('#edf8f5'))
text(91,H-390,'A usable cache hit is a set of prerequisites.',37,TEAL,True)
para(91,H-418,'Represent those prerequisites explicitly: exact static timeout optimization becomes one minimum cut.',W-184,26)

left,right=62,875
cw=745
top=H-548
text(left,top,'1. Model and construction',33,NAVY,True)
y=para(left,top-30,'A request can reuse a block only when its entire preceding prefix is available. Blocks have grouped, reset-on-access timeouts; storage is charged over a finite observation window.',cw,26)
y-=28
box(left,y-115,cw,112,HexColor('#f1f4f8'))
text(left+21,y-37,'Maximize usable prefix blocks',28,NAVY,True)
text(left+21,y-80,'minus λ × occupied block-seconds',26,NAVY)
y-=155
y=para(left,y,'<b>Threshold nodes:</b> choosing a longer timeout incurs incremental storage cost.<br/><b>Hit nodes:</b> a reward requires its local timeout threshold and the previous prefix-hit node.<br/><b>Maximum closure:</b> every selected node includes its prerequisites. Standard minimum cut gives the optimum.',cw,25)
para(left,y-30,'Other requests can refresh ancestors, so longer descendant timeouts can remain useful.',cw,24,color=TEAL)

text(right,top,'2. Mathematical and empirical results',31,NAVY,True)
yr=top-40
for title,body in [
    ('Exact finite-grid optimum','One minimum cut; graph size is linear in block lookups and timeout choices.'),
    ('No discretization error required','Every timeout can be rounded down to a training reuse age without losing a hit or increasing cost.'),
    ('Certify the simpler policy','Coherent optimum ≤ exact optimum ≤ independent local-hit upper bound.')]:
    text(right,yr,title,28,TEAL,True)
    yr=para(right,yr-18,body,cw,25)-38
box(right,yr-230,cw,225,HexColor('#edf2f8'))
text(right+25,yr-76,'118 / 120',70,NAVY,True)
para(right+25,yr-103,'Native fixed-grid cases where ordered timeouts already attain the unrestricted training optimum.',cw-50,25)

section_y=1070
text(62,section_y,'3. Chronological replay of 39,632 public requests',34,NAVY,True)
para(62,section_y-30,'Mooncake FAST’25: conversation, tool-agent and synthetic workloads. Training / validation / test: 40 / 20 / 40% of elapsed time. All ten declared storage prices are reported.',W-124,25)

# Place the manuscript's vector result plot after the base page is generated.
figure=PdfReader(ROOT/'output/poster-utility.pdf').pages[0]
fw,fh=float(figure.mediabox.width),float(figure.mediabox.height)
scale=(W-120)/fw
plot_top=935
plot_bottom=plot_top-fh*scale
caption_y=plot_bottom-14
para(62,caption_y,'Test utility: usable prefix blocks minus storage price times occupied block-seconds, normalized per input block. Lines compare the validation-selected coherent policy with global and group timeouts. Bands are descriptive 60-second-bucket bootstrap intervals; they are not deployment-wide guarantees.',W-124,22,color=MUTED)

footer_y=234
c.setStrokeColor(HexColor('#c4d1df'));c.setLineWidth(2);c.line(62,footer_y+57,W-62,footer_y+57)
text(62,footer_y+10,'Use: an offline configuration oracle and retention-policy audit.',27,TEAL,True)
para(62,footer_y-12,'11 tests include exhaustive profiles, independent event replay and 450 full-policy LP comparisons. This is cache replay with immediate post-batch availability, not measured GPU latency or a hard-capacity guarantee.',W-335,22,color=MUTED)
text(62,79,'Code, proofs, data provenance and complete results:',22,NAVY,True)
text(62,109,'Sources: Picard (1976); Mooncake (FAST25); Kareto (2026).',18,MUTED)
text(62,42,'github.com/shi1720/prefix-certificate-retention',23,NAVY)
qr=QrCodeWidget('https://github.com/shi1720/prefix-certificate-retention')
b=qr.getBounds();sz=145;d=Drawing(sz,sz,transform=[sz/(b[2]-b[0]),0,0,sz/(b[3]-b[1]),0,0]);d.add(qr)
renderPDF.draw(d,c,W-215,47)
c.showPage();c.save();buf.seek(0)
page=PdfReader(buf).pages[0]
page.merge_transformed_page(figure,Transformation().scale(scale).translate(60,plot_bottom))
writer=PdfWriter();writer.add_page(page)
writer.add_metadata({'/Title':'Exact Memory-Time Optimization for Prefix-Cached Language Model Serving - Poster','/Author':'Shivam Gupta'})
out=ROOT/'output/pdf/prefix-certificate-retention-poster.pdf';out.parent.mkdir(parents=True,exist_ok=True)
with out.open('wb') as f:writer.write(f)
print('Poster:',out,'plot bottom:',round(plot_bottom))
