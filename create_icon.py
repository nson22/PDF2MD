"""Generate the PDF2MD logo and multi-resolution Windows icon."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


assets = Path(__file__).parent / 'assets'
assets.mkdir(exist_ok=True)
mark = Image.new('RGBA', (512, 512))
draw = ImageDraw.Draw(mark)
draw.rounded_rectangle((8, 8, 504, 504), radius=116, fill='#151b26', outline='#334760', width=8)
draw.polygon([(120, 84), (300, 84), (391, 175), (391, 425), (120, 425)], fill='#ebf6ff')
draw.polygon([(300, 84), (300, 175), (391, 175)], fill='#87b3d1')
draw.rounded_rectangle((72, 220, 440, 368), radius=36, fill='#79cff5')
draw.line([(118, 327), (118, 262), (156, 298), (194, 262), (194, 327)],
          fill='#142238', width=20, joint='curve')
draw.line([(304, 254), (304, 322), (268, 289)], fill='#142238', width=20, joint='curve')
draw.line([(304, 322), (340, 289)], fill='#142238', width=20, joint='curve')
mark.save(assets / 'app.png')
mark.save(assets / 'app.ico', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

logo = Image.new('RGBA', (960, 240))
logo.alpha_composite(mark.resize((212, 212), Image.Resampling.LANCZOS), (12, 14))
font = ImageFont.truetype('segoeuib.ttf', 150)
draw = ImageDraw.Draw(logo)
draw.text((254, 120), 'PDF', font=font, fill='#ebf6ff', anchor='lm')
draw.text((254 + round(font.getlength('PDF')), 120), '2MD', font=font, fill='#79cff5', anchor='lm')
logo.save(assets / 'logo.png')
