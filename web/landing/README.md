# Mel Theuri — KYLA landing page

A fast, self-contained creator landing page for Mel's TikTok and Instagram edits brand. It uses plain HTML, CSS, and a tiny inline JavaScript snippet; there is no build step and no external library or image dependency.

## Add Mel's hero photo

1. Choose the photo Mel wants to use and name it exactly `hero.jpg`.
2. Put `hero.jpg` in this same directory, beside `index.html`.
3. The existing `<img src="hero.jpg">` will load it automatically. The image is intentionally styled in grayscale with high contrast, grain, and a dark overlay to preserve the mirror-selfie art direction.
4. Remove or edit the small `hero.jpg / Mel uploads photo later` note in `index.html` when the real image is in place.

For best results, use a portrait-oriented JPG with the subject near the center. The page uses `object-fit: cover`, so the edges may be cropped on smaller screens.

## Add real social links

In `index.html`, find the two footer buttons and replace their placeholder `href="#"` values with the real profile URLs:

```html
<a class="social-button" href="https://www.tiktok.com/@mel...">TikTok</a>
<a class="social-button" href="https://www.instagram.com/mel...">IG</a>
```

Keep the links absolute (`https://...`) so they work from the GitHub Pages URL. The nav links already point to the page's Edits, About, and Socials sections.

## GitHub Pages

This directory is directly compatible with GitHub Pages. Serve `web/landing/` as a static path; no install, compilation, or asset bundler is needed. The site is also usable locally by opening `index.html` in a browser.
