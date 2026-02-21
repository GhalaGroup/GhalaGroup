/** @odoo-module **/

/**
 * Zebra font data and size conversion utilities.
 *
 * Zebra printers have built-in bitmap fonts (A-H) and one scalable
 * proportional font (0, similar to Helvetica/Arial).
 */

export const ZEBRA_FONTS = {
    '0': { name: 'Default Proportional', cellH: 15, cellW: 12, scalable: true, desc: 'Scalable, Helvetica-like' },
    'A': { name: 'Font A', cellH: 9, cellW: 5, scalable: false, desc: '9x5 dots — Smallest' },
    'B': { name: 'Font B', cellH: 11, cellW: 7, scalable: false, desc: '11x7 dots' },
    'C': { name: 'Font C', cellH: 18, cellW: 10, scalable: false, desc: '18x10 dots' },
    'D': { name: 'Font D', cellH: 18, cellW: 10, scalable: false, desc: '18x10 dots' },
    'E': { name: 'Font E', cellH: 28, cellW: 15, scalable: false, desc: '28x15 dots — Medium' },
    'F': { name: 'Font F', cellH: 26, cellW: 13, scalable: false, desc: '26x13 dots' },
    'G': { name: 'Font G', cellH: 60, cellW: 40, scalable: false, desc: '60x40 dots — Large/Bold' },
    'H': { name: 'Font H', cellH: 21, cellW: 13, scalable: false, desc: '21x13 dots' },
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
 * Approximate conversion from ZPL dot height to screen pixel font size
 * for Konva.js text rendering. This is visual approximation only.
 */
export function dotsToScreenPx(dots) {
    return Math.max(8, Math.round(dots * 0.75));
}
