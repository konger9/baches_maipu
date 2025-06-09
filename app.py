import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster

DATA_PATH = 'data/baches.csv'
URL_IMG = 'foto_url'
LATITUD = 'lat'
LONGITUD = 'lng'
TIPO = 'tipo'

TIPO_COLORES = {
    'Bache': '#dd4231',
    'Grieta': '#2441e9',
    'Resalto dañado': "#f8ff24"
}

st.set_page_config(
    page_title="Baches en Maipú",
    layout="wide",
    page_icon="🗺️",
    initial_sidebar_state="expanded"
)

hide_buttons = """
    <style>
    .stAppToolbar {
        visibility: hidden;
        display: none;           
    }        
    </style>
"""

st.markdown(hide_buttons, unsafe_allow_html=True)

@st.cache_data
def cargar_datos(path=DATA_PATH):
    df = pd.read_csv(path, sep=';', encoding='utf-8')
    return df

def crear_texto_popup(row):
    """Genera el contenido HTML del popup para un marcador."""
    popup_text = ""

    lat = row.get(LATITUD)
    lng = row.get(LONGITUD)
    tipo = row.get(TIPO)
    url_img = row.get(URL_IMG)

    if tipo and pd.notna(tipo):
        popup_text += f"<b>Tipo:</b> {tipo}<br>"

    if pd.notna(lat) and pd.notna(lng):
        popup_text += f"<b>Latitud:</b> {lat}<br>"
        popup_text += f"<b>Longitud:</b> {lng}<br>"
        # Agregar botón para abrir en Google Maps
        popup_text += f"""
        <a href="https://www.google.com/maps/search/?api=1&query={lat},{lng}" 
        target="_blank" 
        style="font-size: 12px; color: #3366cc; text-decoration: none;">
        &raquo Abrir en Google Maps
        </a><br>
        """

    if url_img and pd.notna(url_img):
        popup_text += f"""
        <a href="{url_img}" target="_blank">
            <img src="{url_img}" height="100" style="margin-top:5px;">
        </a>
        <br><small style="font-size: 12px;"><b>Haz click para ampliar</b></small>"""

    return popup_text

def crear_mapa(map_data):
    """Crea y despliega el mapa"""
    try:
        if not all(col in map_data.columns for col in [LATITUD, LONGITUD]):
            st.warning(f"Faltan columnas '{LATITUD}' o '{LONGITUD}' para crear el mapa")
            return
        
        map_data_valid = map_data.dropna(subset=[LATITUD, LONGITUD]).copy()
        if map_data_valid.empty:
            st.error("No hay datos con coordenadas geográficas válidas para mostrar en el mapa.")
            return

        with st.spinner('Construyendo Mapa...'):
            m = folium.Map(location=[-33.5101, -70.7577], zoom_start=13)
            cluster = MarkerCluster().add_to(m)

            for _, row in map_data_valid.iterrows():
                tipo = row.get(TIPO, "Desconocido")
                color = TIPO_COLORES.get(tipo, "gray")
                popup_html = crear_texto_popup(row)

                folium.CircleMarker(
                    location=[row[LATITUD], row[LONGITUD]],
                    radius=8,
                    color=color,
                    fill=True,
                    fill_opacity=0.7,
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(cluster)

            folium_static(m, width=1000, height=500)
    
    except Exception as e:
        st.error(f"Ocurrió un error al generar el mapa: {e}")

with st.spinner('Cargando datos de baches...'):
    df = cargar_datos()

st.sidebar.title("¡Bienvenido! ✌️")
st.sidebar.markdown("""
Esta es una aplicación que muestra una recopilación de puntos en mal estado en la comuna de **Maipú**, incluyendo:

- **Baches / Hoyos.**
- **Grietas.**
- **Resaltos en mal estado.**

Cada punto en el mapa representa un reporte georreferenciado, acompañado de una imagen y un enlace directo a Google Maps para facilitar su ubicación.
""")
st.sidebar.header("Filtros")
tipos_disponibles = sorted(df[TIPO].dropna().unique())

if "tipos_seleccionados" not in st.session_state:
    st.session_state.tipos_seleccionados = {tipo: True for tipo in tipos_disponibles}

tipos_seleccionados = []
for tipo in tipos_disponibles:
    checked = st.sidebar.checkbox(f"{tipo}", value=st.session_state.tipos_seleccionados.get(tipo, True), key=tipo)
    st.session_state.tipos_seleccionados[tipo] = checked
    if checked:
        tipos_seleccionados.append(tipo)

st.subheader("🗺️ Mapa de Baches en Maipú")

colores_leyenda = ' '.join([
        f'<span style="display:inline-block; background-color:{color}; border-radius:50%; width:10px; height:10px; margin-right:5px; vertical-align: middle;"></span>{name}'
        for name, color in TIPO_COLORES.items()
])

st.markdown(f"**Leyenda:** <br> {colores_leyenda}", unsafe_allow_html=True)

df_filtrado = df[df[TIPO].isin(tipos_seleccionados)]
crear_mapa(df_filtrado)

st.markdown(
    "<i>Nota:</i> Puede existir una pequeña diferencia en las coordenadas con Google Maps, puedes visitar las coordenadas exactas al clickear en un punto.",
    unsafe_allow_html=True
)