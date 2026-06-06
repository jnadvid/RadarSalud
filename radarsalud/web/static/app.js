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
  //  Helpers compartidos por las páginas dinámicas.
  // ----------------------------------------------------------------
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
  function esc(x) {
    const d = document.createElement("div");
    d.textContent = x == null ? "" : String(x);
    return d.innerHTML;
  }

  // ----------------------------------------------------------------
  //  Panel principal: KPIs en vivo, gráficas, pipeline y scheduler.
  // ----------------------------------------------------------------
  if (window.RADARSALUD_DASHBOARD) initDashboard();

  function initDashboard() {

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

  // Scheduler (actualización automática) ---------------------------
  async function loadScheduler() {
    const st = await getJSON("/api/v1/scheduler/status");
    const box = document.getElementById("sched-status");
    const toggle = document.getElementById("sched-toggle");
    if (!box || !st) return;
    if (toggle) toggle.checked = st.enabled;
    box.textContent = st.enabled
      ? "Automático ACTIVO cada " + st.hours + " h" +
        (st.next_run ? " · próxima: " + new Date(st.next_run).toLocaleTimeString() : "")
      : "Automático desactivado";
  }
  const schedToggle = document.getElementById("sched-toggle");
  if (schedToggle) {
    schedToggle.addEventListener("change", async function () {
      const hours = parseFloat(document.getElementById("sched-hours").value) || 12;
      const includeHeavy = document.getElementById("heavy")
        ? document.getElementById("heavy").checked : true;
      if (schedToggle.checked) {
        await fetch("/api/v1/scheduler/start", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ hours: hours, include_heavy: includeHeavy }),
        });
      } else {
        await fetch("/api/v1/scheduler/stop", { method: "POST" });
      }
      loadScheduler();
    });
  }

  loadDashboard();
  loadScheduler();
  // Refresco en vivo de las gráficas cada 30 s (no relanza el pipeline).
  setInterval(loadDashboard, 30000);
  setInterval(loadScheduler, 30000);
  // Si al cargar hay un pipeline en marcha (lanzado antes), engancha el sondeo.
  getJSON("/api/v1/pipeline/status").then((st) => {
    if (st && st.running) {
      if (refreshBtn) refreshBtn.disabled = true;
      polling = setInterval(pollStatus, 2000);
      renderStatus(st);
    }
  });

  }  // fin initDashboard

  // ----------------------------------------------------------------
  //  Página de alertas: tabla con filtros y triaje.
  // ----------------------------------------------------------------
  if (window.RADARSALUD_ALERTS) initAlerts();

  function initAlerts() {
    const sevColors = { low: "#2ecc71", medium: "#f1c40f", high: "#e67e22", critical: "#e74c3c" };
    const body = document.getElementById("alerts-body");
    const fMode = document.getElementById("f-mode");
    const fSev = document.getElementById("f-sev");
    const fStatus = document.getElementById("f-status");

    async function load() {
      const params = new URLSearchParams();
      if (fMode.value) params.set("data_mode", fMode.value);
      if (fSev.value) params.set("severity", fSev.value);
      if (fStatus.value) params.set("status", fStatus.value);
      const list = (await getJSON("/api/v1/alerts?" + params.toString())) || [];
      document.getElementById("alerts-count").textContent = list.length + " alertas";
      document.getElementById("export-alerts").href =
        "/api/v1/alerts.csv?data_mode=" + (fMode.value || "all");
      body.innerHTML = "";
      list.forEach((a) => {
        const tr = document.createElement("tr");
        const sim = a.data_mode === "simulation";
        tr.innerHTML =
          '<td><span class="dot" style="background:' + (sevColors[a.severity] || "#999") +
            '"></span>' + esc(a.severity) + "</td>" +
          "<td>" + (sim ? '<span class="badge sim">SIM</span>' : "real") + "</td>" +
          "<td>" + esc(a.health_event) + "</td>" +
          '<td><a href="/province?name=' + encodeURIComponent(a.province || "") + '">' +
            esc(a.province) + "</a></td>" +
          "<td>" + esc((a.observed_at || "").slice(0, 10)) + "</td>" +
          "<td>" + esc(a.observed_value) + "</td>" +
          "<td>" + esc(a.baseline_value) + "</td>" +
          '<td class="small">' + esc(a.explanation) + "</td>" +
          '<td><span class="badge ' + esc(a.status) + '">' + esc(a.status) + "</span></td>" +
          "<td></td>";
        const actions = tr.lastChild;
        ["reviewed", "dismissed", "open"].forEach((st) => {
          if (st === a.status) return;
          const b = document.createElement("button");
          b.className = "btn small-btn";
          b.textContent = { reviewed: "Revisar", dismissed: "Descartar", open: "Reabrir" }[st];
          b.onclick = async () => {
            await fetch("/api/v1/alerts/" + a.id + "/status", {
              method: "PATCH", headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ status: st }),
            });
            load();
          };
          actions.appendChild(b);
        });
        body.appendChild(tr);
      });
    }
    [fMode, fSev, fStatus].forEach((el) => el.addEventListener("change", load));
    load();
    setInterval(load, 30000);
  }

  // ----------------------------------------------------------------
  //  Página de provincia: serie observada vs. esperada.
  // ----------------------------------------------------------------
  if (window.RADARSALUD_PROVINCE) initProvince();

  function initProvince() {
    const input = document.getElementById("prov-input");
    async function load() {
      const prov = input.value.trim();
      document.getElementById("prov-export").href =
        "/api/v1/observations.csv?data_mode=real&province=" + encodeURIComponent(prov);
      const ts = await getJSON("/api/v1/dashboard/province_timeseries?province=" +
        encodeURIComponent(prov));
      const empty = document.getElementById("prov-empty");
      const summ = document.getElementById("prov-summary");
      if (!ts || !ts.labels.length) {
        if (empty) empty.style.display = "block";
        if (summ) summ.textContent = "";
        upsertChart("chart-province", { type: "line", data: { labels: [], datasets: [] } });
        return;
      }
      if (empty) empty.style.display = "none";
      if (summ) {
        summ.textContent = ts.latest_excess_pct != null
          ? "Exceso último dato: " + ts.latest_excess_pct + "%" : "";
      }
      upsertChart("chart-province", {
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
    }
    document.getElementById("prov-load").addEventListener("click", load);
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") load(); });
    load();
  }

  // ----------------------------------------------------------------
  //  Página de importación CSV.
  // ----------------------------------------------------------------
  if (window.RADARSALUD_IMPORT) initImport();

  function initImport() {
    const form = document.getElementById("import-form");
    const out = document.getElementById("import-result");
    const example =
      "observed_at,autonomous_community,province,municipality,signal_type,health_event,pathogen,value,unit,source_name\n" +
      "2026-01-07,Madrid,Madrid,,incidencia,gripe,Influenza,42,tasa_100k,ISCIII\n" +
      "2026-01-14,Madrid,Madrid,,incidencia,gripe,Influenza,75,tasa_100k,ISCIII\n" +
      "2026-01-21,Madrid,Madrid,,incidencia,gripe,Influenza,160,tasa_100k,ISCIII\n";
    const dl = document.getElementById("dl-example");
    if (dl) {
      dl.addEventListener("click", (e) => {
        e.preventDefault();
        const blob = new Blob([example], { type: "text/csv" });
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "ejemplo_radarsalud.csv";
        a.click();
      });
    }
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      const file = document.getElementById("csv-file").files[0];
      if (!file) return;
      const fd = new FormData();
      fd.append("file", file);
      const sn = document.getElementById("csv-source").value;
      if (sn) fd.append("source_name", sn);
      out.style.color = "#20303c";
      out.textContent = "Importando…";
      const res = await fetch("/api/v1/uploads/csv", { method: "POST", body: fd });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        out.style.color = "#0a6b45";
        out.innerHTML = "✅ Importadas " + data.inserted + " de " + data.rows_total +
          " filas. <a href='/map?mode=real'>Ver en el mapa</a> · " +
          "<a href='/'>analizar en el panel</a>.";
      } else {
        out.style.color = "#a12525";
        const errs = (data.detail && data.detail.errors) || [JSON.stringify(data.detail || data)];
        out.innerHTML = "❌ Rechazado:<br>" + errs.slice(0, 10).map(esc).join("<br>");
      }
    });
  }
})();
