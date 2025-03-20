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
from streamlit_dynamic_filters import DynamicFilters
 

# Set page config
st.set_page_config(page_title="Gauss Online | Dashboard", page_icon="images/white-g.png", layout="wide", initial_sidebar_state="expanded")


# Establecer el locale para el formato deseado
try:
    locale.setlocale(locale.LC_ALL, 'es_AR.UTF-8')
except locale.Error:
    print("La configuración regional 'es_AR.UTF-8' no está disponible, utilizando configuración predeterminada.")

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
        st.session_state.token = token
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

@st.cache_data
def dashboard():
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


authenticate()

df = dashboard()
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


#if not df.empty:
#    st.write(df)
#else:
#    st.warning("No se cargaron datos en el DataFrame.")




columnas_sin_comas = ['ID_de_Operación','ML_id', 'subcat_id']  # Nombres de las keys/columnas del DataFrame

# Formatear solo las columnas especificadas sin comas
for column in columnas_sin_comas:
    df[column] = df[column].map(lambda x: '{:.0f}'.format(x) if isinstance(x, (int, float)) else x)


# Formatear fecha a formato dd/mm/aaaa hh:mm:ss
# Convertir la columna de fechas, manejando fechas con o sin microsegundos


df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
df['original_date'] = df['Fecha']

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
    'subcat_id': [3821,3820,3882,3819,3818,3885,3879,3869,3870,3919,3915,3841,3858,3922,3860,3861,3902,3866,3856,3893,3886,3887,3924,3921,3920,3912,3913,3878,3875,3876,3880,3894,3853,3931,3926,3891,3843,3918,3849,3888,3852,3899,3838,3895,3896,3957,3907],
    'group': [2,2,2,2,2,2,2,3,3,3,3,3,3,4,4,4,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,6,7,7,7,7,8,8,8,8,8,8,3,3]
}

# Verificación de longitudes
if len(data_subcat['subcat_id']) == len(data_subcat['group']):
    df_subcat = pd.DataFrame(data_subcat)
else:
    print("Las listas no tienen la misma longitud. Ajusta los datos.")

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
    'pricelist': [4, 5, 17, 14, 13, 23, 9, 10, 11, 15, 16, 12, 18, 19, 20, 21, 22,6],
    1: [15.5, None, 24.4, 30.4, 35.4, 41, None, 4.83, 13.73, 19.73, 24.73, 15.5, 24.4, 30.4, 35.4, 41, 30.33,29.5],
    2: [12.15, None, 21.05, 27.05, 32.55, 37.65, None, 4.83, 13.73, 19.73, 24.73, 12.15, 21.05, 27.05, 32.55, 37.65, 30.33,26.15],
    3: [12.65, None, 21.55, 27.55, 32.55, 38.15, None, 4.83, 13.73, 19.73, 24.73, 12.65, 21.55, 27.55, 32.55, 38.15, 30.33,26.65],
    4: [13.65, None, 22.55, 28.55, 33.55, 39.15, None, 4.83, 13.73, 19.73, 24.73, 13.65, 22.55, 28.55, 33.55, 39.15, 30.33,27.65],
    5: [14, None, 22.9, 28.9, 33.9, 39.5, None, 4.83, 13.73, 19.73, 24.73, 14, 22.9, 28.9, 33.9, 39.5, 30.33,28],
    6: [14.5, None, 23.4, 29.4, 34.4, 40, None, 4.83, 13.73, 19.73, 24.73, 14.5, 23.4, 29.4, 34.4, 40, 30.33,28.5],
    7: [15, None, 23.9, 29.9, 34.9, 40.5, None, 4.83, 13.73, 19.73, 24.73, 15, 23.9, 29.9, 34.9, 40.5, 30.33,29],
    8: [16, None, 24.9, 30.9, 35.9, 41.5, None, 4.83, 13.73, 19.73, 24.73, 16, 24.9, 30.9, 35.9, 41.5, 30.33,30]
}
2
data_prices_feb_25 = {
    'pricelist2': [4, 5, 17, 14, 13, 23, 9, 10, 11, 15, 16, 12, 18, 19, 20, 21, 22,6],
    1: [15.5, None, 22.9, 27.4, 32, 36.5, None, 4.83, 13.73, 19.73, 24.73, 15.5, 24.4, 30.4, 35.4, 41, 30.33,29.5],
    2: [12.15, None, 19.55, 24.05, 28.65, 33.15, None, 4.83, 13.73, 19.73, 24.73, 12.15, 21.05, 27.05, 32.55, 37.65, 30.33,26.15],
    3: [12.65, None, 20.05, 24.55, 29.15, 33.65, None, 4.83, 13.73, 19.73, 24.73, 12.65, 21.55, 27.55, 32.55, 38.15, 30.33,26.65],
    4: [13.65, None, 21.05, 25.55, 30.15, 34.65, None, 4.83, 13.73, 19.73, 24.73, 13.65, 22.55, 28.55, 33.55, 39.15, 30.33,27.65],
    5: [14, None, 21.4, 25.9, 30.5, 35, None, 4.83, 13.73, 19.73, 24.73, 14, 22.9, 28.9, 33.9, 39.5, 30.33,28],
    6: [14.5, None, 21.9, 26.4, 31, 35.5, None, 4.83, 13.73, 19.73, 24.73, 14.5, 23.4, 29.4, 34.4, 40, 30.33,28.5],
    7: [15, None, 22.4, 26.9, 31.5, 36, None, 4.83, 13.73, 19.73, 24.73, 15, 23.9, 29.9, 34.9, 40.5, 30.33,29],
    8: [16, None, 23.4, 27.9, 32.5, 37, None, 4.83, 13.73, 19.73, 24.73, 16, 24.9, 30.9, 35.9, 41.5, 30.33,30]
}

