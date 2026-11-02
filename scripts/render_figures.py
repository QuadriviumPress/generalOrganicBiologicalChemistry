#!/usr/bin/env python3
"""Reproduce the original, accessible SVG teaching diagrams (standard library)."""
import hashlib
import json
import math
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INK, BLUE, TEAL, GOLD, RED = '#193348', '#2868a6', '#177c73', '#e8b34b', '#bb4354'


class Drawing:
    def __init__(self, title, description, height=620):
        self.height = height
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}" role="img" aria-labelledby="title desc">',
                      f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
                      '<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#2868a6"/></marker></defs>',
                      '<rect width="1000" height="100%" fill="#fff"/>',
                      f'<path d="M40 88 H960" stroke="{TEAL}" stroke-width="4"/>']
        self.text(45, 56, title, 32, anchor='start', weight='bold')

    def add(self, value):
        self.parts.append(value)

    def text(self, x, y, text, size=23, color=INK, anchor='middle', weight='normal'):
        self.add(f'<text x="{x}" y="{y}" font-family="DejaVu Sans, sans-serif" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(text))}</text>')

    def rect(self, x, y, w, h, fill='#edf5f8', stroke=INK, rx=10):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>')

    def line(self, x1, y1, x2, y2, color=INK, width=3, arrow=False, dash=False):
        extra = (' marker-end="url(#arrow)"' if arrow else '') + (' stroke-dasharray="8 7"' if dash else '')
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{extra}/>')

    def circle(self, x, y, r, fill=BLUE, label='', textcolor='white', size=23):
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{INK}" stroke-width="2"/>')
        if label:
            self.text(x, y + size * .35, label, size, textcolor)

    def arrow(self, x1, y1, x2, y2):
        self.line(x1, y1, x2, y2, BLUE, 4, True)

    def path(self, path, fill='none', stroke=INK, width=3):
        self.add(f'<path d="{path}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')

    def flask(self, x, y, liquid=BLUE, label=''):
        self.path(f'M{x+55} {y} v65 l-50 125 q-10 25 20 25 h120 q30 0 20-25 l-50-125 v-65 Z', '#f5fafc')
        self.path(f'M{x+35} {y+125} l-20 55 q-8 20 15 20 h110 q23 0 15-20 l-20-55 Z', liquid, liquid)
        if label:
            self.text(x + 85, y + 250, label)

    def bottle(self, x, y, title, fill=TEAL):
        self.rect(x + 30, y, 100, 35, fill)
        self.rect(x, y + 35, 160, 220, '#f4f7f9')
        self.rect(x + 12, y + 105, 136, 95, fill, fill)
        for n, word in enumerate(title.split('|')):
            self.text(x + 80, y + 140 + 30*n, word, min(22, 210/len(word)), 'white')

    def person(self, x, y, color=TEAL):
        self.circle(x, y, 27, color)
        self.line(x, y + 30, x, y + 125, color, 14)
        self.line(x, y + 65, x - 48, y + 105, color, 12)
        self.line(x, y + 65, x + 48, y + 80, color, 12)
        self.line(x, y + 125, x - 42, y + 197, color, 12)
        self.line(x, y + 125, x + 50, y + 180, color, 12)

    def fruit(self, x, y, fill, radius=65):
        self.circle(x, y, radius, fill)
        self.path(f'M{x} {y-radius} q20-40 60-23 q-15 35-60 23', '#38915c', TEAL)

    def finish(self, target):
        self.text(45, self.height-24, 'QuadriviumPress · Original educational schematic · Not to scale', 16, '#506578', anchor='start')
        self.add('</svg>')
        target.write_text('\n'.join(self.parts) + '\n')


def molecule(d, x, y, oxygen=False):
    if oxygen:
        d.line(x-22, y, x+22, y)
        d.circle(x-22, y, 22, RED, 'O'); d.circle(x+22, y, 22, RED, 'O')
    else:
        d.line(x-22, y, x+22, y)
        d.circle(x-22, y, 18, '#f8f8f8', 'H', INK, 18); d.circle(x+22, y, 18, '#f8f8f8', 'H', INK, 18)


def lattice(d, x, y, step=64, n=4):
    for row in range(n):
        for col in range(n):
            positive = (row + col) % 2 == 0
            d.circle(x + col*step, y + row*step, 23, TEAL if positive else GOLD,
                     'Na⁺' if positive else 'Cl⁻', 'white' if positive else INK, 17)


