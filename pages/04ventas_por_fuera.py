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
from pygwalker.api.streamlit import StreamlitRenderer
from streamlit_dynamic_filters import DynamicFilters


# Set page config
st.set_page_config(page_title="Gauss Online | Ventas ML", page_icon="images/white-g.png", layout="wide", initial_sidebar_state="expanded")

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
        min_fijo = st.number_input("Escriba el monto mínimo designado por ML", value=15000)
        max_fijo = st.number_input("Escriba el monto máximo designado por ML", value=24000)
        min_free = st.number_input("Escriba el monto mínimo para envío gratuito designado por ML", value=33000)
        valor_fijo = st.number_input(f"Escriba el valor fijo designado por ML para montos menores a {min_fijo}", value=1000)
        valor_max_fijo = st.number_input(f"Escriba el valor fijo designado por ML para montos menores a {max_fijo}", value=2000)
        valor_free  = st.number_input(f"Escriba el valor fijo designado por ML para montos menores a {min_free}", value=2400)
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
    fuera_page = st.page_link("pages/04ventas_por_fuera.py",label="Ventas por fuera",icon="📈")

pusername = st.secrets["api"]["username"]
ppassword = st.secrets["api"]["password"]
pcompany = st.secrets["api"]["company"]
pwebwervice = st.secrets["api"]["webwervice"]
url_ws = st.secrets["api"]["url_ws"]

token = st.session_state.token
from_date = st.session_state.from_date
to_date = st.session_state.to_date

@st.cache_data
def ventas_por_fuera():
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
                <strScriptLabel>scriptVentasFuera2</strScriptLabel>
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

df_ventas_por_fuera = ventas_por_fuera()

df_ventas_por_fuera['Fecha'] = pd.to_datetime(df_ventas_por_fuera['Fecha'], errors='coerce')

# Formatear las fechas en un formato más legible
df_ventas_por_fuera['Fecha'] = df_ventas_por_fuera['Fecha'].dt.strftime('%d/%m/%Y %H:%M:%S')



df_ventas_por_fuera['Ganancia'] = (df_ventas_por_fuera['Precio_Final_sin_IVA'] - df_ventas_por_fuera['Costo_Pesos_sin_IVA']) - df_ventas_por_fuera['Precio_Final_sin_IVA']*0.05
df_ventas_por_fuera['MarkUp'] = np.where(df_ventas_por_fuera['Costo_Pesos_sin_IVA'] < 0, (((df_ventas_por_fuera['Precio_Final_sin_IVA']- df_ventas_por_fuera['Precio_Final_sin_IVA']*0.05) / df_ventas_por_fuera['Costo_Pesos_sin_IVA'] )-1) * -100,
    (df_ventas_por_fuera['Precio_Final_sin_IVA'] / df_ventas_por_fuera['Costo_Pesos_sin_IVA'] )-1) * 100
df_ventas_por_fuera['Costo_Pesos_con_IVA'] = df_ventas_por_fuera['Costo_Pesos_sin_IVA'] * (1 + df_ventas_por_fuera["IVA"] / 100)

def total_ventas_sin_iva(df):
    total_ventas_sin_iva = df['Precio_Final_sin_IVA'].sum()
    return total_ventas_sin_iva

def total_costo_sin_iva(df):
    total_costo_sin_iva = df['Costo_Pesos_sin_IVA'].sum()
    return total_costo_sin_iva

def calcular_ganancia(df):
    total_ganancia = df['Ganancia'].sum()
    return total_ganancia

def calcular_markup(df):
    markup = (total_ventas_sin_iva(df) / total_costo_sin_iva(df)-1) * 100
    return markup

if from_date > to_date:
    st.error("La fecha de inicio no puede ser mayor a la fecha de fin.")
else:
    st.success(f"Consultando datos desde {from_date} hasta {to_date}")

def display_top_10_gen(df, col1, col2, label1, label2):
# Agrupar por 'Marca' y sumar 'Monto_Total'
    df_grouped = df.groupby(col1, as_index=False)[col2].sum()

    # Filtrar las 10 marcas con más facturación
    top_10 = df_grouped.nlargest(10, col2)

    # Renombrar la columna 'Monto_Total' a 'Facturación ML'
    top_10 = top_10.rename(columns={col2: label2,col1: label1})

    # Truncar los nombres de productos largos
    top_10[label1] = top_10[label1].apply(lambda x: x[:25] + '...' if len(x) > 25 else x)


    # Crear el gráfico
    fig = px.bar(top_10, x=label1, y=label2,
             title=f'Top 10 {label1}s por {label2}')
    
    st.plotly_chart(fig)




# Main Page
col_overheader = st.columns(3)
col_header = st.columns(3)

with col_header[0]:
    """
    # Ventas por Fuera
    Consulta de Ventas por fuera

    """

with col_overheader[2]:
    st.image(image="images/white-g-logo.png",use_container_width=True)

