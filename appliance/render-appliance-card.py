"""Render a neutral appliance placeholder, not a real family calendar."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

im = Image.new('L', (600, 800), 255)
d = ImageDraw.Draw(im)
font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
large = ImageFont.truetype(font, 38)
normal = ImageFont.truetype(font, 24)
small = ImageFont.truetype(font, 19)
d.rectangle((0, 0, 599, 135), fill=0)
d.text((30, 42), 'FAMILY CALENDAR', font=large, fill=255)
d.text((35, 210), 'Appliance mode', font=large, fill=0)
d.text((35, 290), 'Waiting for calendar data', font=normal, fill=0)
d.line((35, 355, 565, 355), fill=0, width=2)
d.text((35, 410), 'USB display + charging', font=normal, fill=0)
d.text((35, 465), 'Reader applications stopped', font=normal, fill=0)
d.text((35, 680), 'Setup in progress', font=small, fill=0)
d.text((35, 720), 'Boot unplugged, then connect USB', font=small, fill=0)
im.save(Path(__file__).parent / 'build' / 'appliance-card.png')