# Crear DataFrame de precios
df_prices = pd.DataFrame(data_prices)
df_prices_feb_25 = pd.DataFrame(data_prices_feb_25)

# Primero, asegurémonos de que la columna 'pricelist' en df_prices sea un valor único para los precios.
df_prices_melted = df_prices.melt(id_vars='pricelist', var_name='subcat_id', value_name='Comisión')
df_prices_feb_25_melted = df_prices_feb_25.melt(id_vars='pricelist2', var_name='subcat_id2', value_name='Comisión_feb_25')

# Ahora, fusionamos df_merged con df_prices_melted
df_merged = df_merged.merge(
    df_prices_melted,
    left_on=['priceList', 'subcat_id'],
    right_on=['pricelist', 'subcat_id'],
    how='left'
)

df_merged = df_merged.merge(
    df_prices_feb_25_melted,
    left_on=['priceList', 'subcat_id'],
    right_on=['pricelist2', 'subcat_id2'],
    how='left'
)

# Eliminamos pricelist
df_merged.drop(columns=['pricelist'], inplace=True)
df_merged.drop(columns=['pricelist2'], inplace=True)

# Calculamos la comisión en pesos
df_merged['Comisión en pesos'] = np.where(
    df_merged['original_date'] >= pd.Timestamp("2025-02-26"),
    np.where(df_merged['original_date'] >= pd.Timestamp("2025-03-11"),
        np.where(
            df_merged['Monto_Unitario'] >= 30000,
            (df_merged['Monto_Unitario'] * (((df_merged['Comisión_feb_25'] / 100) / 1.21) + (varios_percent / 100))) * df_merged['Cantidad'],
            np.where(
                df_merged['Monto_Unitario'] < 12000,
                (df_merged['Monto_Unitario'] * (((df_merged['Comisión_feb_25'] / 100) / 1.21) + (varios_percent / 100)) + (900 / 1.21)) * df_merged['Cantidad'],
                (df_merged['Monto_Unitario'] * (((df_merged['Comisión_feb_25'] / 100) / 1.21) + (varios_percent / 100)) + (1800 / 1.21)) * df_merged['Cantidad']
            )
        ),
        np.where(
            df_merged['Monto_Unitario'] >= min_free,
            (df_merged['Monto_Unitario'] * (((df_merged['Comisión_feb_25'] / 100) / 1.21) + (varios_percent / 100))) * df_merged['Cantidad'],
            np.where(
                df_merged['Monto_Unitario'] < min_fijo,
                (df_merged['Monto_Unitario'] * (((df_merged['Comisión_feb_25'] / 100) / 1.21) + (varios_percent / 100)) + (valor_fijo / 1.21)) * df_merged['Cantidad'],
                np.where(df_merged['Monto_Unitario'] < max_fijo,
                (df_merged['Monto_Unitario'] * (((df_merged['Comisión_feb_25'] / 100) / 1.21) + (varios_percent / 100)) + (valor_max_fijo / 1.21)) * df_merged['Cantidad'],
                (df_merged['Monto_Unitario'] * (((df_merged['Comisión_feb_25'] / 100) / 1.21) + (varios_percent / 100)) + (valor_free / 1.21)) * df_merged['Cantidad'])
            )
        )
    ),
    np.where(
        df_merged['Monto_Unitario'] >= 30000,
        (df_merged['Monto_Unitario'] * (((df_merged['Comisión'] / 100) / 1.21) + (varios_percent / 100))) * df_merged['Cantidad'],
        np.where(
            df_merged['Monto_Unitario'] < 12000,
            (df_merged['Monto_Unitario'] * (((df_merged['Comisión'] / 100) / 1.21) + (varios_percent / 100)) + (900 / 1.21)) * df_merged['Cantidad'],
            (df_merged['Monto_Unitario'] * (((df_merged['Comisión'] / 100) / 1.21) + (varios_percent / 100)) + (1800 / 1.21)) * df_merged['Cantidad']
        )
    )
)