# Filtro por 'Marca' en el DataFrame
unique_brands = df_ventas_por_fuera['Marca'].unique()
sorted_brands = sorted(unique_brands)
sellers = df_ventas_por_fuera['Vendedor'].unique()    
sorted_sellers = sorted(sellers)
# sorted_sellers = ['TODOS'] + sorted_sellers

    
st.write("Aplicar los filtros en cualquier orden 👇")
col_selectbox = st.columns(5)

# Filtrar por marca seleccionada
df_outside_filter = df_ventas_por_fuera.copy()
# Filtrar el DataFrame en base a las fechas seleccionadas

# Asegurarse de que las columnas de fechas estén en formato datetime
df_outside_filter['Fecha'] = pd.to_datetime(df_outside_filter['Fecha'], errors='coerce', format="%d/%m/%Y %H:%M:%S")


# Crear dos entradas de fecha
with col_selectbox[0]:
    start_date = st.date_input("Fecha inicial:", value=df_outside_filter['Fecha'].min())
    

with col_selectbox[1]:
    end_date = st.date_input("Fecha final:", value=df_outside_filter['Fecha'].max() + timedelta(days=1))

with col_selectbox[4]:
    select_seller = st.multiselect('Selecciona vendedores:', sorted_sellers, default=sorted_sellers)


df_outside_filter = df_outside_filter[(df_outside_filter['Fecha'] >= pd.to_datetime(start_date)) & 
                      (df_outside_filter['Fecha'] <= pd.to_datetime(end_date))]

print(select_seller)
if select_seller != 'TODOS':
    df_outside_filter = df_outside_filter[df_outside_filter['Vendedor'].isin(select_seller)]
#filtro_monto_total = df_outside_filter['Precio_Final_sin_IVA'].sum()


day_before = df_outside_filter['Fecha'].max()
last_day = day_before + timedelta(days=1)

dynamic_filters = DynamicFilters(df_outside_filter, filters=['Marca','SubCategoría','Categoría', 'Descripción'])

dynamic_filters.display_filters(location='columns', num_columns=4, gap='small')

outside_filtered_df = dynamic_filters.filter_df(except_filter='None')

#with col_selectbox[2]:
#    st.markdown("")
#    st.markdown("")
#    st.button("Limpiar Filtros", on_click=dynamic_filters.reset_filters())

filtro_monto_total = outside_filtered_df

col_over_envios = st.columns(3)
col_under_envios = st.columns(3)

# Formatear los totales
total_limpio = filtro_monto_total[filtro_monto_total['Fecha'].notna()]['Precio_Final_sin_IVA'].sum()
total_costo = filtro_monto_total[filtro_monto_total['Fecha'].notna()]['Costo_Pesos_sin_IVA'].sum()
total_ventas_con_IVA = filtro_monto_total[filtro_monto_total['Fecha'].notna()]['Precio_Final_con_IVA'].sum()
total_costo_con_IVA = filtro_monto_total[filtro_monto_total['Fecha'].notna()]['Costo_Pesos_con_IVA'].sum()
total_markup = ((total_limpio / total_costo)-1)*100
total_ganancia = total_limpio - total_costo
total_markup_con_iva = ((total_ventas_con_IVA / total_costo_con_IVA)-1)*100
total_ganancia_con_iva = total_ventas_con_IVA - total_costo_con_IVA

totales = {
    "Total Ventas": f"$ {total_limpio:,.0f}".replace(',', '.'),
    "Total Ganancia": f"$ {total_ganancia:,.0f}".replace(',', '.'),
    "Total Markup": f"{total_markup:,.2f}%".replace(',', '.')
}
with col_over_envios[1]:
    center_selector = st.selectbox("Seleccionar como se expresan los montos:", ["Precios con IVA", "Precios sin IVA"])
with col_under_envios[1]:
    st.markdown("#### Total Periodo:")
    if center_selector == "Precios sin IVA":
        with st.container(border=True):
            st.metric("Facturación Total Sin IVA", f"$ {total_limpio:,.0f}".replace(',', '.'))  # Muestra el total_limpio
            st.metric("Costos Totales Sin IVA", f"$ {total_costo:,.0f}".replace(',', '.'))  # Muestra el total_costo
            st.metric("Total Ganancia", f"$ {total_ganancia:,.0f}".replace(',', '.'))  # Muestra el total_ganancia
            st.metric("Total Markup", f"{total_markup:,.2f}%".replace(',', '.'))  # Muestra el total_markup
    elif center_selector == "Precios con IVA":
        with st.container(border=True):
            st.metric("Facturación Total Con IVA", f"$ {total_ventas_con_IVA:,.0f}".replace(',', '.'))  # Muestra el total_limpio
            st.metric("Costos Totales Con IVA", f"$ {total_costo_con_IVA:,.0f}".replace(',', '.'))  # Muestra el total_costo
            st.metric("Total Ganancia", f"$ {total_ganancia_con_iva:,.0f}".replace(',', '.'))  # Muestra el total_ganancia
            st.metric("Total Markup", f"{total_markup_con_iva:,.2f}%".replace(',', '.'))  # Muestra el total_markup

