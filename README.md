# Isotherm Augmentor

Herramienta profesional para análisis e interpolación de isotermas de adsorción utilizando múltiples métodos numéricos.

## Características

- **Entrada de Datos Flexible:** Carga de archivos (CSV/Excel) o entrada manual
- **5 Métodos Numéricos:** PCHIP, Smoothing Spline, Cubic Spline, Linear, Polynomial
- **Visualización Interactiva:** Gráficos profesionales con Plotly.js
- **Exportación Multi-formato:** CSV y Excel con métodos seleccionables
- **Documentación Técnica:** Explicaciones matemáticas con ecuaciones LaTeX
- **Interfaz Moderna:** Diseño profesional con sistema de pestañas

## Requisitos

- Python 3.8+
- Dependencias listadas en `requirements.txt`

## Instalación

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd isotherm_augmentor
```

### 2. Crear entorno virtual

```bash
python -m venv .venv
```

### 3. Activar entorno virtual

**Windows:**

```bash
.venv\Scripts\activate
```

**Linux/Mac:**

```bash
source .venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

## Uso

### Iniciar el servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Acceder a la aplicación

Abre tu navegador en: **http://localhost:8000**

## Estructura del Proyecto

```
isotherm_augmentor/
├── app/
│   ├── main.py                  # Aplicación FastAPI principal
│   ├── services/
│   │   ├── methods.py           # Implementación de métodos numéricos
│   │   ├── parser.py            # Parseo de archivos CSV/Excel
│   │   └── merger.py            # Combinación de datasets
│   ├── templates/
│   │   └── index.html           # Interfaz de usuario
│   └── static/
│       ├── styles.css           # Estilos profesionales
│       └── app.js               # Lógica del frontend
├── .venv/                       # Entorno virtual (gitignored)
├── data.csv                     # Archivo de datos de ejemplo
├── requirements.txt             # Dependencias Python
├── .gitignore                   # Archivos excluidos de git
└── README.md                    # Este archivo
```

## Guía de Usuario

### 1. Entrada de Datos

#### Opción A: Cargar Archivo

1. Haz clic en la pestaña **"Archivo"** (activa por defecto)
2. Selecciona un archivo CSV o Excel
3. El archivo debe contener las columnas:
   - `P [bar]` - Presión en bar
   - `mmol/g co2` - Adsorción en mmol/g

**Formato CSV ejemplo:**

```csv
P [bar],mmol/g co2
0.1,0.2
0.5,0.62
1.0,0.95
2.0,1.5
```

#### Opción B: Entrada Manual

1. Haz clic en la pestaña **"Manual"**
2. Haz clic en **"+ Agregar"** para agregar filas
3. Ingresa valores de P y Q
4. Mínimo 3 puntos requeridos
5. Usa el botón **×** para eliminar filas

#### Opción C: Combinación

Puedes usar archivos Y entrada manual simultáneamente. Los datos se combinarán automáticamente.

### 2. Configurar Parámetros

Ajusta los parámetros de procesamiento según tus necesidades:

| Parámetro            | Descripción                                            | Valor Recomendado |
| -------------------- | ------------------------------------------------------ | ----------------- |
| **Puntos generados** | Cantidad de puntos en la rejilla de interpolación      | 100-300           |
| **Grado polinómico** | Grado del polinomio (1=lineal, 2=cuadrático, 3=cúbico) | 2-4               |
| **Smoothing**        | Factor de suavizado (0 = sin suavizado)                | 0-1.0             |

**Tooltips informativos:** Pasa el cursor sobre el icono **ⓘ** para más información.

### 3. Ejecutar Análisis

1. Haz clic en **"Ejecutar Análisis"**
2. El botón mostrará:
   - **"Validando..."** - Verificando datos
   - **"Procesando..."** - Ejecutando análisis
3. El gráfico se generará con todos los métodos

### 4. Visualizar Resultados

#### Gráfico Interactivo

- Puntos originales en azul
- 5 métodos con colores distintos
- Hover para ver valores exactos
- Zoom y pan disponibles

#### Selección de Métodos

Usa los checkboxes horizontales para:

- Activar/desactivar métodos en el gráfico
- El gráfico se actualiza en tiempo real
- Selecciona solo los métodos que deseas exportar

### 5. Exportar Datos

1. Selecciona los métodos que deseas exportar (checkboxes)
2. Haz clic en **"CSV"** o **"Excel"**
3. Solo se exportarán los métodos marcados

**Formato CSV:**

```csv
method,P [bar],mmol/g co2
pchip,0.1,0.2
pchip,0.15,0.35
smoothing_spline,0.1,0.21
...
```

**Formato Excel:**

- Una hoja por método
- Columnas: P [bar] y mmol/g co2

## Métodos Numéricos

### PCHIP (Piecewise Cubic Hermite Interpolating Polynomial)

**Descripción:** Interpolación cúbica por segmentos que preserva la forma y monotonía de los datos.

**Ecuación:**

$$P_i(x) = y_i + m_i(x - x_i) + [términos cúbicos]$$

**Continuidad:** C¹

**Ventajas:**

- Preserva forma de los datos
- Sin oscilaciones espurias
- Ideal para datos con tendencias monótonas

### Smoothing Spline

**Descripción:** Spline cúbico que balancea ajuste a los datos con suavidad de la curva.

**Función Objetivo:**