df_merged.drop(columns=['original_date'], inplace=True)
df_merged['Costo envío'] = np.where(
    df_merged['ML_logistic_type'] == 'self_service',
    df_merged['mlp_price4FreeShipping'], df_merged['mlp_price4FreeShipping']
)

# Crea una columna auxiliar con la cuenta de cada 'ML_pack_id'
#df_merged['contar_si'] = df_merged.groupby('ML_pack_id')['ML_pack_id'].transform('count')

def limpiar(row):
    if pd.isnull(row['ML_pack_id']):  # Verifica si ML_pack_id está vacío
        return (row['Monto_Unitario'] * row['Cantidad']) - ((row['Costo envío'] / 1.21)*row['Cantidad'])  - row['Comisión en pesos']
    else:
        #contar_si = row['contar_si']  # Utiliza el valor de 'contar_si' calculado por cada fila
        return (row['Monto_Unitario'] * row['Cantidad']) - ((row['Costo envío'] / 1.21)*row['Cantidad']) - row['Comisión en pesos']


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

def display_top_10_marcas(df):
# Agrupar por 'Marca' y sumar 'Monto_Total'
    df_grouped = df.groupby('Marca', as_index=False)['Monto_Total'].sum()

    # Filtrar las 10 marcas con más facturación
    top_10_marcas = df_grouped.nlargest(10, 'Monto_Total')

    # Renombrar la columna 'Monto_Total' a 'Facturación ML'
    top_10_marcas = top_10_marcas.rename(columns={'Monto_Total': 'Facturación ML'})

    # Crear el gráfico
    fig = px.bar(top_10_marcas, x='Marca', y='Facturación ML',
             title='Top 10 Marcas por Facturación')
    
    st.plotly_chart(fig)

def display_top_10_categorias(df):
# Agrupar por 'Marca' y sumar 'Monto_Total'
    df_grouped = df.groupby('Categoría', as_index=False)['Monto_Total'].sum()

    # Filtrar las 10 marcas con más facturación
    top_10_marcas = df_grouped.nlargest(10, 'Monto_Total')

    # Renombrar la columna 'Monto_Total' a 'Facturación ML'
    top_10_marcas = top_10_marcas.rename(columns={'Monto_Total': 'Facturación ML'})

    # Crear el gráfico
    fig = px.bar(top_10_marcas, x='Categoría', y='Facturación ML',
             title='Top 10 Categoría por Facturación')
    
    st.plotly_chart(fig)

def display_top_10_subcategorias(df):
# Agrupar por 'Marca' y sumar 'Monto_Total'
    df_grouped = df.groupby('SubCategoría', as_index=False)['Monto_Total'].sum()

    # Filtrar las 10 marcas con más facturación
    top_10_marcas = df_grouped.nlargest(10, 'Monto_Total')

    # Renombrar la columna 'Monto_Total' a 'Facturación ML'
    top_10_marcas = top_10_marcas.rename(columns={'Monto_Total': 'Facturación ML'})
    
    # Crear el gráfico
    fig = px.bar(top_10_marcas, x='SubCategoría', y='Facturación ML',
             title='Top 10 SubCategoría por Facturación')
    
    st.plotly_chart(fig)

