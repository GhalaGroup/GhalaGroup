/** @odoo-module **/

import { ZEBRA_FONTS, dotsToScreenPx } from "./font_metrics";

/**
 * Map Zebra font IDs to CSS font families for approximate on-screen rendering.
 */
const FONT_FAMILY_MAP = {
    '0': "'Arial', 'Helvetica', sans-serif",          // Font 0 = scalable proportional (Helvetica-like)
    'A': "'Courier New', monospace",                    // Bitmap fonts → monospace approximation
    'B': "'Courier New', monospace",
    'C': "'Courier New', monospace",
    'D': "'Courier New', monospace",
    'E': "'Courier New', monospace",
    'F': "'Courier New', monospace",
    'G': "'Arial Black', 'Impact', sans-serif",         // Font G is large/bold
    'H': "'Courier New', monospace",
};

/**
 * Factory that creates Konva shapes from vpa.label.element record data.
 * Each element type maps to a specific Konva node or group.
 */
export class ElementFactory {
    constructor(editor) {
        this.editor = editor;
    }

    /**
     * Create a Konva node from element record data.
     * @param {Object} data - field values from the ORM record
     * @param {number|string} recordId - the record's resId or virtualId
     * @returns {Konva.Node|null}
     */
    createFromData(data, recordId) {
        let node;
        const elemType = data.element_type;
        switch (elemType) {
            case 'text':
                node = this._createText(data);
                break;
            case 'variable':
                node = this._createVariable(data);
                break;
            case 'barcode':
                node = this._createBarcode(data);
                break;
            case 'qr_code':
                node = this._createQrCode(data);
                break;
            case 'line':
                node = this._createLine(data);
                break;
            case 'v_line':
                node = this._createVLine(data);
                break;
            case 'box':
                node = this._createBox(data);
                break;
            case 'image':
                node = this._createImageGroup(data);
                break;
            case 'company_logo':
                node = this._createImageGroup(data);
                break;
            default:
                return null;
        }
        node.setAttr('elementRecordId', recordId);
        node.setAttr('elementType', elemType);
        node.draggable(true);
        return node;
    }

    /**
     * Update an existing Konva node from new record data.
     * Returns the node, or a new replacement node if the type changed.
     */
    updateNode(node, data) {
        const elemType = data.element_type;
        const isGroup = elemType === 'barcode' || elemType === 'qr_code' ||
                        elemType === 'image' || elemType === 'company_logo';

        // If the node type doesn't match (e.g. was Text, now needs Group), rebuild entirely
        if (isGroup && typeof node.destroyChildren !== 'function') {
            return null; // signal caller to recreate
        }
        if (!isGroup && typeof node.destroyChildren === 'function' &&
            !(node instanceof Konva.Rect)) {
            return null; // signal caller to recreate
        }

        // Always update position
        node.x(data.pos_x || 0);
        node.y(data.pos_y || 0);

        if (elemType === 'text') {
            this._updateText(node, data);
        } else if (elemType === 'variable') {
            this._updateVariable(node, data);
        } else if (elemType === 'line') {
            this._updateLine(node, data);
        } else if (elemType === 'v_line') {
            this._updateVLine(node, data);
        } else if (elemType === 'box') {
            this._updateBox(node, data);
        } else if (isGroup) {
            this._rebuildGroup(node, data, elemType);
        }

        return node;
    }

    // ─── Update methods for simple nodes ────────────────────────

    _updateText(node, data) {
        const fontSize = dotsToScreenPx(data.font_height || 30);
        const fontId = data.font_id || '0';
        node.fontSize(fontSize);
        node.fontFamily(FONT_FAMILY_MAP[fontId] || FONT_FAMILY_MAP['0']);
        node.text(data.content || 'Text');
        node.rotation(this._getRotationDegrees(data.rotation));
    }

    _updateVariable(node, data) {
        const fontSize = dotsToScreenPx(data.font_height || 30);
        const fontId = data.font_id || '0';
        node.fontSize(fontSize);
        node.fontFamily(FONT_FAMILY_MAP[fontId] || FONT_FAMILY_MAP['0']);
        const varDisplay = this._getVariableDisplay(data);
        node.text(varDisplay);
        node.rotation(this._getRotationDegrees(data.rotation));
    }

    _updateLine(node, data) {
        const w = data.shape_width || 100;
        const h = data.border_thickness || 2;
        const color = data.shape_color === 'W' ? '#ffffff' : '#000000';
        node.width(w);
        node.height(h);
        node.fill(color);
        node.hitStrokeWidth(Math.max(12 - h, 4));
        node.scaleX(1);
        node.scaleY(1);
    }

