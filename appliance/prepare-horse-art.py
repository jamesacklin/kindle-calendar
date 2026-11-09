"""Literal crop/resize of the supplied print; no generated artwork.

Crop bounds enclose the original four-column, three-row black frame and omit
the surrounding paper/title/caption. Center on the Kindle's portrait canvas.
"""
from pathlib import Path
from PIL import Image, ImageOps

assets = Path(__file__).parent / 'assets'
source = assets / 'horse-in-motion-source.png'
with Image.open(source) as original:
    if original.size != (3400, 2096):
        raise ValueError(f'Unexpected original size: {original.size}')
    artwork = original.crop((40, 52, 3346, 1699)).convert('L')
    artwork.save(assets / 'horse-in-motion-crop.png')
    fitted = ImageOps.contain(artwork, (576, 776), Image.Resampling.LANCZOS)
    canvas = Image.new('L', (600, 800), 255)
    canvas.paste(fitted, ((600 - fitted.width) // 2, (800 - fitted.height) // 2))
    canvas.save(assets / 'horse-in-motion-kindle.png')
    print(f'Original {original.size}; crop {artwork.size}; fitted {fitted.size}; canvas {canvas.size}, mode {canvas.mode}')
