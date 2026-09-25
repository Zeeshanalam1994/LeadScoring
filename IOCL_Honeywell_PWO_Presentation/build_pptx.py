#!/usr/bin/env python3
"""Build full executive PowerPoint deck for IOCL / Honeywell PWO."""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Brand colors
IOCL_BLUE = RGBColor(0, 61, 165)
IOCL_ORANGE = RGBColor(244, 121, 32)
HONEY_RED = RGBColor(230, 0, 40)
DARK_NAVY = RGBColor(15, 39, 68)
DARK_BG = RGBColor(26, 26, 46)
WHITE = RGBColor(255, 255, 255)
MUTED = RGBColor(100, 116, 139)
SUCCESS = RGBColor(0, 200, 150)
DANGER = RGBColor(255, 71, 87)
LIGHT_BG = RGBColor(248, 250, 252)
TITLE_DARK = RGBColor(30, 41, 59)

W = Inches(13.333)
H = Inches(7.5)


def blank_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def fill_bg(slide, color):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()
    # send to back
    spTree = slide.shapes._spTree
    sp = bg._element
    spTree.remove(sp)
    spTree.insert(2, sp)


def add_textbox(slide, left, top, width, height, text="", size=18, bold=False, color=TITLE_DARK, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.alignment = align
    return tf


def add_bullets(slide, left, top, width, height, items, size=16, color=TITLE_DARK, spacing=Pt(8)):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = item
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.level = 0
        p.space_after = spacing
    return tf


def slide_title(slide, title, subtitle=None, dark=False):
    tc = WHITE if dark else IOCL_BLUE
    add_textbox(slide, Inches(0.55), Inches(0.35), Inches(12), Inches(0.9), title, 32, True, tc)
    if subtitle:
        add_textbox(slide, Inches(0.55), Inches(1.05), Inches(12), Inches(0.5), subtitle, 14, False, MUTED if not dark else RGBColor(180, 190, 200))
    # accent line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.55), Inches(1.45 if subtitle else 1.15), Inches(1.2), Inches(0.06))
    line.fill.solid()
    line.fill.fore_color.rgb = IOCL_ORANGE
    line.line.fill.background()


def add_card(slide, left, top, width, height, title, body, border=DANGER, bg=RGBColor(255, 240, 242)):
    rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    rect.fill.solid()
    rect.fill.fore_color.rgb = bg
    rect.line.color.rgb = border
    rect.line.width = Pt(1.5)
    tf = rect.text_frame
    tf.margin_left = Inches(0.15)
    tf.margin_top = Inches(0.12)
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = border
    p2 = tf.add_paragraph()
    p2.text = body
    p2.font.size = Pt(12)
    p2.font.color.rgb = TITLE_DARK
    p2.space_before = Pt(6)


def add_table(slide, left, top, width, rows, col_widths=None):
    """rows: list of lists, first row is header."""
    nrows = len(rows)
    ncols = len(rows[0])
    shape = slide.shapes.add_table(nrows, ncols, left, top, width, Inches(0.35 * nrows))
    table = shape.table
    if col_widths:
        for i, w in enumerate(col_widths):
            table.columns[i].width = w
    for r, row in enumerate(rows):
        for c, cell_text in enumerate(row):
            cell = table.cell(r, c)
            cell.text = str(cell_text)
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(11 if r else 12)
                p.font.bold = r == 0
                if r == 0:
                    p.font.color.rgb = WHITE
                else:
                    p.font.color.rgb = TITLE_DARK
            if r == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = IOCL_BLUE
    return table


def progress_bar(slide, left, top, width, label, pct, bar_color, track=RGBColor(220, 220, 225)):
    add_textbox(slide, left, top, width, Inches(0.35), label, 13, True, TITLE_DARK)
    track_y = top + Inches(0.38)
    track_h = Inches(0.28)
    t = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, track_y, width, track_h)
    t.fill.solid()
    t.fill.fore_color.rgb = track
    t.line.fill.background()
    fill_w = width * pct // 100
    if fill_w > 0:
        f = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, track_y, fill_w, track_h)
        f.fill.solid()
        f.fill.fore_color.rgb = bar_color
        f.line.fill.background()
    add_textbox(slide, left + width - Inches(0.5), track_y - Inches(0.05), Inches(0.5), Inches(0.3), f"{pct}%", 12, True, TITLE_DARK, PP_ALIGN.RIGHT)


