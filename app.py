import streamlit as st
import pandas as pd
import plotly.express as px

import geopandas as gpd
import folium

# Forma antigua
from streamlit_folium import folium_static

# ----- Fuentes de datos -----

# URL del archivo de datos. El archivo original está en: 
URL_DATOS_TOTAL = 'paises_comparar.zip'

# URL del archivo de países. El archivo original está en:
# https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_0_sovereignty.zip
URL_DATOS_PAISES = 'paises.gpkg'


# ----- Funciones para recuperar los datos -----

# Función para cargar los datos y almacenarlos en caché 
# para mejorar el rendimiento
@st.cache_data
def cargar_datos_total():
    # Leer el archivo CSV y cargarlo en un DataFrame de pandas
    datos = pd.read_csv(URL_DATOS_TOTAL, compression='zip')
    return datos

# Función para cargar los datos geoespaciales de países
@st.cache_data
def cargar_datos_paises():
    paises = gpd.read_file(URL_DATOS_PAISES)
    return paises


# Título de la aplicación
st.title('Porcentaje de ruralidad en países de América Central para los años 2010 y 2020')

# ----- Carga de datos -----

# Mostrar un mensaje mientras se cargan los datos 
estado_carga_total = st.text('Cargando datos de ruralidad...')
# Cargar los datos
datos = cargar_datos_total()
# Actualizar el mensaje una vez que los datos han sido cargados
estado_carga_total.text('Los datos de ruralidad fueron cargados.')

# Cargar datos geoespaciales de países
estado_carga_paises = st.text('Cargando datos de países...')
paises = cargar_datos_paises()
estado_carga_paises.text('Los datos de países fueron cargados.')

# ----- Preparación de datos -----

# Columnas relevantes del conjunto de datos
columnas = [
    'NAME', 
    '2010', 
    '2020'
]
datos = datos[columnas]

# Nombres de las columnas en español
columnas_espaniol = {
    'NAME': 'País',
    '2010': 'Ruralidad 2010 (%)',
    '2020': 'Ruralidad 2020 (%)'
}
datos = datos.rename(columns=columnas_espaniol)

# ----- Lista de selección en la barra lateral -----

# Obtener la lista de países únicos
lista_paises = datos['País'].unique().tolist()
lista_paises.sort()

# Añadir la opción "Todos" al inicio de la lista
opciones_paises = ['Todos'] + lista_paises

# Crear el selectbox en la barra lateral
pais_seleccionado = st.sidebar.selectbox(
    'Selecciona un país',
    opciones_paises
)

# ----- Filtrar datos según la selección -----

if pais_seleccionado != 'Todos':
    # Filtrar los datos para el país seleccionado
    datos_filtrados = datos[datos['País'] == pais_seleccionado]
    ruralidad = datos_filtrados['Ruralidad 2010 (%)'].iloc[0]
    name = pais_seleccionado

else:
    # No aplicar filtro
    datos_filtrados = datos.copy()
    name = None

# ----- Tabla de porcentajes de ruralidad -----

# Mostrar la tabla
st.subheader('Porcentaje de ruralidad 2010 y 2020')
st.dataframe(datos_filtrados, hide_index=True)

# ----- Gráfico de ruralidad 2010 -----

# Agrupar por fecha y sumar los casos totales
ruralidad_total_2010 = (
    datos_filtrados
    .groupby('País')['Ruralidad 2010 (%)']
    .sum()
    .reset_index()
)

# Crear el gráfico de líneas para casos totales
grafico_2010 = px.bar(
    ruralidad_total_2010, 
    x='País', 
    y='Ruralidad 2010 (%)', 
    title='Porcentaje de ruralidad 2010',
    labels={'País': 'País ', 'Ruralidad 2010 (%) ': 'Ruralidad 2010 (%) '}
)

# Mostrar el gráfico
st.subheader('Porcentaje de ruralidad 2010')
st.plotly_chart(grafico_2010)

# ----- Gráfico de ruralidad 2020 -----

# Agrupar por fecha y sumar los casos totales
ruralidad_total_2020 = (
    datos_filtrados
    .groupby('País')['Ruralidad 2020 (%)']
    .sum()
    .reset_index()
)

# Crear el gráfico de líneas para casos totales
grafico_2010 = px.bar(
    ruralidad_total_2020, 
    x='País', 
    y='Ruralidad 2020 (%)', 
    title='Porcentaje de ruralidad 2020',
    labels={'País': 'País ', 'Ruralidad 2020 (%) ': 'Ruralidad 2020 (%) '}
)

# Mostrar el gráfico
st.subheader('Porcentaje de ruralidad 2020')
st.plotly_chart(grafico_2010)


# ----- Mapa de coropletas con folium ruralidad 2010 -----

# Agrupar ruralidad para el 2010
if pais_seleccionado != 'Todos':
    ruralidad_total_2010 = (
        datos_filtrados
        .groupby('País')['Ruralidad 2010 (%)']
        .max()
        .reset_index()
    )
else:
    ruralidad_total_2010 = (
        datos
        .groupby('País')['Ruralidad 2010 (%)']
        .max()
        .reset_index()
    )

# Unir los datos de ruralidad con el GeoDataFrame de países
paises_merged = paises.merge(
    ruralidad_total_2010, 
    how='left', 
    left_on='NAME', 
    right_on='País'
)