    _updateVLine(node, data) {
        const w = data.border_thickness || 2;
        const h = data.shape_height || 100;
        const color = data.shape_color === 'W' ? '#ffffff' : '#000000';
        node.width(w);
        node.height(h);
        node.fill(color);
        node.hitStrokeWidth(Math.max(12 - w, 4));
        node.scaleX(1);
        node.scaleY(1);
    }

    _updateBox(node, data) {
        const w = data.shape_width || 100;
        const h = data.shape_height || 100;
        const t = data.border_thickness || 2;
        const color = data.shape_color === 'W' ? '#ffffff' : '#000000';
        node.width(w);
        node.height(h);
        node.strokeWidth(t);
        node.stroke(color);
        node.scaleX(1);
        node.scaleY(1);
    }

    /**
     * Rebuild a Group node's children (for barcode, QR, image, company_logo).
     */
    _rebuildGroup(group, data, elemType) {
        group.destroyChildren();

        if (elemType === 'barcode') {
            this._addBarcodeChildren(group, data);
        } else if (elemType === 'qr_code') {
            this._addQrCodeChildren(group, data);
        } else if (elemType === 'image' || elemType === 'company_logo') {
            this._addImageGroupChildren(group, data, elemType);
        }
    }

    // ─── Create methods ────────────────────────────────────────

    _createText(data) {
        const fontSize = dotsToScreenPx(data.font_height || 30);
        const fontId = data.font_id || '0';
        return new Konva.Text({
            x: data.pos_x || 0,
            y: data.pos_y || 0,
            text: data.content || 'Text',
            fontSize: fontSize,
            fontFamily: FONT_FAMILY_MAP[fontId] || FONT_FAMILY_MAP['0'],
            fill: '#000000',
            rotation: this._getRotationDegrees(data.rotation),
        });
    }

    _createVariable(data) {
        const fontSize = dotsToScreenPx(data.font_height || 30);
        const fontId = data.font_id || '0';
        const varDisplay = this._getVariableDisplay(data);
        return new Konva.Text({
            x: data.pos_x || 0,
            y: data.pos_y || 0,
            text: varDisplay,
            fontSize: fontSize,
            fontFamily: FONT_FAMILY_MAP[fontId] || FONT_FAMILY_MAP['0'],
            fill: '#0055aa',
            fontStyle: 'italic',
            rotation: this._getRotationDegrees(data.rotation),
        });
    }

    _createBarcode(data) {
        const group = new Konva.Group({
            x: data.pos_x || 0,
            y: data.pos_y || 0,
        });
        this._addBarcodeChildren(group, data);
        return group;
    }

    _addBarcodeChildren(group, data) {
        const height = data.barcode_height || 100;
        const moduleW = data.barcode_module_width || 2;

        const pattern = [3, 1, 1, 2, 3, 1, 2, 1, 1, 2, 3, 1, 1, 2, 2, 1, 3, 1, 2, 1, 1, 2, 3, 1, 1, 2, 2, 1];
        let xPos = 0;
        for (let i = 0; i < pattern.length; i++) {
            const w = pattern[i] * (moduleW * 0.5);
            if (i % 2 === 0) {
                group.add(new Konva.Rect({
                    x: xPos, y: 0,
                    width: Math.max(w, 1), height: height,
                    fill: '#000000',
                }));
            }
            xPos += w;
        }

        if (data.show_text_below !== false) {
            group.add(new Konva.Text({
                x: 0, y: height + 3,
                text: data.content || '{{BARCODE}}',
                fontSize: 10,
                fontFamily: "'Courier New', monospace",
                fill: '#000000',
            }));
        }
    }

    _createQrCode(data) {
        const group = new Konva.Group({
            x: data.pos_x || 0,
            y: data.pos_y || 0,
        });
        this._addQrCodeChildren(group, data);
        return group;
    }

    _addQrCodeChildren(group, data) {
        const mag = data.qr_magnification || 5;
        const size = mag * 21;

        group.add(new Konva.Rect({
            x: 0, y: 0,
            width: size, height: size,
            fill: '#ffffff',
            stroke: '#000000',
            strokeWidth: 1,
        }));

        const cornerSize = mag * 7;
        const positions = [[0, 0], [size - cornerSize, 0], [0, size - cornerSize]];
        for (const [cx, cy] of positions) {
            group.add(new Konva.Rect({
                x: cx + mag, y: cy + mag,
                width: cornerSize - mag * 2,
                height: cornerSize - mag * 2,
                fill: '#000000',
            }));
            group.add(new Konva.Rect({
                x: cx, y: cy,
                width: cornerSize, height: cornerSize,
                stroke: '#000000', strokeWidth: mag,
                fill: 'transparent',
            }));
        }

        group.add(new Konva.Text({
            x: size / 2 - 8, y: size / 2 - 5,
            text: 'QR', fontSize: 10, fill: '#999',
        }));
    }

