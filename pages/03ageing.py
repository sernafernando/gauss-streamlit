import requests
from lxml import etree
import xml.sax
import html
import json
import re
from dateutil.relativedelta import relativedelta
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import locale
import numpy as np
import io
import matplotlib.pyplot as plt
import plotly.express as px
from st_app import LargeXMLHandler

# Set page config
st.set_page_config(page_title="Gauss Online | Ageing", page_icon="images/white-g.png", layout="wide", initial_sidebar_state="expanded")

st.logo(image="images/white-g-logo.png", 
        icon_image="images/white-g.png")

with st.sidebar:
    st.header("⚙️ Opciones")
    # Seleccionar fechas de inicio y fin
    time_frame = st.selectbox("Seleccionar periodo", ("Todo el tiempo", "Último año calendario", "Últimos 12 meses", "Últimos 6 meses", "Últimos 3 meses", "Último mes"), index=5)
    #from_date = st.date_input("Escriba fecha de inicio", value=datetime.date(2024, 10, 1))
    #to_date = st.date_input("Escriba fecha de fin", value=datetime.date(2024, 10, 31))
    today = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    if time_frame == "Todo el tiempo":
        from_date = datetime(2022, 12, 1).replace(hour=0, minute=0, second=0, microsecond=0)
        to_date = today
    elif time_frame == "Último año calendario":
        from_date = datetime(today.year, 1, 1).replace(hour=0, minute=0, second=0, microsecond=0)
        to_date = today
    elif time_frame == "Últimos 12 meses":
        from_date = (datetime.now() - relativedelta(months=12)).replace(hour=0, minute=0, second=0, microsecond=0)
        to_date = today
    elif time_frame == "Últimos 6 meses":
        from_date = (datetime.now() - relativedelta(months=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        to_date = today
    elif time_frame == "Últimos 3 meses":
        from_date = (datetime.now() - relativedelta(months=3)).replace(hour=0, minute=0, second=0, microsecond=0)
        to_date = today
    elif time_frame == "Último mes":
        from_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        to_date = today

    with st.expander("Parámetros"):
        min_fijo = st.number_input("Escriba el monto mínimo designado por ML", value=12000)
        min_free = st.number_input("Escriba el monto mínimo para envío gratuito designado por ML", value=30000)
        valor_fijo = st.number_input(f"Escriba el valor fijo designado por ML para montos menores a {min_fijo}", value=900)
        valor_free  = st.number_input(f"Escriba el valor fijo designado por ML para montos menores a {min_free}", value=1800)
        varios_percent = st.number_input("Escriba el porcentaje para montos varios", value=7)
        from_date = st.date_input("Escriba fecha de inicio", value=from_date)
        to_date = st.date_input("Escriba fecha de fin", value=to_date)

    st.session_state["from_date"] = from_date
    st.session_state["to_date"] = to_date

    if st.button("Actualizar datos"):
        st.cache_data.clear()  # Borra la caché de la función
    
    st.markdown("---")
    
    st.markdown("##### Seleccione la página:")
    main_page = st.page_link("st_app.py",label="Dashboard",icon="🏠")
    ventas_page = st.page_link("pages/02ventas_ml.py",label="Ventas ML",icon="📈")
    ageing_page = st.page_link("pages/03ageing.py",label="Ageing",icon="⌛")

pusername = st.secrets["api"]["username"]
ppassword = st.secrets["api"]["password"]
pcompany = st.secrets["api"]["company"]
pwebwervice = st.secrets["api"]["webwervice"]
url_ws = st.secrets["api"]["url_ws"]

token = st.session_state.token
from_date = st.session_state.from_date
to_date = st.session_state.to_date

@st.cache_data
def ageing():
    xml_payload = f'''<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Header>
        <wsBasicQueryHeader xmlns="http://microsoft.com/webservices/">
            <pUsername>{pusername}</pUsername>
            <pPassword>{ppassword}</pPassword>
            <pCompany>{pcompany}</pCompany>
            <pWebWervice>{pwebwervice}</pWebWervice>
            <pAuthenticatedToken>{token}</pAuthenticatedToken>
        </wsBasicQueryHeader>
    </soap:Header>
    <soap:Body>
            <wsGBPScriptExecute4Dataset xmlns="http://microsoft.com/webservices/">
                <strScriptLabel>scriptAgeing</strScriptLabel>
                <strJSonParameters>{{"fromDate": "{from_date}", "toDate": "{to_date}"}}</strJSonParameters>
            </wsGBPScriptExecute4Dataset>
        </soap:Body>
    </soap:Envelope>'''
    
    header_ws = {"Content-Type": "text/xml", "muteHttpExceptions": "true"}
    response = requests.post(url_ws, data=xml_payload.encode('utf-8'), headers=header_ws)

    if response.status_code != 200:
        print(f"Error en la solicitud: {response.status_code}")
        return

    print("Consulta a la API exitosa")
    
    # Creamos el parser y el manejador
    parser = xml.sax.make_parser()
    handler = LargeXMLHandler()
    parser.setContentHandler(handler)
    
    # Parseamos el XML
    xml_content = response.content
    xml.sax.parseString(xml_content, handler)

    # Obtenemos el contenido de wsGBPScriptExecute4DatasetResult
    result_content = ''.join(handler.result_content)

    # Procesar el JSON que está dentro de <Column1>
    unescaped_result = html.unescape(result_content)
    match = re.search(r'\[.*?\]', unescaped_result)
    
    if match:
        column1_json = match.group(0)
    else:
        print("No se encontró contenido JSON en Column1.")
        return

    try:
        column1_list = json.loads(column1_json)
    except json.JSONDecodeError as e:
        print(f"Error al decodificar el JSON: {e}")

    
    df = pd.DataFrame(column1_list)
    return df

df_ageing = ageing()
df_ageing_unique = df_ageing.drop_duplicates(subset=["Código"])

def top_10_gen(df, col1, col2, label1, label2, title, color_bar='#83c9ff'):
    top_10 = df.nlargest(10, col2)

    # Renombrar la columna 'columna' a 'label'
    top_10 = top_10.rename(columns={col2: label2, col1: label1})

    # Verificar los datos antes de graficar
    if (top_10[label2] < 0).any():
        print("Hay valores negativos en la columna:", top_10[label2][top_10[label2] < 0])

    # Ordenar por el valor de 'label2' de mayor a menor
    top_10 = top_10.sort_values(by=label2, ascending=False)

    # Crear el gráfico usando nombres completos para los valores
    fig = px.bar(top_10, y=top_10[label1], x=top_10[label2],
                 title=title,
                 orientation='h',
                 color_discrete_sequence=[color_bar])  # Gráfico horizontal

    # Truncar los nombres de productos largos solo para la visualización en el eje Y
    truncated_names = [(name[:25] + '...') if len(name) > 25 else name for name in top_10[label1]]

    # Actualizar el gráfico para usar los nombres truncados en el eje Y
    fig.update_layout(yaxis_tickvals=top_10[label1],
                      yaxis_ticktext=truncated_names, 
                      yaxis=dict(categoryorder='total ascending'))  # Invertir el orden en el eje Y



    st.plotly_chart(fig)



# Main Page
col_overheader = st.columns(3)
col_header = st.columns(2)

with col_header[0]:
    """
    # Ageing de productos
    Con publicaciones activas y/o pausadas.

    """

with col_overheader[2]:
    st.image(image="images/white-g-logo.png",use_column_width=True)

df_ageing_active = df_ageing_unique[(df_ageing_unique['Activa'] != False)]
df_ageing_90 = df_ageing_unique[(df_ageing_unique['Ageing'] > 90)]
df_ageing_deactive = df_ageing_unique[(df_ageing_unique['Activa'] == False)]


col_underheader = st.columns(3)

with col_underheader[0]:
    top_10_gen(df_ageing_90, 'Descripción', 'Stock_Disponible', 'Producto', 'Stock Disponible', '10 Productos con mayor stock con más de 90 días','#5b8cb2')
with col_underheader[1]:
    top_10_gen(df_ageing_active, 'Descripción', 'Ageing', 'Producto', 'Ageing', 'Top 10 Productos Activos con mayor Ageing')
with col_underheader[2]:
    top_10_gen(df_ageing_deactive, 'Descripción', 'Stock_Disponible', 'Producto', 'Stock Disponible', 'Top 10 Productos Pausados con mayor Stock','#5b8cb2')

with st.expander("Ageing Activas"):
    df_ageing_active

with st.expander("Ageing Pausadas"):
    df_ageing_deactive

with st.expander("Ageing completo"): 
    df_ageing_unique
