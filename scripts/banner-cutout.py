"""Derive the transparent banner from banner.jpg: the artwork without its light background
and its painted hexagons, so the page's own hexagon grid shows through at every width.

Run it again whenever banner.jpg changes:

    uv run --no-project --with pillow --with numpy --with scipy \
        python scripts/banner-cutout.py docs/assets/images/banner.jpg docs/assets/images/banner.webp

Colour-to-alpha against white, then everything faint (the background and its grey hexagon
lines) made fully transparent, with a short ramp so edges stay soft. White parts *inside*
the artwork (the vaquita's belly and eye, the check marks) are filled back in, so the grid
doesn't show through them; the lettering below the artwork is left alone, so the counters
of D and O stay open.
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

src, out = sys.argv[1:3]
rgb = np.asarray(Image.open(src).convert("RGB")).astype(np.float64) / 255.0
h, w, _ = rgb.shape

# Colour to alpha against white: the least alpha that explains the pixel over white.
alpha = (1.0 - rgb).max(axis=2)
# The background is near-white with light grey hexagon lines: alpha up to ~0.15 there.
low, high = 0.16, 0.30
a = np.clip((alpha - low) / (high - low), 0.0, 1.0)

# Un-blend the colour from white for the alpha we keep.
safe = np.where(alpha > 1e-6, alpha, 1.0)[..., None]
colour = np.clip((rgb - (1.0 - alpha[..., None])) / safe, 0.0, 1.0)
colour = np.where(alpha[..., None] > 1e-6, colour, rgb)

# White inside the artwork: fill the holes of the solid shape, above the lettering only.
solid = a > 0.5
filled = ndimage.binary_fill_holes(solid)
holes = filled & ~solid
lettering_top = int(h * 0.72)
holes[lettering_top:, :] = False
# Only real holes (a few pixels and up), not specks.
labels, n = ndimage.label(holes)
sizes = ndimage.sum(holes, labels, range(1, n + 1))
keep = np.isin(labels, 1 + np.flatnonzero(sizes >= 30))
a = np.where(keep, 1.0, a)
colour = np.where(keep[..., None], rgb, colour)

# Inside the artwork's outline, light pixels are artwork too (the cube's top face, for one),
# not background: opaque, in their own colour. Only a 2-pixel outer edge keeps its soft alpha.
inside = ndimage.binary_erosion(ndimage.binary_fill_holes(a > 0.5), iterations=2)
inside[lettering_top:, :] = False
a = np.where(inside, 1.0, a)
colour = np.where(inside[..., None], rgb, colour)

rgba = np.dstack([colour, a])
img = Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), "RGBA")
img.save(out, quality=90, method=6)
print(f"{w}x{h}, holes filled: {int(keep.sum())} px in {int((sizes >= 30).sum())} regions")
