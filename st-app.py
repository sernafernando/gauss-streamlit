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


# Set page config
st.set_page_config(page_title="Gauss Online Dashboard", page_icon="images/white-g.png", layout="wide", initial_sidebar_state="expanded")
# Establecer el locale para el formato deseado
try:
    locale.setlocale(locale.LC_ALL, 'es_AR.UTF-8')
except locale.Error:
    print("La configuración regional 'es_AR.UTF-8' no está disponible, utilizando configuración predeterminada.")

st.logo(image="images/white-g-logo.png", 
        icon_image="images/white-g.png")

with st.sidebar:
    st.title("Gauss Online Dashboard")
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

    if st.button("Actualizar datos"):
        fetch_data_and_create_df.clear()  # Borra la caché de la función



#  Verificar que la fecha de inicio no sea mayor a la fecha de fin
#if from_date > to_date:
#    st.error("La fecha de inicio no puede ser mayor a la fecha de fin.")
#else:
#    st.success(f"Consultando datos desde {from_date} hasta {to_date}")

# Aquí puedes continuar con el resto de tu código usando las fechas seleccionadas
#st.write(f"Rango de fechas seleccionado: {from_date} a {to_date}")

pusername = st.secrets["api"]["username"]
ppassword = st.secrets["api"]["password"]
pcompany = st.secrets["api"]["company"]
pwebwervice = st.secrets["api"]["webwervice"]
url_ws = st.secrets["api"]["url_ws"]

token = ""




def authenticate():
    soap_action = "http://microsoft.com/webservices/AuthenticateUser"
    xml_payload = f'<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Header><wsBasicQueryHeader xmlns="http://microsoft.com/webservices/"><pUsername>{pusername}</pUsername><pPassword>{ppassword}</pPassword><pCompany>{pcompany}</pCompany><pBranch>1</pBranch><pLanguage>2</pLanguage><pWebWervice>{pwebwervice}</pWebWervice></wsBasicQueryHeader></soap:Header><soap:Body><AuthenticateUser xmlns="http://microsoft.com/webservices/" /></soap:Body></soap:Envelope>'
    header_ws =  {"Content-Type": "text/xml", "SOAPAction": soap_action, "muteHttpExceptions": "true"}
    response = requests.post(url_ws, data=xml_payload,headers=header_ws)
    # Parsear la respuesta XML (suponiendo que response.content tiene el XML)
    root = etree.fromstring(response.content)

    # Definir los espacios de nombres para usarlos en las consultas XPath
    namespaces = {
        'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
        'microsoft': 'http://microsoft.com/webservices/'
    }


    # Busca el nodo AuthenticateUserResponse dentro del body
    # Buscar el contenido dentro de AuthenticateUserResult usando XPath
    auth_result = root.xpath('//microsoft:AuthenticateUserResult', namespaces=namespaces)

    # Mostrar el contenido si existe
    if auth_result:
        global token
        token = auth_result[0].text
        
    else:
        print("No se encontró el elemento AuthenticateUserResult") # Muestra el contenido del nodo si lo tiene
    
    return token

class LargeXMLHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.result_content = []
        self.is_in_result = False

    def startElement(self, name, attrs):
        # Cuando el parser encuentra el inicio de un elemento
        if name == 'wsGBPScriptExecute4DatasetResult':
            self.is_in_result = True

    def endElement(self, name):
        # Cuando el parser encuentra el final de un elemento
        if name == 'wsGBPScriptExecute4DatasetResult':
            self.is_in_result = False

    def characters(self, content):
        # Al encontrar contenido de texto dentro de un nodo
        if self.is_in_result:
            self.result_content.append(content)

authenticate()
# Utilizar @st.cache_resource para almacenar en caché la respuesta de la API
@st.cache_resource(ttl=3600)  # Puedes ajustar el tiempo de vida en segundos
# Clase para manejar el contenido del XML grande
class LargeXMLHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.result_content = []
        
    def characters(self, content):
        self.result_content.append(content)

