import { useEffect, useRef } from "react";
import * as d3 from "d3";

const BASE_URL = "http://127.0.0.1:8000/api";

export default function AMLGraph() {
  const svgRef = useRef(null);

  useEffect(() => {
    Promise.all([
      fetch(`${BASE_URL}/graph/`).then(r => r.json()),
      fetch(`${BASE_URL}/final-risk/`).then(r => r.json())
    ])
      .then(([graph, finalRisk]) => {
        renderGraph(graph, finalRisk);
      })
      .catch(err => console.error("❌ API error:", err));
  }, []);

  const renderGraph = (graph, finalRisk) => {
    if (!svgRef.current) return;

    const width = window.innerWidth;
    const height = window.innerHeight;

    const riskMap = {};
    finalRisk.wallets.forEach(w => {
      riskMap[w.id] = w;
    });

    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .style("background", "#020617");

    svg.selectAll("*").remove();

    const container = svg.append("g");

    svg.call(
      d3.zoom()
        .scaleExtent([0.3, 4])
        .on("zoom", e => container.attr("transform", e.transform))
    );

    /* ============================
       DEFINITIONS (Glow + Arrow)
    ============================ */
    const defs = svg.append("defs");

    defs.append("marker")
      .attr("id", "arrow")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 22)
      .attr("refY", 0)
      .attr("markerWidth", 5)
      .attr("markerHeight", 5)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "#ef4444");

    defs.append("filter")
      .attr("id", "glow")
      .append("feGaussianBlur")
      .attr("stdDeviation", "4")
      .attr("result", "coloredBlur");

    defs.append("filter")
      .attr("id", "smurfing-glow")
      .append("feGaussianBlur")
      .attr("stdDeviation", "3")
      .attr("result", "coloredBlur");

    defs.select("#smurfing-glow")
      .append("feFlood")
      .attr("flood-color", "#ef4444")
      .attr("result", "coloredBlur");

    defs.select("#smurfing-glow")
      .append("feComposite")
      .attr("in", "coloredBlur")
      .attr("in2", "SourceGraphic")
      .attr("operator", "in")
      .attr("result", "colored");

    defs.select("#smurfing-glow")
      .append("feMerge")
      .append("feMergeNode")
      .attr("in", "colored");

    defs.select("#smurfing-glow")
      .select("feMerge")
      .append("feMergeNode")
      .attr("in", "SourceGraphic");

    /* ============================
       DEGREE → NODE SIZE
    ============================ */
    const degree = {};
    graph.edges.forEach(e => {
      degree[e.source] = (degree[e.source] || 0) + 1;
      degree[e.target] = (degree[e.target] || 0) + 1;
    });

    const radius = d3.scaleLinear()
      .domain(d3.extent(Object.values(degree)))
      .range([8, 26]);

    /* ============================
       FORCE SIMULATION
    ============================ */
    const sim = d3.forceSimulation(graph.nodes)
      .force("link", d3.forceLink(graph.edges).id(d => d.id).distance(140))
      .force("charge", d3.forceManyBody().strength(-420))
      .force("center", d3.forceCenter(width / 2, height / 2));

    /* ============================
       TOOLTIP
    ============================ */
    const tooltip = d3.select("body")
      .append("div")
      .style("position", "absolute")
      .style("background", "#020617")
      .style("border", "1px solid #334155")
      .style("padding", "8px 10px")
      .style("border-radius", "8px")
      .style("font-size", "12px")
      .style("color", "#e5e7eb")
      .style("pointer-events", "none")
      .style("opacity", 0);

    /* ============================
       LINKS (Animated)
    ============================ */
    const link = container.append("g")
      .selectAll("line")
      .data(graph.edges)
      .enter()
      .append("line")
      .attr("stroke", d =>
        d.pattern === "smurfing" ? "#ef4444" :
        d.pattern === "peeling" ? "#a855f7" :
        "#64748b"
      )
      .attr("stroke-width", d =>
        d.pattern === "smurfing" ? 4 :
        d.pattern === "peeling" ? 3 : 1.2
      )
      .attr("stroke-dasharray", d =>
        d.pattern === "peeling" ? "6 6" : "4 6"
      )
      .attr("marker-end", d =>
        d.pattern ? "url(#arrow)" : null
      )
      .attr("filter", d =>
        d.pattern === "smurfing" ? "url(#smurfing-glow)" : null
      );

    /* Animated flow */
    let dash = 0;
    d3.timer(() => {
      dash -= 0.8;
      link.attr("stroke-dashoffset", dash);
    });

    /* ============================
       NODES
    ============================ */
    const node = container.append("g")
      .selectAll("circle")
      .data(graph.nodes)
      .enter()
      .append("circle")
      .attr("r", d => radius(degree[d.id] || 1))
      .attr("fill", d => {
        const info = riskMap[d.id];
        const r = info?.final_risk ?? 0;
        if (r >= 0.85) return "#dc2626";
        if (r >= 0.6) return "#f97316";
        if (r >= 0.3) return "#22c55e";
        return "#2563eb";
      })
      .attr("filter", d =>
        d.is_involved && riskMap[d.id]?.final_risk >= 0.85
          ? "url(#glow)"
          : null
      )
      .on("mouseover", (e, d) => {
        const info = riskMap[d.id];
        tooltip
          .style("opacity", 1)
          .html(`
            <strong>${d.id}</strong><br/>
            Risk: ${(info?.final_risk * 100).toFixed(1)}%<br/>
            ${info?.reasons?.map(r => `• ${r}`).join("<br/>") || ""}
          `);
      })
      .on("mousemove", e => {
        tooltip
          .style("left", e.pageX + 12 + "px")
          .style("top", e.pageY + 12 + "px");
      })
      .on("mouseout", () => {
        tooltip.style("opacity", 0);
      })
      .call(
        d3.drag()
          .on("start", e => {
            if (!e.active) sim.alphaTarget(0.3).restart();
          })
          .on("drag", (e, d) => {
            d.fx = e.x;
            d.fy = e.y;
          })
          .on("end", e => {
            if (!e.active) sim.alphaTarget(0);
          })
      );

    /* ============================
       SIM TICK
    ============================ */
    sim.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);
    });

    /* ============================
       LEGEND
    ============================ */
    const legend = svg.append("g")
      .attr("transform", "translate(20,20)");

    const legendData = [
      { label: "High Risk Wallet", color: "#dc2626" },
      { label: "Medium Risk Wallet", color: "#f97316" },
      { label: "Low Risk Wallet", color: "#22c55e" },
      { label: "Normal Wallet", color: "#2563eb" },
      { label: "Smurfing Path", color: "#ef4444" },
      { label: "Peeling Chain", color: "#a855f7" }
    ];

    legend.selectAll("g")
      .data(legendData)
      .enter()
      .append("g")
      .attr("transform", (_, i) => `translate(0, ${i * 22})`)
      .each(function (d) {
        const g = d3.select(this);
        g.append("rect")
          .attr("width", 14)
          .attr("height", 14)
          .attr("fill", d.color);
        g.append("text")
          .attr("x", 20)
          .attr("y", 12)
          .attr("font-size", "12px")
          .attr("fill", "#e5e7eb")
          .text(d.label);
      });
  };

  return <svg ref={svgRef} className="fixed inset-0 w-full h-full" />;
}