expresion_iva = "Precio_Final_con_IVA"
label_iva = "Facturación c/IVA"

if center_selector == "Precios sin IVA":
    expresion_iva = "Precio_Final_sin_IVA"
    label_iva = "Facturación s/IVA"
elif center_selector == "Precio con IVA":
    expresion_iva = "Precio_Final_con_IVA"
    label_iva = "Facturación c/IVA"

with col_over_envios[0]:
    left_graphic = st.selectbox("Seleccionar gráfico", ["Top 10 Marcas por Ventas", "Top 10 SubCategoría por Ventas", "Top 10 Categoría por Ventas", "Top 10 Productos por Ventas","Top 10 Marcas por Facturación", "Top 10 SubCategoría por Facturación", "Top 10 Categoría por Facturación", "Top 10 Productos por Facturación"])
with col_under_envios[0]:
    if left_graphic == "Top 10 SubCategoría por Facturación":
        display_top_10_gen(filtro_monto_total, 'SubCategoría', expresion_iva, 'SubCategoría', label_iva)
    elif left_graphic == "Top 10 Categoría por Facturación":
        display_top_10_gen(filtro_monto_total, 'Categoría', expresion_iva, 'Categoría', label_iva)
    elif left_graphic == "Top 10 Marcas por Facturación":
        display_top_10_gen(filtro_monto_total, 'Marca', expresion_iva, 'Marca', label_iva)
    elif left_graphic == "Top 10 Productos por Facturación":
        display_top_10_gen(filtro_monto_total, 'Descripción', expresion_iva, 'Producto', label_iva)
    elif left_graphic == "Top 10 Marcas por Ventas":
        display_top_10_gen(filtro_monto_total, 'Marca', 'Cantidad', 'Marca', 'Unidades Vendidas')
    elif left_graphic == "Top 10 SubCategoría por Ventas":
        display_top_10_gen(filtro_monto_total, 'SubCategoría', 'Cantidad', 'SubCategoría', 'Unidades Vendidas')    
    elif left_graphic == "Top 10 Categoría por Ventas":
        display_top_10_gen(filtro_monto_total, 'Categoría', 'Cantidad', 'Categoría', 'Unidades Vendidas')
    elif left_graphic == "Top 10 Productos por Ventas":
        display_top_10_gen(filtro_monto_total, 'Descripción', 'Cantidad', 'Producto', 'Unidades Vendidas')

with col_over_envios[2]:
    seleccionar_grafico = st.selectbox("Seleccionar gráfico", ["Top 10 Marcas por Facturación", "Top 10 SubCategoría por Facturación", "Top 10 Categoría por Facturación", "Top 10 Productos por Facturación","Top 10 Marcas por Ventas", "Top 10 SubCategoría por Ventas", "Top 10 Categoría por Ventas", "Top 10 Productos por Ventas"])
with col_under_envios[2]:
    if seleccionar_grafico == "Top 10 SubCategoría por Facturación":
        display_top_10_gen(filtro_monto_total, 'SubCategoría', expresion_iva, 'SubCategoría', label_iva)
    elif seleccionar_grafico == "Top 10 Categoría por Facturación":
        display_top_10_gen(filtro_monto_total, 'Categoría', expresion_iva, 'Categoría', label_iva)
    elif seleccionar_grafico == "Top 10 Marcas por Facturación":
        display_top_10_gen(filtro_monto_total, 'Marca', expresion_iva, 'Marca', label_iva)
    elif seleccionar_grafico == "Top 10 Productos por Facturación":
        display_top_10_gen(filtro_monto_total, 'Descripción', expresion_iva, 'Producto', label_iva)
    elif seleccionar_grafico == "Top 10 Marcas por Ventas":
        display_top_10_gen(filtro_monto_total, 'Marca', 'Cantidad', 'Marca', 'Unidades Vendidas')
    elif seleccionar_grafico == "Top 10 SubCategoría por Ventas":
        display_top_10_gen(filtro_monto_total, 'SubCategoría', 'Cantidad', 'SubCategoría', 'Unidades Vendidas')    
    elif seleccionar_grafico == "Top 10 Categoría por Ventas":
        display_top_10_gen(filtro_monto_total, 'Categoría', 'Cantidad', 'Categoría', 'Unidades Vendidas')
    elif seleccionar_grafico == "Top 10 Productos por Ventas":
        display_top_10_gen(filtro_monto_total, 'Descripción', 'Cantidad', 'Producto', 'Unidades Vendidas')

filtro_monto_total

@st.cache_resource
def get_pyg_renderer() -> "StreamlitRenderer":
    df = df_ventas_por_fuera

    # If you want to use feature of saving chart config, set `spec_io_mode="rw"`
    return StreamlitRenderer(df, spec="./gw_config.json", spec_io_mode="rw")

renderer = get_pyg_renderer()

with st.expander("Generar grafico"):
    renderer.explorer()