def display_top_10_productos(df):
# Agrupar por 'Marca' y sumar 'Monto_Total'
    df_grouped = df.groupby('Descripción', as_index=False)['Monto_Total'].sum()

    # Filtrar las 10 marcas con más facturación
    top_10_productos = df_grouped.nlargest(10, 'Monto_Total')

    # Renombrar la columna 'Monto_Total' a 'Facturación ML'
    top_10_productos = top_10_productos.rename(columns={'Monto_Total': 'Facturación ML','Descripción': 'Producto'})

    # Truncar los nombres de productos largos
    top_10_productos['Producto'] = top_10_productos['Producto'].apply(lambda x: x[:25] + '...' if len(x) > 25 else x)


    # Crear el gráfico
    fig = px.bar(top_10_productos, x='Producto', y='Facturación ML',
             title='Top 10 Producto por Facturación')
    
    st.plotly_chart(fig)

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


# Aplicamos la función y formateamos el resultado.
df_merged['MarkUp'] = df_merged.apply(markupear, axis=1)
df_merged['MarkUp'] = df_merged['MarkUp'].apply(lambda x: f"{x:.2f}%")

def prueba_torta(df):
    # Calcular los totales y porcentajes
    total_operaciones, total_flex, total_colecta, total_retiros, total_full, porcentaje_flex, porcentaje_colecta, porcentaje_retiros, porcentaje_full = calcular_flex(df)
    
    # Crear diccionario de valores
    total_operaciones_dict = {
        "Total Flex": total_flex,
        "Total Colecta": total_colecta,
        "Total Retiros": total_retiros,
        "Total Full": total_full
    }
    
    # Preparar datos para el gráfico
    labels = list(total_operaciones_dict.keys())
    sizes = list(total_operaciones_dict.values())
    
    # Calcular porcentajes
    total = sum(sizes)
    porcentajes = [size / total * 100 for size in sizes]

    # Crear una lista de etiquetas con valores y porcentajes
    labels_with_values = [f"{label} ({size} - {pct:.1f}%)" for label, size, pct in zip(labels, sizes, porcentajes)]

    colors =  plt.get_cmap('Blues')(np.linspace(0.2, 0.7, len(total_operaciones_dict))) # Colores personalizados
    explode = (0, 0, 0, 0)  # Destacar el primer sector

    # Crear el gráfico de torta
    fig, ax = plt.subplots(facecolor='none')  # Fondo de la figura transparente
    ax.set_facecolor('none')  # Fondo del eje transparente

    # Crear el gráfico de torta
    wedges, texts = ax.pie(
        sizes, labels=None, startangle=90,
        colors=colors, explode=explode, pctdistance=0.85
    )
    ax.axis('equal')  # Hace que el gráfico sea un círculo

    # Añadir título
    #ax.set_title("Distribución de Operaciones", fontsize=14)

    # Agregar leyenda con valores y porcentajes
    ax.legend(wedges, labels_with_values, title=f"Operaciones: {total_operaciones}",  loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)

    # Mostrar el gráfico en Streamlit
    st.pyplot(fig)

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
col_overheader = st.columns(3)
col_header = st.columns(2)

with col_header[0]:
    """
    # Resumen de Ventas
    
    """

with col_overheader[2]:
    st.image("images/white-g-logo.png",use_container_width=True)

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
#st.subheader("Total periodo")
#display_totals(totales)
#display_envios(df_merged)
col_over_envios = st.columns(3)
col_under_envios = st.columns(3)

with col_under_envios[0]:
    st.markdown("#### Total Periodo:")
    with st.container(border=True):
        st.metric("Total Ventas ML", f"$ {total_ventas_ml:,.0f}".replace(',', '.'))  # Muestra el total_ventas_ml
        st.metric("Total Limpio", f"$ {total_limpio:,.0f}".replace(',', '.'))  # Muestra el total_limpio
        st.metric("Total Ganancia", f"$ {total_ganancia:,.0f}".replace(',', '.'))  # Muestra el total_ganancia
        st.metric("Total Markup", f"{total_markup:,.2f}%".replace(',', '.'))  # Muestra el total_markup
with col_under_envios[1]:
    st.markdown("#### Detalle de envíos:")
    prueba_torta(df_merged)