    _createLine(data) {
        const w = data.shape_width || 100;
        const h = data.border_thickness || 2;
        const color = data.shape_color === 'W' ? '#ffffff' : '#000000';
        return new Konva.Rect({
            x: data.pos_x || 0,
            y: data.pos_y || 0,
            width: w,
            height: h,
            fill: color,
            hitStrokeWidth: Math.max(12 - h, 4),
        });
    }

    _createVLine(data) {
        const w = data.border_thickness || 2;
        const h = data.shape_height || 100;
        const color = data.shape_color === 'W' ? '#ffffff' : '#000000';
        return new Konva.Rect({
            x: data.pos_x || 0,
            y: data.pos_y || 0,
            width: w,
            height: h,
            fill: color,
            hitStrokeWidth: Math.max(12 - w, 4),
        });
    }

    _createBox(data) {
        const w = data.shape_width || 100;
        const h = data.shape_height || 100;
        const t = data.border_thickness || 2;
        const color = data.shape_color === 'W' ? '#ffffff' : '#000000';
        return new Konva.Rect({
            x: data.pos_x || 0,
            y: data.pos_y || 0,
            width: w,
            height: h,
            stroke: color,
            strokeWidth: t,
            fill: 'transparent',
        });
    }

    // ─── Image / Company Logo ────────────────────────────────────

    _createImageGroup(data) {
        const group = new Konva.Group({
            x: data.pos_x || 0,
            y: data.pos_y || 0,
        });
        this._addImageGroupChildren(group, data, data.element_type);
        return group;
    }

    _addImageGroupChildren(group, data, elemType) {
        const width = data.image_width || 100;

        // Determine the image source
        let imgSrc = null;
        if (elemType === 'company_logo' && this.editor.companyLogoDataUri) {
            imgSrc = this.editor.companyLogoDataUri;
        } else if (elemType === 'image' && data.image_data) {
            // image_data is raw base64 from the record
            const b64 = typeof data.image_data === 'string' ? data.image_data : '';
            if (b64) {
                imgSrc = 'data:image/png;base64,' + b64;
            }
        }

        if (imgSrc) {
            // Add placeholder while loading
            const placeholderRect = new Konva.Rect({
                x: 0, y: 0, width: width, height: width,
                fill: '#f0f0f0', stroke: '#ccc', strokeWidth: 1,
            });
            group.add(placeholderRect);
            const loadingText = new Konva.Text({
                x: 4, y: 4, text: '...', fontSize: 10, fill: '#999',
            });
            group.add(loadingText);

            // Load actual image asynchronously
            const imgObj = new window.Image();
            imgObj.onload = () => {
                // Remove placeholder
                placeholderRect.destroy();
                loadingText.destroy();

                const ratio = imgObj.height / imgObj.width;
                const h = Math.round(width * ratio);

                const konvaImg = new Konva.Image({
                    x: 0, y: 0,
                    image: imgObj,
                    width: width,
                    height: h,
                });
                group.add(konvaImg);

                if (group.getLayer()) {
                    group.getLayer().draw();
                }
            };
            imgObj.onerror = () => {
                // On error, show broken placeholder
                placeholderRect.destroy();
                loadingText.text(elemType === 'company_logo' ? 'LOGO' : 'IMG');
            };
            imgObj.src = imgSrc;
        } else {
            // No image data — show placeholder
            const height = width;
            group.add(new Konva.Rect({
                x: 0, y: 0, width, height,
                fill: '#f0f0f0', stroke: '#ccc', strokeWidth: 1,
            }));
            const label = elemType === 'company_logo' ? 'LOGO' : 'IMG';
            group.add(new Konva.Text({
                x: width / 2 - 14, y: height / 2 - 6,
                text: label, fontSize: 12, fill: '#999',
            }));
        }
    }

    // ─── Helpers ────────────────────────────────────────────────

    _getVariableDisplay(data) {
        if (data.variable_id) {
            const varName = Array.isArray(data.variable_id)
                ? data.variable_id[1]
                : (data.variable_id.display_name || data.variable_id.name || 'VAR');
            return `{{${varName}}}`;
        }
        return '{{VARIABLE}}';
    }

    _getRotationDegrees(rotation) {
        const map = { 'N': 0, 'R': 90, 'I': 180, 'B': 270 };
        return map[rotation] || 0;
    }
}