# Reemplazar valores faltantes con 0 o con un valor predeterminado
paises_merged['Ruralidad 2010 (%)'] = paises_merged['Ruralidad 2010 (%)'].fillna(0)


# Crear el mapa base
if pais_seleccionado != 'Todos':
    # Obtener el nombre del país seleccionado
    nombre = name
    # Filtrar el GeoDataFrame para obtener la geometría del país
    pais_geom = paises_merged[paises_merged['NAME'] == name]
    if not pais_geom.empty:
        # Obtener el centroide de la geometría del país
        centroid = pais_geom.geometry.centroid.iloc[0]
        coordenadas = [centroid.y, centroid.x]
        zoom_level = 6
    else:
        # Valores por defecto si no se encuentra el país
        coordenadas = [13.5, -85]
        zoom_level = 5
else:
    coordenadas = [13.5, -85]
    zoom_level = 5

mapa = folium.Map(location=coordenadas, zoom_start=zoom_level)

# Crear una paleta de colores
from branca.colormap import linear
paleta_colores = linear.YlOrRd_09.scale(paises_merged['Ruralidad 2010 (%)'].min(), paises_merged['Ruralidad 2010 (%)'].max())

# Añadir los polígonos al mapa
folium.GeoJson(
    paises_merged,
    name='Ruralidad por país para el 2010 (%)',
    style_function=lambda feature: {
        'fillColor': paleta_colores(feature['properties']['Ruralidad 2010 (%)']),
        'color': 'black',
        'weight': 0.5,
        'fillOpacity': 0.7,
    },
    highlight_function=lambda feature: {
        'weight': 3,
        'color': 'black',
        'fillOpacity': 0.9,
    },
    tooltip=folium.features.GeoJsonTooltip(
        fields=['NAME', 'Ruralidad 2010 (%)'],
        aliases=['País: ', 'Ruralidad 2010 (%): '],
        localize=True
    )
).add_to(mapa)

# Añadir la leyenda al mapa
paleta_colores.caption = '% Ruralidad por país para el 2010'
paleta_colores.add_to(mapa)

# Agregar el control de capas al mapa
folium.LayerControl().add_to(mapa)

# Mostrar el mapa
st.subheader('Mapa de porcentaje de ruralidad en países de América Central para el año 2010')

# Forma antigua
folium_static(mapa)


# ----- Mapa de coropletas con folium ruralidad 2020 -----

# Agrupar ruralidad para el 2010
if pais_seleccionado != 'Todos':
    ruralidad_total_2020 = (
        datos_filtrados
        .groupby('País')['Ruralidad 2020 (%)']
        .max()
        .reset_index()
    )
else:
    ruralidad_total_2020 = (
        datos
        .groupby('País')['Ruralidad 2020 (%)']
        .max()
        .reset_index()
    )

# Unir los datos de ruralidad con el GeoDataFrame de países
paises_merged = paises.merge(
    ruralidad_total_2020, 
    how='left', 
    left_on='NAME', 
    right_on='País'
)

# Reemplazar valores faltantes con 0 o con un valor predeterminado
paises_merged['Ruralidad 2020 (%)'] = paises_merged['Ruralidad 2020 (%)'].fillna(0)


# Crear el mapa base
if pais_seleccionado != 'Todos':
    # Obtener el nombre del país seleccionado
    nombre = name
    # Filtrar el GeoDataFrame para obtener la geometría del país
    pais_geom = paises_merged[paises_merged['NAME'] == name]
    if not pais_geom.empty:
        # Obtener el centroide de la geometría del país
        centroid = pais_geom.geometry.centroid.iloc[0]
        coordenadas = [centroid.y, centroid.x]
        zoom_level = 6
    else:
        # Valores por defecto si no se encuentra el país
        coordenadas = [13.5, -85]
        zoom_level = 5
else:
    coordenadas = [13.5, -85]
    zoom_level = 5

mapa2 = folium.Map(location=coordenadas, zoom_start=zoom_level)

# Crear una paleta de colores
from branca.colormap import linear
paleta_colores = linear.YlOrRd_09.scale(paises_merged['Ruralidad 2020 (%)'].min(), paises_merged['Ruralidad 2020 (%)'].max())

# Añadir los polígonos al mapa
folium.GeoJson(
    paises_merged,
    name='Ruralidad por país para el 2010 (%)',
    style_function=lambda feature: {
        'fillColor': paleta_colores(feature['properties']['Ruralidad 2020 (%)']),
        'color': 'black',
        'weight': 0.5,
        'fillOpacity': 0.7,
    },
    highlight_function=lambda feature: {
        'weight': 3,
        'color': 'black',
        'fillOpacity': 0.9,
    },
    tooltip=folium.features.GeoJsonTooltip(
        fields=['NAME', 'Ruralidad 2020 (%)'],
        aliases=['País: ', 'Ruralidad 2020 (%): '],
        localize=True
    )
).add_to(mapa2)

# Añadir la leyenda al mapa
paleta_colores.caption = '% Ruralidad por país para el 2020'
paleta_colores.add_to(mapa2)

# Agregar el control de capas al mapa
folium.LayerControl().add_to(mapa2)

# Mostrar el mapa
st.subheader('Mapa de porcentaje de ruralidad en países de América Central para el año 2020')

# Forma antigua
folium_static(mapa2)