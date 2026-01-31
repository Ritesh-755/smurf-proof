import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

export default function AMLTransactionGraph() {
  const svgRef = useRef(null);
  const [mode, setMode] = useState("rule");

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = window.innerWidth;
    const height = svgRef.current.clientHeight;

    // ===== ARROW =====
    svg.append("defs")
      .append("marker")
      .attr("id", "arrow")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 26)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "#ffd166");

    // ===== DATA =====
    const nodes = [
      { id: "wallet1" }, { id: "wallet2" }, { id: "wallet3" },
      { id: "wallet4" }, { id: "wallet5" }, { id: "wallet6" },
      { id: "wallet7" }, { id: "wallet8" },
      { id: "wallet9" }, { id: "wallet10" },
      { id: "wallet11" }, { id: "wallet12" },
      { id: "wallet13" }, { id: "wallet14" }
    ];

    const links = [
      { source: "wallet1", target: "wallet2" },
      { source: "wallet1", target: "wallet3" },
      { source: "wallet1", target: "wallet4" },
      { source: "wallet1", target: "wallet9" },
      { source: "wallet2", target: "wallet5" },
      { source: "wallet3", target: "wallet6" },
      { source: "wallet4", target: "wallet7" },
      { source: "wallet9", target: "wallet10" },
      { source: "wallet5", target: "wallet8" },
      { source: "wallet6", target: "wallet8" },
      { source: "wallet7", target: "wallet8" },
      { source: "wallet10", target: "wallet8" },
      { source: "wallet8", target: "wallet11" },
      { source: "wallet11", target: "wallet12" },
      { source: "wallet11", target: "wallet13" },
      { source: "wallet12", target: "wallet14" },
      { source: "wallet13", target: "wallet14" }
    ];

    // ===== FAN COUNTS =====
    const fanOut = {}, fanIn = {};
    nodes.forEach(n => fanOut[n.id] = fanIn[n.id] = 0);
    links.forEach(l => { fanOut[l.source]++; fanIn[l.target]++; });

    // ===== RISKS =====
    const ruleRisk = {}, gnnRiskBase = {};
    nodes.forEach((n, i) => {
      ruleRisk[n.id] = Math.max(0.15, 0.95 - i * 0.05);
      gnnRiskBase[n.id] = Math.max(0.2, 0.97 - i * 0.05);
    });

    let gnnRisk = { ...gnnRiskBase };

    // ===== SIM =====
    const sim = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(85))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2));

    // ===== DRAG =====
    const drag = d3.drag()
      .on("start", (e, d) => {
        if (!e.active) sim.alphaTarget(0.3).restart();
        d.fx = d.x; d.fy = d.y;
      })
      .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; })
      .on("end", (e, d) => {
        if (!e.active) sim.alphaTarget(0);
        d.fx = null; d.fy = null;
      });

    // ===== LINKS =====
    const link = svg.append("g")
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("stroke", "#94a3b8")
      .attr("stroke-width", 1.4)
      .attr("stroke-dasharray", "6 6")
      .attr("marker-end", "url(#arrow)");

    // ===== NODES =====
    const node = svg.append("g")
      .selectAll("g")
      .data(nodes)
      .enter()
      .append("g")
      .call(drag);

    node.append("circle")
      .attr("r", 9)
      .attr("stroke", "white")
      .attr("stroke-width", 1.3)
      .attr("fill", "#facc15");

    node.append("text")
      .attr("dx", 14)
      .attr("dy", 4)
      .attr("fill", "white")
      .attr("font-size", 11)
      .text(d => d.id);

    const riskText = node.append("text")
      .attr("dx", 14)
      .attr("dy", 16)
      .attr("fill", "#facc15")
      .attr("font-size", 10);

    // ===== DASH ANIMATION =====
    let dash = 0;
    d3.timer(() => {
      dash -= 0.6;
      link.attr("stroke-dashoffset", dash);
    });

    // ===== TICK =====
    sim.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    // ===== UPDATE =====
    function update() {
      const risk = mode === "rule" ? ruleRisk : gnnRisk;

      node.select("circle")
        .attr("fill", d =>
          fanOut[d.id] >= 2 && risk[d.id] > 0.6 ? "#ef4444" :
          fanIn[d.id] >= 2 && risk[d.id] > 0.6 ? "#38bdf8" :
          "#facc15"
        );

      link
        .attr("stroke", d =>
          fanOut[d.source.id] >= 2 && risk[d.source.id] > 0.6 ? "#ef4444" :
          fanIn[d.target.id] >= 2 && risk[d.target.id] > 0.6 ? "#38bdf8" :
          "#94a3b8"
        )
        .attr("stroke-width", d =>
          (fanOut[d.source.id] >= 2 && risk[d.source.id] > 0.6) ||
          (fanIn[d.target.id] >= 2 && risk[d.target.id] > 0.6)
            ? 3
            : 1.4
        );

      riskText.text(d => `Risk ${(risk[d.id] * 100).toFixed(0)}%`);
    }

    // ===== GNN PROP =====
    const interval = setInterval(() => {
      if (mode === "gnn") {
        links.forEach(l => {
          gnnRisk[l.target.id] = Math.max(
            gnnRisk[l.target.id],
            gnnRisk[l.source.id] * 0.85
          );
        });
        update();
      }
    }, 1200);

    update();
    sim.alpha(1).restart();

    return () => clearInterval(interval);
  }, [mode]);

  return (
    <div className="bg-slate-950 text-white min-h-screen">
      <header className="flex items-center gap-5 px-6 py-4 bg-slate-900">
        <h1 className="text-lg font-semibold">AML Smurfing Detection</h1>
        <select
          className="bg-slate-800 border border-slate-600 rounded px-3 py-1"
          value={mode}
          onChange={e => setMode(e.target.value)}
        >
          <option value="rule">Rule-Based AML</option>
          <option value="gnn">GNN-Based AML</option>
        </select>
      </header>

      <div className="px-6 py-2 text-sm opacity-90 bg-slate-950">
        {mode === "rule"
          ? "Rule-based AML: flags fan-in / fan-out only when risk exceeds threshold."
          : "GNN AML: risk propagates through transaction paths revealing hidden smurfing."}
      </div>

      <svg ref={svgRef} className="w-screen h-[70vh]" />
    </div>
  );
}