with col_over_envios[2]:
    seleccionar_grafico = st.selectbox("Seleccionar gráfico", ["Top 10 Marcas por Facturación", "Top 10 SubCategoría por Facturación", "Top 10 Categoría por Facturación", "Top 10 Productos por Facturación","Top 10 Marcas por Ventas", "Top 10 SubCategoría por Ventas", "Top 10 Categoría por Ventas", "Top 10 Productos por Ventas"])
with col_under_envios[2]:
    if seleccionar_grafico == "Top 10 SubCategoría por Facturación":
        display_top_10_subcategorias(df_merged)
    elif seleccionar_grafico == "Top 10 Categoría por Facturación":
        display_top_10_categorias(df_merged)
    elif seleccionar_grafico == "Top 10 Marcas por Facturación":
        display_top_10_marcas(df_merged)
    elif seleccionar_grafico == "Top 10 Productos por Facturación":
        display_top_10_productos(df_merged)
    elif seleccionar_grafico == "Top 10 Marcas por Ventas":
        display_top_10_gen(df_merged, 'Marca', 'Cantidad', 'Marca', 'Unidades Vendidas')
    elif seleccionar_grafico == "Top 10 SubCategoría por Ventas":
        display_top_10_gen(df_merged, 'SubCategoría', 'Cantidad', 'SubCategoría', 'Unidades Vendidas')    
    elif seleccionar_grafico == "Top 10 Categoría por Ventas":
        display_top_10_gen(df_merged, 'Categoría', 'Cantidad', 'Categoría', 'Unidades Vendidas')
    elif seleccionar_grafico == "Top 10 Productos por Ventas":
        display_top_10_gen(df_merged, 'Descripción', 'Cantidad', 'Producto', 'Unidades Vendidas')

# Visualización del contenido

with st.expander("DataFrame periodo:"):
    st.dataframe(df_merged)

# Línea separadora
st.markdown("---")



# Asegurarse de que las columnas de fechas estén en formato datetime
df_merged['Fecha'] = pd.to_datetime(df_merged['Fecha'], errors='coerce', format="%d/%m/%Y %H:%M:%S")

# Filtro por 'Marca' en el DataFrame
unique_brands = df_merged['Marca'].unique()
sorted_brands = sorted(unique_brands)

    
st.write("Aplicar los filtros en cualquier orden 👇")
col_selectbox = st.columns(5)

#with col_selectbox[0]:
#   selected_brand = st.selectbox("Selecciona una marca:", ["Todas"] + sorted_brands)


# Filtrar por marca seleccionada
df_filter = df_merged.copy()
# Filtrar el DataFrame en base a las fechas seleccionadas




# Crear dos entradas de fecha
with col_selectbox[0]:
    start_date = st.date_input("Fecha inicial:", value=df_merged['Fecha'].min())
    

with col_selectbox[1]:
    end_date = st.date_input("Fecha final:", value=df_merged['Fecha'].max() + timedelta(days=1))



with col_selectbox[4]:
        seleccionar_grafico_filtrado = st.selectbox("Elegir gráfico:", ["Top 10 Marcas por Facturación","Top 10 SubCategoría por Facturación", "Top 10 Categoría por Facturación","Top 10 Productos por Facturación","Top 10 Marcas por Ventas", "Top 10 SubCategoría por Ventas", "Top 10 Categoría por Ventas", "Top 10 Productos por Ventas"])


df_filter = df_filter[(df_filter['Fecha'] >= pd.to_datetime(start_date)) & 
                      (df_filter['Fecha'] <= pd.to_datetime(end_date))]


filtro_monto_total = df_filter['Monto_Total'].sum()

last_day = df_filter['Fecha'].max() + timedelta(days=1)
day_before = last_day - pd.Timedelta(days=1)  # Obtener la fecha de ayer

dynamic_filters = DynamicFilters(df_filter, filters=['Marca','SubCategoría','Categoría', 'Descripción'])

dynamic_filters.display_filters(location='columns', num_columns=4, gap='small')

filtered_df = dynamic_filters.filter_df(except_filter='None')

#with col_selectbox[2]:
#    st.markdown("")
#    st.markdown("")
#    st.button("Limpiar Filtros", on_click=dynamic_filters.reset_filters())

df_filter = filtered_df

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
#st.subheader("Total filtro")
#display_totals_filtered(totales_filtered)
#display_envios_filtered(df_filter)

col_under_flex = st.columns(3)



