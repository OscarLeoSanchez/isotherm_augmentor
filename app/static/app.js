// archivo: app/static/app.js

// Referencias DOM
const fileInput = document.getElementById("fileInput");
const addRowBtn = document.getElementById("addRowBtn");
const pointsTableBody = document.querySelector("#pointsTable tbody");

const nPointsInput = document.getElementById("nPoints");
const tableMethodSelect = document.getElementById("tableMethod");
const smoothingSInput = document.getElementById("smoothingS");
const polyDegreeInput = document.getElementById("polyDegree");


const runBtn = document.getElementById("runBtn");
const exportCsvBtn = document.getElementById("exportCsvBtn");
const exportXlsxBtn = document.getElementById("exportXlsxBtn");

const statusDiv = document.getElementById("status");
const datasetInfo = document.getElementById("datasetInfo");

const plotMain = document.getElementById("plotMain");
const methodTogglesDiv = document.getElementById("methodToggles");

const generatedTableBody = document.querySelector("#generatedTable tbody");

// Estado de la aplicación
let lastPayload = null;
let selectedMethods = new Set();
let methodOrder = [];

// ===== Sistema de Pestañas =====
function initTabs() {
    const tabButtons = document.querySelectorAll('.tabBtn');
    const tabContents = document.querySelectorAll('.tabContent');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;

            // Desactivar todas las pestañas
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Activar la pestaña seleccionada
            button.classList.add('active');
            const targetContent = document.getElementById(`tab${targetTab.charAt(0).toUpperCase() + targetTab.slice(1)}`);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
}

// ===== Sistema de Pestañas de Documentación =====
function initMethodDocs() {
    const methodTabBtns = document.querySelectorAll('.methodTabBtn');
    const methodDocs = document.querySelectorAll('.methodDoc');

    methodTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetMethod = btn.dataset.method;

            // Desactivar todos
            methodTabBtns.forEach(b => b.classList.remove('active'));
            methodDocs.forEach(doc => doc.classList.remove('active'));

            // Activar seleccionado
            btn.classList.add('active');
            const targetDoc = document.getElementById(`doc-${targetMethod}`);
            if (targetDoc) {
                targetDoc.classList.add('active');
                // Re-renderizar MathJax si está disponible
                if (window.MathJax) {
                    MathJax.typesetPromise([targetDoc]).catch(err => console.log('MathJax error:', err));
                }
            }
        });
    });
}


// ===== Funciones de Utilidad =====
function setStatus(msg, type = 'info') {
    statusDiv.textContent = msg || "";
    statusDiv.style.color = type === 'error' ? 'var(--danger)' :
        type === 'success' ? 'var(--success)' :
            'var(--text-tertiary)';
}

function addRow(p = "", q = "") {
    const tr = document.createElement("tr");

    const tdP = document.createElement("td");
    const inpP = document.createElement("input");
    inpP.type = "number";
    inpP.step = "any";
    inpP.placeholder = "Ej: 0.5";
    inpP.value = p;
    tdP.appendChild(inpP);

    const tdQ = document.createElement("td");
    const inpQ = document.createElement("input");
    inpQ.type = "number";
    inpQ.step = "any";
    inpQ.placeholder = "Ej: 0.62";
    inpQ.value = q;
    tdQ.appendChild(inpQ);

    const tdDel = document.createElement("td");
    const btnDel = document.createElement("button");
    btnDel.className = "iconBtn danger";
    btnDel.type = "button";
    btnDel.textContent = "×";
    btnDel.title = "Eliminar fila";
    btnDel.onclick = () => {
        tr.style.transition = 'opacity 0.2s ease';
        tr.style.opacity = '0';
        setTimeout(() => tr.remove(), 200);
    };
    tdDel.appendChild(btnDel);

    tr.appendChild(tdP);
    tr.appendChild(tdQ);
    tr.appendChild(tdDel);
    pointsTableBody.appendChild(tr);

    // Animación de entrada
    tr.style.opacity = '0';
    setTimeout(() => {
        tr.style.transition = 'opacity 0.3s ease';
        tr.style.opacity = '1';
    }, 10);
}

function getManualPoints() {
    const rows = Array.from(pointsTableBody.querySelectorAll("tr"));
    const pts = [];

    for (const r of rows) {
        const inputs = r.querySelectorAll("input");
        const p = inputs[0].value;
        const q = inputs[1].value;
        if (p === "" || q === "") continue;

        const pNum = Number(p);
        const qNum = Number(q);
        if (!Number.isFinite(pNum) || !Number.isFinite(qNum)) continue;

        pts.push({ p: pNum, q: qNum });
    }
    return pts;
}

