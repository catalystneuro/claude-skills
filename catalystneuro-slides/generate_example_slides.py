"""Generate CatalystNeuro branded PowerPoint slides.

Style inspired by existing CatalystNeuro presentations:
- Clean white backgrounds, minimal decoration
- Bold navy/black titles, simple dash bullets
- Small logo in bottom-right of content slides
- Subtle footer with presenter info
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import os

# --- Brand Colors ---
CN_NAVY = RGBColor(2, 18, 66)          # #021242
CN_BLUE = RGBColor(7, 101, 165)        # #0765A5
CN_LIGHT_BLUE = RGBColor(94, 155, 196) # #5E9BC4
WHITE = RGBColor(255, 255, 255)
LIGHT_GRAY = RGBColor(245, 246, 248)
MEDIUM_GRAY = RGBColor(150, 150, 160)
BODY_TEXT = RGBColor(50, 50, 55)
BLACK = RGBColor(0, 0, 0)

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
LOGO_HORIZONTAL = os.path.join(ASSETS_DIR, "logo_horizontal_light.png")
LOGO_SQUARE = os.path.join(ASSETS_DIR, "logo_square.png")

# Presentation metadata
PRESENTER = "Benjamin Dichter"
PRES_TITLE = "NWB Data Conversion & DANDI Publishing"


def set_slide_bg(slide, color):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_text(slide, left, top, width, height, text, font_size=18,
             font_color=BODY_TEXT, bold=False, alignment=PP_ALIGN.LEFT,
             font_name="Calibri"):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = font_color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    return txBox


def add_bullets(slide, left, top, width, bullets, font_size=20,
                font_color=BODY_TEXT, spacing=0.65):
    """Add a bulleted list using dash markers, matching the reference style."""
    txBox = slide.shapes.add_textbox(left, top, width, Inches(len(bullets) * spacing + 0.5))
    tf = txBox.text_frame
    tf.word_wrap = True

    for i, bullet in enumerate(bullets):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = f"-   {bullet}"
        p.font.size = Pt(font_size)
        p.font.color.rgb = font_color
        p.font.name = "Calibri"
        p.space_before = Pt(12)
        p.space_after = Pt(4)

    return txBox


def add_footer(slide, section=""):
    """Dark footer bar flush to bottom with logo, presenter, title, section."""
    bar_height = Inches(0.55)
    bar_top = SLIDE_HEIGHT - bar_height

    # Dark background bar
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), bar_top, SLIDE_WIDTH, bar_height
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = CN_NAVY
    bar.line.fill.background()

    text_y = bar_top + Inches(0.08)
    footer_white = RGBColor(220, 225, 235)

    # Small square logo (left)
    slide.shapes.add_picture(
        LOGO_SQUARE, Inches(0.4), bar_top + Inches(0.05), Inches(0.45)
    )

    # Presenter name
    add_text(
        slide, Inches(1.0), text_y, Inches(3), Inches(0.4),
        PRESENTER, font_size=12, font_color=footer_white
    )

    # Presentation title (center)
    add_text(
        slide, Inches(4), text_y, Inches(5.3), Inches(0.4),
        PRES_TITLE, font_size=12, font_color=footer_white,
        alignment=PP_ALIGN.CENTER
    )

    # Section (right)
    if section:
        add_text(
            slide, Inches(9.5), text_y, Inches(3.5), Inches(0.4),
            section, font_size=12, font_color=footer_white,
            alignment=PP_ALIGN.RIGHT
        )


# ── Slide 1: Title ──────────────────────────────────────────────────────────

def make_title_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)

    # Title (large, bold, left-aligned)
    add_text(
        slide, Inches(0.8), Inches(0.6), Inches(7.5), Inches(2.5),
        "NWB Data Conversion\n& DANDI Publishing",
        font_size=48, font_color=CN_NAVY, bold=True
    )

    # Subtitle
    add_text(
        slide, Inches(0.8), Inches(3.5), Inches(7), Inches(0.8),
        "Standardizing Neurophysiology Data for Open Science",
        font_size=24, font_color=MEDIUM_GRAY
    )

    # Presenter info
    add_text(
        slide, Inches(0.8), Inches(5.0), Inches(5), Inches(0.8),
        "Ben Dichter",
        font_size=28, font_color=BLACK
    )
    add_text(
        slide, Inches(0.8), Inches(5.6), Inches(5), Inches(0.5),
        "Founder, CatalystNeuro",
        font_size=20, font_color=MEDIUM_GRAY
    )

    # Square logo (vertically centered, right side)
    slide.shapes.add_picture(
        LOGO_SQUARE, Inches(9.5), Inches(2.0), Inches(3.0)
    )


# ── Slide 2: Section Divider ────────────────────────────────────────────────

def make_section_divider(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, LIGHT_GRAY)

    # Section label (small)
    add_text(
        slide, Inches(0.8), Inches(2.2), Inches(6), Inches(0.6),
        "The Challenge", font_size=20, font_color=MEDIUM_GRAY
    )

    # Topic title (large)
    add_text(
        slide, Inches(0.8), Inches(3.0), Inches(10), Inches(1.8),
        "Why neurophysiology data\nneeds standardization",
        font_size=42, font_color=CN_NAVY, bold=True
    )

    add_footer(slide, section="The Challenge")


# ── Slide 3: Content (Bullet Points) ────────────────────────────────────────

def make_content_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)

    # Title (bold, top)
    add_text(
        slide, Inches(0.6), Inches(0.4), Inches(11), Inches(1.0),
        "Need for neurophysiology data standard",
        font_size=36, font_color=BLACK, bold=True
    )

    # Bullets
    add_bullets(slide, Inches(0.8), Inches(1.5), Inches(10), [
        "Data are expensive to collect (money, time, animal use)",
        "Sharing neurophysiology data within a lab and with collaborators is tedious",
        "Sharing scientific software is also difficult",
        "It is often easier to just collect new data and build new tools",
        "Difficult for labs to devote time and effort to sharing data and software",
    ], font_size=22, spacing=0.75)

    add_footer(slide, section="The Challenge")


# ── Slide 4: Two-Column Layout ──────────────────────────────────────────────

def make_two_column_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)

    # Title
    add_text(
        slide, Inches(0.6), Inches(0.4), Inches(11), Inches(1.0),
        "Our Approach",
        font_size=36, font_color=BLACK, bold=True
    )

    # Left column header
    add_text(
        slide, Inches(0.8), Inches(1.6), Inches(5), Inches(0.6),
        "NWB Conversion", font_size=26, font_color=CN_BLUE, bold=True
    )
    add_bullets(slide, Inches(1.0), Inches(2.3), Inches(5), [
        "Automated pipeline from 40+ formats",
        "Full metadata preservation",
        "Validation against NWB schema",
        "Handles multi-modal recordings",
    ], font_size=20, spacing=0.65)

    # Right column header
    add_text(
        slide, Inches(7.0), Inches(1.6), Inches(5), Inches(0.6),
        "DANDI Publishing", font_size=26, font_color=CN_BLUE, bold=True
    )
    add_bullets(slide, Inches(7.2), Inches(2.3), Inches(5), [
        "Upload to DANDI Archive",
        "DOI minting for citation",
        "BIDS-compatible organization",
        "Streaming access via LINDI",
    ], font_size=20, spacing=0.65)

    add_footer(slide, section="Our Approach")


# ── Slide 5: Closing ────────────────────────────────────────────────────────

def make_closing_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)

    # Horizontal logo centered
    slide.shapes.add_picture(
        LOGO_HORIZONTAL, Inches(3.8), Inches(1.5), Inches(5.5)
    )

    # Thank you
    add_text(
        slide, Inches(1), Inches(3.8), Inches(11.3), Inches(1.0),
        "Thank You",
        font_size=42, font_color=CN_NAVY, bold=True,
        alignment=PP_ALIGN.CENTER
    )

    # Contact info
    add_text(
        slide, Inches(1), Inches(5.0), Inches(11.3), Inches(0.5),
        "ben.dichter@catalystneuro.com",
        font_size=20, font_color=CN_BLUE,
        alignment=PP_ALIGN.CENTER
    )
    add_text(
        slide, Inches(1), Inches(5.5), Inches(11.3), Inches(0.5),
        "www.catalystneuro.com  |  github.com/catalystneuro",
        font_size=18, font_color=MEDIUM_GRAY,
        alignment=PP_ALIGN.CENTER
    )

    add_footer(slide)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    make_title_slide(prs)
    make_section_divider(prs)
    make_content_slide(prs)
    make_two_column_slide(prs)
    make_closing_slide(prs)

    output_path = os.path.join(os.path.dirname(__file__), "example_slides.pptx")
    prs.save(output_path)
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