def arch_box(slide, left, top, width, height, title, sub="", fill=IOCL_BLUE, font_size=11):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    sh.line.color.rgb = RGBColor(200, 200, 210)
    tf = sh.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(font_size)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER
    if sub:
        p2 = tf.add_paragraph()
        p2.text = sub
        p2.font.size = Pt(9)
        p2.font.color.rgb = RGBColor(220, 230, 240)
        p2.alignment = PP_ALIGN.CENTER


def connector_arrow(slide, x1, y1, x2, y2):
    conn = slide.shapes.add_connector(1, x1, y1, x2, y2)  # straight
    conn.line.color.rgb = IOCL_ORANGE
    conn.line.width = Pt(2)


def build():
    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H

    # --- 1 Title ---
    s = blank_slide(prs)
    fill_bg(s, DARK_NAVY)
    add_textbox(s, Inches(0.8), Inches(0.6), Inches(4), Inches(0.4), "EXECUTIVE BRIEFING · CONFIDENTIAL", 10, True, IOCL_ORANGE)
    add_textbox(s, Inches(0.8), Inches(1.4), Inches(11.5), Inches(1.8),
                "From Local RTO Silos to\nPlantwide Dynamic Optimization", 40, True, WHITE)
    add_textbox(s, Inches(0.8), Inches(3.3), Inches(11), Inches(0.8),
                "Why Honeywell PWO + HPDT belong in every IOCL Honeywell Template", 20, False, RGBColor(180, 195, 210))
    add_textbox(s, Inches(0.8), Inches(4.5), Inches(11), Inches(0.5), "INDIAN OIL  ×  HONEYWELL FORGE", 22, True, WHITE)
    add_textbox(s, Inches(0.8), Inches(5.1), Inches(11), Inches(0.4), "Refining & Petrochemicals · Digital Optimization Strategy", 12, False, MUTED)

    # --- 2 Agenda ---
    s = blank_slide(prs)
    fill_bg(s, LIGHT_BG)
    slide_title(s, "What we will cover")
    add_bullets(s, Inches(0.55), Inches(1.7), Inches(6.5), Inches(5),
                [
                    "The profit gap between planning and the control room",
                    "Why unit-local RTO under-delivers at IOCL scale",
                    "Honeywell Plantwide Optimizer — Dynamic RTO architecture",
                    "Honeywell Process Digital Twin (HPDT) — model integrity",
                    "Template standard: end-to-end optimization stack",
                    "Investment logic & recommended path for IOCL",
                ], 15)
    add_card(s, Inches(7.5), Inches(2), Inches(5), Inches(1.5), "90%",
             "Of refinery time is NOT steady state — legacy RTO optimizes as if it were.",
             IOCL_ORANGE, RGBColor(255, 248, 240))
    add_card(s, Inches(7.5), Inches(3.8), Inches(5), Inches(1.5), "1 → n",
             "PWO coordinates the whole site through one dynamic optimization layer.",
             IOCL_BLUE, RGBColor(235, 242, 255))

    # --- 3 Challenge ---
    s = blank_slide(prs)
    fill_bg(s, LIGHT_BG)
    slide_title(s, "IOCL's optimization challenge is enterprise-scale",
                "Multiple refineries · molecule management · volatile margins · sustainability")
    pills = "LP / PIMS (hours–days)   →   GAP   →   Unit APC (minutes)   |   Local RTO (2–4 hr)"
    add_textbox(s, Inches(0.55), Inches(1.65), Inches(12), Inches(0.4), pills, 12, False, TITLE_DARK)
    arch_box(s, Inches(0.6), Inches(2.3), Inches(2.2), Inches(1.1), "Business LP", "Weekly plan", IOCL_BLUE)
    arch_box(s, Inches(3.3), Inches(2.1), Inches(2.6), Inches(1.5), "Disconnected", "Local RTO islands\nDuplicate models", DANGER)
    arch_box(s, Inches(6.8), Inches(2.3), Inches(2.2), Inches(1.1), "DCS / APC", "Real time", RGBColor(51, 65, 85))
    connector_arrow(s, Inches(2.8), Inches(2.85), Inches(3.3), Inches(2.85))
    connector_arrow(s, Inches(5.9), Inches(2.85), Inches(6.8), Inches(2.85))
    add_textbox(s, Inches(0.55), Inches(4.2), Inches(12), Inches(0.6),
                "Result: quality giveaway, off-spec during moves, planner vs operator mismatch", 14, True, IOCL_ORANGE, PP_ALIGN.CENTER)

    # --- 4 Traditional RTO ---
    s = blank_slide(prs)
    fill_bg(s, LIGHT_BG)
    slide_title(s, "Traditional steady-state RTO — how it was built to work")
    add_bullets(s, Inches(0.55), Inches(1.75), Inches(6.2), Inches(4.5), [
        "Large first-principles or rigorous simulation model per unit",
        "Solve economic optimum assuming steady state",
        "Execute every 2–4 hours; push setpoints / bounds to MPC",
        "Separate model team, APC team, and planner",
    ], 16)
    add_card(s, Inches(7.2), Inches(2.2), Inches(5.5), Inches(2.2),
             "Designed for the 1990s operating model",
             "Plants ran longer on stable feeds; optimization was a periodic advisory layer — not continuous profit execution.",
             DANGER)

    # --- 5 Local RTO ---
    s = blank_slide(prs)
    fill_bg(s, RGBColor(35, 20, 28))
    slide_title(s, "Unit-local RTO at IOCL: diminishing returns", dark=True)
    add_table(s, Inches(0.5), Inches(1.75), Inches(12.3), [
        ["Typical local RTO reality", "Business impact"],
        ["Duplicate models (RTO + APC + LP)", "3× engineering & maintenance cost"],
        ["Optimizes one unit, ignores site balances", "FCC vs hydrocracker vs blend conflicts"],
        ["Inactive during transients & grade changes", "Off-spec on ~90% of operating time"],
        ["18–24 month projects", "Benefits erode before payback"],
        ["Often OFF in operations", "Sunk CAPEX, no sustained margin lift"],
    ], [Inches(6.2), Inches(6.1)])
    add_textbox(s, Inches(0.55), Inches(5.5), Inches(12), Inches(0.8),
                "Executive view: Another local RTO without plantwide coordination is optimization SPEND, not optimization STRATEGY.",
                14, True, IOCL_ORANGE)

    # --- 6 TCO ---
    s = blank_slide(prs)
    fill_bg(s, LIGHT_BG)
    slide_title(s, "Total cost of ownership: local RTO vs PWO stack",
                "Illustrative index — traditional per-unit RTO normalized to 100")
    progress_bar(s, Inches(0.7), Inches(2.2), Inches(5.5), "Traditional local RTO (per major unit)", 100, DANGER)
    add_bullets(s, Inches(0.7), Inches(3.1), Inches(5.5), Inches(2), [
        "Rigorous model build & validation",
        "Ongoing mismatch with APC",
        "Limited cross-unit coordination",
    ], 12)
    progress_bar(s, Inches(7), Inches(2.2), Inches(5.5), "PWO dynamic layer (site scope)", 35, SUCCESS)
    add_bullets(s, Inches(7), Inches(3.1), Inches(5.5), Inches(2), [
        "Reuses APC dynamics & planning yields",
        "Proxy limits — no duplicate constraints",
        "One optimization narrative for operations",
    ], 12)
    add_textbox(s, Inches(0.55), Inches(5.2), Inches(12), Inches(0.9),
                "Honeywell evidence: dynamic optimization delivers traditional RTO economics with dramatically lower modeling effort.",
                13, False, TITLE_DARK)

    # --- 7 PWO Hero ---
    s = blank_slide(prs)
    fill_bg(s, HONEY_RED)
    add_textbox(s, Inches(0.8), Inches(0.8), Inches(11), Inches(0.5),
                "Hydrocarbon Processing 2022 — Best Automation Technology", 11, True, WHITE)
    add_textbox(s, Inches(0.8), Inches(1.6), Inches(11.5), Inches(1.2), "Honeywell Plantwide Optimizer", 44, True, WHITE)
    add_textbox(s, Inches(0.8), Inches(2.9), Inches(11), Inches(1),
                "Dynamic Real-Time Optimization — a different control architecture, not a bigger steady-state model",
                18, False, RGBColor(255, 230, 230))
    for i, pill in enumerate(["Runs ~every minute", "Dynamic models", "Planning-aligned economics", "Proxy limits"]):
        arch_box(s, Inches(0.8 + i * 3.05), Inches(4.5), Inches(2.85), Inches(0.65), pill, "",
                 RGBColor(180, 0, 30))

    # --- 8 Architecture ---
    s = blank_slide(prs)
    fill_bg(s, LIGHT_BG)
    slide_title(s, "PWO architecture: 1 primary MPC → n unit APCs")
    arch_box(s, Inches(0.5), Inches(1.9), Inches(2), Inches(0.75), "LP / PIMS", "Economics & yields", IOCL_BLUE, 10)
    arch_box(s, Inches(3.8), Inches(1.75), Inches(5.7), Inches(0.95), "PLANTWIDE OPTIMIZER (Dynamic RTO)",
             "Planning yields · site balances · inventories · quality", HONEY_RED, 12)
    connector_arrow(s, Inches(2.5), Inches(2.1), Inches(3.8), Inches(2.1))
    for i, (t, st) in enumerate([("CDU / VDU APC", "Proxy limits"), ("FCC / Coker APC", "Proxy limits"), ("Hydro / Reforming", "Proxy limits")]):
        arch_box(s, Inches(0.8 + i * 4.1), Inches(3.3), Inches(3.5), Inches(0.9), t, st, RGBColor(51, 65, 85), 10)
        connector_arrow(s, Inches(6.65), Inches(2.7), Inches(2.05 + i * 4.1), Inches(3.3))
    arch_box(s, Inches(2.5), Inches(4.6), Inches(8.3), Inches(0.75), "DCS · Blend Optimizer · Analyzers", "", RGBColor(71, 85, 105), 12)
    add_textbox(s, Inches(0.55), Inches(5.6), Inches(12), Inches(0.7),
                "PWO inherits the planner's structure; APC retains constraint fidelity — no need to replicate every valve at site level.",
                12, False, TITLE_DARK)

    # --- 9 VS ---
    s = blank_slide(prs)
    fill_bg(s, LIGHT_BG)
    slide_title(s, "Dynamic RTO vs traditional RTO")
    add_card(s, Inches(0.5), Inches(1.85), Inches(5.5), Inches(3.2), "Traditional RTO", "", DANGER, RGBColor(255, 245, 245))
    add_bullets(s, Inches(0.7), Inches(2.35), Inches(5), Inches(2.5), [
        "Wait for steady state",
        "2–4 hour execution cycle",
        "Steady-state simulation core",
        "Per-unit scope",
        "Heavy model maintenance",
    ], 14)
    add_textbox(s, Inches(6.2), Inches(3), Inches(0.8), Inches(0.6), "VS", 28, True, MUTED, PP_ALIGN.CENTER)
    add_card(s, Inches(7), Inches(1.85), Inches(5.8), Inches(3.2), "PWO Dynamic RTO", "", SUCCESS, RGBColor(230, 255, 248))
    add_bullets(s, Inches(7.2), Inches(2.35), Inches(5.3), Inches(2.5), [
        "Optimize during moves & disturbances",
        "~1 minute coordination cycle",
        "Leverages live APC dynamic models",
        "Full site / train scope",
        "Gain matrix from plan + history",
    ], 14)
    add_textbox(s, Inches(0.55), Inches(5.3), Inches(12), Inches(0.6),
                "~50% reduction in off-spec during transients (literature & Honeywell deployments)", 13, True, IOCL_BLUE)

    # --- 10 Proxy limits ---
    s = blank_slide(prs)
    fill_bg(s, LIGHT_BG)
    slide_title(s, "Patented proxy limits — feasibility without model bloat")
    add_bullets(s, Inches(0.55), Inches(1.75), Inches(6.5), Inches(4.5), [
        "APC calculates feasible envelope on demand",
        "PWO sees aggregated limits — not thousands of inner constraints",
        "APC model updates automatically flow to optimization",
        "Smaller problem → faster solve → operator-trusted moves",
    ], 16)
    # hub diagram
    arch_box(s, Inches(9.2), Inches(2.8), Inches(2.2), Inches(1.2), "PWO", "Site objective", IOCL_BLUE, 14)
    for dx, dy in [(9.9, 1.9), (8.2, 4.5), (10.6, 4.5)]:
        c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(dx), Inches(dy), Inches(0.9), Inches(0.9))
        c.fill.solid()
        c.fill.fore_color.rgb = RGBColor(200, 255, 235)
        c.line.color.rgb = SUCCESS
        c.text_frame.text = "APC"
        c.text_frame.paragraphs[0].font.size = Pt(10)
        c.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    # --- 11 HPDT ---
    s = blank_slide(prs)
    fill_bg(s, DARK_NAVY)
    slide_title(s, "Honeywell Process Digital Twin (HPDT)",
                "Keeps planning, optimization, and reality aligned", dark=True)
    add_bullets(s, Inches(0.55), Inches(1.85), Inches(6.8), Inches(4.5), [
        "Online simulation & scenarios tied to live plant data",
        "Validates yield vectors before they enter PWO",
        "Supports APC lifecycle (what-if, debottleneck, training)",
        "Closes the loop: LP assumptions ↔ actual unit capability",
    ], 16, RGBColor(230, 235, 245))
    add_card(s, Inches(7.5), Inches(2.3), Inches(5.2), Inches(2.8), "HPDT + PWO",
             "Digital twin = trusted model estate\nPWO = continuous profit execution\nTogether: replace ad-hoc RTO rebuilds every turnaround.",
             SUCCESS, RGBColor(20, 50, 70))

    # --- 12 Template ---
    s = blank_slide(prs)
    fill_bg(s, LIGHT_BG)
    slide_title(s, "Must-have in the Honeywell Template for IOCL", "Standardize the full stack — not à la carte APC projects")
    phases = ["Experion/DCS", "Forge APC", "PWO", "HPDT", "Blend Opt", "CPA-U"]
    for i, ph in enumerate(phases):
        x = Inches(0.5 + i * 2.05)
        highlight = ph in ("PWO", "HPDT")
        arch_box(s, x, Inches(1.75), Inches(1.85), Inches(0.7), ph, "",
                 HONEY_RED if ph == "PWO" else (SUCCESS if ph == "HPDT" else IOCL_BLUE), 10)
    add_table(s, Inches(0.5), Inches(2.7), Inches(12.3), [
        ["Component", "Role", "Without it"],
        ["Unit APC (Forge)", "Constraint control & dynamic models", "PWO has nothing to coordinate"],
        ["PWO", "Site dynamic RTO", "Local RTO silos return"],
        ["HPDT", "Model governance & scenarios", "Stale yields, failed revamps"],
        ["Blend Optimizer", "Gate-to-gate quality & inventory", "Loss at rundown"],
    ], [Inches(2.8), Inches(4.5), Inches(5)])

    # --- 13 Proof ---
    s = blank_slide(prs)
    fill_bg(s, LIGHT_BG)
    slide_title(s, "Proven in refining — relevant to IOCL complexity")
    cases = [
        ("Hellenic Petroleum", "Dynamic coordination — payback < 1 year cited; margin improvements."),
        ("SECCO (ethylene)", "Reuses APC dynamics; naphtha feed +1.27% after revamp."),
        ("Literature (FCC DRTO)", "Higher objective during disturbances — IOCL FCC prime candidates."),
        ("IOCL opportunity", "Coordinate crude, intermediates, blend once — not per-unit RTO battles."),
    ]
    for i, (t, b) in enumerate(cases):
        col, row = i % 2, i // 2
        add_card(s, Inches(0.55 + col * 6.4), Inches(1.85 + row * 2.35), Inches(6), Inches(2), t, b, IOCL_BLUE, RGBColor(245, 248, 255))

    # --- 14 Value ---
    s = blank_slide(prs)
    fill_bg(s, LIGHT_BG)
    slide_title(s, "What IOCL gains with PWO + HPDT")
    benefits = ["₹ margin per barrel — sustained", "Reduced quality giveaway", "Faster crude/margin response",
                "Lower optimization OPEX", "Standard Honeywell delivery playbook"]
    for i, b in enumerate(benefits):
        arch_box(s, Inches(0.5 + (i % 3) * 4.2), Inches(1.9 + (i // 3) * 0.85), Inches(3.9), Inches(0.6), b, "", IOCL_ORANGE, 10)
    add_textbox(s, Inches(0.8), Inches(4.2), Inches(11.5), Inches(1.2),
                "Replace multiple local RTO capital requests with ONE template-based plantwide program per refinery — integrated with existing Forge APC.",
                16, False, TITLE_DARK, PP_ALIGN.CENTER)

    # --- 15 Decision ---
    s = blank_slide(prs)
    fill_bg(s, RGBColor(15, 23, 42))
    slide_title(s, "Executive decision framework", dark=True)
    add_table(s, Inches(0.45), Inches(1.7), Inches(12.4), [
        ["Option A — Local RTO proliferation", "Option B — Template (PWO + HPDT)"],
        ["High CAPEX per unit, overlapping models", "✓ Single site optimization layer"],
        ["Benefits isolated to one train", "✓ Crude-to-blend coordination"],
        ["Frequent model OFF", "✓ Proxy limits + CPA-U"],
        ["Planner ↔ operations friction", "✓ LP structure in real time"],
    ], [Inches(6.2), Inches(6.2)])
    rect = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.55), Inches(5.15), Inches(12.2), Inches(1.35))
    rect.fill.solid()
    rect.fill.fore_color.rgb = IOCL_BLUE
    rect.line.fill.background()
    tf = rect.text_frame
    tf.paragraphs[0].text = "Recommendation: Mandate PWO and HPDT as non-optional in IOCL Honeywell Templates."
    tf.paragraphs[0].font.size = Pt(16)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = WHITE
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    p2 = tf.add_paragraph()
    p2.text = "Defer standalone local RTO expansions — route investment to plantwide dynamic optimization."
    p2.font.size = Pt(12)
    p2.font.color.rgb = RGBColor(200, 215, 235)
    p2.alignment = PP_ALIGN.CENTER

    # --- 16 Roadmap ---
    s = blank_slide(prs)
    fill_bg(s, LIGHT_BG)
    slide_title(s, "Proposed IOCL rollout (template-based)")
    roadmap = [
        ("Phase 1", "APC baseline + CPA-U"),
        ("Phase 2", "HPDT model alignment"),
        ("Phase 3", "PWO live — 1 refinery"),
        ("Phase 4", "Blend gate-to-gate"),
        ("Phase 5", "Replicate nationally"),
    ]
    for i, (ph, desc) in enumerate(roadmap):
        x = Inches(0.45 + i * 2.5)
        circ = s.shapes.add_shape(MSO_SHAPE.OVAL, x + Inches(0.7), Inches(2.1), Inches(0.45), Inches(0.45))
        circ.fill.solid()
        circ.fill.fore_color.rgb = HONEY_RED if i == 2 else (SUCCESS if i == 4 else IOCL_BLUE)
        circ.line.fill.background()
        add_textbox(s, x, Inches(2.7), Inches(2.2), Inches(0.4), ph, 13, True, TITLE_DARK, PP_ALIGN.CENTER)
        add_textbox(s, x, Inches(3.05), Inches(2.2), Inches(0.8), desc, 11, False, MUTED, PP_ALIGN.CENTER)
    if len(roadmap) > 1:
        line = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(2.32), Inches(10.5), Inches(0.04))
        line.fill.solid()
        line.fill.fore_color.rgb = IOCL_ORANGE
        line.line.fill.background()
    add_textbox(s, Inches(0.55), Inches(4.5), Inches(12), Inches(0.8),
                "Pilot: highest intermediate-pool complexity + existing Forge APC = fastest time-to-value.", 13, False, TITLE_DARK)

    # --- 17 Close ---
    s = blank_slide(prs)
    fill_bg(s, IOCL_BLUE)
    add_textbox(s, Inches(0.8), Inches(2.2), Inches(11.5), Inches(1.5),
                "Optimize the plant,\nnot the project portfolio", 40, True, WHITE, PP_ALIGN.CENTER)
    add_textbox(s, Inches(0.8), Inches(4), Inches(11.5), Inches(0.6),
                "Plantwide Dynamic RTO · Honeywell PWO · HPDT in every IOCL template", 18, False, IOCL_ORANGE, PP_ALIGN.CENTER)
    add_textbox(s, Inches(0.8), Inches(5), Inches(11.5), Inches(0.5), "INDIAN OIL  ·  HONEYWELL PROCESS SOLUTIONS", 16, True, WHITE, PP_ALIGN.CENTER)

    out = "/workspace/IOCL_Honeywell_PWO_Presentation/IOCL_Honeywell_PWO_Executive.pptx"
    prs.save(out)
    print(f"Wrote {len(prs.slides)} slides -> {out}")


if __name__ == "__main__":
    build()