$$\min \left\{ \sum_{i=1}^{m}(y_i - f(x_i))^2 + \lambda \int (f''(x))^2 dx \right\}$$

**Continuidad:** C²

**Parámetro:** λ (smoothing factor)

- λ = 0: interpola todos los puntos
- λ → ∞: regresión lineal

**Ventajas:**

- Reduce ruido
- Ajustable vía parámetro
- Suavidad controlable

### Cubic Spline (Natural)

**Descripción:** Interpolación con polinomios cúbicos que pasan exactamente por todos los puntos.

**Ecuación:**

$$S_i(x) = a_i + b_i(x - x_i) + c_i(x - x_i)^2 + d_i(x - x_i)^3$$

**Continuidad:** C²

**Condiciones de frontera:** $S''(x₀) = S''(xₙ) = 0$

**Ventajas:**

- Muy suave
- Bien condicionado
- Interpolación precisa

### Linear Interpolation

**Descripción:** Conexión de puntos consecutivos con segmentos de línea recta.

**Ecuación:**

$$f(x) = y_i + [(y_{i+1} - y_i)/(x_{i+1} - x_i)](x - x_i)$$

**Continuidad:** C⁰

**Ventajas:**

- Simple y rápido
- Estable
- No requiere cómputo complejo

**Limitaciones:** No diferenciable en los puntos de datos

### Polynomial Regression

**Descripción:** Ajuste de un único polinomio de grado n mediante mínimos cuadrados.

**Ecuación:**

$$P_n(x) = a_0 + a_1x + a_2x^2 + \dots + a_nx^n$$

**Grado:** Ajustable (1-10)

**Minimización:** $\sum_{i=1}^{m}(y_i - P_n(x_i))^2$

**Ventajas:**

- Suave globalmente
- Captura tendencias generales
- Fácil de evaluar

**Precaución:** Grados muy altos pueden causar oscilaciones (fenómeno de Runge)

## API Endpoints

### POST `/api/compute`

Ejecuta el análisis con múltiples métodos.

**Parámetros FormData:**

- `file` (opcional): Archivo CSV/Excel
- `manual_points_json` (opcional): JSON con puntos manuales
- `n_points`: Número de puntos generados (default: 200)
- `smoothing_s`: Factor de suavizado (default: 0.0)
- `poly_degree`: Grado polinomial (default: 3)

**Respuesta:**

```json
{
  "grid": [0.1, 0.15, 0.2, ...],
  "original": {
    "x": [0.1, 0.5, 1.0],
    "y": [0.2, 0.62, 0.95],
    "n_original": 3
  },
  "methods": {
    "pchip": {"y": [...]},
    "smoothing_spline": {"y": [...]},
    "cubic_spline": {"y": [...]},
    "linear": {"y": [...]},
    "poly": {"y": [...]}
  },
  "method_order": ["pchip", "smoothing_spline", "cubic_spline", "linear", "poly"]
}
```

### POST `/api/export`

Exporta métodos seleccionados en CSV o Excel.

**Parámetros FormData:**

- `selected_methods_json`: JSON array con métodos a exportar
- `grid_json`: JSON array con rejilla x
- `results_json`: JSON object con resultados
- `export_format`: "csv" o "xlsx"

## Validación de Datos

La aplicación valida automáticamente:

- **Sin datos:** "Debes cargar un archivo o ingresar datos manualmente"
- **1 punto:** "Se requieren mínimo 3 puntos. Actualmente tienes 1 punto"
- **2 puntos:** "Se requieren mínimo 3 puntos. Actualmente tienes 2 puntos"
- **3+ puntos:** Análisis se ejecuta correctamente

## Tecnologías

### Backend

- **FastAPI** - Framework web moderno y rápido
- **NumPy** - Computación numérica
- **SciPy** - Métodos científicos
- **Pandas** - Manipulación de datos
- **Jinja2** - Templates HTML

### Frontend

- **HTML5 + CSS3** - Estructura y estilos
- **JavaScript ES6+** - Lógica de interacción
- **Plotly.js** - Visualización de gráficos
- **MathJax 3.x** - Renderizado de ecuaciones LaTeX

### Diseño

- **Google Fonts (Inter)** - Tipografía moderna
- **CSS Variables** - Sistema de diseño
- **CSS Grid/Flexbox** - Layout responsivo

## Solución de Problemas

### El servidor no inicia

**Error:** `uvicorn: command not found`

**Solución:**

1. Verifica que el entorno virtual esté activado
2. Reinstala dependencias: `pip install -r requirements.txt`

### Error al cargar archivo

**Error:** "Error leyendo archivo"

**Solución:**

1. Verifica que el archivo sea CSV o Excel válido
2. Asegúrate de tener las columnas `P [bar]` y `mmol/g co2`
3. Revisa que no haya valores no numéricos

### No se ejecuta el análisis

**Error:** "Se requieren mínimo 3 puntos"

**Solución:**

1. Verifica que hayas cargado un archivo O ingresado mínimo 3 puntos manualmente
2. Revisa que los valores sean números válidos

### Las ecuaciones no se ven bien

**Problema:** Ecuaciones aparecen como texto plano

**Solución:**

1. Verifica conexión a internet (MathJax se carga desde CDN)
2. Recarga la página con Ctrl+Shift+R (fuerza recarga sin caché)
3. Verifica en consola del navegador (F12) si hay errores

**Versión:** 3.0.0  
**Última actualización:** Febrero 2026
