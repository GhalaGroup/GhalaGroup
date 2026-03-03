/** @odoo-module **/

import { Component, onWillStart, useEffect, useRef, useState, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { loadBundle } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";
import { ElementFactory } from "./canvas/element_factory";
import { GridLayer } from "./canvas/grid_layer";
import { ZEBRA_FONTS, FONT_PRESETS, dotsToPoints, dotsToScreenPx } from "./canvas/font_metrics";

/**
 * Visual Label Canvas Editor
 *
 * OWL field widget that provides a drag-drop WYSIWYG canvas for designing
 * Zebra ZPL labels. Uses Konva.js for interactive 2D canvas rendering.
 *
 * Usage: <field name="element_ids" widget="label_canvas_editor"/>
 */
class LabelCanvasEditor extends Component {
    static template = "vpa_label_designer.LabelCanvasEditor";
    static props = {
        ...standardFieldProps,
        "*": true,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.canvasContainerRef = useRef("canvasContainer");

        this.stage = null;
        this.bgLayer = null;
        this.elementLayer = null;
        this.gridLayerObj = null;
        this.transformer = null;
        this.factory = null;
        this.nodeMap = new Map();
        this.availableVariables = [];
        this.companyLogoDataUri = null;
        this._keyHandler = null;

        this.state = useState({
            zoom: 100,
            gridVisible: true,
            snapEnabled: true,
            gridSpacingMm: 1,
            selectedElementId: null,
            selectedData: null,
            selectedElementIds: [],
            multiSelectCount: 0,
            canvasReady: false,
            labelWidth: 0,
            labelHeight: 0,
            dpi: 203,
        });

        onWillStart(async () => {
            try {
                await loadBundle("vpa_label_designer.konva_lib");
            } catch (e) {
                console.error("[VPA Canvas] Failed to load Konva:", e);
            }
            await this._loadAvailableVariables();
            await this._loadCompanyLogo();
        });

        useEffect(
            () => {
                const el = this.canvasContainerRef.el;
                if (el) {
                    try {
                        this._initCanvas();
                        this._loadElementsToCanvas();
                    } catch (e) {
                        console.error("[VPA Canvas] Init error:", e);
                    }
                }
                return () => this._destroyCanvas();
            },
            () => [this.canvasContainerRef.el]
        );

        // Watch for label size changes and rebuild the canvas
        // Also handles initial load when label_width_dots/label_height_dots arrive after canvas init
        useEffect(
            () => {
                const config = this.labelConfig;
                if (config.width <= 0 || config.height <= 0) return;
                const el = this.canvasContainerRef.el;
                if (!el) return;
                try {
                    if (!this.stage) {
                        // Canvas was skipped earlier because dots weren't loaded yet — init now
                        this._initCanvas();
                        this._loadElementsToCanvas();
                    } else if (config.width !== this.state.labelWidth || config.height !== this.state.labelHeight || config.dpi !== this.state.dpi) {
                        // Label size changed — rebuild
                        this._destroyCanvas();
                        this._initCanvas();
                        this._loadElementsToCanvas();
                    }
                } catch (e) {
                    console.error("[VPA Canvas] Rebuild error:", e);
                }
            },
            () => {
                const config = this.labelConfig;
                return [config.width, config.height, config.dpi];
            }
        );

        useEffect(
            () => {
                if (this.stage && this._getList()) {
                    try {
                        this._syncElementsToCanvas();
                    } catch (e) {
                        console.error("[VPA Canvas] Sync error:", e);
                    }
                }
            },
            () => {
                const list = this._getList();
                if (!list) return [0, ""];
                const recs = list.records || [];
                // Include a data fingerprint so changes after save/reload trigger re-sync
                const fingerprint = recs.map(r => {
                    const d = r.data;
                    return this._recordKey(r) + ":" + (d.pos_x || 0) + "," + (d.pos_y || 0) +
                           "," + (d.element_type || "") + "," + (d.content || "") +
                           "," + (d.font_height || 0) + "," + (d.shape_width || 0) +
                           "," + (d.image_width || 0);
                }).join("|");
                return [recs.length, fingerprint];
            }
        );

        onWillUnmount(() => this._destroyCanvas());
    }

    // ─── Accessors ──────────────────────────────────────────────

    _getList() {
        try {
            return this.props.record.data[this.props.name];
        } catch (e) {
            return null;
        }
    }

    get list() {
        return this._getList();
    }

    get labelConfig() {
        try {
            const rec = this.props.record.data;
            const sizeId = rec.label_size_id;
            if (!sizeId || (Array.isArray(sizeId) && !sizeId[0]) || (typeof sizeId === "object" && !sizeId.id && !Array.isArray(sizeId))) {
                return { width: 640, height: 640, dpi: 203 };
            }
            return {
                width: rec.label_width_dots || 640,
                height: rec.label_height_dots || 640,
                dpi: rec.label_dpi || 203,
            };
        } catch (e) {
            return { width: 640, height: 640, dpi: 203 };
        }
    }

    get fontOptions() {
        return Object.entries(ZEBRA_FONTS).map(([id, font]) => ({
            value: id,
            label: id + " \u2014 " + font.desc,
        }));
    }

    get fontPresetOptions() {
        return [
            { value: "custom", label: "Custom Size" },
            ...Object.entries(FONT_PRESETS).map(([id, p]) => ({
                value: id,
                label: p.label,
            })),
        ];
    }

    get fontPointSize() {
        if (!this.state.selectedData) return "";
        const dots = this.state.selectedData.font_height || 30;
        return "~" + dotsToPoints(dots, this.labelConfig.dpi) + "pt";
    }

    get variableOptions() {
        try {
            const modelName = this.props.record.data.model_name;
            return this.availableVariables
                .filter(v => !modelName || !v.model_name || v.model_name === modelName)
                .map(v => ({
                    value: v.id,
                    label: v.display_name_custom || v.name,
                    name: v.name,
                    category: v.category,
                }));
        } catch (e) {
            return [];
        }
    }

    /**
     * Known variable placeholders for barcode/QR content source dropdown.
     * If the current content matches one of these, the dropdown shows that option;
     * otherwise it shows "Custom Value".
     */
    static CONTENT_SOURCE_VARS = [
        '{{PRODUCT_BARCODE}}', '{{PRODUCT_SKU}}', '{{PRODUCT_NAME}}',
        '{{PRODUCT_PRICE}}', '{{LOT_NUMBER}}', '{{COMPANY_WEBSITE}}',
    ];

    get contentSource() {
        const content = (this.state.selectedData && this.state.selectedData.content) || '';
        if (LabelCanvasEditor.CONTENT_SOURCE_VARS.includes(content)) {
            return content;
        }
        return '__custom__';
    }

    get selectedVariableId() {
        try {
            if (!this.state.selectedData || !this.state.selectedData.variable_id) return "";
            const vid = this.state.selectedData.variable_id;
            if (Array.isArray(vid)) return String(vid[0]);
            if (vid && typeof vid === "object" && vid.id) return String(vid.id);
            return String(vid || "");
        } catch (e) {
            return "";
        }
    }

    async _loadAvailableVariables() {
        try {
            this.availableVariables = await this.orm.searchRead(
                "vpa.label.variable",
                [],
                ["id", "name", "display_name_custom", "category", "model_name"],
                { order: "category, name" }
            );
        } catch (e) {
            if (!String(e).includes("destroyed")) {
                console.warn("[VPA Canvas] Failed to load variables:", e);
            }
            this.availableVariables = [];
        }
    }

    async _loadCompanyLogo() {
        try {
            const companyId = this.props.record.data.company_id;
            const cid = companyId ? (Array.isArray(companyId) ? companyId[0] : (companyId.id || companyId)) : false;
            if (!cid) return;
            const result = await this.orm.read("res.company", [cid], ["logo"]);
            if (result && result[0] && result[0].logo) {
                this.companyLogoDataUri = "data:image/png;base64," + result[0].logo;
            }
        } catch (e) {
            if (!String(e).includes("destroyed")) {
                console.warn("[VPA Canvas] Failed to load company logo:", e);
            }
        }
    }

    // ─── Canvas Initialization ──────────────────────────────────

    _initCanvas() {
        const container = this.canvasContainerRef.el;
        if (!container || this.stage) return;

        if (typeof Konva === "undefined") {
            console.error("[VPA Canvas] Konva.js not loaded");
            return;
        }

        const config = this.labelConfig;
        if (!config.width || !config.height) return;
        const padding = 40;
        const containerWidth = container.clientWidth || 700;
        const containerHeight = container.clientHeight || 500;
        const scaleX = (containerWidth - padding * 2) / config.width;
        const scaleY = (containerHeight - padding * 2) / config.height;
        const autoZoom = Math.min(scaleX, scaleY, 1.5);

        const stageWidth = containerWidth;
        const stageHeight = Math.max(config.height * autoZoom + padding * 2, containerHeight);

        this.state.zoom = Math.round(autoZoom * 100);
        this.state.labelWidth = config.width;
        this.state.labelHeight = config.height;
        this.state.dpi = config.dpi;

        this.stage = new Konva.Stage({
            container: container,
            width: stageWidth,
            height: stageHeight,
        });

        this.labelOffsetX = Math.round((stageWidth - config.width * autoZoom) / 2);
        this.labelOffsetY = padding;

        // Background layer
        this.bgLayer = new Konva.Layer({ listening: false });
        this.stage.add(this.bgLayer);
        this.bgLayer.add(new Konva.Rect({
            x: 0, y: 0, width: stageWidth, height: stageHeight, fill: "#e8e8e8",
        }));
        this.bgLayer.add(new Konva.Rect({
            x: this.labelOffsetX, y: this.labelOffsetY,
            width: config.width * autoZoom, height: config.height * autoZoom,
            fill: "#ffffff",
            shadowColor: "rgba(0,0,0,0.2)", shadowBlur: 10, shadowOffsetX: 2, shadowOffsetY: 2,
            cornerRadius: 2,
        }));
        this.bgLayer.draw();

        // Grid layer
        this.gridLayerObj = new GridLayer(this.stage, {
            labelOffsetX: this.labelOffsetX, labelOffsetY: this.labelOffsetY,
            labelWidth: config.width, labelHeight: config.height,
            zoom: autoZoom, spacingMm: this.state.gridSpacingMm,
            dpi: config.dpi, visible: this.state.gridVisible,
        });

        // Element layer
        this.elementLayer = new Konva.Layer({
            x: this.labelOffsetX, y: this.labelOffsetY,
            scaleX: autoZoom, scaleY: autoZoom,
            clip: { x: 0, y: 0, width: config.width, height: config.height },
        });
        this.stage.add(this.elementLayer);

        // Transformer
        this.transformer = new Konva.Transformer({
            rotateEnabled: false,
            enabledAnchors: [
                "middle-left", "middle-right", "top-center", "bottom-center",
                "top-left", "top-right", "bottom-left", "bottom-right",
            ],
            borderStroke: "#0078d4", borderStrokeWidth: 1.5,
            anchorStroke: "#0078d4", anchorFill: "#ffffff", anchorSize: 8, padding: 2,
        });
        this.elementLayer.add(this.transformer);

        // Stage click handler (Shift+click = multi-select)
        this.stage.on("click tap", (e) => {
            if (e.target === this.stage || e.target.getLayer() === this.bgLayer) {
                this._deselectAll();
                return;
            }
            let node = e.target;
            while (node && !node.getAttr("elementRecordId") && node.parent) {
                node = node.parent;
            }
            if (node && node.getAttr("elementRecordId")) {
                if (e.evt && e.evt.shiftKey) {
                    this._toggleMultiSelect(node);
                } else {
                    this._selectNode(node);
                }
            }
        });

        // Keyboard handler
        this._keyHandler = (e) => this._onKeyDown(e);
        document.addEventListener("keydown", this._keyHandler);

        this.factory = new ElementFactory(this);
        this.state.canvasReady = true;

    }

    _destroyCanvas() {
        if (this._keyHandler) {
            document.removeEventListener("keydown", this._keyHandler);
            this._keyHandler = null;
        }
        if (this.gridLayerObj) {
            this.gridLayerObj.destroy();
            this.gridLayerObj = null;
        }
        if (this.stage) {
            this.stage.destroy();
            this.stage = null;
        }
        this.bgLayer = null;
        this.elementLayer = null;
        this.transformer = null;
        this.factory = null;
        this.nodeMap.clear();
        this.state.canvasReady = false;
    }

    // ─── Element Rendering ──────────────────────────────────────

    _loadElementsToCanvas() {
        if (!this.stage || !this.factory) return;
        const list = this._getList();
        if (!list) return;

        this.nodeMap.forEach((node) => node.destroy());
        this.nodeMap.clear();

        const records = list.records || [];
        for (const record of records) {
            this._addNodeForRecord(record);
        }
        this.elementLayer.draw();
    }

    _syncElementsToCanvas() {
        if (!this.stage || !this.factory) return;
        const list = this._getList();
        if (!list) return;

        const records = list.records || [];
        const currentKeys = new Set(records.map(r => this._recordKey(r)));

        // Detach transformer before destroying nodes to avoid stale references
        const selectedNodes = this.transformer ? this.transformer.nodes() : [];
        let needReattach = false;

        for (const [key, node] of this.nodeMap.entries()) {
            if (!currentKeys.has(key)) {
                if (selectedNodes.includes(node)) needReattach = true;
                node.destroy();
                this.nodeMap.delete(key);
            }
        }

        for (const record of records) {
            const key = this._recordKey(record);
            if (this.nodeMap.has(key)) {
                const existing = this.nodeMap.get(key);
                const result = this.factory.updateNode(existing, record.data);
                if (!result) {
                    // Node type mismatch — destroy old and recreate
                    if (selectedNodes.includes(existing)) needReattach = true;
                    existing.destroy();
                    this.nodeMap.delete(key);
                    this._addNodeForRecord(record);
                }
            } else {
                this._addNodeForRecord(record);
            }
        }

        // Re-attach transformer to the current selected node(s)
        if (needReattach && this.transformer) {
            const selKey = this.state.selectedElementId;
            const newNode = selKey ? this.nodeMap.get(selKey) : null;
            this.transformer.nodes(newNode ? [newNode] : []);
        }

        this.elementLayer.draw();
    }

    _addNodeForRecord(record) {
        const key = this._recordKey(record);
        const node = this.factory.createFromData(record.data, key);
        if (!node) return;

        node.on("dragstart", () => {
            // Don't reset multi-selection if this node is already selected
            if (!this.state.selectedElementIds.includes(key)) {
                this._selectNode(node);
            }
        });
        node.on("dragmove", () => {
            if (this.state.snapEnabled) {
                node.x(this._snapToGrid(node.x()));
                node.y(this._snapToGrid(node.y()));
            }
        });
        node.on("dragend", () => {
            // Save positions of all selected nodes (handles multi-select drag)
            for (const id of this.state.selectedElementIds) {
                const n = this.nodeMap.get(id);
                if (n) {
                    this._updateRecordPosition(id, Math.round(n.x()), Math.round(n.y()));
                }
            }
        });
        node.on("transformend", () => this._onTransformEnd(node, key));

        this.elementLayer.add(node);
        this.transformer.moveToTop();
        this.nodeMap.set(key, node);
    }

    _recordKey(record) {
        if (record.resId) return String(record.resId);
        if (record._virtualId) return record._virtualId;
        return "idx_" + (this.list ? this.list.records.indexOf(record) : 0);
    }

    // ─── Selection ──────────────────────────────────────────────

    _selectNode(node) {
        const key = node.getAttr("elementRecordId");
        const elemType = node.getAttr("elementType");

        if (elemType === "line") {
            this.transformer.enabledAnchors(["middle-left", "middle-right"]);
        } else if (elemType === "v_line") {
            this.transformer.enabledAnchors(["top-center", "bottom-center"]);
        } else if (elemType === "barcode") {
            this.transformer.enabledAnchors(["bottom-center"]);
        } else if (elemType === "qr_code") {
            this.transformer.enabledAnchors([]);
        } else if (elemType === "text" || elemType === "variable") {
            const record = this._findRecord(key);
            const hasMaxWidth = record && record.data.max_width > 0;
            if (hasMaxWidth) {
                this.transformer.enabledAnchors([
                    "middle-left", "middle-right",
                ]);
            } else {
                this.transformer.enabledAnchors(["top-left", "top-right", "bottom-left", "bottom-right"]);
            }
        } else if (elemType === "image" || elemType === "company_logo") {
            this.transformer.enabledAnchors(["top-left", "top-right", "bottom-left", "bottom-right"]);
        } else {
            this.transformer.enabledAnchors([
                "middle-left", "middle-right", "top-center", "bottom-center",
                "top-left", "top-right", "bottom-left", "bottom-right",
            ]);
        }

        this.transformer.nodes([node]);
        this.elementLayer.draw();
        this.state.selectedElementId = key;
        this.state.selectedElementIds = [key];
        this.state.multiSelectCount = 1;
        this._refreshSelectedData(key);
    }

    _toggleMultiSelect(node) {
        const key = node.getAttr("elementRecordId");
        const ids = [...this.state.selectedElementIds];
        const idx = ids.indexOf(key);

        if (idx >= 0) {
            // Remove from selection
            ids.splice(idx, 1);
        } else {
            // Add to selection
            ids.push(key);
        }

        if (ids.length === 0) {
            this._deselectAll();
            return;
        }

        // Gather nodes for transformer
        const nodes = [];
        for (const id of ids) {
            const n = this.nodeMap.get(id);
            if (n) nodes.push(n);
        }

        // Multi-select: disable resize anchors, only allow drag
        if (nodes.length > 1) {
            this.transformer.enabledAnchors([]);
        } else if (nodes.length === 1) {
            // Single selection — restore anchors
            this._selectNode(nodes[0]);
            return;
        }

        this.transformer.nodes(nodes);
        this.elementLayer.draw();
        this.state.selectedElementIds = ids;
        this.state.multiSelectCount = ids.length;
        // Primary selection = last item for properties panel
        this.state.selectedElementId = ids[ids.length - 1];
        this._refreshSelectedData(ids[ids.length - 1]);
    }

    _deselectAll() {
        if (this.transformer) {
            this.transformer.nodes([]);
            if (this.elementLayer) this.elementLayer.draw();
        }
        this.state.selectedElementId = null;
        this.state.selectedElementIds = [];
        this.state.multiSelectCount = 0;
        this.state.selectedData = null;
    }

    _refreshSelectedData(key) {
        const record = this._findRecord(key);
        if (record) {
            this.state.selectedData = Object.assign({}, record.data);
        } else {
            this.state.selectedData = null;
        }
    }

    _findRecord(key) {
        const list = this._getList();
        if (!list) return null;
        const records = list.records || [];
        return records.find(r => this._recordKey(r) === key) || null;
    }

    // ─── Grid & Snap ────────────────────────────────────────────

    _snapToGrid(value) {
        if (!this.state.snapEnabled) return value;
        const dotsPerMm = this.state.dpi / 25.4;
        const gridDots = this.state.gridSpacingMm * dotsPerMm;
        return Math.round(value / gridDots) * gridDots;
    }

    // ─── Data Sync ──────────────────────────────────────────────

    async _updateRecordPosition(key, x, y) {
        const record = this._findRecord(key);
        if (!record) return;
        await record.update({ pos_x: x, pos_y: y });
        if (this.state.selectedElementId === key) {
            this._refreshSelectedData(key);
        }
    }

    async _updateRecordField(key, fieldName, value) {
        const record = this._findRecord(key);
        if (!record) return;
        await record.update({ [fieldName]: value });

        const updated = this._findRecord(key);
        if (!updated) return;
        this.state.selectedData = Object.assign({}, updated.data);

        const node = this.nodeMap.get(key);
        if (node && this.factory) {
            this.factory.updateNode(node, updated.data);
            if (this.elementLayer) this.elementLayer.draw();
        }
    }

    async _onTransformEnd(node, key) {
        const elemType = node.getAttr("elementType");
        const scaleX = node.scaleX();
        const scaleY = node.scaleY();
        const updates = {
            pos_x: Math.round(node.x()),
            pos_y: Math.round(node.y()),
        };

        if (elemType === "line") {
            updates.shape_width = Math.max(1, Math.round(node.width() * scaleX));
            updates.border_thickness = Math.max(1, Math.round(node.height() * scaleY));
        } else if (elemType === "v_line") {
            updates.shape_height = Math.max(1, Math.round(node.height() * scaleY));
            updates.border_thickness = Math.max(1, Math.round(node.width() * scaleX));
        } else if (elemType === "box") {
            updates.shape_width = Math.max(1, Math.round(node.width() * scaleX));
            updates.shape_height = Math.max(1, Math.round(node.height() * scaleY));
        } else if (elemType === "barcode") {
            const record = this._findRecord(key);
            const currentH = (record && record.data.barcode_height) || 100;
            updates.barcode_height = Math.max(20, Math.round(currentH * scaleY));
        } else if (elemType === "image" || elemType === "company_logo") {
            // For image groups, compute new width from the group's first child or scale
            const children = node.getChildren ? node.getChildren() : [];
            const firstChild = children.length > 0 ? children[0] : null;
            const childW = firstChild ? (firstChild.width ? firstChild.width() : 100) : 100;
            updates.image_width = Math.max(10, Math.round(childW * scaleX));
        } else if (elemType === "text" || elemType === "variable") {
            // Resize only changes max_width (box size), never font size
            const isTextGroup = typeof node.getChildren === 'function' && !(node instanceof Konva.Text);
            if (isTextGroup) {
                const children = node.getChildren();
                const rectChild = children[0];
                const currentMaxW = rectChild ? rectChild.width() : 0;
                if (currentMaxW > 0 && scaleX !== 1) {
                    updates.max_width = Math.max(20, Math.round(currentMaxW * scaleX));
                }
            } else if (scaleX !== 1) {
                const currentMaxW = node.width() || 0;
                if (currentMaxW > 0) {
                    updates.max_width = Math.max(20, Math.round(currentMaxW * scaleX));
                }
            }
        }

        node.scaleX(1);
        node.scaleY(1);

        const record = this._findRecord(key);
        if (record) {
            await record.update(updates);
            const updated = this._findRecord(key);
            if (updated) {
                this.factory.updateNode(node, updated.data);
                this.state.selectedData = Object.assign({}, updated.data);
            }
            if (this.elementLayer) this.elementLayer.draw();
        }
    }

    // ─── Keyboard Shortcuts ─────────────────────────────────────

    _onKeyDown(e) {
        if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA") return;
        if ((e.key === "Delete" || e.key === "Backspace") && this.state.selectedElementId) {
            e.preventDefault();
            this.onDeleteElement();
        }
        if (e.key === "d" && (e.ctrlKey || e.metaKey) && this.state.selectedElementId) {
            e.preventDefault();
            this.onDuplicateElement();
        }
        if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key) && this.state.selectedElementId) {
            e.preventDefault();
            const step = e.shiftKey ? 10 : 1;
            const node = this.nodeMap.get(this.state.selectedElementId);
            if (!node) return;
            let dx = 0, dy = 0;
            if (e.key === "ArrowLeft") dx = -step;
            if (e.key === "ArrowRight") dx = step;
            if (e.key === "ArrowUp") dy = -step;
            if (e.key === "ArrowDown") dy = step;
            node.x(node.x() + dx);
            node.y(node.y() + dy);
            if (this.elementLayer) this.elementLayer.draw();
            this._updateRecordPosition(this.state.selectedElementId, Math.round(node.x()), Math.round(node.y()));
        }
    }

    // ─── Toolbar Actions ────────────────────────────────────────

    async onAddElement(type) {
        const list = this._getList();
        if (!list) return;
        const defaults = this._getDefaultsForType(type);
        try {
            const newRecord = await list.addNewRecord({ position: "bottom" });
            if (newRecord) {
                await newRecord.update(defaults);
                // The sync effect creates the node; select it after a micro-task
                const key = this._recordKey(newRecord);
                setTimeout(() => {
                    const node = this.nodeMap.get(key);
                    if (node) this._selectNode(node);
                }, 50);
            }
        } catch (e) {
            console.error("[VPA Canvas] Add element error:", e);
        }
    }

    _getDefaultsForType(type) {
        const cx = Math.round(this.state.labelWidth / 4);
        const cy = Math.round(this.state.labelHeight / 4);
        const seq = (this.list && this.list.records ? this.list.records.length : 0) * 10 + 10;
        const base = { element_type: type, pos_x: cx, pos_y: cy, sequence: seq };
        switch (type) {
            case "text":
                return Object.assign(base, { content: "Text", name: "Text", font_id: "0", font_height: 30 });
            case "variable":
                return Object.assign(base, { name: "Variable" });
            case "barcode":
                return Object.assign(base, { content: "{{PRODUCT_BARCODE}}", name: "Barcode", barcode_type: "C", barcode_height: 80, barcode_module_width: 1 });
            case "qr_code":
                return Object.assign(base, { content: "{{PRODUCT_BARCODE}}", name: "QR Code", qr_magnification: 5 });
            case "line":
                return Object.assign(base, { name: "Horizontal Line", shape_width: 200, border_thickness: 3 });
            case "v_line":
                return Object.assign(base, { name: "Vertical Line", shape_height: 200, border_thickness: 3 });
            case "box":
                return Object.assign(base, { name: "Box", shape_width: 150, shape_height: 100, border_thickness: 2 });
            case "image":
                return Object.assign(base, { name: "Image", image_width: 100 });
            case "company_logo":
                return Object.assign(base, { name: "Company Logo", image_width: 100 });
            default:
                return base;
        }
    }

    async onDeleteElement() {
        if (!this.state.selectedElementId) return;
        const list = this._getList();
        if (!list) return;
        const key = this.state.selectedElementId;
        const record = this._findRecord(key);
        if (!record) return;

        const node = this.nodeMap.get(key);
        if (node) { node.destroy(); this.nodeMap.delete(key); }
        this._deselectAll();
        await list.delete(record);
        if (this.elementLayer) this.elementLayer.draw();
    }

    async onDuplicateElement() {
        if (!this.state.selectedElementId) return;
        const list = this._getList();
        if (!list) return;
        const record = this._findRecord(this.state.selectedElementId);
        if (!record) return;

        try {
            // Use server-side copy() to duplicate with all fields properly
            const srcId = record.resId;
            if (!srcId) {
                console.warn("[VPA Canvas] Cannot duplicate unsaved element");
                return;
            }
            const newId = await this.orm.call("vpa.label.element", "copy", [srcId], {
                default: {
                    pos_x: (record.data.pos_x || 0) + 20,
                    pos_y: (record.data.pos_y || 0) + 20,
                    name: (record.data.name || "Element") + " (copy)",
                    sequence: (record.data.sequence || 0) + 1,
                },
            });
            // Reload the parent record to pick up the new element
            await this.props.record.load();
            this.props.record.model.notify();
            // Select the new element after re-render
            setTimeout(() => {
                const node = this.nodeMap.get(String(newId));
                if (node) this._selectNode(node);
            }, 100);
        } catch (e) {
            console.error("[VPA Canvas] Duplicate error:", e);
        }
    }

    // ─── Zoom Controls ──────────────────────────────────────────

    onZoomIn() { this._setZoom(Math.min(this.state.zoom + 10, 200)); }
    onZoomOut() { this._setZoom(Math.max(this.state.zoom - 10, 30)); }

    onZoomFit() {
        if (!this.canvasContainerRef.el) return;
        const c = this.canvasContainerRef.el;
        const cfg = this.labelConfig;
        const p = 40;
        this._setZoom(Math.round(Math.min((c.clientWidth - p * 2) / cfg.width, (c.clientHeight - p * 2) / cfg.height, 1.5) * 100));
    }

    _setZoom(zoomPct) {
        if (!this.stage) return;
        this.state.zoom = zoomPct;
        const zoom = zoomPct / 100;

        if (this.elementLayer) {
            this.elementLayer.scaleX(zoom);
            this.elementLayer.scaleY(zoom);
            this.labelOffsetX = Math.round((this.stage.width() - this.state.labelWidth * zoom) / 2);
            this.labelOffsetY = 40;
            this.elementLayer.x(this.labelOffsetX);
            this.elementLayer.y(this.labelOffsetY);
        }

        if (this.bgLayer) {
            const children = this.bgLayer.getChildren();
            if (children.length >= 2) {
                children[1].x(this.labelOffsetX);
                children[1].y(this.labelOffsetY);
                children[1].width(this.state.labelWidth * zoom);
                children[1].height(this.state.labelHeight * zoom);
            }
            this.bgLayer.draw();
        }

        if (this.gridLayerObj) {
            this.gridLayerObj.options.zoom = zoom;
            this.gridLayerObj.options.labelOffsetX = this.labelOffsetX;
            this.gridLayerObj.options.labelOffsetY = this.labelOffsetY;
            if (this.state.gridVisible) this.gridLayerObj.draw();
        }

        if (this.elementLayer) this.elementLayer.draw();
    }

    onToggleGrid() {
        this.state.gridVisible = !this.state.gridVisible;
        if (this.gridLayerObj) this.gridLayerObj.toggle(this.state.gridVisible);
    }

    onToggleSnap() {
        this.state.snapEnabled = !this.state.snapEnabled;
    }

    // ─── Properties Panel ───────────────────────────────────────

    onPropertyChange(fieldName, ev) {
        if (!this.state.selectedElementId) return;
        let value = ev.target.value;
        const intFields = [
            "pos_x", "pos_y", "font_height", "font_width",
            "barcode_height", "barcode_module_width", "qr_magnification",
            "shape_width", "shape_height", "border_thickness", "image_width", "max_width", "sequence",
        ];
        if (intFields.includes(fieldName)) value = parseInt(value) || 0;
        if (fieldName === "show_text_below") value = ev.target.checked;
        this._updateRecordField(this.state.selectedElementId, fieldName, value);
    }

    onContentSourceChange(ev) {
        if (!this.state.selectedElementId) return;
        const source = ev.target.value;
        if (source === '__custom__') {
            // Keep existing content — user will type their own value
            return;
        }
        // Set content to the selected variable placeholder
        this._updateRecordField(this.state.selectedElementId, 'content', source);
    }

    async onVariableChange(ev) {
        if (!this.state.selectedElementId) return;
        const varId = parseInt(ev.target.value) || false;
        const key = this.state.selectedElementId;
        const record = this._findRecord(key);
        if (!record) return;

        const varRec = this.availableVariables.find(v => v.id === varId);
        await record.update({
            variable_id: varId ? { id: varId, display_name: varRec ? (varRec.display_name_custom || varRec.name) : "" } : false,
        });

        const updated = this._findRecord(key);
        if (!updated) return;
        this.state.selectedData = Object.assign({}, updated.data);
        const node = this.nodeMap.get(key);
        if (node && this.factory) {
            this.factory.updateNode(node, updated.data);
            if (this.elementLayer) this.elementLayer.draw();
        }
    }

    async onFontPresetChange(ev) {
        if (!this.state.selectedElementId) return;
        const preset = ev.target.value;
        if (preset === "custom") return;
        const presetData = FONT_PRESETS[preset];
        if (!presetData) return;

        const key = this.state.selectedElementId;
        const record = this._findRecord(key);
        if (!record) return;

        await record.update({ font_id: presetData.fontId, font_height: presetData.height, font_width: presetData.width });
        const updated = this._findRecord(key);
        if (!updated) return;
        this.state.selectedData = Object.assign({}, updated.data);
        const node = this.nodeMap.get(key);
        if (node && this.factory) {
            this.factory.updateNode(node, updated.data);
            if (this.elementLayer) this.elementLayer.draw();
        }
    }

    async onImageUpload(ev) {
        if (!this.state.selectedElementId) return;
        const file = ev.target.files && ev.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (e) => {
            const dataUrl = e.target.result;
            // Extract base64 part (after "data:image/...;base64,")
            const b64 = dataUrl.split(",")[1];
            if (!b64) return;

            const key = this.state.selectedElementId;
            const record = this._findRecord(key);
            if (!record) return;

            await record.update({ image_data: b64 });
            const updated = this._findRecord(key);
            if (!updated) return;
            this.state.selectedData = Object.assign({}, updated.data);

            const node = this.nodeMap.get(key);
            if (node && this.factory) {
                this.factory.updateNode(node, updated.data);
                if (this.elementLayer) this.elementLayer.draw();
            }
        };
        reader.readAsDataURL(file);
    }

    // ─── Z-Order ────────────────────────────────────────────────

    onBringForward() {
        if (!this.state.selectedElementId) return;
        const node = this.nodeMap.get(this.state.selectedElementId);
        if (node) { node.moveUp(); this.transformer.moveToTop(); this.elementLayer.draw(); }
    }

    onSendBackward() {
        if (!this.state.selectedElementId) return;
        const node = this.nodeMap.get(this.state.selectedElementId);
        if (node) { node.moveDown(); this.transformer.moveToTop(); this.elementLayer.draw(); }
    }

    // ─── Alignment ────────────────────────────────────────────────

    _getSelectedNodes() {
        const nodes = [];
        for (const id of this.state.selectedElementIds) {
            const n = this.nodeMap.get(id);
            if (n) nodes.push({ node: n, key: id });
        }
        return nodes;
    }

    _getNodeBounds(node) {
        const rect = node.getClientRect({ relativeTo: this.elementLayer });
        return {
            x: rect.x,
            y: rect.y,
            width: rect.width,
            height: rect.height,
            right: rect.x + rect.width,
            bottom: rect.y + rect.height,
        };
    }

    async _applyAlignmentPositions(items) {
        for (const { node, key, x, y } of items) {
            const newX = x !== undefined ? x : node.x();
            const newY = y !== undefined ? y : node.y();
            node.x(newX);
            node.y(newY);
            await this._updateRecordPosition(key, Math.round(newX), Math.round(newY));
        }
        if (this.elementLayer) this.elementLayer.draw();
    }

    async onAlignLeft() {
        const selected = this._getSelectedNodes();
        if (selected.length < 2) return;
        const bounds = selected.map(s => ({ ...s, bounds: this._getNodeBounds(s.node) }));
        const minX = Math.min(...bounds.map(b => b.bounds.x));
        const items = bounds.map(b => ({
            node: b.node, key: b.key,
            x: b.node.x() + (minX - b.bounds.x),
        }));
        await this._applyAlignmentPositions(items);
    }

    async onAlignRight() {
        const selected = this._getSelectedNodes();
        if (selected.length < 2) return;
        const bounds = selected.map(s => ({ ...s, bounds: this._getNodeBounds(s.node) }));
        const maxRight = Math.max(...bounds.map(b => b.bounds.right));
        const items = bounds.map(b => ({
            node: b.node, key: b.key,
            x: b.node.x() + (maxRight - b.bounds.right),
        }));
        await this._applyAlignmentPositions(items);
    }

    async onAlignTop() {
        const selected = this._getSelectedNodes();
        if (selected.length < 2) return;
        const bounds = selected.map(s => ({ ...s, bounds: this._getNodeBounds(s.node) }));
        const minY = Math.min(...bounds.map(b => b.bounds.y));
        const items = bounds.map(b => ({
            node: b.node, key: b.key,
            y: b.node.y() + (minY - b.bounds.y),
        }));
        await this._applyAlignmentPositions(items);
    }

    async onAlignBottom() {
        const selected = this._getSelectedNodes();
        if (selected.length < 2) return;
        const bounds = selected.map(s => ({ ...s, bounds: this._getNodeBounds(s.node) }));
        const maxBottom = Math.max(...bounds.map(b => b.bounds.bottom));
        const items = bounds.map(b => ({
            node: b.node, key: b.key,
            y: b.node.y() + (maxBottom - b.bounds.bottom),
        }));
        await this._applyAlignmentPositions(items);
    }

    async onAlignCenterH() {
        const selected = this._getSelectedNodes();
        if (selected.length < 2) return;
        const bounds = selected.map(s => ({ ...s, bounds: this._getNodeBounds(s.node) }));
        const centerXs = bounds.map(b => b.bounds.x + b.bounds.width / 2);
        const avgCenterX = centerXs.reduce((a, b) => a + b, 0) / centerXs.length;
        const items = bounds.map(b => ({
            node: b.node, key: b.key,
            x: b.node.x() + (avgCenterX - (b.bounds.x + b.bounds.width / 2)),
        }));
        await this._applyAlignmentPositions(items);
    }

    async onAlignCenterV() {
        const selected = this._getSelectedNodes();
        if (selected.length < 2) return;
        const bounds = selected.map(s => ({ ...s, bounds: this._getNodeBounds(s.node) }));
        const centerYs = bounds.map(b => b.bounds.y + b.bounds.height / 2);
        const avgCenterY = centerYs.reduce((a, b) => a + b, 0) / centerYs.length;
        const items = bounds.map(b => ({
            node: b.node, key: b.key,
            y: b.node.y() + (avgCenterY - (b.bounds.y + b.bounds.height / 2)),
        }));
        await this._applyAlignmentPositions(items);
    }
}

export const labelCanvasEditor = {
    component: LabelCanvasEditor,
    displayName: _t("Label Canvas Editor"),
    supportedTypes: ["one2many"],
};

registry.category("fields").add("label_canvas_editor", labelCanvasEditor);