function buildLayout(xLabel, yLabel) {
    return {
        margin: { l: 70, r: 30, t: 20, b: 70 },
        xaxis: {
            title: { text: xLabel, font: { size: 14, family: 'Inter' } },
            showgrid: true,
            zeroline: false,
            gridcolor: '#e2e8f0'
        },
        yaxis: {
            title: { text: yLabel, font: { size: 14, family: 'Inter' } },
            showgrid: true,
            zeroline: false,
            gridcolor: '#e2e8f0'
        },
        legend: {
            orientation: "h",
            y: -0.2,
            font: { family: 'Inter', size: 12 }
        },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { color: "#1a202c", family: 'Inter' },
        hovermode: "x unified",
    };
}

function rebuildMainPlot() {
    if (!lastPayload) return;

    const xLabel = lastPayload.labels?.x || "P [bar]";
    const yLabel = lastPayload.labels?.y || "mmol/g co2";

    const traces = [];

    // Original con estilo distintivo
    traces.push({
        x: lastPayload.original.x,
        y: lastPayload.original.y,
        mode: "markers",
        name: "Datos Originales",
        marker: {
            size: 10,
            symbol: "circle",
            color: '#2c5aa0',
            opacity: 0.8,
            line: { width: 2, color: 'white' }
        },
    });

    // Métodos seleccionados
    const colors = [
        '#0f9d58', '#f0ad4e', '#d9534f', '#5bc0de',
        '#9b59b6', '#1abc9c', '#e74c3c', '#3498db'
    ];

    let colorIndex = 0;
    for (const m of methodOrder) {
        if (!selectedMethods.has(m)) continue;
        traces.push({
            x: lastPayload.grid,
            y: lastPayload.methods[m].y,
            mode: "lines",
            name: lastPayload.methods[m].meta?.name || m,
            line: {
                width: 2.5,
                color: colors[colorIndex % colors.length]
            },
        });
        colorIndex++;
    }

    Plotly.newPlot(plotMain, traces, buildLayout(xLabel, yLabel), {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        displaylogo: false
    });
}

function renderMethodToggles() {
    methodTogglesDiv.innerHTML = "";
    selectedMethods.clear();

    for (const m of methodOrder) selectedMethods.add(m);

    for (const m of methodOrder) {
        const meta = lastPayload.methods[m]?.meta || {};
        const row = document.createElement("div");
        row.className = "toggle";

        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.checked = true;
        cb.value = m;
        cb.onchange = () => {
            if (cb.checked) selectedMethods.add(m);
            else selectedMethods.delete(m);

            // Verificar que los botones existan antes de modificarlos
            if (exportCsvBtn) exportCsvBtn.disabled = selectedMethods.size === 0;
            if (exportXlsxBtn) exportXlsxBtn.disabled = selectedMethods.size === 0;

            rebuildMainPlot();
        };

        const name = document.createElement("div");
        name.className = "name";
        name.textContent = meta.name || m;

        const metaDiv = document.createElement("div");
        metaDiv.className = "meta";
        metaDiv.textContent = meta.family || "";

        row.appendChild(cb);
        row.appendChild(name);
        row.appendChild(metaDiv);
        methodTogglesDiv.appendChild(row);
    }

    // Habilitar/deshabilitar botones de exportación
    if (exportCsvBtn) exportCsvBtn.disabled = selectedMethods.size === 0;
    if (exportXlsxBtn) exportXlsxBtn.disabled = selectedMethods.size === 0;
}

function initTableMethodSelect() {
    tableMethodSelect.innerHTML = "";
    for (const m of methodOrder) {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = lastPayload.methods[m]?.meta?.name || m;
        tableMethodSelect.appendChild(opt);
    }
    tableMethodSelect.value = methodOrder.includes("pchip") ? "pchip" : methodOrder[0];
}

function renderGeneratedTable(x, y) {
    generatedTableBody.innerHTML = "";
    const maxRows = Math.min(x.length, 2000);

    for (let i = 0; i < maxRows; i++) {
        const tr = document.createElement("tr");

        const tdI = document.createElement("td");
        tdI.textContent = String(i + 1);

        const tdX = document.createElement("td");
        tdX.textContent = Number(x[i]).toFixed(6);

        const tdY = document.createElement("td");
        tdY.textContent = Number(y[i]).toFixed(6);

        tr.appendChild(tdI);
        tr.appendChild(tdX);
        tr.appendChild(tdY);
        generatedTableBody.appendChild(tr);
    }
}

