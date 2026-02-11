---
name: catalystneuro-slides
description: >
  Use this skill when creating professional CatalystNeuro-branded PowerPoint
  presentations for scientific talks, lab meetings, conferences, and workshops.
  Generates branded slides with consistent styling, Greg Dunn neuroscience art
  backgrounds, and proper attribution. Use python-pptx to build presentations
  programmatically.
---

<objective>
Help users create polished, on-brand CatalystNeuro PowerPoint presentations using python-pptx.
Presentations feature consistent brand colors, typography, Greg Dunn neuroscience art backgrounds
on key slides, and proper footer styling.
</objective>

<core_concepts>

## Brand Identity

CatalystNeuro presentations use a navy/blue color palette with Calibri typography:

| Color | Hex | Usage |
|-------|-----|-------|
| CN Navy | `#021242` | Primary headings, overlays, emphasis |
| CN Blue | `#0765A5` | Subheadings, accents, links |
| CN Light Blue | `#5E9BC4` | Secondary accents, highlights |
| Footer BG | `#DCE1EB` | Footer background (light silver-blue) |
| Footer Text | `#1F497D` | Footer text (dark blue) |

**Typography**: Calibri throughout. Titles 36-48pt bold, body 18-22pt, footer 12pt.

## Slide Types

1. **Title slide** — White background, presenter info, logo
2. **Section divider** — Light gray background, section label + large title, footer
3. **Content slide** — White background, title + bullets, footer
4. **Two-column slide** — White background, side-by-side content, footer
5. **Closing slide** — White background, logo, thank you, contact info, footer

## Greg Dunn Art (Optional)

Neuroscience artwork from gregadunn.com can optionally be added to title, divider, and
closing slides. The default style is minimalist. When art is enabled, images are downloaded
at runtime and placed as full-slide backgrounds with semi-transparent white overlays
(55-60% alpha). Text gets additional white backing rectangles for readability.
Helper functions (`add_art_background`, `add_text_backing`, `add_art_attribution`) are
available in `generate_example_slides.py`.

**Attribution is required** on every slide using art:
`Art: [Title], [Year], Greg Dunn | gregadunn.com` — 8pt, bottom-left corner.

</core_concepts>

<routing>

## Reference Files

| Need | File |
|------|------|
| Full style guide (colors, typography, layouts, art pool, footer specs) | `./style-guide.md` |
| Working example with all slide types and helper functions | `./generate_example_slides.py` |
| Logo assets | `./assets/` directory |

Read `./style-guide.md` for the complete image pool URLs, overlay alpha values, and design rules.
Read `./generate_example_slides.py` for working python-pptx code for every slide type and helper function.

</routing>

<important_patterns>

## Creating a Presentation

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
import urllib.request, tempfile, os

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
```

## Adding Art Backgrounds

Download art, place as full-slide image, add semi-transparent overlay:
```python
def download_image(url):
    suffix = os.path.splitext(url.split("?")[0])[-1] or ".jpg"
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    urllib.request.urlretrieve(url, path)
    return path

# On a slide:
img_path = download_image(art_url)
slide.shapes.add_picture(img_path, Emu(0), Emu(0), SLIDE_WIDTH, SLIDE_HEIGHT)

# Semi-transparent overlay
overlay = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(0), Emu(0), SLIDE_WIDTH, SLIDE_HEIGHT)
overlay.fill.solid()
overlay.fill.fore_color.rgb = RGBColor(255, 255, 255)  # White
overlay.line.fill.background()
# Set alpha via lxml (python-pptx lacks native alpha support)
srgb = overlay.fill._fill._solidFill.find(qn("a:srgbClr"))
alpha_elem = srgb.makeelement(qn("a:alpha"), {"val": "60000"})  # 60%
srgb.append(alpha_elem)
```

## Footer Pattern

Light silver-blue bar at bottom, horizontal transparent logo, dark blue text:
```python
bar_height = Inches(0.44)
bar_top = Inches(7.5) - bar_height
bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), bar_top, Inches(13.333), bar_height)
bar.fill.solid()
bar.fill.fore_color.rgb = RGBColor(220, 225, 235)  # #DCE1EB
bar.line.fill.background()
# Add logo_horizontal_transparent.png, presenter name, title, section
```

## Licensing Constraints

- Greg Dunn art images are copyrighted — use only images from the approved pool in the style guide
- Every slide using art **must** have attribution text
- Do not crop, filter, or modify the art beyond the overlay treatment
- Art is for CatalystNeuro internal/conference presentations only

</important_patterns>
