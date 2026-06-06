"""Render del mapa interactivo de España con Folium."""
from __future__ import annotations

import html
from typing import Any

import folium

from radarsalud.maps.layers import color_for_severity, layer_name
from radarsalud.maps.spain_geojson import SPAIN_CENTER, SPAIN_ZOOM


def _popup_html(alert: dict[str, Any]) -> str:
    """Genera el HTML del popup de una alerta/observación en el mapa."""
    mode = alert.get("data_mode", "real")
    mode_badge = (
        '<span style="background:#8e44ad;color:#fff;padding:2px 6px;border-radius:4px;'
        'font-weight:bold;">SIMULACIÓN</span>'
        if mode == "simulation"
        else '<span style="background:#16a085;color:#fff;padding:2px 6px;'
        'border-radius:4px;">REAL</span>'
    )

    def esc(x: Any) -> str:
        return html.escape("" if x is None else str(x))

    rows = [
        f"<b>Modo:</b> {mode_badge}",
        f"<b>Evento:</b> {esc(alert.get('health_event'))}",
        f"<b>Provincia:</b> {esc(alert.get('province'))}",
        f"<b>Fecha:</b> {esc(alert.get('observed_at'))}",
        f"<b>Severidad:</b> {esc(alert.get('severity'))}",
        f"<b>Valor observado:</b> {esc(alert.get('observed_value'))}",
        f"<b>Baseline:</b> {esc(alert.get('baseline_value'))}",
        f"<b>Explicación:</b> {esc(alert.get('explanation'))}",
        f"<b>Fuente:</b> {esc(alert.get('source'))}",
        f"<b>Recomendación:</b> {esc(alert.get('recommendation'))}",
    ]
    return (
        '<div style="font-size:13px;max-width:320px;line-height:1.4">'
        + "<br>".join(rows)
        + "</div>"
    )


def _source_popup_html(s: dict[str, Any]) -> str:
    def esc(x: Any) -> str:
        return html.escape("" if x is None else str(x))

    url = s.get("url")
    url_html = f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(url)}</a>' if url else "—"
    rows = [
        f"<b>📡 Fuente:</b> {esc(s.get('name'))}",
        f"<b>Organización:</b> {esc(s.get('organization'))}",
        f"<b>Ámbito:</b> {esc(s.get('level'))} {esc(s.get('autonomous_community') or '')}",
        f"<b>Categoría:</b> {esc(s.get('category'))}",
        f"<b>Acceso:</b> {esc(s.get('access_mode'))}",
        f"<b>Habilitada:</b> {'sí' if s.get('enabled') else 'no'}",
        f"<b>Estado:</b> {esc(s.get('status'))} ({esc(s.get('message'))})",
        f"<b>Última comprobación:</b> {esc(s.get('last_checked_at'))}",
        f"<b>URL:</b> {url_html}",
    ]
    return '<div style="font-size:13px;max-width:320px;line-height:1.4">' + "<br>".join(rows) + "</div>"


def _add_sources_layer(fmap: folium.Map, sources: list[dict[str, Any]]) -> None:
    """Añade una capa de cobertura de fuentes, coloreada por estado."""
    if not sources:
        return
    group = folium.FeatureGroup(name="📡 Fuentes (cobertura)", show=False)
    for s in sources:
        lat, lon = s.get("latitude"), s.get("longitude")
        if lat is None or lon is None:
            continue
        color = s.get("color", "#95a5a6")
        folium.CircleMarker(
            location=[lat, lon],
            radius=5,
            color="#2c3e50",
            weight=1,
            fill=True,
            fill_color=color if s.get("enabled") else "#ffffff",
            fill_opacity=0.9 if s.get("enabled") else 0.4,
            popup=folium.Popup(_source_popup_html(s), max_width=340),
            tooltip=f"📡 {s.get('name')} · {s.get('status')}",
        ).add_to(group)
    group.add_to(fmap)


def build_map(alerts: list[dict[str, Any]], *, sources: list[dict[str, Any]] | None = None,
              title: str = "RadarSalud") -> folium.Map:
    """Construye un objeto folium.Map con marcadores y capas conmutables."""
    fmap = folium.Map(
        location=list(SPAIN_CENTER),
        zoom_start=SPAIN_ZOOM,
        tiles="cartodbpositron",
        control_scale=True,
    )

    # Grupos de capas: por modo y por evento.
    groups: dict[str, folium.FeatureGroup] = {}

    def get_group(name: str, show: bool = True) -> folium.FeatureGroup:
        if name not in groups:
            fg = folium.FeatureGroup(name=name, show=show)
            fg.add_to(fmap)
            groups[name] = fg
        return groups[name]

    for alert in alerts:
        lat = alert.get("latitude")
        lon = alert.get("longitude")
        if lat is None or lon is None:
            continue
        mode = alert.get("data_mode", "real")
        severity = alert.get("severity", "low")
        color = color_for_severity(severity)
        event = alert.get("health_event")

        popup = folium.Popup(_popup_html(alert), max_width=340)

        # Marcador: círculo coloreado por severidad; las simulaciones llevan
        # borde discontinuo y etiqueta para diferenciarlas claramente.
        is_sim = mode == "simulation"
        folium.CircleMarker(
            location=[lat, lon],
            radius=9 if is_sim else 7,
            color="#8e44ad" if is_sim else color,
            weight=3 if is_sim else 1,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            dash_array="5,5" if is_sim else None,
            popup=popup,
            tooltip=("[SIM] " if is_sim else "")
            + f"{event or 'señal'} · {alert.get('province') or ''} · {severity}",
        ).add_to(get_group(f"{'Simulación' if is_sim else 'Datos reales'}"))

        # También añade a la capa temática del evento.
        folium.CircleMarker(
            location=[lat, lon],
            radius=9 if is_sim else 7,
            color="#8e44ad" if is_sim else color,
            weight=3 if is_sim else 1,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            dash_array="5,5" if is_sim else None,
            popup=folium.Popup(_popup_html(alert), max_width=340),
        ).add_to(get_group(layer_name(event), show=False))

    _add_sources_layer(fmap, sources or [])

    folium.LayerControl(collapsed=False).add_to(fmap)

    # Leyenda fija con aviso de simulación.
    legend = """
    <div style="position: fixed; bottom: 24px; left: 24px; z-index: 9999;
        background: white; padding: 10px 12px; border:1px solid #ccc; border-radius:6px;
        font-size:12px; box-shadow:0 1px 4px rgba(0,0,0,.2)">
      <b>Severidad</b><br>
      <span style="color:#2ecc71">●</span> Baja
      <span style="color:#f1c40f">●</span> Media
      <span style="color:#e67e22">●</span> Alta
      <span style="color:#e74c3c">●</span> Crítica<br>
      <span style="color:#8e44ad">◌</span> Borde morado discontinuo = SIMULACIÓN<br>
      <b>Fuentes</b> (capa opcional):
      <span style="color:#27ae60">●</span> operativa
      <span style="color:#c0392b">●</span> caída
      <span style="color:#95a5a6">●</span> sin comprobar
    </div>
    """
    fmap.get_root().html.add_child(folium.Element(legend))
    return fmap


def render_map_html(alerts: list[dict[str, Any]],
                    sources: list[dict[str, Any]] | None = None) -> str:
    """Devuelve el HTML de página completa del mapa (standalone)."""
    return build_map(alerts, sources=sources).get_root().render()
