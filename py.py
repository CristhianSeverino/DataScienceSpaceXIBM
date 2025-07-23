import dash
from dash.dependencies import Input, Output
from dash import dcc  # <-- ¡CORREGIDO! Importación moderna de dash_core_components
from dash import html # <-- ¡CORREGIDO! Importación moderna de dash_html_components
import pandas as pd
import plotly.express as px
import io # Necesario para procesar el archivo CSV desde la URL

# --- 0. Carga y Preprocesamiento de Datos ---
# URL del archivo CSV
URL = 'https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DS0321EN-SkillsNetwork/datasets/spacex_launch_geo.csv'

# Carga de datos: Para un entorno Dash estándar, pandas puede leer directamente desde la URL.
# Si estás en un entorno como JupyterLite/Pyodide donde 'fetch' es necesario,
# la carga de datos con 'await fetch' debe hacerse en un contexto asíncrono
# o antes de que la aplicación Dash intente acceder a 'spacex_df'.
# Para la compatibilidad general de Dash, usaremos pd.read_csv directo desde la URL.
try:
    spacex_df = pd.read_csv(URL)
except Exception as e:
    print(f"Error al cargar el CSV desde la URL: {e}")
    print("Intentando cargar un DataFrame de ejemplo para continuar con la demostración.")
    # DataFrame de ejemplo si la carga falla (para desarrollo local sin conexión)
    data_example = {
        'Launch Site': ['CCAFS LC-40', 'CCAFS LC-40', 'KSC LC-39A', 'VAFB SLC-4E', 'CCAFS LC-40', 'KSC LC-39A', 'CCAFS LC-40'],
        'Lat': [28.562302, 28.562302, 28.573255, 34.632834, 28.562302, 28.573255, 28.562302],
        'Long': [-80.577356, -80.577356, -80.646895, -120.610745, -80.577356, -80.646895, -80.577356],
        'class': [1, 0, 1, 1, 0, 1, 1], # 1 para éxito, 0 para fracaso
        'Payload Mass (kg)': [1000, 2000, 3000, 4000, 5000, 6000, 7000],
        'Booster Version': ['F9 v1.0 B0003', 'F9 v1.0 B0004', 'F9 v1.0 B0005', 'F9 v1.0 B0006', 'F9 v1.1 B1003', 'F9 v1.1 B1004', 'F9 v1.1 B1005']
    }
    spacex_df = pd.DataFrame(data_example)


# Crear la columna 'Booster Version Category' necesaria para el gráfico de dispersión (Tarea 4)
# Esto extrae la primera parte del nombre de la versión del cohete (ej. 'F9 v1.0')
spacex_df['Booster Version Category'] = spacex_df['Booster Version'].apply(lambda x: x.split(' ')[0])


# --- 1. Inicialización de la Aplicación Dash ---
app = dash.Dash(__name__)


# --- 2. Preparación de Componentes (Tareas 1 y 3) ---

# TAREA 1: Componente de Entrada de Desplegable para el Sitio de Lanzamiento
# Obtener los nombres únicos de los sitios de lanzamiento
launch_sites = spacex_df['Launch Site'].unique().tolist()

# Crear la lista de opciones para el Dropdown
dropdown_options = [{'label': 'All Sites', 'value': 'ALL'}]
for site in launch_sites:
    dropdown_options.append({'label': site, 'value': site})

launch_site_dropdown = dcc.Dropdown(
    id='site-dropdown',
    options=dropdown_options,
    value='ALL',
    placeholder="Select a Launch Site here",
    searchable=True
)

# TAREA 3: Control deslizante de rango para seleccionar la carga útil
min_payload = spacex_df['Payload Mass (kg)'].min()
max_payload = spacex_df['Payload Mass (kg)'].max()

payload_range_slider = dcc.RangeSlider(
    id='payload-slider',
    min=0,
    max=10000,
    step=1000,
    value=[min_payload, max_payload], # Valor predeterminado al rango real de los datos
    marks={i: str(i) for i in range(0, 10001, 1000)}
)


