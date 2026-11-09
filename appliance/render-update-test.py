"""Generate a distinct synthetic test card; no real calendar data."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

im = Image.new('L', (600, 800), 255)
draw = ImageDraw.Draw(im)
font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
large = ImageFont.truetype(font, 44)
normal = ImageFont.truetype(font, 25)
draw.rectangle((0, 0, 600, 150), fill=0)
draw.text((35, 48), 'UPDATE TEST 2', font=large, fill=255)
for y, line in [(220, 'Image updated over USB'), (280, 'Reader services stopped'),
                (390, 'Sleep / wake test'), (460, 'This card should return'),
                (510, 'after a brief sleep and wake.'),
                (700, 'Temporary trial - automatic rollback')]:
    draw.text((30, y), line, font=normal, fill=0)
im.save(Path(__file__).parent / 'build' / 'update-test.png')
