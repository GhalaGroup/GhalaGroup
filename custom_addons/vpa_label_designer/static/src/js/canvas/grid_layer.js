/** @odoo-module **/

/**
 * Grid overlay for the label canvas.
 * Draws mm-based grid lines on a Konva layer.
 */
export class GridLayer {
    constructor(stage, options) {
        this.stage = stage;
        this.options = options;
        this.layer = new Konva.Layer({ listening: false });
        this.stage.add(this.layer);
        // Position grid above background but below elements
        this.layer.moveToBottom();
        if (this.stage.children.length > 1) {
            this.layer.setZIndex(1);
        }
        if (options.visible) {
            this.draw();
        }
    }

    draw() {
        this.layer.destroyChildren();
        const { labelOffsetX, labelOffsetY, labelWidth, labelHeight,
                zoom, spacingMm, dpi } = this.options;

        const dotsPerMm = dpi / 25.4;
        const spacingDots = spacingMm * dotsPerMm;

        // Vertical grid lines
        for (let x = spacingDots; x < labelWidth; x += spacingDots) {
            this.layer.add(new Konva.Line({
                points: [
                    labelOffsetX + x * zoom, labelOffsetY,
                    labelOffsetX + x * zoom, labelOffsetY + labelHeight * zoom
                ],
                stroke: 'rgba(180, 180, 200, 0.3)',
                strokeWidth: 0.5,
            }));
        }

        // Horizontal grid lines
        for (let y = spacingDots; y < labelHeight; y += spacingDots) {
            this.layer.add(new Konva.Line({
                points: [
                    labelOffsetX, labelOffsetY + y * zoom,
                    labelOffsetX + labelWidth * zoom, labelOffsetY + y * zoom
                ],
                stroke: 'rgba(180, 180, 200, 0.3)',
                strokeWidth: 0.5,
            }));
        }

        this.layer.draw();
    }

    toggle(visible) {
        this.options.visible = visible;
        if (visible) {
            this.draw();
            this.layer.show();
        } else {
            this.layer.hide();
        }
        this.layer.draw();
    }

    updateSpacing(spacingMm) {
        this.options.spacingMm = spacingMm;
        if (this.options.visible) {
            this.draw();
        }
    }

    destroy() {
        if (this.layer) {
            this.layer.destroy();
            this.layer = null;
        }
    }
}
