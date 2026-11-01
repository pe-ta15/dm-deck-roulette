from PIL import Image, ImageDraw, ImageFilter
import math, random, subprocess, os

W,H,FPS,DUR = 960,540,30,3.6
OUT = "case-opening.webm"
random.seed(17)
particles = [(random.uniform(0.2,3.1), random.uniform(-1,1), random.uniform(-1,1), random.uniform(1.2,4.0), random.uniform(0.5,1.0)) for _ in range(150)]
frames = "frames"
os.makedirs(frames, exist_ok=True)

def ease(x):
    x=max(0,min(1,x)); return x*x*(3-2*x)
def mix(a,b,t): return a+(b-a)*t
def polygon(draw, pts, fill, outline=None, width=1):
    draw.polygon(pts, fill=fill)
    if outline: draw.line(pts+[pts[0]], fill=outline, width=width, joint="curve")

for fi in range(int(FPS*DUR)):
    t=fi/FPS
    im=Image.new("RGB",(W,H))
    px=im.load()
    pulse=0.5+0.5*math.sin(t*7)
    for y in range(H):
        for x in range(W):
            r=((x-W/2)/(W*.72))**2+((y-H/2)/(H*.78))**2
            vign=max(0,1-r)
            glow=max(0,1-math.sqrt(((x-W/2)/(W*.48))**2+((y-H*.48)/(H*.58))**2))
            px[x,y]=(int(3+9*vign+5*glow),int(5+17*vign+24*glow),int(13+32*vign+53*glow))
    d=ImageDraw.Draw(im,"RGBA")
    # atmospheric rays after the case arrives
    arrival=ease((t-.15)/.55)
    flash=max(0,1-abs(t-2.25)/.42)
    if t>1.5:
        for k in range(22):
            a=k*math.pi/11+t*.14
            x2=W/2+math.cos(a)*650; y2=H/2+math.sin(a)*650
            d.line((W/2,H/2,x2,y2),fill=(40,170,255,int(22*flash)),width=2)
    # floor reflection
    d.ellipse((245,390,715,470),fill=(20,110,190,int(28+55*arrival)),outline=(40,180,255,int(30+60*arrival)),width=2)
    # case body perspective, subtle bob + turn
    bob=math.sin(t*5)*5
    cx,cy=W/2,270+bob
    scale=.72+.28*arrival
    tilt=math.sin(t*3.3)*.07
    # construct a premium black deck case with chamfered edges
    bw,bh=300*scale,178*scale
    left,right=cx-bw/2,cx+bw/2
    top,bottom=cy-bh/2,cy+bh/2
    dx=24*scale; dy=17*scale
    # rear side / thickness
    polygon(d,[(left,top),(right,top),(right+dx,top-dy),(left+dx,top-dy)],(29,43,60,255),(105,157,190,255),3)
    polygon(d,[(right,top),(right+dx,top-dy),(right+dx,bottom-dy),(right,bottom)],(9,17,28,255),(90,137,170,255),3)
    polygon(d,[(left,top),(left+dx,top-dy),(left+dx,bottom-dy),(left,bottom)],(32,48,66,255),(112,158,190,255),3)
    polygon(d,[(left,top),(right,top),(right,bottom),(left,bottom)],(13,23,37,255),(139,188,218,255),4)
    # inset front panel with brushed-metal gradient bands
    d.rounded_rectangle((left+12*scale,top+12*scale,right-12*scale,bottom-12*scale),radius=int(13*scale),fill=(19,34,51,255),outline=(77,119,151,255),width=max(2,int(3*scale)))
    d.line((left+22*scale,top+23*scale,right-22*scale,top+23*scale),fill=(180,224,250,95),width=2)
    # central embossed emblem
    ex,ey=cx,cy+4*scale
    d.rounded_rectangle((ex-70*scale,ey-43*scale,ex+70*scale,ey+43*scale),radius=int(12*scale),fill=(8,19,31,255),outline=(70,157,211,255),width=3)
    d.text((ex-48*scale,ey-19*scale),"DM",font=None,fill=(205,232,250,255),stroke_width=1,stroke_fill=(32,118,176,255))
    d.text((ex-43*scale,ey+15*scale),"DECK CASE",fill=(112,183,224,255))
    # metallic corner protectors and latch
    for xx in (left+12*scale,right-27*scale):
        for yy in (top+12*scale,bottom-27*scale):
            d.rounded_rectangle((xx,yy,xx+15*scale,yy+15*scale),radius=3,fill=(122,157,181,255),outline=(220,239,250,220),width=1)
    d.rounded_rectangle((cx-16*scale,bottom-7*scale,cx+16*scale,bottom+9*scale),radius=4,fill=(158,190,210,255),outline=(235,247,255,255),width=2)
    # lid swings open upward in second half; stylized hinged trapezoid
    lid=ease((t-1.15)/.72)
    lid_h=88*scale*(1-lid*.68)
    if lid<.995:
        ly=top-8*scale-lid_h
        polygon(d,[(left+5*scale,top+4*scale),(right-5*scale,top+4*scale),(right-5*scale,ly),(left+5*scale,ly)],(24,43,62,245),(130,194,228,255),4)
        polygon(d,[(left+5*scale,ly),(right-5*scale,ly),(right+dx-5*scale,ly-14*scale),(left+dx-5*scale,ly-14*scale)],(68,105,133,255),(180,220,245,255),2)
        d.line((left+20*scale,ly+10*scale,right-20*scale,ly+10*scale),fill=(190,230,255,180),width=3)
        d.rounded_rectangle((cx-42*scale,ly+24*scale,cx+42*scale,ly+55*scale),radius=5,fill=(9,25,42,255),outline=(74,170,225,255),width=2)
    # brilliant energy burst and expanding shock rings
    if t>1.7:
        p=ease((t-1.7)/.32)
        radius=20+260*p
        alpha=int(180*(1-p)*flash)
        d.ellipse((cx-radius,cy-radius*.52,cx+radius,cy+radius*.52),outline=(105,220,255,alpha),width=5)
        d.ellipse((cx-radius*.72,cy-radius*.38,cx+radius*.72,cy+radius*.38),outline=(230,250,255,int(alpha*.7)),width=2)
    # particles stream outward from case
    for born,nx,ny,size,bright in particles:
        age=t-born
        if 0<=age<=1.15:
            travel=age*150
            x=cx+nx*travel*2.1
            y=cy+ny*travel*1.25
            a=int(220*(1-age/1.15)*bright)
            rr=max(1,int(size*(1-age/1.15)))
            d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(115,220,255,a))
            if rr>2: d.line((x-nx*rr*4,y-ny*rr*4,x,y),fill=(90,190,255,a//2),width=1)
    # flash bloom
    if flash>0:
        overlay=Image.new("RGBA",(W,H),(80,190,255,int(70*flash)))
        im=Image.alpha_composite(im.convert("RGBA"),overlay).convert("RGB")
    # fade down into transparent-looking dark hold for safe video cleanup
    if t>2.85:
        f=1-ease((t-2.85)/.65)
        im=Image.blend(Image.new("RGB",(W,H),(3,5,12)),im,f)
    im.save(f"{frames}/f{fi:04d}.jpg",quality=91)

subprocess.run(["ffmpeg","-y","-framerate",str(FPS),"-i",f"{frames}/f%04d.jpg","-c:v","libvpx","-b:v","1500k","-crf","10","-deadline","good","-cpu-used","4","-pix_fmt","yuv420p","-an",OUT],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print(f"Rendered {OUT}")