function updateTableFromSelectedMethod() {
    if (!lastPayload) return;
    const m = tableMethodSelect.value;
    const y = lastPayload.methods[m]?.y;
    if (!y) return;
    renderGeneratedTable(lastPayload.grid, y);
}

async function compute() {
    setStatus("Validando datos...", "info");
    runBtn.disabled = true;
    runBtn.textContent = "Validando...";

    try {
        const form = new FormData();
        const file = fileInput.files && fileInput.files[0] ? fileInput.files[0] : null;
        const manualPoints = getManualPoints();

        // Validación antes de enviar
        if (!file && manualPoints.length === 0) {
            setStatus("Error: Debes cargar un archivo o ingresar datos manualmente.", "error");
            runBtn.disabled = false;
            runBtn.textContent = "Ejecutar Análisis";
            return;
        }

        if (!file && manualPoints.length > 0 && manualPoints.length < 3) {
            setStatus(`Error: Se requieren mínimo 3 puntos. Actualmente tienes ${manualPoints.length} punto${manualPoints.length === 1 ? '' : 's'}.`, "error");
            runBtn.disabled = false;
            runBtn.textContent = "Ejecutar Análisis";
            return;
        }

        // Si llegamos aquí, tenemos datos suficientes
        setStatus("Ejecutando análisis...", "info");
        runBtn.textContent = "Procesando...";

        if (file) form.append("file", file);
        form.append("manual_points_json", JSON.stringify(manualPoints));

        form.append("n_points", String(Number(nPointsInput.value || 200)));
        form.append("smoothing_s", String(Number(smoothingSInput.value || 0.0)));
        form.append("poly_degree", String(Number(polyDegreeInput.value || 3)));

        const res = await fetch("/api/compute", { method: "POST", body: form });
        const data = await res.json();

        if (!res.ok) {
            setStatus(`Error: ${data.detail || "No se pudo completar el análisis."}`, "error");
            runBtn.disabled = false;
            runBtn.textContent = "Ejecutar Análisis";
            return;
        }

        lastPayload = data;
        methodOrder = data.method_order || Object.keys(data.methods);

        const xmin = Math.min(...data.original.x);
        const xmax = Math.max(...data.original.x);
        datasetInfo.textContent = `${data.original.n_original} puntos · Rango: ${xmin.toFixed(3)}–${xmax.toFixed(3)} bar`;

        renderMethodToggles();
        initTableMethodSelect();
        rebuildMainPlot();
        updateTableFromSelectedMethod();

        setStatus("✓ Análisis completado exitosamente", "success");
    } catch (error) {
        setStatus(`Error de red: ${error.message}`, "error");
    } finally {
        runBtn.disabled = false;
        runBtn.textContent = "Ejecutar Análisis";
    }
}

async function exportSelected(fmt) {
    if (!lastPayload) return;

    const selected = Array.from(selectedMethods);
    if (selected.length === 0) {
        setStatus("Selecciona al menos un método para exportar.", "error");
        return;
    }

    setStatus("Generando exportación...", "info");

    try {
        const payload = {};
        for (const m of selected) payload[m] = lastPayload.methods[m].y;

        const form = new FormData();
        form.append("export_format", fmt);
        form.append("selected_methods_json", JSON.stringify(selected));
        form.append("grid_json", JSON.stringify(lastPayload.grid));
        form.append("results_json", JSON.stringify(payload));

        const res = await fetch("/api/export", { method: "POST", body: form });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            setStatus(`Error exportando: ${err.detail || "falló"}`, "error");
            return;
        }

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = fmt === "csv" ? "export_selected_methods.csv" : "export_selected_methods.xlsx";
        document.body.appendChild(a);
        a.click();
        a.remove();

        window.URL.revokeObjectURL(url);
        setStatus("✓ Exportación completada", "success");
    } catch (error) {
        setStatus(`Error: ${error.message}`, "error");
    }
}

// ===== Event Listeners =====
addRowBtn.addEventListener("click", () => addRow());
runBtn.addEventListener("click", () => compute());
tableMethodSelect.addEventListener("change", () => updateTableFromSelectedMethod());
exportCsvBtn.addEventListener("click", () => exportSelected("csv"));
exportXlsxBtn.addEventListener("click", () => exportSelected("xlsx"));

// ===== Inicialización =====
initTabs();
initMethodDocs();

// Plot vacío inicial con estilo profesional
Plotly.newPlot(plotMain, [], buildLayout("P [bar]", "mmol/g co2"), {
    responsive: true,
    displayModeBar: false
});

// Mensaje inicial
setStatus("Carga un archivo o ingresa datos manualmente para comenzar", "info");
