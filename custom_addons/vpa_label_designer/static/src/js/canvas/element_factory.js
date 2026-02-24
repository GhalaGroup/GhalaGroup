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

        // Text/variable with max_width or price variable needs a Group; others need plain Text
        if (elemType === 'text' || elemType === 'variable') {
            const needsGroup = (data.max_width || 0) > 0 ||
                (elemType === 'variable' && this._getVatNote(this._getVariableName(data)));
            const hasGroup = typeof node.destroyChildren === 'function' && !(node instanceof Konva.Rect);
            if (needsGroup && !hasGroup) return null; // need Group, have Text → recreate
            if (!needsGroup && hasGroup) return null; // need Text, have Group → recreate
        }

        // If the node type doesn't match (e.g. was Text, now needs Group), rebuild entirely
        if (isGroup && typeof node.destroyChildren !== 'function') {
            return null; // signal caller to recreate
        }
        if (!isGroup && typeof node.destroyChildren === 'function' &&
            !(node instanceof Konva.Rect) && elemType !== 'text' && elemType !== 'variable') {
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
        const maxW = data.max_width || 0;
        if (maxW > 0 && typeof node.destroyChildren === 'function') {
            this._updateTextGroup(node, data, data.content || 'Text', '#000000', false);
        } else {
            const fontSize = dotsToScreenPx(data.font_height || 30);
            const fontId = data.font_id || '0';
            node.fontSize(fontSize);
            node.fontFamily(FONT_FAMILY_MAP[fontId] || FONT_FAMILY_MAP['0']);
            node.text(data.content || 'Text');
            node.rotation(this._getRotationDegrees(data.rotation));
        }
    }

    _updateVariable(node, data) {
        const maxW = data.max_width || 0;
        const varDisplay = this._getVariableDisplay(data);
        const varName = this._getVariableName(data);
        const vatNote = this._getVatNote(varName);

        if (maxW > 0 && typeof node.destroyChildren === 'function') {
            this._updateTextGroup(node, data, varDisplay, '#0055aa', true);
            if (vatNote) this._addVatNoteToGroup(node, data, vatNote);
        } else if (vatNote && typeof node.destroyChildren === 'function') {
            // Price variable Group without max_width
            node.destroyChildren();
            const fontSize = dotsToScreenPx(data.font_height || 30);
            const fontId = data.font_id || '0';
            node.add(new Konva.Text({
                x: 0, y: 0,
                text: varDisplay,
                fontSize: fontSize,
                fontFamily: FONT_FAMILY_MAP[fontId] || FONT_FAMILY_MAP['0'],
                fill: '#0055aa',
                fontStyle: 'italic',
            }));
            const noteSize = Math.max(8, Math.round(fontSize * 0.6));
            node.add(new Konva.Text({
                x: 0, y: fontSize + 2,
                text: `(${vatNote})`,
                fontSize: noteSize,
                fontFamily: FONT_FAMILY_MAP[fontId] || FONT_FAMILY_MAP['0'],
                fill: '#666666',
                fontStyle: 'italic',
            }));
            node.rotation(this._getRotationDegrees(data.rotation));
        } else if (!vatNote && typeof node.fontSize === 'function') {
            const fontSize = dotsToScreenPx(data.font_height || 30);
            const fontId = data.font_id || '0';
            node.fontSize(fontSize);
            node.fontFamily(FONT_FAMILY_MAP[fontId] || FONT_FAMILY_MAP['0']);
            node.text(varDisplay);
            node.rotation(this._getRotationDegrees(data.rotation));
        } else {
            // Type mismatch — signal recreate
            return null;
        }
    }

    /**
     * Update a text Group (bounding box + text) with new data.
     */
    _updateTextGroup(group, data, text, color, isItalic) {
        const fontSize = dotsToScreenPx(data.font_height || 30);
        const fontId = data.font_id || '0';
        const maxW = data.max_width;
        const lines = parseInt(data.max_lines) || 1;
        const boxHeight = fontSize * lines + 4;

        group.rotation(this._getRotationDegrees(data.rotation));

        // Update children
        const children = group.getChildren();
        // First child = Rect (bounding box)
        if (children[0]) {
            children[0].width(maxW);
            children[0].height(boxHeight);
        }
        // Second child = Text
        if (children[1]) {
            const alignMap = { 'L': 'left', 'C': 'center', 'R': 'right' };
            children[1].fontSize(fontSize);
            children[1].fontFamily(FONT_FAMILY_MAP[fontId] || FONT_FAMILY_MAP['0']);
            children[1].text(text);
            children[1].fill(color);
            children[1].width(maxW);
            children[1].align(alignMap[data.text_alignment] || 'left');
            if (lines === 1) {
                children[1].wrap('none');
                children[1].ellipsis(true);
                children[1].height(undefined);
            } else {
                children[1].wrap('word');
                children[1].ellipsis(false);
                children[1].height(boxHeight - 4);
            }
        }
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
     * Rebuild a Group node's children.
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
        const maxW = data.max_width || 0;
        if (maxW > 0) {
            return this._createTextGroup(data, data.content || 'Text', '#000000', false);
        }
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
        const maxW = data.max_width || 0;
        const varDisplay = this._getVariableDisplay(data);
        const varName = this._getVariableName(data);
        const vatNote = this._getVatNote(varName);

        if (maxW > 0) {
            const node = this._createTextGroup(data, varDisplay, '#0055aa', true);
            if (vatNote) this._addVatNoteToGroup(node, data, vatNote);
            return node;
        }

        if (vatNote) {
            // Use a Group for price variable + VAT note
            const fontSize = dotsToScreenPx(data.font_height || 30);
            const fontId = data.font_id || '0';
            const group = new Konva.Group({
                x: data.pos_x || 0,
                y: data.pos_y || 0,
                rotation: this._getRotationDegrees(data.rotation),
            });
            group.add(new Konva.Text({
                x: 0, y: 0,
                text: varDisplay,
                fontSize: fontSize,
                fontFamily: FONT_FAMILY_MAP[fontId] || FONT_FAMILY_MAP['0'],
                fill: '#0055aa',
                fontStyle: 'italic',
            }));
            const noteSize = Math.max(8, Math.round(fontSize * 0.6));
            group.add(new Konva.Text({
                x: 0, y: fontSize + 2,
                text: `(${vatNote})`,
                fontSize: noteSize,
                fontFamily: FONT_FAMILY_MAP[fontId] || FONT_FAMILY_MAP['0'],
                fill: '#666666',
                fontStyle: 'italic',
            }));
            return group;
        }

        const fontSize = dotsToScreenPx(data.font_height || 30);
        const fontId = data.font_id || '0';
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

    /**
     * Create a Group with blue dashed bounding box + Text for max_width elements.
     */
    _createTextGroup(data, text, color, isItalic) {
        const fontSize = dotsToScreenPx(data.font_height || 30);
        const fontId = data.font_id || '0';
        const maxW = data.max_width;
        const lines = parseInt(data.max_lines) || 1;
        const boxHeight = fontSize * lines + 4;

        const group = new Konva.Group({
            x: data.pos_x || 0,
            y: data.pos_y || 0,
            rotation: this._getRotationDegrees(data.rotation),
        });

        // Blue dashed bounding box
        group.add(new Konva.Rect({
            x: 0, y: 0,
            width: maxW,
            height: boxHeight,
            stroke: '#3388dd',
            strokeWidth: 1,
            dash: [4, 3],
            fill: 'rgba(51, 136, 221, 0.04)',
        }));

        // Text node
        const alignMap = { 'L': 'left', 'C': 'center', 'R': 'right' };
        const textProps = {
            x: 0, y: 2,
            text: text,
            fontSize: fontSize,
            fontFamily: FONT_FAMILY_MAP[fontId] || FONT_FAMILY_MAP['0'],
            fill: color,
            width: maxW,
            align: alignMap[data.text_alignment] || 'left',
        };
        if (isItalic) textProps.fontStyle = 'italic';
        if (lines === 1) {
            textProps.wrap = 'none';
            textProps.ellipsis = true;
        } else {
            textProps.wrap = 'word';
            textProps.height = boxHeight - 4;
        }
        group.add(new Konva.Text(textProps));

        return group;
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
        const content = data.content || '{{PRODUCT_BARCODE}}';

        // Estimate content length for preview width
        let charCount = content.length;
        // If it's a variable placeholder, use typical resolved length
        if (content.match(/^\{\{.+\}\}$/)) {
            charCount = 13; // typical barcode length (EAN-13)
        }

        // Code 128 structure: Start(11) + Data(N*11) + Checksum(11) + Stop(13)
        // Total modules = 11 + charCount*11 + 11 + 13
        const totalModules = 11 + charCount * 11 + 11 + 13;
        const totalWidth = totalModules * moduleW;

        // Generate a realistic-looking Code 128 bar pattern
        // Code 128 Start Code B pattern: 2-1-1-2-3-2
        const startPattern = [2,1,1,2,3,2];
        // Code 128 Stop pattern: 2-3-3-1-1-1-2
        const stopPattern = [2,3,3,1,1,1,2];
        // Representative data character patterns (each sums to 11)
        const charPatterns = [
            [1,1,2,3,1,3], [2,1,1,2,2,3], [1,2,3,1,1,3],
            [3,1,1,2,1,3], [1,3,1,2,2,2], [2,2,1,1,3,2],
            [1,1,3,2,1,3], [2,3,1,1,2,2], [1,2,1,3,2,2],
            [3,2,1,1,1,3], [1,1,2,2,3,2], [2,1,3,1,1,3],
            [1,3,2,1,2,2], [2,2,3,1,1,2], [1,2,2,3,1,2],
        ];
        // Checksum pattern
        const checksumPattern = [2,1,1,3,2,2];

        // Build full pattern: start + data chars + checksum + stop
        const fullPattern = [...startPattern];
        for (let i = 0; i < charCount; i++) {
            const cp = charPatterns[i % charPatterns.length];
            fullPattern.push(...cp);
        }
        fullPattern.push(...checksumPattern);
        fullPattern.push(...stopPattern);

        // Draw bars
        let xPos = 0;
        for (let i = 0; i < fullPattern.length; i++) {
            const w = fullPattern[i] * moduleW;
            if (i % 2 === 0) {
                // Even indices = bars (black)
                group.add(new Konva.Rect({
                    x: xPos, y: 0,
                    width: Math.max(w, 1), height: height,
                    fill: '#000000',
                }));
            }
            xPos += w;
        }

        // Store total width on group for resize calculations
        group.setAttr('barcodeWidth', xPos);

        if (data.show_text_below !== false) {
            const displayText = content.replace(/\{\{|\}\}/g, '');
            const fontSize = Math.max(8, Math.min(16, Math.round(height * 0.12)));
            group.add(new Konva.Text({
                x: 0, y: height + 2,
                text: displayText,
                fontSize: fontSize,
                fontFamily: "'Courier New', monospace",
                fill: '#000000',
                width: xPos,
                align: 'center',
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
        const m = mag;  // module size in dots
        const size = m * 21;  // QR version 1 = 21x21 modules

        // White background with thin border
        group.add(new Konva.Rect({
            x: 0, y: 0,
            width: size, height: size,
            fill: '#ffffff',
            stroke: '#cccccc',
            strokeWidth: 1,
        }));

        // Helper: draw a finder pattern (7x7 modules) at position ox,oy
        const drawFinder = (ox, oy) => {
            // Outer 7x7 black border (1 module thick)
            group.add(new Konva.Rect({
                x: ox, y: oy, width: m * 7, height: m * 7,
                fill: '#000000',
            }));
            // Inner 5x5 white (1 module gap)
            group.add(new Konva.Rect({
                x: ox + m, y: oy + m, width: m * 5, height: m * 5,
                fill: '#ffffff',
            }));
            // Center 3x3 black
            group.add(new Konva.Rect({
                x: ox + m * 2, y: oy + m * 2, width: m * 3, height: m * 3,
                fill: '#000000',
            }));
        };

        // Three finder patterns: top-left, top-right, bottom-left
        drawFinder(0, 0);
        drawFinder(size - m * 7, 0);
        drawFinder(0, size - m * 7);

        // Timing patterns (alternating black/white between finders)
        for (let i = 8; i < 13; i += 2) {
            // Horizontal timing (row 6)
            group.add(new Konva.Rect({
                x: m * i, y: m * 6, width: m, height: m,
                fill: '#000000',
            }));
            // Vertical timing (col 6)
            group.add(new Konva.Rect({
                x: m * 6, y: m * i, width: m, height: m,
                fill: '#000000',
            }));
        }

        // Some scattered data modules for visual effect
        const dataModules = [
            [8,8], [9,8], [10,9], [8,10], [11,8],
            [9,10], [10,11], [11,10], [12,9], [8,12],
            [9,13], [11,12], [12,11], [13,9], [13,11],
            [10,13], [12,13], [14,8], [14,10], [14,12],
        ];
        for (const [dx, dy] of dataModules) {
            if (dx < 21 && dy < 21) {
                group.add(new Konva.Rect({
                    x: m * dx, y: m * dy, width: m, height: m,
                    fill: '#000000',
                }));
            }
        }

        // "QR" label in center
        group.add(new Konva.Text({
            x: 0, y: size / 2 - 5,
            width: size,
            align: 'center',
            text: 'QR', fontSize: Math.max(8, m * 2), fill: '#aaaaaa',
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

    _getVariableName(data) {
        if (!data.variable_id) return '';
        // Get the variable ID
        const varId = Array.isArray(data.variable_id)
            ? data.variable_id[0]
            : (data.variable_id.id || data.variable_id);
        // Look up the technical name from the editor's loaded variables
        if (varId && this.editor && this.editor.availableVariables) {
            const varRec = this.editor.availableVariables.find(v => v.id === varId);
            if (varRec) return varRec.name;
        }
        // Fallback: try to extract from display name
        const displayName = Array.isArray(data.variable_id)
            ? data.variable_id[1]
            : (data.variable_id.display_name || data.variable_id.name || '');
        const match = displayName.match(/\{\{(\w+)\}\}/);
        if (match) return match[1];
        return displayName;
    }

    _getVatNote(varName) {
        if (varName === 'PRODUCT_PRICE') return 'Excl. VAT';
        if (varName === 'PRODUCT_PRICE_INCL') return 'Incl. VAT';
        return null;
    }

    _addVatNoteToGroup(group, data, vatNote) {
        const fontSize = dotsToScreenPx(data.font_height || 30);
        const fontId = data.font_id || '0';
        const lines = parseInt(data.max_lines) || 1;
        const boxHeight = fontSize * lines + 4;
        const noteSize = Math.max(8, Math.round(fontSize * 0.6));
        const alignMap = { 'L': 'left', 'C': 'center', 'R': 'right' };
        const textProps = {
            x: 0, y: boxHeight + 2,
            text: `(${vatNote})`,
            fontSize: noteSize,
            fontFamily: FONT_FAMILY_MAP[fontId] || FONT_FAMILY_MAP['0'],
            fill: '#666666',
            fontStyle: 'italic',
        };
        if (data.max_width > 0) {
            textProps.width = data.max_width;
            textProps.align = alignMap[data.text_alignment] || 'left';
        }
        group.add(new Konva.Text(textProps));
    }

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
