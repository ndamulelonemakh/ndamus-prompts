# Github Copilot Prompts


## 1. Ask `Copilot` to generate `copilit-instructions.md`

```markdown
Please  explore this project proactively and then use the results to generate the copilot instructions file.
You can find more info about what this file should contain here: https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot
```

## Agent Mode

### Style Guide

```bash
- Avoid using comments in code, instead use descriptive symbols, logical project structure optimised for feature localisaion
- ALWAYS ground your answers in authoritative sources(i.e. Official docs or reputable web sources) before giving conclusions.
```

## 2. Ask `Copilot` to generate og assets

```markdown
You are a creative Graphic Design specialist with an illustrious track record for elegant designs with some of your clients like Apple.
Goal: generate project-specific Open Graph (OG) and Twitter Card assets that replace the generic template images currently in use.

Style constraints: No copyright-protected stock images; only code-generated art or your own logo.
Creative twist: Surprise me with a generative flourish that reacts to the project name
Tech stack you may use: Python + any OSS combo, e.g. Pillow for raster text/layout, CairoSVG or svglib if you prefer vector → raster, Gradients, noise, halftone, ASCII overlays, etc.
Output specs:
- OG image: 1200×630 px, PNG, < 300 kB
- Twitter image: 1200×675 px, PNG, < 300 kB
- Safe zone: keep critical text inside 1000×500 px centered
- File names: og.png and twitter.png dropped in /static/img/
```
