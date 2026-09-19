"use client";
import "@xyflow/react/dist/style.css";
import "./process-map.css";
import * as React from "react";
import Link from "next/link";
import { Background, BackgroundVariant, Controls, MarkerType, MiniMap, Panel, ReactFlow, ReactFlowProvider, useReactFlow } from "@xyflow/react";
import { ArrowUpRight, ChevronDown } from "lucide-react";
import type { GraphNode, NodeType } from "@/lib/synforma/types";
import { cn } from "@/lib/utils";
import { COLORS } from "../constants";
import { MapInteractionContext, type MapInteraction } from "./context";
import { edgeColor, edgeTypes, type MapFlowEdge } from "./edges";
import type { ProcessLayout } from "./layout";
import { TRUST_TONE_LABEL, type Lens, type MapNode, type TrustTone } from "./model";
import { nodeTypes, type MapFlowNode } from "./nodes";

/**
 * ProcessMap — the 2D process map of the Work Graph (React Flow + the layered
 * layout in ./layout.ts). Fits the view on mount and whenever the lens or the
 * set of nodes changes; pans to a node on request; hover lights a node's
 * neighbourhood; click selects. Nodes are buttons, so the map is keyboard
 * reachable. The legend changes per lens.
 */

export interface FocusRequest {
  id: string;
  nonce: number;
}

export interface ProcessMapProps {
  layout: ProcessLayout;
  lens: Lens;
  selectedId: string | null;
  highlightIds: readonly string[];
  onSelectNode: (node: GraphNode | null) => void;
  /** Pan and zoom to this node whenever the nonce changes. */
  focus?: FocusRequest | null;
  sample?: boolean;
  /** Open the legend by default (large viewports). */
  legendOpen?: boolean;
  /** Node count of the stored graph, for "N of M nodes on this lens". */
  totalNodes: number;
  className?: string;
}

const MINIMAP_COLOR: Partial<Record<NodeType, string>> = {
  objective: COLORS.ink,
  outcome: COLORS.ink,
  workflow: COLORS.graphite,
  step: COLORS.graphite,
  screen: COLORS.mist,
  application: COLORS.slate,
};

const TONES: readonly TrustTone[] = ["live", "approved", "observed", "inferred", "contested"];
const TONE_COLOR: Record<TrustTone, string> = {
  live: "var(--verdant)",
  approved: "var(--ink)",
  observed: "var(--graphite)",
  inferred: "var(--amber)",
  contested: "var(--signal)",
  unknown: "var(--mist)",
  illustrative: "var(--mist)",
};