# --- 3. Definición del Layout de la Aplicación ---
app.layout = html.Div([
    html.H1("SpaceX Launch Records Dashboard",
            style={'textAlign': 'center', 'color': '#503D36', 'font-size': 40}),

    # TAREA 1: Menú desplegable para seleccionar el sitio de lanzamiento
    html.Div([
        html.Label("Seleccionar Sitio de Lanzamiento:"),
        launch_site_dropdown
    ]),
    html.Br(),

    # TAREA 2: Gráfico de pastel para los resultados de éxito/fracaso
    html.Div(dcc.Graph(id='success-pie-chart')),
    html.Br(),

    # TAREA 3: Control deslizante de rango para la carga útil
    html.Div([
        html.Label("Rango de Carga Útil (kg):"),
        payload_range_slider
    ]),
    html.Br(),

    # TAREA 4: Gráfico de dispersión para la correlación carga útil/resultado
    html.Div(dcc.Graph(id='success-payload-scatter-chart')),
])


# --- 4. Funciones de Callback (Tareas 2 y 4) ---

# TAREA 2: Función de callback para el gráfico de pastel
@app.callback(Output(component_id='success-pie-chart', component_property='figure'),
              Input(component_id='site-dropdown', component_property='value'))
def get_pie_chart(entered_site):
    filtered_df = spacex_df.copy()

    if entered_site == 'ALL':
        outcome_counts = filtered_df['class'].value_counts().reset_index()
        outcome_counts.columns = ['Outcome', 'Count']
        outcome_counts['Outcome'] = outcome_counts['Outcome'].map({1: 'Éxito', 0: 'Fracaso'})
        fig = px.pie(
            outcome_counts,
            values='Count',
            names='Outcome',
            title='Total de Lanzamientos Exitosos vs. Fallidos (Todos los Sitios)'
        )
        return fig
    else:
        filtered_site_df = filtered_df[filtered_df['Launch Site'] == entered_site]
        outcome_counts_site = filtered_site_df['class'].value_counts().reset_index()
        outcome_counts_site.columns = ['Outcome', 'Count']
        outcome_counts_site['Outcome'] = outcome_counts_site['Outcome'].map({1: 'Éxito', 0: 'Fracaso'})
        fig = px.pie(
            outcome_counts_site,
            values='Count',
            names='Outcome',
            title=f'Lanzamientos Exitosos vs. Fallidos en {entered_site}'
        )
        return fig

# TAREA 4: Función de callback para el gráfico de dispersión
@app.callback(Output(component_id='success-payload-scatter-chart', component_property='figure'),
              [Input(component_id='site-dropdown', component_property='value'),
               Input(component_id="payload-slider", component_property="value")])
def get_scatter_chart(entered_site, payload_range):
    filtered_df = spacex_df.copy()

    # Filtrar el DataFrame por el rango de carga útil seleccionado
    low, high = payload_range
    filtered_df = filtered_df[(filtered_df['Payload Mass (kg)'] >= low) & (filtered_df['Payload Mass (kg)'] <= high)]

    if entered_site == 'ALL':
        fig = px.scatter(
            filtered_df,
            x='Payload Mass (kg)',
            y='class',
            color='Booster Version Category',
            title='Correlación de Carga Útil y Resultado de Lanzamiento (Todos los Sitios)'
        )
        return fig
    else:
        filtered_site_df = filtered_df[filtered_df['Launch Site'] == entered_site]
        fig = px.scatter(
            filtered_site_df,
            x='Payload Mass (kg)',
            y='class',
            color='Booster Version Category',
            title=f'Correlación de Carga Útil y Resultado de Lanzamiento en {entered_site}'
        )
        return fig


# --- 5. Ejecución de la Aplicación Dash ---
if __name__ == '__main__':
    app.run(debug=True) # <-- ¡CORREGIDO! Cambiado de app.run_server a app.run