#!/usr/bin/env node
/** Render the test site's current-wordmark 1200 x 630 social-share image. */

import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";


const WIDTH = 1200;
const HEIGHT = 630;
const modulePath = process.env.KC_SHARP_MODULE || "sharp";
const sharpModule = modulePath.startsWith("/") ? pathToFileURL(modulePath).href : modulePath;
const { default: sharp } = await import(sharpModule);

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, "..");
const output = path.resolve(
  process.argv[2] || path.join(root, "test-overrides/assets/social-preview-wordmark-20260917.png"),
);

// Rasterize the exact SVG used in the visible site header, then trim its
// transparent viewBox padding so the current wordmark is truly centered.
const renderedWordmark = await sharp(path.join(root, "assets/logo-wordmark.svg"), { density: 300 })
  .png()
  .toBuffer();
const wordmark = await sharp(renderedWordmark)
  .trim()
  .resize({ width: 960 })
  .png()
  .toBuffer();
const wordmarkInfo = await sharp(wordmark).metadata();

const background = `<svg xmlns="http://www.w3.org/2000/svg" width="${WIDTH}" height="${HEIGHT}">
  <defs>
    <radialGradient id="glow" cx="88%" cy="30%" r="70%">
      <stop offset="0" stop-color="#c84a32" stop-opacity=".20"/>
      <stop offset=".42" stop-color="#c84a32" stop-opacity=".07"/>
      <stop offset="1" stop-color="#080808" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="accent" x1="0" x2="1">
      <stop stop-color="#c84a32"/>
      <stop offset="1" stop-color="#df725c"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="#080808"/>
  <rect width="1200" height="630" fill="url(#glow)"/>
  <rect x="34" y="34" width="1132" height="562" rx="20" fill="none" stroke="#3a211c" stroke-width="2"/>
  <rect x="96" y="76" width="1008" height="4" rx="2" fill="url(#accent)"/>
  <text x="600" y="420" text-anchor="middle" fill="#f5f2ea" font-family="Arial, Helvetica, sans-serif" font-size="49" font-weight="700">Find Christian Hip-Hop Shows &amp; Festivals</text>
  <line x1="100" y1="514" x2="390" y2="514" stroke="#8f3928" stroke-width="2"/>
  <line x1="810" y1="514" x2="1100" y2="514" stroke="#8f3928" stroke-width="2"/>
  <text x="600" y="524" text-anchor="middle" fill="#df725c" font-family="Arial, Helvetica, sans-serif" font-size="21" font-weight="700" letter-spacing="5">KINGDOMCIRCUIT.COM</text>
</svg>`;

await sharp(Buffer.from(background))
  .composite([
    {
      input: wordmark,
      left: Math.round((WIDTH - wordmarkInfo.width) / 2),
      top: 155,
    },
  ])
  .png({ compressionLevel: 9 })
  .toFile(output);

process.stdout.write(`${output}\n`);
