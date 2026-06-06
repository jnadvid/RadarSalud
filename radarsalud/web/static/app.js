// RadarSalud - interacción de la página de simulación.
(function () {
  "use strict";

  const result = document.getElementById("sim-result");
  function show(msg, ok) {
    if (!result) return;
    result.innerHTML = '<div class="' + (ok ? "ok" : "err") + '">' + msg + "</div>";
    result.style.color = ok ? "#0a6b45" : "#a12525";
  }

  async function postJSON(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : null,
    });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, data };
  }

  const form = document.getElementById("sim-form");
  if (form) {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      const fd = new FormData(form);
      const payload = {
        event: fd.get("event"),
        province: fd.get("province") || null,
        autonomous_community: fd.get("autonomous_community") || null,
        severity: fd.get("severity"),
        days: parseInt(fd.get("days"), 10),
        multiplier: parseFloat(fd.get("multiplier")),
      };
      show("Lanzando simulación…", true);
      const { ok, data } = await postJSON("/api/v1/simulation/run", payload);
      if (ok) {
        show(
          "✅ Simulación #" + data.simulation_id + " creada: " +
            data.observations_created + " observaciones, " +
            data.alerts_created + " alertas (SIMULACIÓN). " +
            '<a href="/map?mode=simulation">Ver en el mapa</a>.',
          true
        );
        setTimeout(() => location.reload(), 1500);
      } else {
        show("❌ Error: " + JSON.stringify(data), false);
      }
    });
  }

  document.querySelectorAll(".preset-btn").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const name = btn.getAttribute("data-preset");
      show("Lanzando preset " + name + "…", true);
      const { ok, data } = await postJSON("/api/v1/simulation/preset/" + name, null);
      if (ok) {
        show(
          "✅ Preset '" + name + "' lanzado: simulación #" + data.simulation_id +
            ", " + data.observations_created + " obs, " + data.alerts_created +
            ' alertas. <a href="/map?mode=simulation">Ver mapa</a>.',
          true
        );
        setTimeout(() => location.reload(), 1500);
      } else {
        show("❌ Error: " + JSON.stringify(data), false);
      }
    });
  });

  // ----------------------------------------------------------------
  //  Página de fuentes: comprobar todas + toggles de activación.
  // ----------------------------------------------------------------
  async function patchJSON(url, body) {
    const res = await fetch(url, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return { ok: res.ok, data: await res.json().catch(() => ({})) };
  }

  function setRowStatus(row, ok, message) {
    const cell = row.querySelector(".cell-status");
    if (!cell) return;
    if (ok === true) cell.innerHTML = '<span title="' + (message || "") + '">🟢 operativa</span>';
    else if (ok === false) cell.innerHTML = '<span title="' + (message || "") + '">🔴 caída</span>';
    else cell.innerHTML = '<span class="muted" title="' + (message || "") + '">⚪ —</span>';
  }

  const checkBtn = document.getElementById("btn-check-all");
  if (checkBtn) {
    const out = document.getElementById("check-result");
    checkBtn.addEventListener("click", async function () {
      const includeDatasets = document.getElementById("include-datasets").checked;
      checkBtn.disabled = true;
      out.textContent = "Comprobando fuentes… (puede tardar)";
      const { ok, data } = await postJSON(
        "/api/v1/sources/check?include_datasets=" + includeDatasets, null
      );
      checkBtn.disabled = false;
      if (!ok) { out.textContent = "❌ Error al comprobar."; return; }
      out.innerHTML =
        "✅ " + data.checked + " comprobadas · 🟢 " + data.reachable +
        " operativas · 🔴 " + data.down + " caídas · ⚪ " + data.not_checkable + " sin URL.";
      // Actualiza las filas con el resultado.
      const byId = {};
      (data.results || []).forEach((r) => (byId[r.id] = r));
      document.querySelectorAll("#sources-table tr[data-source-id]").forEach((row) => {
        const r = byId[parseInt(row.getAttribute("data-source-id"), 10)];
        if (r) setRowStatus(row, r.ok, r.message);
      });
    });
  }

  document.querySelectorAll(".toggle-enabled").forEach(function (cb) {
    cb.addEventListener("change", async function () {
      const row = cb.closest("tr[data-source-id]");
      const id = row.getAttribute("data-source-id");
      const { ok } = await patchJSON("/api/v1/sources/" + id + "/toggle", {
        enabled: cb.checked,
      });
      if (!ok) {
        cb.checked = !cb.checked; // revertir en caso de error
        alert("No se pudo cambiar el estado de la fuente.");
      }
    });
  });

  const clearBtn = document.getElementById("btn-clear");
  if (clearBtn) {
    clearBtn.addEventListener("click", async function () {
      if (!confirm("¿Eliminar TODAS las simulaciones? Los datos reales no se tocan.")) return;
      show("Limpiando simulaciones…", true);
      const { ok, data } = await postJSON("/api/v1/simulation/clear", null);
      if (ok) {
        show(
          "🧹 Limpieza completada: " + data.observations_deleted +
            " observaciones y " + data.alerts_deleted + " alertas simuladas eliminadas.",
          true
        );
        setTimeout(() => location.reload(), 1500);
      } else {
        show("❌ Error: " + JSON.stringify(data), false);
      }
    });
  }

  // ----------------------------------------------------------------
  //  Panel principal: KPIs en vivo, gráficas y pipeline de datos reales.
  // ----------------------------------------------------------------
  if (!window.RADARSALUD_DASHBOARD) return;

  async function getJSON(url) {
    const r = await fetch(url);
    return r.ok ? r.json() : null;
  }
  function setText(id, v) {
    const el = document.getElementById(id);
    if (el) el.textContent = v;
  }

  const charts = {};
  function upsertChart(id, config) {
    if (typeof Chart === "undefined") return;
    const ctx = document.getElementById(id);
    if (!ctx) return;
    if (charts[id]) { charts[id].destroy(); }
    charts[id] = new Chart(ctx, config);
  }

  async function loadDashboard() {
    const s = await getJSON("/api/v1/dashboard/summary");
    if (s) {
      setText("kpi-obs-real", s.observations_real);
      setText("kpi-alerts-real", s.alerts_real);
      setText("kpi-obs-sim", s.observations_sim);
      setText("kpi-alerts-sim", s.alerts_sim);
      setText("kpi-sources", s.sources);
      setText("kpi-last", s.last_real_observation ? s.last_real_observation.slice(0, 10) : "—");
      setText("last-update", "Actualizado: " + new Date(s.updated_at).toLocaleTimeString());
      const sev = s.alerts_by_severity || {};
      upsertChart("chart-severity", {
        type: "doughnut",
        data: {
          labels: ["Baja", "Media", "Alta", "Crítica"],
          datasets: [{
            data: [sev.low || 0, sev.medium || 0, sev.high || 0, sev.critical || 0],
            backgroundColor: ["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c"],
          }],
        },
        options: { plugins: { legend: { position: "bottom" } } },
      });
    }

    const ts = await getJSON("/api/v1/dashboard/mortality_timeseries");
    const noMort = document.getElementById("no-mortality");
    if (ts && ts.labels && ts.labels.length) {
      if (noMort) noMort.style.display = "none";
      upsertChart("chart-mortality", {
        type: "line",
        data: {
          labels: ts.labels,
          datasets: [
            { label: "Observada", data: ts.observed, borderColor: "#2980b9",
              backgroundColor: "rgba(41,128,185,.15)", fill: true, tension: 0.25, pointRadius: 0 },
            { label: "Esperada", data: ts.expected, borderColor: "#7f8c8d",
              borderDash: [6, 4], fill: false, tension: 0.25, pointRadius: 0 },
          ],
        },
        options: { responsive: true, maintainAspectRatio: false,
          plugins: { legend: { position: "bottom" } },
          scales: { x: { ticks: { maxTicksLimit: 10 } } } },
      });
    } else if (noMort) {
      noMort.style.display = "block";
    }

    const te = await getJSON("/api/v1/dashboard/top_excess?limit=10");
    if (te && te.items) {
      upsertChart("chart-excess", {
        type: "bar",
        data: {
          labels: te.items.map((i) => i.province),
          datasets: [{
            label: "Exceso (%) sobre lo esperado",
            data: te.items.map((i) => i.excess_pct),
            backgroundColor: te.items.map((i) => (i.excess_pct > 0 ? "#e74c3c" : "#27ae60")),
          }],
        },
        options: { indexAxis: "y", responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } } },
      });
    }
  }

  // Pipeline de actualización (extrae + analiza en segundo plano).
  const refreshBtn = document.getElementById("btn-refresh");
  const statusBox = document.getElementById("pipeline-status");
  let polling = null;

  function renderStatus(st) {
    if (!statusBox) return;
    if (st.running) {
      statusBox.className = "pipeline-status running";
      statusBox.innerHTML = '<span class="spinner"></span> ' +
        "(" + st.step + ") " + st.message;
    } else if (st.step === "completado") {
      statusBox.className = "pipeline-status ok";
      statusBox.textContent = st.message;
    } else if (st.step === "error") {
      statusBox.className = "pipeline-status err";
      statusBox.textContent = st.message;
    } else {
      statusBox.className = "pipeline-status";
      statusBox.textContent = st.message || "";
    }
  }

  async function pollStatus() {
    const st = await getJSON("/api/v1/pipeline/status");
    if (!st) return;
    renderStatus(st);
    if (!st.running) {
      clearInterval(polling); polling = null;
      if (refreshBtn) refreshBtn.disabled = false;
      loadDashboard();
    }
  }

  if (refreshBtn) {
    refreshBtn.addEventListener("click", async function () {
      const includeHeavy = document.getElementById("heavy").checked;
      refreshBtn.disabled = true;
      renderStatus({ running: true, step: "iniciando", message: "Iniciando…" });
      await fetch("/api/v1/pipeline/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ include_heavy: includeHeavy, include_light: true }),
      });
      if (polling) clearInterval(polling);
      polling = setInterval(pollStatus, 2000);
      pollStatus();
    });
  }

  loadDashboard();
  // Refresco en vivo de las gráficas cada 30 s (no relanza el pipeline).
  setInterval(loadDashboard, 30000);
  // Si al cargar hay un pipeline en marcha (lanzado antes), engancha el sondeo.
  getJSON("/api/v1/pipeline/status").then((st) => {
    if (st && st.running) {
      if (refreshBtn) refreshBtn.disabled = true;
      polling = setInterval(pollStatus, 2000);
      renderStatus(st);
    }
  });
})();
