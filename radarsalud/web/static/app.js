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
})();
