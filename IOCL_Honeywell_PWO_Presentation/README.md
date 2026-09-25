# IOCL Executive Presentation — Honeywell PWO vs Traditional RTO

Executive-level HTML presentation (Reveal.js) with animations, architecture graphics, and IOCL-focused messaging.

## Files

| File | Purpose |
|------|---------|
| `index.html` | Full animated deck (17 slides) — **primary deliverable** |
| `styles.css` | IOCL / Honeywell branding, animations |
| **`IOCL_Honeywell_PWO_Executive.pptx`** | **Full 17-slide PowerPoint** (primary PPT deliverable) |
| `build_pptx.py` | Regenerate the `.pptx` after editing slide content |

## View the presentation

### Option 1: Local browser (recommended)

```bash
cd IOCL_Honeywell_PWO_Presentation
python3 -m http.server 8765
```

Open `http://localhost:8765` in a browser. Use **arrow keys** or **space** to advance; **F** for fullscreen; **S** for speaker notes (if added).

### Option 2: Open file directly

Open `index.html` in Chrome or Edge (some browsers restrict CDN assets on `file://`; use Option 1 if styles fail to load).

## Export to PDF (for email distribution)

1. Open the presentation in Chrome at `http://localhost:8765/?print-pdf`
2. Print → Save as PDF, landscape, margins none, background graphics enabled

## Contents (17 slides)

1. Title — IOCL × Honeywell Forge  
2. Agenda & key stats  
3. Enterprise optimization gap  
4. Traditional steady-state RTO  
5. Why unit-local RTO under-delivers  
6. TCO comparison (animated meters)  
7. Plantwide Optimizer introduction  
8. 1→n MPC cascade architecture (SVG)  
9. Dynamic vs traditional RTO  
10. Proxy limits  
11. HPDT (Process Digital Twin)  
12. Honeywell Template must-haves  
13. Industry proof points  
14. IOCL value proposition  
15. Executive decision framework  
16. Phased rollout  
17. Closing call to action  

## Customization

- Edit `index.html` for slide copy and `styles.css` for branding.
- IOCL / Honeywell colors are defined in CSS variables at the top of `styles.css`.

## References

Based on publicly available Honeywell materials: Plantwide Optimizer product pages, *Plant Wide Optimization — A Better Way* white paper, and *End-to-End Autonomous Plant* white paper.
