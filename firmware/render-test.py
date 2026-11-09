"""Create a 600x800 grayscale diagnostic PNG for the Kindle's native renderer."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
image = Image.new('L', (600, 800), 255)
draw = ImageDraw.Draw(image)
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
large = ImageFont.truetype(font_path, 38)
normal = ImageFont.truetype(font_path, 24)
small = ImageFont.truetype(font_path, 19)
draw.rectangle((14, 14, 585, 785), outline=0, width=3)
draw.text((40, 55), 'Kindle calendar display', font=large, fill=0)
draw.line((40, 115, 560, 115), fill=0, width=2)
draw.text((40, 150), 'USB image transfer: OK', font=normal, fill=0)
draw.text((40, 200), '600 x 800 pixels', font=normal, fill=0)
draw.text((40, 250), 'One cable: power + data', font=normal, fill=0)
draw.text((40, 330), 'Grayscale check', font=small, fill=0)
for index in range(16):
    x = 44 + index * 32
    draw.rectangle((x, 370, x + 31, 455), fill=index * 17)
draw.rectangle((44, 370, 555, 455), outline=0)
draw.text((40, 540), 'Ready for a family calendar', font=normal, fill=0)
draw.text((40, 700), 'Display test - no calendar data loaded', font=small, fill=0)
output = root / 'display-test.png'
image.save(output)
print(output)