function Legend({ layout, lens, sample, open, totalNodes }: { layout: ProcessLayout; lens: Lens; sample: boolean; open: boolean; totalNodes: number }) {
  const { model } = layout;
  const shown = layout.nodes.length;
  const dialogs = layout.nodes.filter((n) => n.type === "screen" && n.dialog).length;
  return (
    <details className="pm-legend" open={open} data-testid="graph-legend" data-lens={lens}>
      <summary>
        <span className="eyebrow text-[9px]">Legend · {lens}</span>
        <ChevronDown className="h-3 w-3 text-mist" aria-hidden="true" />
      </summary>
      <div className="pm-legend-body">
        <p className="pm-legend-note mono-data" data-testid="graph-legend-count">
          {shown} of {totalNodes} nodes on this lens
        </p>
        {lens === "workflow" || lens === "evidence" || lens === "runs" ? (
          <>
            <div className="pm-legend-row">
              <span className={cn("pm-legend-line", lens === "runs" && "pm-legend-line--traffic")} aria-hidden="true" />
              <span>{lens === "runs" ? "Intended path · width and count: runs that took it" : "Intended path (objective → steps → outcome)"}</span>
            </div>
            {lens === "runs" ? (
              <div className="pm-legend-row">
                <span className="pm-legend-line pm-legend-line--observed" aria-hidden="true" />
                <span>Observed detour: back or skip</span>
              </div>
            ) : null}
            <div className="pm-legend-row">
              <span className="pm-legend-line pm-legend-line--dashed" aria-hidden="true" />
              <span>Attached: screen a step touches, requirement, policy</span>
            </div>
            <div className="pm-legend-row">
              <span className="pm-legend-line pm-legend-line--thin" aria-hidden="true" />
              <span>Navigation between screens</span>
            </div>
            {lens === "runs" ? (
              <>
                <div className="pm-legend-row">
                  <span className="pm-badge pm-badge--friction">3</span>
                  <span>Friction events on the step: hesitation, validation error, backtrack, inferred states</span>
                </div>
                <div className="pm-legend-row">
                  <span className="pm-badge pm-badge--heal">2</span>
                  <span>Self-healed: actions re-grounded after the interface changed</span>
                </div>
                <div className="pm-legend-row">
                  <span className="pm-badge pm-badge--drop">−1</span>
                  <span>Runs that ended on the step without completing</span>
                </div>
                <p className="pm-legend-note">Median time is step entered → step completed, across all runs of this program.</p>
              </>
            ) : null}
            {lens === "evidence" ? (
              <>
                {TONES.map((t) => (
                  <div key={t} className="pm-legend-row" data-testid={`graph-legend-tone-${t}`}>
                    <span className="pm-legend-swatch" style={{ borderLeft: `4px solid ${TONE_COLOR[t]}` }} aria-hidden="true" />
                    <span>{TRUST_TONE_LABEL[t]}</span>
                  </div>
                ))}
                {sample ? <p className="pm-legend-note">The sample carries no provenance: every node is illustrative.</p> : null}
              </>
            ) : null}
            {model.hiddenScreens ? (
              <p className="pm-legend-note" data-testid="graph-hidden-screens" data-count={model.hiddenScreens}>
                {model.hiddenScreens} discovered screen{model.hiddenScreens === 1 ? "" : "s"} not on the workflow are hidden.
              </p>
            ) : null}
          </>
        ) : (
          <>
            <div className="pm-legend-row">
              <span className="pm-legend-line pm-legend-line--thin" aria-hidden="true" />
              <span>Navigation observed during discovery, labelled by the control that caused it</span>
            </div>
            <div className="pm-legend-row">
              <span className="pm-legend-line" aria-hidden="true" />
              <span>Navigation the intended workflow uses</span>
            </div>
            <div className="pm-legend-row">
              <span className="pm-legend-line pm-legend-line--dashed" aria-hidden="true" />
              <span>Entry from the application · object a screen shows</span>
            </div>
            <p className="pm-legend-note">
              Actions and fields are counted on each screen; select a screen to list them.
              {dialogs ? ` ${dialogs} dialog${dialogs === 1 ? "" : "s"} appear as screens.` : ""}
            </p>
          </>
        )}
      </div>
    </details>
  );
}

