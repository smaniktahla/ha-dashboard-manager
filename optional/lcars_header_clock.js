// Requires lcars_header_clock.yaml (the Home Assistant clock package).
// Copy this file to /config/www, then add /local/lcars_header_clock.js as a
// JavaScript module in Settings > Dashboards > Resources. Refresh the dashboard.
// This resource can be installed without restarting Home Assistant.
(() => {
  const elementId = "dashboard-manager-header-clock";
  if (window.dashboardManagerHeaderClock) return;
  window.dashboardManagerHeaderClock = true;

  function updateClock() {
    const app = document.querySelector("home-assistant");
    const main = app?.shadowRoot?.querySelector("home-assistant-main");
    const panel = main?.shadowRoot?.querySelector("ha-panel-lovelace");
    const root = panel?.shadowRoot?.querySelector("hui-root");
    const toolbar = root?.shadowRoot?.querySelector(".header .toolbar");
    if (!toolbar) return;

    const state = app.hass?.states["sensor.lcars_header"]?.state;
    let clock = toolbar.querySelector("#" + elementId);
    const theme = app.hass?.selectedTheme?.theme;
    if (!state || !/^\d{1,2}:\d{2}(?: [AP]M)?$/.test(state) ||
        !/^LCARS\b/i.test(theme || "") || toolbar.clientWidth < 580) {
      clock?.remove();
      return;
    }
    if (!clock) {
      clock = document.createElement("time");
      clock.id = elementId;
      clock.setAttribute("aria-label", "Current time");
      Object.assign(clock.style, {
        position: "absolute",
        left: "50%",
        transform: "translateX(-50%)",
        pointerEvents: "none",
        whiteSpace: "nowrap",
        fontSize: "var(--header-font-size, 1.25rem)",
        fontVariantNumeric: "tabular-nums"
      });
      toolbar.append(clock);
    }
    if (clock.textContent !== state) clock.textContent = state;
  }

  updateClock();
  setInterval(updateClock, 1000);
})();
