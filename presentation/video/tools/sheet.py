import os, sys
from PIL import Image, ImageDraw, ImageFont
A='/home/user/me5412-bedexit-proposal/presentation/animations/'
P='comic/panels/'
def pick(name, fb): return (P+name, None) if os.path.exists(P+name) else (fb, "漫画格生成中（姿势参考）")
cells=[("S1 · 4 s · 二维手绘","凌晨三点，她要起床。","sb_S1.png",None),
("S2 · 5.5 s · 二维手绘","床太低，最难的是站起来那一下。","sb_S2.png",None),
("S3 · 2.5 s · 片名（水彩）","—","sb_S3.png",None),
("S4 · 5 s · 速写 → 三维（无人）","平时，它和床一样低。","3d/prev/S4_3.00.png",None),
("K5 · 4 s · 动态漫画","往前挪一点，就坐上了座板。",*pick("C1.png",A+"seat_step1.png")),
("K6 · 3.5 s · 动态漫画「咔哒」","握住横杆，按住开关。",*pick("C4.png",A+"seat_step2.png")),
("K7 · 6 s · 翻页式起身「嗡——」","座板跟着大腿，往前、往上，一路托着她。",*pick("R4.png",A+"seat_step4.png")),
("S8 · 6.5 s · X 光蓝图","她卸掉多少体重，座板就升多快。","sb_S8.png",None),
("K9 · 5 s · 漫画「晕…」「停」","一松手就停，坐回去也接得住。",*pick("S9b.png",A+"seat_step3.png")),
("K10a · 2.5 s · 漫画","站稳了，再走。",*pick("C5.png",A+"seat_step5.png")),
("S10 · 4 s · 二维手绘","（无旁白）","sb_S10.png",None),
("S11 · 5 s · 结尾卡（水彩）","床边起身台，让夜里的每一次起身都有依靠。","sb_S11.png",None)]
W,H=640,360; CAP=92; cols=3
sheet=Image.new('RGB',(W*cols+40*(cols+1),(H+CAP+30)*4+90),'#F4EFE6')
f=lambda s:ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',s)
d=ImageDraw.Draw(sheet); d.text((40,28),"床边起身台 · 概念短片分镜效果图（约 48 s）",fill='#18202A',font=f(34))
for i,(t,n,p,ph) in enumerate(cells):
    x=40+(i%cols)*(W+40); y=90+(i//cols)*(H+CAP+30)
    im=Image.open(p).convert('RGB'); bg=Image.new('RGB',(W,H),'white'); im.thumbnail((W,H)); bg.paste(im,((W-im.size[0])//2,(H-im.size[1])//2))
    if ph:
        bg=Image.alpha_composite(bg.convert('RGBA'),Image.new('RGBA',(W,H),(244,239,230,110))).convert('RGB')
        dd=ImageDraw.Draw(bg); dd.rectangle([0,0,W-1,H-1],outline='#18202A',width=5); dd.text((16,14),ph,fill='#9A5408',font=f(24))
    sheet.paste(bg,(x,y)); d.rectangle([x,y,x+W,y+H],outline='#18202A',width=2)
    d.text((x,y+H+10),t,fill='#9A5408',font=f(24)); d.text((x,y+H+46),"旁白："+n,fill='#3F4A57',font=f(22))
sheet.save(sys.argv[1] if len(sys.argv)>1 else 'storyboard_sheet.png'); print(sheet.size)
