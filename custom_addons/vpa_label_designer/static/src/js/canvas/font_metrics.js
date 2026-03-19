/** @odoo-module **/

/**
 * Zebra font data and size conversion utilities.
 *
 * Zebra printers have built-in bitmap fonts (A-H) and one scalable
 * proportional font (0, similar to Helvetica/Arial).
 */

export const ZEBRA_FONTS = {
    '0': { name: 'Font 0', cellH: 15, cellW: 12, scalable: true, desc: 'Font 0 — Scalable (Helvetica)' },
    'A': { name: 'Font A', cellH: 9, cellW: 5, scalable: false, desc: 'Font A — Condensed' },
    'B': { name: 'Font B', cellH: 11, cellW: 7, scalable: false, desc: 'Font B — Narrow' },
    'C': { name: 'Font C', cellH: 18, cellW: 10, scalable: false, desc: 'Font C — Standard' },
    'D': { name: 'Font D', cellH: 18, cellW: 10, scalable: false, desc: 'Font D — Standard Wide' },
    'E': { name: 'Font E', cellH: 28, cellW: 15, scalable: false, desc: 'Font E — Medium Bold' },
    'F': { name: 'Font F', cellH: 26, cellW: 13, scalable: false, desc: 'Font F — Medium' },
    'G': { name: 'Font G', cellH: 60, cellW: 40, scalable: false, desc: 'Font G — Large Bold' },
    'H': { name: 'Font H', cellH: 21, cellW: 13, scalable: false, desc: 'Font H — Regular' },
};

/**
 * Pre-defined size aliases P through V (Font 0 at common preset sizes).
 */
export const FONT_PRESETS = {
    'P': { fontId: '0', height: 20, width: 18, label: 'P — Tiny (~7pt)' },
    'Q': { fontId: '0', height: 28, width: 24, label: 'Q — Small (~10pt)' },
    'R': { fontId: '0', height: 35, width: 30, label: 'R — Medium (~12pt)' },
    'S': { fontId: '0', height: 42, width: 36, label: 'S — Regular (~15pt)' },
    'T': { fontId: '0', height: 56, width: 42, label: 'T — Large (~20pt)' },
    'U': { fontId: '0', height: 70, width: 54, label: 'U — X-Large (~25pt)' },
    'V': { fontId: '0', height: 100, width: 72, label: 'V — XX-Large (~35pt)' },
};

/**
 * Convert ZPL dot height to approximate point size for UI display.
 * At 203 DPI: 1 dot = 1/203 inch, 1 point = 1/72 inch
 * pts = dots * (72 / dpi)
 */
export function dotsToPoints(dots, dpi = 203) {
    return Math.round(dots * (72 / dpi) * 10) / 10;
}

/**
 * Convert ZPL dot height to screen pixel font size for Konva.js text
 * rendering.
 *
 * Zebra bitmap fonts fill ~92% of their cell height (characters nearly
 * touch the top and bottom of the dot-height box). Web fonts (IBM Plex
 * Mono / IBM Plex Sans) have a cap-height of ~68% of their fontSize em.
 *
 * To make the rendered cap-height on screen match the ZPL dot height:
 *   fontSize = dots / capHeightRatio  →  capHeight = fontSize × 0.68 ≈ dots × 0.92
 *
 * Correction factor = 0.92 / 0.68 ≈ 1.35
 *
 * The element layer zoom handles scaling to fit the screen container.
 */
export function dotsToScreenPx(dots) {
    const CAP_HEIGHT_CORRECTION = 1.0; // No correction — direct dot-to-pixel mapping
    return Math.max(8, Math.round(dots * CAP_HEIGHT_CORRECTION));
}