with col_under_flex[0]:
    st.markdown("#### Total Filtrado:")
    with st.container(border=True):
        st.metric("Total Ventas ML", f"$ {total_venta_ml_filtered:,.0f}".replace(',', '.'))  # Muestra el total_ventas_ml
        st.metric("Total Limpio", f"$ {total_limpio_filtered:,.0f}".replace(',', '.'))  # Muestra el total_limpio
        st.metric("Total Ganancia", f"$ {total_ganancia_filtered:,.0f}".replace(',', '.'))  # Muestra el total_ganancia
        st.metric("Total Markup", f"{total_markup_filtered:,.2f}%".replace(',', '.'))  # Muestra el total_markup

with col_under_flex[1]:
    st.markdown("#### Detalle de envíos filtrados:")
    prueba_torta(df_filter)

with col_under_flex[2]:
        if seleccionar_grafico_filtrado == "Top 10 SubCategoría por Facturación":
            display_top_10_subcategorias(df_filter)
        elif seleccionar_grafico_filtrado == "Top 10 Categoría por Facturación":
            display_top_10_categorias(df_filter)
        elif seleccionar_grafico_filtrado == "Top 10 Marcas por Facturación":
            display_top_10_marcas(df_filter)
        elif seleccionar_grafico_filtrado == "Top 10 Productos por Facturación":
            display_top_10_productos(df_filter)
        elif seleccionar_grafico_filtrado == "Top 10 Marcas por Ventas":
            display_top_10_gen(df_filter, 'Marca', 'Cantidad', 'Marca', 'Unidades Vendidas')
        elif seleccionar_grafico_filtrado == "Top 10 SubCategoría por Ventas":
            display_top_10_gen(df_filter, 'SubCategoría', 'Cantidad', 'SubCategoría', 'Unidades Vendidas')    
        elif seleccionar_grafico_filtrado == "Top 10 Categoría por Ventas":
            display_top_10_gen(df_filter, 'Categoría', 'Cantidad', 'Categoría', 'Unidades Vendidas')
        elif seleccionar_grafico_filtrado == "Top 10 Productos por Ventas":
            display_top_10_gen(df_filter, 'Descripción', 'Cantidad', 'Producto', 'Unidades Vendidas')

# Línea separadora
st.markdown("---")


with st.expander("Filtro de columnas"):
    # Inicializa el estado de la sesión si no existe
    if 'selected_columns' not in st.session_state:
        # Aquí se especifican las columnas que deben estar seleccionadas por defecto
        st.session_state.selected_columns = ["Fecha", "Marca", "Categoría","SubCategoría","Código_Item","Descripción","Cantidad","Monto_Unitario","Monto_Total","IVA","Costo en pesos","Comisión", "Comisión en pesos","Limpio","MarkUp","costo_total_iva","Costo envío"]  # Empieza vacío para que todas estén destildadas

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


df_group = filtered_df.copy()
# Línea separadora

df_groupbybrand = df_group.groupby(['Marca'], as_index=False).agg({'Cantidad': 'sum','Monto_Total': 'sum','Limpio': 'sum','Costo en pesos': 'sum','Costo envío': 'sum', 'costo_total_iva': 'sum'})
df_groupbyitem = df_group.groupby(['Código_Item'], as_index=False).agg({'Descripción': 'first','Cantidad': 'sum','Monto_Total': 'sum','Limpio': 'sum','Costo en pesos': 'sum','Costo envío': 'sum', 'costo_total_iva': 'sum'})

# Aplicamos la función y formateamos el resultado.
df_groupbybrand['MarkUp'] = df_groupbybrand.apply(markupear, axis=1)
df_groupbybrand['MarkUp'] = df_groupbybrand['MarkUp'].apply(lambda x: f"{x:.2f}%")

# Aplicamos la función y formateamos el resultado.
df_groupbyitem['MarkUp'] = df_groupbyitem.apply(markupear, axis=1)
df_groupbyitem['MarkUp'] = df_groupbyitem['MarkUp'].apply(lambda x: f"{x:.2f}%")


with st.expander("Agrupado por Marcas:"):
    st.dataframe(df_groupbybrand)

df_final = df_groupbyitem.merge(df_ageing_unique[['Código', 'Ageing']], 
                                left_on='Código_Item', right_on='Código', 
                                how='left')

df_final.drop(columns='Código', inplace=True)


with st.expander("Agrupado por Productos:"):
    st.dataframe(df_final)