def ring(d, cx, cy, r=67):
    pts = [(cx+r*math.sin(i*math.pi/3), cy-r*math.cos(i*math.pi/3)) for i in range(6)]
    d.path('M'+' L'.join(f'{x},{y}' for x,y in pts)+' Z', '#fff')
    d.add(f'<circle cx="{cx}" cy="{cy}" r="{r*.52}" fill="none" stroke="{INK}" stroke-width="2"/>')
    return pts


def draw(name, a):
    d = Drawing(a['title'], a['alt'], 760 if name == 'hexoses' else 620)
    if name == 'ruler':
        d.rect(140,330,700,100,'#f8efd7',rx=0)
        d.rect(160,235,548,65,'#aecbdc',rx=0)
        for i in range(18):
            x=160+i*40;d.line(x,330,x,370 if i%5 else 390)
            if i%5==0:d.text(x,415,f'{i/10:.1f}',20)
        d.line(708,295,708,440,RED,2,dash=True)
        d.text(500,180,'Object aligned to zero',26)
        d.text(500,515,'1.37 cm — final digit estimated',29)
    elif name == 'pauling':
        d.text(500,170,'Linus Pauling',40,weight='bold')
        d.circle(300,335,45,'#f9fafb','H',INK,35)
        d.circle(690,335,67,TEAL,'Cl',size=38)
        d.line(350,335,618,335,width=6)
        d.text(300,260,'δ+',30);d.text(690,225,'δ−',30)
        d.arrow(420,410,580,410);d.text(500,475,'Electron density drawn toward chlorine',25)
        d.text(500,540,'Bonding · Electronegativity',28)
    elif name == 'dalton':
        d.text(500,170,'John Dalton · circa 1803',38,weight='bold')
        for x,y in [(250,310),(500,310),(750,310),(375,435),(625,435)]:d.circle(x,y,35,TEAL)
        d.text(500,540,'Atoms of one element share the same chemical identity.',25)
    elif name == 'radiocarbon':
        d.arrow(130,490,910,490);d.arrow(130,490,130,150)
        points=[(130+i*240,180+300*(1-2**(-i))) for i in range(4)]
        curve=[(130+i*8,180+300*(1-2**(-i/30))) for i in range(91)]
        d.path('M'+' L'.join(f'{x},{y}' for x,y in curve),stroke=TEAL,width=4)
        for i,(x,y) in enumerate(points):
            d.circle(x,y,7,TEAL);d.line(x,y,x,490,color='#899daa',width=1,dash=True)
            d.text(x,525,str(i),23)
        for y,t in [(180,'1'),(330,'½'),(405,'¼'),(442.5,'⅛')]:d.text(105,y+8,t,24,anchor='end')
        d.text(500,565,'Elapsed time / half-lives',25)
        d.text(500,135,'Fraction of original carbon-14 remaining',26)
    elif name == 'benedict':
        for x,title,positive in [(220,'Fructose',True),(500,'Glucose',True),(780,'Sucrose',False)]:
            d.path(f'M{x-45} 180 V400 Q{x} 480 {x+45} 400 V180', '#fff')
            d.path(f'M{x-35} 285 V395 Q{x} 460 {x+35} 395 V285 Z','#82bdde',BLUE)
            if positive:d.path(f'M{x-35} 385 V395 Q{x} 460 {x+35} 395 V385 Z','#be5c37','#be5c37')
            d.text(x,510,title,26);d.text(x,550,'Positive' if positive else 'Negative',23)
        d.text(500,140,'Results after heating (schematic)',25)
    elif name == 'polarizers':
        for y,crossed in [(240,False),(440,True)]:
            d.arrow(110,y,265,y)
            for x in [320,600]:d.rect(x-35,y-65,70,130,'#d7e7ef')
            d.line(320,y-45,320,y+45,TEAL,5)
            d.arrow(365,y,550,y)
            if crossed:
                d.line(575,y,625,y,RED,5);d.text(805,y+8,'Blocked',28,RED)
            else:
                d.line(600,y-45,600,y+45,TEAL,5);d.arrow(650,y,900,y)
            d.text(460,y-90,'Crossed axes' if crossed else 'Parallel axes',25)
        d.text(500,560,'Ideal transmission axes determine the transmitted light.',24)
    elif name == 'insulin-pump':
        d.rect(120,190,230,290,'#dae9ef',rx=28);d.rect(150,220,170,90,'#fff')
        d.text(235,277,'Pump',27);d.rect(180,350,110,55,TEAL)
        d.path('M350 380 H420 V230 H735 V325',stroke=BLUE,width=5)
        d.arrow(460,230,620,230)
        d.rect(540,330,360,130,'#eacdb8',rx=0);d.line(540,350,900,350,RED,4)
        d.line(735,325,735,390,BLUE,5)
        d.text(720,510,'Skin and cannula',26);d.text(585,180,'Insulin delivery',25)
    elif name == 'ninhydrin':
        for cx,color in [(250,'#c3ccd1'),(750,'#8856a7')]:
            for r in range(30,130,13):
                d.add(f'<ellipse cx="{cx}" cy="330" rx="{r*.7}" ry="{r}" fill="none" stroke="{color}" stroke-width="4"/>')
        d.arrow(420,330,580,330);d.text(500,275,'Ninhydrin',23)
        d.text(250,520,'Amino-acid residue',25);d.text(750,520,'Purple color reaction',25)
    elif name == 'cellulose':
        for row in range(3):
            for col in range(5):
                x=100+col*85;y=230+row*75
                d.circle(x,y,19,TEAL,label='G',size=17)
                if col<4:d.line(x+20,y,x+65,y)
                if row<2:d.line(x,y+22,x,y+52,BLUE,2,dash=True)
        d.text(270,145,'Extended glucose chains',25)
        d.text(270,490,'β-1,4 linkages',25);d.text(270,535,'Dashed: hydrogen bonds',22)
        for row in range(10):d.line(620,200+row*24,890,215+row*24,TEAL,8)
        d.text(755,490,'Aligned fibers',26)
        d.text(755,535,'Conceptual model',22)
    elif name == 'element-key':
        d.rect(100,160,250,325,'#edf7f4')
        d.text(225,215,'6',32);d.text(225,315,'C',85,weight='bold')
        d.text(225,380,'carbon',29);d.text(225,445,'12.011',31)
        for y,title in [(215,'Atomic number: number of protons'),(305,'Chemical symbol'),(375,'Element name'),(445,'Standard atomic weight')]:
            d.line(365,y-8,445,y-8);d.text(470,y,title,25,anchor='start')
        d.text(500,550,'[294] denotes an isotope mass number, not an atomic weight.',23)
    elif name.startswith('author-'):
        initials = ''.join(w[0] for w in a['title'].split())
        d.circle(500, 260, 90, TEAL, initials, size=46)
        d.text(500, 410, a['title'], 38, weight='bold')
        d.text(500, 462, 'Author of the source textbook', 25)
    elif name == 'alchemy':
        for x, symbol, title in zip([150, 380, 610, 840], ['☉','☽','♀','♂'], ['Gold','Silver','Copper','Iron']):
            d.text(x, 330, symbol, 120, TEAL)
            d.text(x, 430, title, 28)
        d.text(500, 510, 'Symbols used before modern chemical notation', 24)
    elif name == 'blood-pressure':
        d.rect(100, 270, 430, 90, '#eecfb5', rx=42)
        d.rect(260, 250, 140, 130, BLUE)
        d.path('M330 380 V450 H710 V335')
        d.circle(710, 250, 90, '#fff')
        for theta in range(-140, 141, 40):
            rad=math.radians(theta-90)
            d.line(710+72*math.cos(rad),250+72*math.sin(rad),710+82*math.cos(rad),250+82*math.sin(rad))
        d.line(710,250,668,205,RED,5)
        d.text(710,300,'mmHg',22)
        d.text(330,205,'Inflatable cuff',25);d.text(710,130,'Pressure gauge',25)
        d.text(500,525,'A measured pressure has a numerical value and a unit.',23)
    elif name == 'kilogram':
        d.rect(120,235,190,190,'#c0c8cf',rx=0)
        d.add('<ellipse cx="215" cy="235" rx="95" ry="26" fill="#e0e6eb" stroke="#193348" stroke-width="3"/>')
        d.line(100,235,100,425);d.text(75,340,'39 mm',19,anchor='end')
        d.text(215,480,'Platinum–iridium',24); d.text(215,515,'Historical artifact',21)
        d.rect(445,200,490,270,'#edf7f4')
        d.text(690,265,'SI definition since 2019',26,weight='bold')
        d.text(690,330,'h = 6.62607015 × 10⁻³⁴ J s',26)
        d.text(690,390,'Planck constant: fixed exactly',23)
        d.text(690,435,'kg = J s² / m²',25)
    elif name == 'pharmacy':
        d.bottle(145,170,'Medicine')
        d.rect(570,180,150,270,'#eaf5fa',rx=0)
        for y,t in [(410,'20'),(350,'40'),(290,'60'),(230,'80')]:
            d.line(570,y,610,y);d.text(625,y+7,t,20,anchor='start')
        d.text(645,150,'Volume / mL',25)
        d.arrow(330,310,535,310)
        d.text(500,525,'Concentration × measured volume = amount of solute',25)
    elif name == 'elements':
        d.path('M100 280 L155 220 H290 L345 280 V375 H100 Z','#e6b849')
        d.rect(405,260,180,120,'#b8c3cd')
        d.path('M745 250 C740 310 665 350 690 395 C730 450 865 430 870 380 C870 335 775 310 745 250','#aebecb')
        for x,t,s in [(225,'Au — gold','Yellow solid'),(495,'Fe — iron','Silvery solid'),(780,'Hg — mercury','Silvery liquid')]:
            d.text(x,480,t,26,weight='bold');d.text(x,525,s,23)
    elif name == 'cast':
        d.rect(120,210,520,100,'#eecfb5',rx=45)
        d.rect(265,195,225,130,'#eff1f3')
        for x in range(280,480,22):d.line(x,202,x+10,318,'#a7b5bf',2)
        d.text(760,275,'Plaster cast',29)
        d.text(500,425,'CaSO₄·½H₂O + 1½H₂O → CaSO₄·2H₂O',30)
        d.text(500,490,'Hemihydrate + water → gypsum',26)
    elif name == 'bread':
        d.rect(110,260,310,170,'#d7a25c',rx=65)
        for x,y in [(180,320),(235,365),(295,310),(355,375),(360,300)]:d.circle(x,y,16,'#f2d8a5')
        d.path('M625 240 V430 H885 V240','#f0f7fa')
        d.path('M635 370 Q750 210 875 370 V420 H635 Z','#ead1a0')
        for x,y in [(680,345),(720,310),(790,340),(835,375)]:d.circle(x,y,12,'#fff')
        d.text(760,180,'CO₂ bubbles expand dough',24)
        d.text(500,510,'C₆H₁₂O₆ → 2 C₂H₅OH + 2 CO₂',31)
    elif name == 'recipe':
        molecule(d,140,280);molecule(d,140,390);molecule(d,360,330,True)
        d.text(140,190,'2 H₂',30);d.text(360,190,'1 O₂',30)
        d.text(250,340,'+',36);d.arrow(460,330,590,330)
        for x,y in [(710,280),(835,390)]:
            d.line(x,y,x-40,y+32);d.line(x,y,x+40,y+32)
            d.circle(x,y,25,RED,'O');d.circle(x-40,y+32,18,'#fafafa','H',INK,18);d.circle(x+40,y+32,18,'#fafafa','H',INK,18)
        d.text(780,190,'2 H₂O',30);d.text(500,520,'Fixed proportions conserve every atom.',27)
    elif name == 'citrus':
        for x,c in [(180,'#ed932c'),(430,'#f0da55'),(680,'#74aa4d')]:d.fruit(x,280,c)
        d.text(180,410,'Orange');d.text(430,410,'Lemon');d.text(680,410,'Lime')
        d.arrow(280,500,720,500);d.text(500,470,'Vitamin C can donate electrons',26)
    elif name == 'boiling':
        d.path('M260 180 V470 H650 V180','#eaf6fa')
        d.rect(270,340,370,120,'#a7d5ef',stroke='#a7d5ef',rx=0)
        for x,y in [(310,430),(460,400),(590,360),(390,310)]:d.circle(x,y,12,'#fff')
        for x,y in [(310,230),(450,200),(580,270)]:
            d.circle(x,y,12,RED)
        d.text(780,230,'Vapor: 100°C',25);d.line(650,230,680,230)
        d.text(780,400,'Liquid: 100°C',25);d.line(650,400,680,400)
        d.arrow(450,545,450,480);d.text(320,540,'Heat in',24)
        d.text(450,145,'Pressure = 1 atm',25)
    elif name == 'crystal':
        lattice(d,160,195,85,4)
        d.text(740,260,'Repeating ionic lattice',27)
        d.text(740,325,'Regular arrangement',24)
        d.text(740,370,'Alternating charges',24)
        d.text(500,530,'A two-dimensional slice of a three-dimensional crystal',24)
    elif name == 'oil-water':
        d.path('M260 160 V490 H590 V160','#fff')
        d.rect(270,220,310,100,'#efd66d',stroke='#efd66d',rx=0)
        d.rect(270,320,310,160,'#e69ba3',stroke='#e69ba3',rx=0)
        d.text(770,280,'Oil — upper layer',26);d.line(580,275,620,275)
        d.text(770,400,'Water — lower layer',26);d.line(580,395,620,395)
        d.text(500,550,'Two liquid phases; the liquids are not miscible.',25)
    elif name == 'saline':
        d.rect(85,300,270,100,'#e5edf3')
        d.rect(130,260,180,30,'#ccd7df')
        d.text(220,365,'0.9 g NaCl',28)
        d.arrow(400,330,555,330)
        d.flask(640,160,'#a2cfe9')
        d.path('M695 228 L645 350 Q635 375 665 375 H785 Q815 375 805 350 L755 228 Z','#a2cfe9','#a2cfe9')
        d.line(690,228,760,228,RED)
        d.text(725,470,'100 mL final solution',26)
        d.text(500,550,'0.9 g / 100 mL = 0.9% (m/v)',29)
    elif name == 'water-balance':
        for x,r,count,title in [(230,75,8,'Before dilution'),(740,110,4,'After dilution')]:
            d.circle(x,315,r,'#d5ebe4')
            d.text(x,160,title,27)
            for i in range(count):
                theta=i*2*math.pi/count;d.circle(x+155*math.cos(theta),315+145*math.sin(theta),10,GOLD)
        d.arrow(430,315,540,315);d.text(500,275,'Dilution',22)
        d.arrow(925,315,855,315);d.text(890,265,'H₂O',22)
        d.text(500,545,'Lower external solute concentration → water enters cells',25)
    elif name == 'solvation':
        for cx,positive in [(250,True),(750,False)]:
            d.circle(cx,320,40,TEAL if positive else GOLD,'Na⁺' if positive else 'Cl⁻','white' if positive else INK,25)
            for theta in [0,math.pi/2,math.pi,3*math.pi/2]:
                # Oxygen is closer to a cation; hydrogens are closer to an anion.
                ox=cx+110*math.cos(theta);oy=320+110*math.sin(theta)
                direction=1 if positive else -1
                for delta in [-.55,.55]:
                    hx=ox+direction*38*math.cos(theta+delta);hy=oy+direction*38*math.sin(theta+delta)
                    d.line(ox,oy,hx,hy);d.circle(hx,hy,14,'#fff','H',INK,15)
                d.circle(ox,oy,22,RED,'O',size=20)
        d.text(250,535,'Oxygen (δ−) faces Na⁺',25);d.text(750,535,'Hydrogen (δ+) faces Cl⁻',25)
    elif name == 'dissociation':
        lattice(d,115,220,65,4);d.arrow(390,325,520,325)
        d.rect(570,175,350,310,'#edf7fc')
        for i in range(16):
            x=610+(i%4)*87+((i//4)%2)*8;y=215+(i//4)*78
            positive=i%2==0;d.circle(x,y,23,TEAL if positive else GOLD,'Na⁺' if positive else 'Cl⁻','white' if positive else INK,17)
        d.text(235,540,'Ionic solid',26);d.text(745,540,'Separated ions in water',26)
    elif name == 'dialysis':
        d.rect(100,170,800,145,'#f7dfe2');d.rect(100,335,800,145,'#e0eff8')
        d.rect(100,315,800,20,'#d2d8de',rx=0)
        d.arrow(130,205,850,205);d.arrow(850,445,130,445)
        for x in [230,420,680]:d.circle(x,267,22,RED)
        for x in [340,540,790]:
            d.circle(x,275,7,GOLD);d.arrow(x,290,x,385);d.circle(x,405,7,GOLD)
        d.text(500,140,'Blood: cells retained; small waste solutes can cross',24)
        d.text(500,525,'Dialysate: lower concentration of waste solutes',24)
        d.text(500,570,'Membrane separates the two flowing fluids',21)
    elif name == 'hydrochloride':
        for x,w,text,title in [(155,180,'RNH₂','Amine base'),(405,160,'HCl','Acid'),(770,300,'RNH₃⁺ Cl⁻','Hydrochloride salt')]:
            d.rect(x-w/2,220,w,160,'#eff7f5');d.text(x,310,text,36);d.text(x,435,title,25)
        d.text(280,315,'+',32);d.arrow(545,300,625,300)
        d.text(500,525,'The amine accepts a proton from hydrochloric acid.',25)
    elif name == 'cleaners':
        d.bottle(180,160,'Alkaline|drain cleaner',BLUE)
        d.bottle(640,160,'Plant-derived|formulation',TEAL)
        d.text(500,515,'Ingredients and chemical properties vary by product.',25)
        d.text(500,555,'Read the product label.',24)
    elif name == 'pet':
        d.add('<ellipse cx="500" cy="330" rx="180" ry="195" fill="#f3f6f8" stroke="#193348" stroke-width="18"/>')
        d.rect(440,270,120,170,'#d9e7ed',rx=50);d.circle(500,230,28,'#d9e7ed')
        d.circle(500,330,9,RED);d.arrow(490,330,300,330);d.arrow(510,330,700,330)
        d.text(200,285,'511 keV γ',24);d.text(800,285,'511 keV γ',24)
        d.text(500,125,'Detector ring',26)
        d.text(500,560,'Coincident photons locate an annihilation line.',25)
    elif name == 'tomato':
        d.fruit(320,230,'#d34a3d',68);d.fruit(650,260,'#c93c39',90)
        points=[(170+i*55,440+(i%2)*36) for i in range(13)]
        for i,(p,q) in enumerate(zip(points,points[1:])):
            d.line(*p,*q,width=4)
            if i%2==0:d.line(p[0]+4,p[1]-10,q[0]-4,q[1]-10,width=3)
        d.text(500,545,'Alternating bonds in a conjugated system (segment)',24)
    elif name == 'antiseptics':
        pts=ring(d,250,320);d.line(*pts[0],250,210);d.text(250,188,'OH',28);d.text(250,475,'Phenol',28)
        pts=ring(d,690,320);d.line(*pts[0],690,210);d.text(690,188,'OH',28)
        d.line(*pts[2],800,385);d.text(840,410,'OH',28)
        d.line(*pts[3],690,435);d.text(690,465,'(CH₂)₅CH₃',25)
        d.text(690,530,'4-Hexylresorcinol',27)
    elif name == 'silvering':
        d.path('M455 150 V215 L405 340 Q395 365 425 365 H545 Q575 365 565 340 L515 215 V150 Z','#f3f8fb')
        d.path('M463 170 V217 L417 340 Q412 353 430 353 H540 Q555 353 553 340 L507 217 V170',stroke='#adbcc6',width=13)
        d.text(730,300,'Deposited silver',25);d.line(575,310,620,310)
        d.text(500,475,'RCHO + 2 Ag⁺ + 3 OH⁻ → RCOO⁻ + 2 Ag + 2 H₂O',27)
        d.text(500,535,'Aldehyde oxidized; silver(I) reduced',25)
    elif name == 'household-acids':
        d.bottle(90,160,'Vinegar',BLUE);d.text(170,470,'Acetic acid',23)
        d.circle(385,275,60,'#fff');d.line(340,275,430,275);d.text(385,390,'Aspirin',23);d.text(385,430,'Acetylsalicylic',19);d.text(385,457,'acid',19)
        d.fruit(620,275,'#f2d84f');d.text(620,430,'Citric acid',23)
        d.path('M800 355 Q770 160 920 210 Q955 350 800 355','#5f9b63',TEAL)
        d.line(800,355,900,235,TEAL,4);d.text(855,430,'Oxalic acid',23)
        d.text(500,535,'Vitamin C: ascorbic acid is an acidic lactone.',24)
    elif name == 'glucose-meter':
        d.rect(550,145,250,320,'#d4e6ef',rx=38);d.rect(580,190,190,110,'#fff')
        d.text(675,260,'mg/dL',30);d.circle(675,380,25,TEAL)
        d.rect(430,323,120,44,'#f9f8f2',rx=0)
        d.path('M380 240 C375 280 345 300 350 325 C355 365 410 365 415 325 C420 300 390 280 380 240',RED)
        d.text(245,385,'Blood sample',24);d.arrow(360,390,460,365)
        d.text(500,535,'Test strip → chemical signal → glucose measurement',25)
    elif name == 'hexoses':
        for cx,name,pattern,food in [(170,'D-Glucose',['R','L','R','R'],'Grapes'),(500,'D-Galactose',['R','L','L','R'],'Milk lactose'),(830,'D-Fructose',['K','L','R','R'],'Honey')]:
            d.text(cx,140,name,26,weight='bold')
            d.text(cx,205,'CH₂OH' if pattern[0]=='K' else 'CHO',24)
            for idx,side in enumerate(pattern):
                y=265+idx*70;d.line(cx,y-40,cx,y+33)
                if side=='K':
                    d.line(cx,y,cx+56,y);d.line(cx,y+8,cx+56,y+8);d.text(cx+79,y+9,'O',24)
                else:
                    d.line(cx-56,y,cx+56,y)
                    d.text(cx-83,y+9,'H' if side=='R' else 'HO',23)
                    d.text(cx+83,y+9,'OH' if side=='R' else 'H',23)
            d.line(cx,210,cx,225);d.line(cx,508,cx,552)
            d.text(cx,580,'CH₂OH',24);d.text(cx,655,food,24)
        d.text(500,710,'Fischer projections · Horizontal bonds point toward the viewer',21)
    elif name == 'diabetes-education':
        positions=[(230,200,'Glucose monitoring'),(740,200,'Nutrition'),(230,425,'Physical activity'),(740,425,'Prescribed medication')]
        for x,y,label in positions:d.rect(x-180,y-60,360,150,'#f1f7f7');d.text(x,y+60,label,22)
        d.rect(200,155,60,64,'#b5d8e8');d.rect(208,165,44,24,'#fff');d.text(230,185,'mg/dL',10)
        d.circle(740,185,37,'#fff');d.line(704,185,776,185,TEAL);d.line(740,148,740,185,TEAL)
        d.add('<g transform="translate(230 363) scale(.32)">');d.person(0,0);d.add('</g>')
        d.add('<g transform="translate(713 352) scale(.34)">');d.bottle(0,0,'Rx');d.add('</g>')
    elif name == 'exercise':
        d.person(220,220)
        d.path('M500 325 C450 260 500 230 535 265 C570 230 620 260 570 325 L535 360 Z',RED,RED)
        d.arrow(310,305,440,305);d.arrow(630,305,755,305)
        d.text(830,290,'ATP',40,TEAL,weight='bold');d.text(830,335,'demand',25)
        d.text(500,515,'Activity ↔ oxygen use ↔ energy metabolism',27)
    elif name == 'hemoglobin':
        for x,y,c,label in [(390,240,TEAL,'Globin 1'),(610,240,BLUE,'Globin 2'),(390,420,GOLD,'Globin 3'),(610,420,RED,'Globin 4')]:
            d.circle(x,y,95,c);d.text(x,y-20,label,21,'white' if c!=GOLD else INK)
            d.circle(x,y+27,24,'#eee', 'heme', INK,12)
        d.text(500,555,'Four subunits; one heme group per subunit',25)
    elif name == 'insulin':
        d.bottle(190,170,'Insulin',TEAL)
        d.rect(650,180,60,260,'#dde8ef',rx=20);d.rect(660,140,40,55,TEAL)
        d.text(680,485,'Injection pen',24);d.text(270,485,'Vial',24)
        d.text(500,550,'Insulin gene → expression → purified human insulin',25)
    else:
        raise ValueError(f'Unimplemented diagram: {name}')
    return d


def main():
    ledger_path = ROOT / 'figure-replacements.json'
    ledger = json.loads(ledger_path.read_text())
    for entry in ledger['entries'].values():
        if 'diagram' not in entry:
            continue
        for asset in entry['assets']:
            target = ROOT / asset['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            draw(entry['diagram'], asset).finish(target)
            asset['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + '\n')
    print('Original SVG diagrams regenerated; asset hashes updated.')


if __name__ == '__main__':
    main()
