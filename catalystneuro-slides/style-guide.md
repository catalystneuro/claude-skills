# CatalystNeuro Presentation Style Guide

## Brand Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| CN Navy | `#021242` | (2, 18, 66) | Primary headings, dark backgrounds, emphasis text |
| CN Blue | `#0765A5` | (7, 101, 165) | Subheadings, accents, "NEURO" brand element |
| CN Light Blue | `#5E9BC4` | (94, 155, 196) | Secondary accents, highlights, hover states |
| White | `#FFFFFF` | (255, 255, 255) | Backgrounds, text on dark surfaces |
| Light Gray | `#F0F2F6` | (240, 242, 246) | Subtle backgrounds, card fills |
| Medium Gray | `#6F7894` | (111, 120, 148) | Body text, captions, secondary info |

## Typography

- **Headings**: Calibri Bold (or system sans-serif), ALL CAPS for slide titles
- **Subheadings**: Calibri, sentence case
- **Body text**: Calibri, 18-20pt minimum for readability
- **Title slides**: 36-44pt titles, 20-24pt subtitles

## Logo Usage

- **Light backgrounds**: Use `logo_horizontal_light.png` (navy + blue on transparent)
- **Dark backgrounds**: Use `logo_horizontal_dark.png` (gray/silver on transparent)
- **Square contexts**: Use `logo_square.png` for small placements
- Logo should appear on the title slide (prominent) and optionally in footer of content slides
- Minimum clear space around logo: equivalent to the height of the "N" in NEURO

## Slide Layouts

### 1. Title Slide
- CN Navy background with subtle gradient or white background with navy accent bar
- Logo centered or top-left
- Title in large bold text
- Subtitle / presenter name below

### 2. Section Divider
- CN Navy full background
- Large white text for section name
- Optional CN Blue accent line

### 3. Content Slide (Bullets)
- White background
- CN Navy title bar or top accent stripe
- Bullet points in dark gray/navy
- CN Blue for bullet markers or emphasis

### 4. Two-Column Layout
- White background
- Left/right split with optional CN Light Blue divider
- Good for text + image or comparison layouts

### 5. Closing Slide
- CN Navy background
- Logo centered
- Contact info / thank you message in white

## Footer Styling

- **Height**: 0.44 inches, flush to the bottom of the slide
- **Background**: `#DCE1EB` (light silver-blue) — keeps the footer visible but unobtrusive
- **Text color**: `#1F497D` (dark blue), 12pt Calibri bold
- **Logo**: `logo_horizontal_transparent.png` at left (1.2 inches wide, vertically centered)
- **Layout**: Logo | Presenter name | Presentation title (center) | Section name (right)
- Footer appears on content slides, divider slides, and closing slides (not the title slide)

## Greg Dunn Art Backgrounds (Optional)

Neuroscience artwork by Greg Dunn (gregadunn.com) can optionally be used as backgrounds on title, section divider, and closing slides. The default style is minimalist (clean white/gray backgrounds). Art backgrounds give presentations a distinctive scientific aesthetic when desired.

### Image Pool

| Title | Year | URL |
|-------|------|-----|
| Cortical Columns | 2021 | `https://www.gregadunn.com/wp-content/uploads/2021/07/36-x-48-cortical-columns-esque-full-painting-1200-lines.jpg` |
| Neurogenesis I | 2018 | `https://www.gregadunn.com/wp-content/uploads/2018/09/Neurogenesis-I-final.jpg` |
| Hippocampus II | 2012 | `https://www.gregadunn.com/wp-content/uploads/2012/05/hippocampus-II-small.jpg` |
| NG2 Flare | 2012 | `https://www.gregadunn.com/wp-content/uploads/2012/05/NG2-flare.jpg` |
| Two Pyramidals | 2012 | `https://www.gregadunn.com/wp-content/uploads/2012/05/Two-Pyramidals-16-X-20.jpg` |
| Beyond the Horizon | 2012 | `https://www.gregadunn.com/wp-content/uploads/2012/05/Beyond-the-Horizon.jpg` |
| Brainbow Hippocampus | 2016 | `https://www.gregadunn.com/wp-content/uploads/2016/03/Brainbow-Hippocampus-blue-and-gold.jpg` |
| Myelination | 2023 | `https://www.gregadunn.com/wp-content/uploads/2024/02/myelination-ink-painting-2023.jpg` |
| Cortical Circuitboard | 2019 | `https://www.gregadunn.com/wp-content/uploads/2019/06/Cortical-Circuitboard-purple-2023.jpg` |
| Retina in Inks | 2016 | `https://www.gregadunn.com/wp-content/uploads/2016/10/retina-in-inks-1.jpg` |

### Licensing & Attribution

- **Required**: Every slide using Greg Dunn art must include attribution text
- **Format**: `Art: [Title], [Year], Greg Dunn | gregadunn.com`
- **Placement**: Bottom-left corner, 12pt Calibri, dark gray color `(80, 80, 95)`
- **Website**: gregadunn.com

### Overlay Treatment

Art images are placed as full-slide backgrounds with semi-transparent overlays for readability:

| Slide Type | Overlay Color | Overlay Alpha | Text Backing Alpha |
|------------|--------------|---------------|-------------------|
| Title slide | White | 60% | 45% |
| Section divider | White | 55% | 40% |
| Closing slide | White | 60% | 45% |

- **Overlay**: A full-slide rectangle in white with the specified alpha, placed on top of the art image — keeps the art visible while providing a light base for dark text
- **Text backing**: Additional semi-transparent white rectangles behind text blocks for extra readability
- **Text colors on art slides**: CN Navy for titles, CN Blue for subtitles/labels, Black for names, Medium Gray for secondary info
- **Implementation**: Uses lxml to set `a:alpha` on `a:srgbClr` elements (python-pptx doesn't natively support fill alpha)

### Which Slides Can Get Art

When art backgrounds are enabled, apply them to:
- **Title slide** — sets the visual tone
- **Section dividers** — marks transitions between sections
- **Closing slide** — bookends the presentation
- **Content slides** — never; keep clean white backgrounds for readability

## Design Principles

1. **Clean and professional**: Generous white space, no clutter
2. **Consistent accent usage**: CN Blue for emphasis, CN Navy for structure
3. **Readable**: High contrast, minimum 18pt body text
4. **Scientific credibility**: Clean data presentation, proper figure labels
5. **Brand presence**: Logo on title and closing slides at minimum
6. **Art with purpose**: Greg Dunn neuroscience art reinforces scientific identity while maintaining readability through overlays