# Almacena en caché la función que obtiene los datos y crea el DataFrame
@st.cache_resource(ttl=3600)
def fetch_data_and_create_df():
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
                <strScriptLabel>scriptDashboard</strScriptLabel>
                <strJSonParameters>{{"fromDate": "{from_date}", "toDate": "{to_date}"}}</strJSonParameters>
            </wsGBPScriptExecute4Dataset>
        </soap:Body>
    </soap:Envelope>'''

    header_ws = {"Content-Type": "text/xml", "muteHttpExceptions": "true"}
    response = requests.post(url_ws, data=xml_payload.encode('utf-8'), headers=header_ws)

    if response.status_code != 200:
        st.error(f"Error en la solicitud: {response.status_code}")
        return pd.DataFrame()

    # Crear y parsear el XML
    parser = xml.sax.make_parser()
    handler = LargeXMLHandler()
    parser.setContentHandler(handler)
    
    xml_content = response.content
    xml.sax.parseString(xml_content, handler)

    # Extraer el JSON de <Column1>
    result_content = ''.join(handler.result_content)
    unescaped_result = html.unescape(result_content)
    match = re.search(r'\[.*?\]', unescaped_result)
    
    if match:
        column1_json = match.group(0)
    else:
        st.error("No se encontró contenido JSON en Column1.")
        return pd.DataFrame()

    try:
        column1_list = json.loads(column1_json)
        df = pd.DataFrame(column1_list)
        return df
    except json.JSONDecodeError as e:
        st.error(f"Error al decodificar el JSON: {e}")
        return pd.DataFrame()

# Llamada a la función en el dashboard
df = fetch_data_and_create_df()

#if not df.empty:
#    st.write(df)
#else:
#    st.warning("No se cargaron datos en el DataFrame.")


#dashboard()


columnas_sin_comas = ['ID_de_Operación','ML_id', 'subcat_id']  # Nombres de las keys/columnas del DataFrame

# Formatear solo las columnas especificadas sin comas
for column in columnas_sin_comas:
    df[column] = df[column].map(lambda x: '{:.0f}'.format(x) if isinstance(x, (int, float)) else x)


# Formatear fecha a formato dd/mm/aaaa hh:mm:ss
# Convertir la columna de fechas, manejando fechas con o sin microsegundos
df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce',dayfirst=True)

# Formatear las fechas en un formato más legible
df['Fecha'] = df['Fecha'].dt.strftime('%d/%m/%Y %H:%M:%S')

# Crear columna de costo en pesos
df['Costo en pesos'] = np.where(
    df['Moneda_Costo'] == 2,
    df['Costo_sin_IVA'] * df['Cambio_al_Momento'],
    df['Costo_sin_IVA']
)

# subcat to group
data_subcat = {
    'subcat_id': [3821,3820,3882,3819,3818,3885,3879,3869,3870,3919,3915,3841,3858,3922,3860,3861,3902,3866,3856,3893,3886,3887,3924,3921,3920,3912,3913,3878,3875,3876,3880,3894,3853,3931,3926,3891,3843,3918,3849,3888,3852,3899,3838,3895,3896,3957],
    'group': [2,2,2,2,2,2,2,3,3,3,3,3,3,4,4,4,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,6,7,7,7,7,8,8,8,8,8,8,3]
}

# Verificación de longitudes
if len(data_subcat['subcat_id']) == len(data_subcat['group']):
    df_subcat = pd.DataFrame(data_subcat)
else:
    print("Las listas no tienen la misma longitud. Ajusta los datos. Filho da puta.")

# Asegúrate de que ambas columnas 'subcat_id' sean del mismo tipo (int)
df['subcat_id'] = df['subcat_id'].astype(int)
df_subcat['subcat_id'] = df_subcat['subcat_id'].astype(int)

# Merge para agregar la columna 'group' al DataFrame original
df_merged = df.merge(df_subcat, on='subcat_id', how='left')

# Establecer el grupo en 1 donde no hay coincidencia
df_merged['group'] = df_merged['group'].fillna(1).astype(int)

# Si deseas reemplazar 'subcat_id' con los grupos, puedes hacer lo siguiente
df_merged['subcat_id'] = df_merged['group']

# Si no necesitas la columna 'group' después, puedes eliminarla
df_merged.drop(columns=['group'], inplace=True)

# Resultado final
#print(df_merged)

# Datos de precios
data_prices = {
    'pricelist': [4, 5, 17, 14, 6, 13, 9, 10, 11, 15, 16, 12, 18, 19, 20, 21, 22],
    1: [15.5, None, 24.4, 30.4, 35.4, 41, None, 4.83, 13.73, 19.73, 24.73, 15.5, 24.4, 30.4, 35.4, 41, 30.33],
    2: [12.15, None, 21.05, 27.05, 32.55, 37.65, None, 4.83, 13.73, 19.73, 24.73, 12.15, 21.05, 27.05, 32.55, 37.65, 30.33],
    3: [12.65, None, 21.55, 27.55, 32.55, 38.15, None, 4.83, 13.73, 19.73, 24.73, 12.65, 21.55, 27.55, 32.55, 38.15, 30.33],
    4: [13.65, None, 22.55, 28.55, 33.55, 39.15, None, 4.83, 13.73, 19.73, 24.73, 13.65, 22.55, 28.55, 33.55, 39.15, 30.33],
    5: [14, None, 22.9, 28.9, 33.9, 39.5, None, 4.83, 13.73, 19.73, 24.73, 14, 22.9, 28.9, 33.9, 39.5, 30.33],
    6: [14.5, None, 23.4, 29.4, 34.4, 40, None, 4.83, 13.73, 19.73, 24.73, 14.5, 23.4, 29.4, 34.4, 40, 30.33],
    7: [15, None, 23.9, 29.9, 34.9, 40.5, None, 4.83, 13.73, 19.73, 24.73, 15, 23.9, 29.9, 34.9, 40.5, 30.33],
    8: [16, None, 24.9, 30.9, 35.9, 41.5, None, 4.83, 13.73, 19.73, 24.73, 16, 24.9, 30.9, 35.9, 41.5, 30.33]
}

# Crear DataFrame de precios
df_prices = pd.DataFrame(data_prices)

# Primero, asegurémonos de que la columna 'pricelist' en df_prices sea un valor único para los precios.
df_prices_melted = df_prices.melt(id_vars='pricelist', var_name='subcat_id', value_name='Comisión')

# Ahora, fusionamos df_merged con df_prices_melted
df_merged = df_merged.merge(
    df_prices_melted,
    left_on=['priceList', 'subcat_id'],
    right_on=['pricelist', 'subcat_id'],
    how='left'
)

# Eliminamos pricelist
df_merged.drop(columns=['pricelist'], inplace=True)

# Calculamos la comisión en pesos

df_merged['Comisión en pesos'] = np.where(
    df_merged['Monto_Unitario'] >= min_free,
    (df_merged['Monto_Unitario'] * (((df_merged['Comisión'] / 100) / 1.21) + (varios_percent / 100))) * df_merged['Cantidad'],
    np.where(
        df_merged['Monto_Unitario'] < min_fijo,
        (df_merged['Monto_Unitario'] * (((df_merged['Comisión'] / 100) / 1.21) + (varios_percent / 100)) + (valor_fijo / 1.21)) * df_merged['Cantidad'],
        (df_merged['Monto_Unitario'] * (((df_merged['Comisión'] / 100) / 1.21) + (varios_percent / 100)) + (valor_free / 1.21)) * df_merged['Cantidad']
    )
)

df_merged['Costo envío'] = np.where(
    df_merged['ML_logistic_type'] == 'self_service',
    df_merged['mlp_price4FreeShipping'], df_merged['mlp_price4FreeShipping']
)

def limpiar(row):
    if pd.isnull(row['ML_pack_id']):  # Verifica si ML_pack_id está vacío
        return (row['Monto_Unitario'] * row['Cantidad']) - (row['Costo envío'] / 1.21) - row['Comisión en pesos']
    else:
        contar_si = df_merged['ML_pack_id'].value_counts().get(row['ML_pack_id'], 1)  # Cuenta las ocurrencias de ML_pack_id en la columna
        return (row['Monto_Unitario'] * row['Cantidad']) - ((row['Costo envío'] / contar_si) / 1.21) - row['Comisión en pesos']



# Aplicar la función a cada fila y guardar el resultado en una nueva columna
df_merged['Limpio'] = df_merged.apply(limpiar, axis=1)

def totalizar_costo(row):
    return row['Costo en pesos']*row['Cantidad']

df_merged['costo_total'] = df_merged.apply(totalizar_costo, axis=1)

def totalizar_costo_iva(row):
    return row['costo_total']*(1+(row['IVA']/100))

df_merged['costo_total_iva'] = df_merged.apply(totalizar_costo_iva, axis=1)

# Calculamos el MarkUp
def markupear(row):
    # Manejar división por cero y valores nulos
    if row['costo_total_iva'] == 0 or pd.isnull(row['costo_total_iva']):
        return None  # O un valor adecuado que prefieras
    return ((row['Limpio'] / row['costo_total_iva']) - 1) * 100

def calcular_flex(df):
    total_operaciones = df[df['Fecha'].notna()]['Limpio'].count()
    total_flex =    df[(df['ML_logistic_type'] == 'self_service') & (df['Fecha'].notna())]['Limpio'].count()
    total_colecta = df[(df['ML_logistic_type'] == 'cross_docking') & (df['Fecha'].notna())]['Limpio'].count()
    total_retiros = df[(df['ML_logistic_type'].isnull()) & (df['Fecha'].notna())]['Limpio'].count()
    total_full = df[(df['ML_logistic_type'] == 'fulfillment') & (df['Fecha'].notna())]['Limpio'].count()
    porcentaje_flex = (total_flex / total_operaciones) * 100
    porcentaje_colecta = (total_colecta / total_operaciones) * 100  
    porcentaje_retiros = (total_retiros / total_operaciones) * 100
    porcentaje_full = (total_full / total_operaciones) * 100
    return total_operaciones, total_flex, total_colecta, total_retiros, total_full, porcentaje_flex, porcentaje_colecta, porcentaje_retiros, porcentaje_full


# Aplicamos la función y formateamos el resultado.
df_merged['MarkUp'] = df_merged.apply(markupear, axis=1)
df_merged['MarkUp'] = df_merged['MarkUp'].apply(lambda x: f"{x:.2f}%")

# Definimos la variable para calcular los delta
#def calcular_delta(df,title,last_day,day_before):
#    if title == "MarkUp":
#        current_value = (df[df['Fecha'] == last_day]['Limpio'].sum() / df[df['Fecha'] == last_day]['costo_total_iva'].sum())-1
#        previous_value = (df[df['Fecha'] == day_before]['Limpio'].sum() / df[df['Fecha'] == day_before]['costo_total_iva'].sum())-1
#        delta = current_value - previous_value
#        delta_percent = (delta / previous_value) * 100 if previous_value != 0 else 0
#        return delta, delta_percent
#    current_value = df[df['Fecha'] == last_day][title].sum()
#    previous_value = df[df['Fecha'] == day_before][title].sum()
#    delta = current_value - previous_value
#    delta_percent = (delta / previous_value) * 100 if previous_value != 0 else 0
#    return delta, delta_percent
    

# Main Page

"""
# Ventas ML
Consulta de Ventas ML

"""
#  Verificar que la fecha de inicio no sea mayor a la fecha de fin
if from_date > to_date:
    st.error("La fecha de inicio no puede ser mayor a la fecha de fin.")
else:
    st.success(f"Consultando datos desde {from_date} hasta {to_date}")
# Teoricamente hacemos gráficos con esto
# Definir las métricas a mostrar
# Formatear los totales
total_limpio = df_merged[df_merged['Fecha'].notna()]['Limpio'].sum()
total_costo = df_merged[df_merged['Fecha'].notna()]['costo_total_iva'].sum()
total_ventas_ml = df_merged[df_merged['Fecha'].notna()]['Monto_Total'].sum()
total_comision = df_merged[df_merged['Fecha'].notna()]['Comisión en pesos'].sum()
total_markup = ((total_limpio / total_costo)-1)*100
total_ganancia = total_limpio - total_costo

totales = {
    "Total Ventas ML": f"$ {total_ventas_ml:,.0f}".replace(',', '.'),
    "Total Limpio": f"$ {total_limpio:,.0f}".replace(',', '.'),
    "Total Ganancia": f"$ {total_ganancia:,.0f}".replace(',', '.'),
    "Total Markup": f"{total_markup:,.2f}%".replace(',', '.')
}

# Crear gráficos para los totales
def display_totals(totales):
    cols = st.columns(len(totales))
    for col, (title, value) in zip(cols, totales.items()):
        with col:
            with st.container(border=True):
                    st.metric(title, value)  # Muestra la métrica
            #   st.bar_chart([total_limpio, total_costo, total_comision], use_container_width=True)  # Gráfico de barras

def display_envios(df):
    total_operaciones, total_flex, total_colecta, total_retiros, total_full, porcentaje_flex, porcentaje_colecta, porcentaje_retiros, porcentaje_full = calcular_flex(df)
    total_operaciones_dict = {
        "Total Operaciones": f"{total_operaciones:,.0f}".replace(',', '.'),
        "Total Flex": f"{total_flex:,.0f}".replace(',', '.'),
        "Total Colecta": f"{total_colecta:,.0f}".replace(',', '.'),
        "Total Retiros": f"{total_retiros:,.0f}".replace(',', '.'),
        "Total Full": f"{total_full:,.0f}".replace(',', '.'),
        "Porcentaje Flex": f"{porcentaje_flex:.2f}%".replace(',', '.'),
        "Porcentaje Colecta": f"{porcentaje_colecta:.2f}%".replace(',', '.'),
        "Porcentaje Retiros": f"{porcentaje_retiros:.2f}%".replace(',', '.'),
        "Porcentaje Full": f"{porcentaje_full:.2f}%".replace(',', '.')
    }
    cols = st.columns(len(total_operaciones_dict))
    for col, (title, value) in zip(cols, total_operaciones_dict.items()):
        with col:
            with st.container(border=True):
                st.metric(title, value)

# Mostrar totales en la aplicación
st.subheader("Total periodo")
display_totals(totales)
display_envios(df_merged)

# Visualización del contenido

with st.expander("DataFrame periodo:"):
    st.dataframe(df_merged)

# Línea separadora
st.markdown("---")



# Copia de df_merged
df_filter = df_merged.copy()

# Asegurarse de que las columnas de fechas estén en formato datetime
df_merged['Fecha'] = pd.to_datetime(df_merged['Fecha'], errors='coerce', format="%d/%m/%Y %H:%M:%S")

# Filtro por 'Marca' en el DataFrame
unique_brands = df_merged['Marca'].unique()
sorted_brands = sorted(unique_brands)
col_selectbox = st.columns(5)

with col_selectbox[0]:
    selected_brand = st.selectbox("Selecciona una marca:", ["Todas"] + sorted_brands)

# Filtrar por marca seleccionada
df_filter = df_merged.copy()
if selected_brand != "Todas":
    df_filter = df_filter[df_filter['Marca'] == selected_brand]
        


# Crear dos entradas de fecha
with col_selectbox[1]:
    start_date = st.date_input("Fecha inicial:", value=df_merged['Fecha'].min())

with col_selectbox[2]:
    end_date = st.date_input("Fecha final:", value=df_merged['Fecha'].max() + timedelta(days=1))

# Filtrar el DataFrame en base a las fechas seleccionadas
df_filter = df_filter[(df_filter['Fecha'] >= pd.to_datetime(start_date)) & 
                      (df_filter['Fecha'] <= pd.to_datetime(end_date))]


filtro_monto_total = df_filter['Monto_Total'].sum()

last_day = df_filter['Fecha'].max() + timedelta(days=1)
day_before = last_day - pd.Timedelta(days=1)  # Obtener la fecha de ayer


# Formatear los totales
total_limpio_filtered = df_filter['Limpio'].sum()
total_costo_filtered = df_filter['costo_total_iva'].sum()
total_comision_filtered = df_filter['Comisión en pesos'].sum()
total_markup_filtered = ((total_limpio_filtered / total_costo_filtered) - 1) * 100
total_venta_ml_filtered = df_filter['Monto_Total'].sum()
total_ganancia_filtered = total_limpio_filtered - total_costo_filtered



totales_filtered = {
    "Total Ventas ML": f"$ {total_venta_ml_filtered:,.0f}".replace(',', '.'),
    "Total Limpio": f"$ {total_limpio_filtered:,.0f}".replace(',', '.'),
    "Total Ganancia": f"$ {total_ganancia_filtered:,.0f}".replace(',', '.'),
    "Total Markup": f"{total_markup_filtered:+.2f}%".replace(',', '.'),
}

# Crear gráficos para los totales
def display_totals_filtered(totales, last_day=last_day, day_before=day_before):
    cols = st.columns(len(totales))
    for col, (title, value) in zip(cols, totales.items()):
        with col:
            with st.container(border=True):
                #if title == "Total Markup":
                #    columna = 'MarkUp'
                #    delta, delta_percent = calcular_delta(df_filter, columna, last_day, day_before)
                #    st.metric(title, value, delta=f"{delta:+,.0f} ({delta_percent:+.2f}%))" , delta_color="inverse")
                #else:
                #    # Calcular delta
                #    if title == "Total Ventas ML":
                #        columna = 'Monto_Total'
                #    elif title == "Total Limpio":
                #        columna = 'Limpio'
                #    elif title == "Total Ganancia":
                #        columna = 'costo_total_iva'
                #    delta, delta_percent = calcular_delta(df_filter, columna, last_day, day_before)
                #    delta_color = "inverse" if delta < 0 else "normal"
                #    st.metric(title, value, delta=f"vs. día anterior: $ {delta:+,.0f} ($ {delta_percent:+.2f}))",delta_color=delta_color)  # Muestra la métrica con delta
                st.metric(title, value)
def display_envios_filtered(df):
    total_operaciones, total_flex, total_colecta, total_retiros, total_full, porcentaje_flex, porcentaje_colecta, porcentaje_retiros, porcentaje_full = calcular_flex(df)
    total_operaciones_dict = {
        "Total Operaciones": f"{total_operaciones:,.0f}".replace(',', '.'),
        "Total Flex": f"{total_flex:,.0f}".replace(',', '.'),
        "Total Colecta": f"{total_colecta:,.0f}".replace(',', '.'),
        "Total Retiros": f"{total_retiros:,.0f}".replace(',', '.'),
        "Total Full": f"{total_full:,.0f}".replace(',', '.'),
        "Porcentaje Flex": f"{porcentaje_flex:.2f}%".replace(',', '.'),
        "Porcentaje Colecta": f"{porcentaje_colecta:.2f}%".replace(',', '.'),
        "Porcentaje Retiros": f"{porcentaje_retiros:.2f}%".replace(',', '.'),
        "Porcentaje Full": f"{porcentaje_full:.2f}%".replace(',', '.')
    }
    cols = st.columns(len(total_operaciones_dict))
    for col, (title, value) in zip(cols, total_operaciones_dict.items()):
        with col:
            with st.container(border=True):
                st.metric(title, value)

# Mostrar totales en la aplicación
st.subheader("Total filtro")
display_totals_filtered(totales_filtered)
display_envios_filtered(df_filter)

# Línea separadora
st.markdown("---")

with st.expander("Filtro de columnas"):
    # Inicializa el estado de la sesión si no existe
    if 'selected_columns' not in st.session_state:
        # Aquí se especifican las columnas que deben estar seleccionadas por defecto
        st.session_state.selected_columns = ["Fecha", "Marca", "Categoría","SubCategoría","Código_Item","Descripción","Cantidad","Monto_Unitario","Monto_Total","IVA","Costo en pesos","Comisión", "Comisión en pesos","Limpio","MarkUp"]  # Empieza vacío para que todas estén destildadas

    # Título de la aplicación
    st.subheader("Seleccionar las columnas a visualizar")

    # Número de columnas en la interfaz
    num_columns = 5
    columns = st.columns(num_columns)  # Crear las columnas para los checkboxes


    # Crear checkboxes para cada columna
    for i, column in enumerate(df_filter.columns):
        with columns[i % num_columns]:  # Colocar el checkbox en la columna correspondiente
            checked = column in st.session_state.selected_columns
            if st.checkbox(column, value=checked):
                if column not in st.session_state.selected_columns:
                    st.session_state.selected_columns.append(column)
            else:
                if column in st.session_state.selected_columns:
                    st.session_state.selected_columns.remove(column)

# Filtrar el DataFrame según las columnas seleccionadas
filtered_df = df_filter[st.session_state.selected_columns]


# Mostrar el DataFrame filtrado
with st.expander("DataFrame filtrado:"):
    st.dataframe(filtered_df)

def prueba_torta(df):
    total_operaciones, total_flex, total_colecta, total_retiros, total_full, porcentaje_flex, porcentaje_colecta, porcentaje_retiros, porcentaje_full = calcular_flex(df)
    total_operaciones_dict = {
        "Total Flex": total_flex,
        "Total Colecta": total_colecta,
        "Total Retiros": total_retiros,
        "Total Full": total_full
    }
    # Convertir el diccionario en listas para Matplotlib
    labels = list(total_operaciones_dict.keys())
    sizes = list(total_operaciones_dict.values())

    # Crear el gráfico de torta
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Hace que el gráfico sea un círculo

    # Mostrar en Streamlit
    st.pyplot(fig)

prueba_torta(df_filter)