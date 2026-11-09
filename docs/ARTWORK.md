# Appliance artwork

The [Kindle horse artwork](../appliance/assets/horse-in-motion-kindle.png) is
a 600x800, 8-bit grayscale image. It is a literal crop from the user-supplied
[source image](../appliance/assets/horse-in-motion-source.png) (3400x2096),
with Pillow: bounds (40,52)-(3346,1699), proportional resize to576x287,
centered on a white portrait canvas. All twelve panels remain in original order.
Title/caption below the artwork is excluded. No AI-generated pixels are used.

Reproduce with `python3 appliance/prepare-horse-art.py` from the project root.
The [full-resolution crop](../appliance/assets/horse-in-motion-crop.png)
is retained alongside the source.

An earlier built-in image-editor preview altered details and was not installed.
User accepted a literal pixel crop/resize instead. The previous Kindle card is
backed up as `rootfs/data/current.before-horse.png` within the appliance folder.
