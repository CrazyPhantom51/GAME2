# Emberdeep: Chromebook Web Edition

Emberdeep now runs as a **browser game** (no Linux mode required on Chromebook).

## How to run (Chromebook-friendly)

### Option A: Open directly
1. Download or copy this project.
2. Open `index.html` in Chrome.
3. Enter a username and play.

### Option B: Host as static files (recommended)
Upload `index.html`, `style.css`, and `webgame.js` to any static host (GitHub Pages, Netlify, etc.) and open the URL in Chrome.

## Save system
- Saves are tied to username and stored in browser `localStorage`.
- Data stays on the same browser profile/device unless exported by the host environment.

## Notes
- Each run uses randomized seeds and procedural encounters.
- No server, Python, or Linux terminal is required to play.