function Canvas({ layout, lens, selectedId, highlightIds, onSelectNode, focus, sample = false, legendOpen = true, totalNodes }: ProcessMapProps) {
  const rf = useReactFlow<MapFlowNode, MapFlowEdge>();
  const [hoveredId, setHoveredId] = React.useState<string | null>(null);

  const nodes = React.useMemo<MapFlowNode[]>(
    () =>
      layout.nodes.map((n) => ({
        id: n.id,
        type: "map",
        position: { x: n.x, y: n.y },
        width: n.width,
        height: n.height,
        data: { node: n },
        draggable: false,
        selectable: false,
        connectable: false,
        focusable: false,
      })),
    [layout],
  );
  const edges = React.useMemo<MapFlowEdge[]>(
    () =>
      layout.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: `s-${e.sourceHandle}`,
        targetHandle: `t-${e.targetHandle}`,
        type: "map",
        data: { edge: e },
        markerEnd: e.kind === "structural" ? undefined : { type: MarkerType.ArrowClosed, color: edgeColor(e), width: 14, height: 14 },
        selectable: false,
        focusable: false,
        zIndex: e.happy ? 2 : e.kind === "traffic" ? 1 : 0,
      })),
    [layout],
  );

  const adjacency = React.useMemo(() => {
    const m = new Map<string, Set<string>>();
    for (const e of layout.edges) {
      (m.get(e.source) ?? m.set(e.source, new Set()).get(e.source)!).add(e.target);
      (m.get(e.target) ?? m.set(e.target, new Set()).get(e.target)!).add(e.source);
    }
    return m;
  }, [layout]);
  const highlight = React.useMemo(() => new Set(highlightIds), [highlightIds]);
  const related = React.useMemo(() => {
    const focusId = hoveredId ?? (highlight.size ? null : selectedId);
    if (!focusId) return null;
    const set = new Set<string>([focusId]);
    for (const id of adjacency.get(focusId) ?? []) set.add(id);
    return set;
  }, [hoveredId, selectedId, highlight, adjacency]);

  const select = React.useCallback((n: MapNode | null) => onSelectNode(n ? n.node : null), [onSelectNode]);
  const interaction = React.useMemo<MapInteraction>(
    () => ({ lens, selectedId, hoveredId, highlight, related, focusId: focus?.id ?? null, maxTraffic: layout.model.maxTraffic, sample, setHovered: setHoveredId, select }),
    [lens, selectedId, hoveredId, highlight, related, focus, layout.model.maxTraffic, sample, select],
  );

  // Fit the view on mount, on lens change and when the set of nodes changes.
  const nodeKey = React.useMemo(() => layout.nodes.map((n) => n.id).join("|"), [layout]);
  React.useEffect(() => {
    const id = window.requestAnimationFrame(() => {
      void rf.fitView({ padding: 0.12, maxZoom: 1, duration: 280 });
    });
    return () => window.cancelAnimationFrame(id);
  }, [rf, lens, nodeKey]);

  // Pan to a node on request (search result, intent-flow hop, detail-panel neighbour).
  React.useEffect(() => {
    if (!focus) return;
    const n = layout.nodes.find((x) => x.id === focus.id);
    if (!n) return;
    const zoom = Math.min(1.2, Math.max(rf.getZoom(), 0.85));
    void rf.setCenter(n.x + n.width / 2, n.y + n.height / 2, { zoom, duration: 360 });
  }, [rf, focus, layout]);

  const onPaneClick = React.useCallback(() => onSelectNode(null), [onSelectNode]);
  const onKeyDown = React.useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") onSelectNode(null);
    },
    [onSelectNode],
  );
  const minimapColor = React.useCallback((n: MapFlowNode) => MINIMAP_COLOR[n.data.node.type] ?? COLORS.lineStrong, []);

  return (
    <MapInteractionContext.Provider value={interaction}>
      <div className="process-map" data-testid="process-map" data-lens={lens} data-nodes={layout.nodes.length} onKeyDown={onKeyDown}>
        <ReactFlow<MapFlowNode, MapFlowEdge>
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          fitViewOptions={{ padding: 0.12, maxZoom: 1 }}
          minZoom={0.1}
          maxZoom={2.5}
          nodesDraggable={false}
          nodesConnectable={false}
          nodesFocusable={false}
          edgesFocusable={false}
          elementsSelectable={false}
          selectNodesOnDrag={false}
          zoomOnDoubleClick={false}
          panOnScroll={false}
          deleteKeyCode={null}
          selectionKeyCode={null}
          multiSelectionKeyCode={null}
          onPaneClick={onPaneClick}
          proOptions={{ hideAttribution: false }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color={COLORS.lineStrong} />
          <Controls position="bottom-left" showInteractive={false} />
          <MiniMap position="bottom-right" pannable zoomable nodeColor={minimapColor} nodeStrokeWidth={0} nodeBorderRadius={2} />
          <Panel position="top-right">
            <Legend layout={layout} lens={lens} sample={sample} open={legendOpen} totalNodes={totalNodes} />
          </Panel>
          {lens === "runs" && layout.model.runCount === 0 ? (
            <Panel position="top-left">
              <div className="max-w-xs rounded-md border border-line bg-surface/95 px-3 py-2 text-xs text-graphite shadow-sm backdrop-blur-sm" data-testid="graph-runs-empty">
                <p className="font-medium text-ink">No runs recorded for this workflow.</p>
                <p className="mt-1 leading-relaxed text-slate">
                  Run the demo in Mission Control first; traffic, friction and self-healing then appear on the intended path.
                </p>
                <Link href="/demo" className="mt-1.5 inline-flex items-center gap-1 text-ink underline-offset-2 hover:underline">
                  Open Mission Control
                  <ArrowUpRight className="h-3 w-3" aria-hidden="true" />
                </Link>
              </div>
            </Panel>
          ) : null}
        </ReactFlow>
        {layout.nodes.length === 0 ? (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center p-6" data-testid="process-map-empty">
            <div className="pointer-events-auto max-w-sm rounded-lg border border-line bg-surface px-5 py-4 text-center">
              <p className="eyebrow">Nothing on this lens</p>
              <p className="mt-2 text-xs leading-relaxed text-slate">
                {lens === "application" ? "No screens have been discovered for this program." : "This graph has no workflow to lay out, or every layer is hidden."}
              </p>
            </div>
          </div>
        ) : null}
      </div>
    </MapInteractionContext.Provider>
  );
}

export function ProcessMap(props: ProcessMapProps) {
  return (
    <ReactFlowProvider>
      <Canvas {...props} />
    </ReactFlowProvider>
  );
}
