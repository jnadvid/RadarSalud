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
