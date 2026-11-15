let timelineChart;
let methodsChart;
let statusChart;
let refreshTimer;

document.addEventListener("DOMContentLoaded", async () => {
    try {
        const user = await getCurrentUser();
        if (user.role !== "admin") {
            window.location.href = "/dashboard";
            return;
        }
        document.getElementById("currentUsername").textContent = user.username;
        document.getElementById("currentRole").textContent = user.role;
        applyRoleVisibility(user);
        await loadUsage();
        document.getElementById("refreshUsage").addEventListener("click", loadUsage);
        refreshTimer = window.setInterval(loadUsage, 30000);
        window.addEventListener("beforeunload", () => window.clearInterval(refreshTimer));
    } catch (error) {
        console.error("No se pudo cargar utilización:", error);
    }
});

async function loadUsage() {
    const button = document.getElementById("refreshUsage");
    button.disabled = true;
    try {
        const response = await apiFetch("/dashboard/usage");
        if (!response.ok) throw new Error("No se pudieron obtener las métricas");
        const data = await response.json();

        setUsageValue("usageRequests", data.requests_total);
        setUsageValue("usageErrors", data.errors_total);
        setUsageValue("usageErrorRate", data.error_rate_percent + "%");
        setUsageValue("usageLatency", data.average_latency_ms + " ms");
        setUsageValue("usageP95", data.p95_latency_ms === null ? "Sin datos" : data.p95_latency_ms + " ms");
        setUsageValue("usageRecent", data.requests_last_5m);
        setUsageValue("usageUptime", formatDuration(data.uptime_seconds));
        setUsageValue("usageCache", String(data.cache_backend || "memory").toUpperCase());
        setUsageValue("usageScope", "Proceso actual");

        renderTimeline(data.requests_by_minute || []);
        renderMethods(data.requests_by_method || {});
        renderStatus(data.requests_by_status || {});
        renderRoutes(data.requests_by_path || []);
        document.getElementById("usageUpdated").textContent =
            "Actualizado: " + new Date().toLocaleTimeString("es-PE");
    } catch (error) {
        document.getElementById("usageUpdated").textContent = error.message;
    } finally {
        button.disabled = false;
    }
}

function setUsageValue(id, value) {
    document.getElementById(id).textContent = value;
}

function formatDuration(seconds) {
    const total = Math.floor(seconds || 0);
    const hours = Math.floor(total / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const remaining = total % 60;
    return hours + " h " + minutes + " min " + remaining + " s";
}

function createOrUpdateChart(existing, canvasId, config) {
    if (existing) {
        existing.data = config.data;
        existing.update();
        return existing;
    }
    return new Chart(document.getElementById(canvasId), config);
}

function renderTimeline(items) {
    timelineChart = createOrUpdateChart(timelineChart, "usageTimeline", {
        type: "line",
        data: {
            labels: items.map(item => new Date(item.timestamp).toLocaleTimeString("es-PE", {hour:"2-digit",minute:"2-digit"})),
            datasets: [
                {label:"Solicitudes",data:items.map(item=>item.requests),borderColor:"#2563eb",tension:0.3},
                {label:"Errores",data:items.map(item=>item.errors),borderColor:"#dc2626",tension:0.3}
            ]
        },
        options: {responsive:true,maintainAspectRatio:false,scales:{y:{beginAtZero:true,ticks:{precision:0}}}}
    });
}

function renderMethods(values) {
    const entries = Object.entries(values);
    methodsChart = createOrUpdateChart(methodsChart, "usageMethods", {
        type:"bar",
        data:{labels:entries.map(item=>item[0]),datasets:[{label:"Solicitudes",data:entries.map(item=>item[1]),backgroundColor:"#2563eb"}]},
        options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,ticks:{precision:0}}}}
    });
}

function renderStatus(values) {
    const entries = Object.entries(values).sort((a,b)=>Number(a[0])-Number(b[0]));
    statusChart = createOrUpdateChart(statusChart, "usageStatus", {
        type:"doughnut",
        data:{labels:entries.map(item=>item[0]),datasets:[{data:entries.map(item=>item[1]),backgroundColor:entries.map(item=>Number(item[0])>=500?"#dc2626":Number(item[0])>=400?"#f97316":Number(item[0])>=300?"#eab308":"#22c55e")}]},
        options:{responsive:true,maintainAspectRatio:false}
    });
}

function renderRoutes(items) {
    const tbody = document.getElementById("usageRoutes");
    if (!items.length) {
        tbody.innerHTML = '<tr><td colspan="2" class="empty-table">Todavía no hay solicitudes registradas</td></tr>';
        return;
    }
    tbody.innerHTML = items.map(item =>
        '<tr><td><code>' + escapeHtml(item.path) + '</code></td><td>' + Number(item.count) + '</td></tr>'
    ).join("");
}

function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, char => ({
        "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
    })[char]);
}
