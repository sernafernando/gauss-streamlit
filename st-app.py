import requests
from lxml import etree
import html
import json
import re
from dateutil.relativedelta import relativedelta
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import locale
import numpy as np

# Set page config
st.set_page_config(page_title="Gauss Online Dashboard", page_icon="images/white-g.png", layout="wide", initial_sidebar_state="expanded")
# Establecer el locale para el formato deseado
try:
    locale.setlocale(locale.LC_ALL, 'es_AR.UTF-8')
except locale.Error:
    print("La configuración regional 'es_AR.UTF-8' no está disponible, utilizando configuración predeterminada.")

st.title("Dashboard")

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
        to_date = st.date_input("Escriba fecha de fin", value=to_date)



#  Verificar que la fecha de inicio no sea mayor a la fecha de fin
#if from_date > to_date:
#    st.error("La fecha de inicio no puede ser mayor a la fecha de fin.")
#else:
#    st.success(f"Consultando datos desde {from_date} hasta {to_date}")

# Aquí puedes continuar con el resto de tu código usando las fechas seleccionadas
#st.write(f"Rango de fechas seleccionado: {from_date} a {to_date}")


"""
# Ventas ML
Consulta de Ventas ML

"""

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
    header_ws =  {"Content-Type": "text/xml", "muteHttpExceptions": "true"}
    # Hacemos la solicitud POST
    response = requests.post(url_ws, data=xml_payload.encode('utf-8'), headers=header_ws)

    # Verificamos si la respuesta fue exitosa
    if response.status_code != 200:
        print(f"Error en la solicitud: {response.status_code}")
        return

    print("Consulta a la API exitosa")
    # Parsear la respuesta XML
    namespaces = {
        'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
        'microsoft': 'http://microsoft.com/webservices/'
    }

    # Pasar el contenido directamente como bytes
    xml_string = response.content  # Aquí ya tienes el contenido en bytes

    # Parsear el XML
    root = etree.fromstring(xml_string)

    # Extraer el contenido de wsGBPScriptExecute4DatasetResult
    result_node = root.xpath('//microsoft:wsGBPScriptExecute4DatasetResult', namespaces=namespaces)
    if not result_node:
        print("No se encontró el nodo wsGBPScriptExecute4DatasetResult.")
        return

    result_content = result_node[0].text
    

    

    # Desescapar el contenido HTML
    unescaped_result = html.unescape(result_content)

    # Extraer el JSON dentro de <Column1>
    match = re.search(r'\[.*?\]', unescaped_result)
    if match:
        column1_json = match.group(0)  # Esto te dará la parte JSON entre corchetes
    else:
        print("No se encontró contenido JSON en Column1.")
        return

    
    
    try:
        column1_list = json.loads(column1_json)
    except json.JSONDecodeError as e:
        print(f"Error al decodificar el JSON: {e}")

    
    global df
    df = pd.DataFrame(column1_list)

   


authenticate()
dashboard()


columnas_sin_comas = ['ID_de_Operación','ML_id', 'subcat_id']  # Nombres de las keys/columnas del DataFrame

# Formatear solo las columnas especificadas sin comas
for column in columnas_sin_comas:
    df[column] = df[column].map(lambda x: '{:.0f}'.format(x) if isinstance(x, (int, float)) else x)


# Formatear fecha a formato dd/mm/aaaa hh:mm:ss
# Convertir la columna de fechas, manejando fechas con o sin microsegundos
df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')

# Formatear las fechas en un formato más legible
df['Fecha'] = df['Fecha'].dt.strftime('%d/%m/%Y %H:%M:%S')

# Crear columna de costo en pesos
df['Costo en pesos'] = df['Costo_sin_IVA'] * df['Cambio_al_Momento']

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
    'pricelist': [4, 5, 17, 14, 6, 13, 9, 10, 11, 15, 16],
    1: [15.5, None, 23.9, 29.5, 29.35, 33.5, None, 13.2, 18.8, 18.65, 22.8],
    2: [12.15, None, 20.55, 26.15, 26, 30.15, None, 13.2, 18.8, 18.65, 22.8],
    3: [12.65, None, 21.05, 26.65, 26.5, 30.65, None, 13.2, 18.8, 18.65, 22.8],
    4: [13.65, None, 22.05, 27.65, 27.5, 31.65, None, 13.2, 18.8, 18.65, 22.8],
    5: [14, None, 22.4, 28, 27.85, 32, None, 13.2, 18.8, 18.65, 22.8],
    6: [14.5, None, 22.9, 28.5, 28.35, 32.5, None, 13.2, 18.8, 18.65, 22.8],
    7: [15, None, 23.4, 29, 28.85, 33, None, 13.2, 18.8, 18.65, 22.8],
    8: [16, None, 24.4, 30, 29.85, 34, None, 13.2, 18.8, 18.65, 22.8]
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
    df_merged['MLShippmentCost4Seller'], df_merged['MLShippmentCost4Seller']
)

def limpiar(row):
    if pd.isnull(row['ML_pack_id']):  # Verifica si ML_pack_id está vacío
        return (row['Monto_Unitario'] * row['Cantidad']) - (row['Costo envío'] / 1.21) - row['Comisión en pesos']
    else:
        contar_si = df_merged['ML_pack_id'].value_counts().get(row['ML_pack_id'], 1)  # Cuenta las ocurrencias de ML_pack_id en la columna
        return (row['Monto_Unitario'] * row['Cantidad']) - ((row['Costo envío'] / contar_si) / 1.21) - row['Comisión en pesos']

# Aplicar la función a cada fila y guardar el resultado en una nueva columna
df_merged['Limpio'] = df_merged.apply(limpiar, axis=1)

# Calculamos el MarkUp
def markupear(row):
    return ((row['Limpio'] / ((row['Costo en pesos']*row['Cantidad'])*(1+(row['IVA']/100))))-1)*100

# Aplicamos la función y formateamos el resultado.
df_merged['MarkUp'] = df_merged.apply(markupear, axis=1)
df_merged['MarkUp'] = df_merged['MarkUp'].apply(lambda x: f"{x:.2f}%")

print(df_merged['Limpio'][:10], df_merged['Costo en pesos'][:10], df_merged['Cantidad'][:10], df_merged['IVA'][:10])
# Resultado final
df_merged

# Inicializa el estado de la sesión si no existe
if 'selected_columns' not in st.session_state:
    # Aquí se especifican las columnas que deben estar seleccionadas por defecto
    st.session_state.selected_columns = []  # Empieza vacío para que todas estén destildadas

# Título de la aplicación
st.title("Seleccionar columnas para visualizar")

# Número de columnas en la interfaz
num_columns = 5
columns = st.columns(num_columns)  # Crear las columnas para los checkboxes

# Crear checkboxes para cada columna
for i, column in enumerate(df_merged.columns):
    with columns[i % num_columns]:  # Colocar el checkbox en la columna correspondiente
        checked = column in st.session_state.selected_columns
        if st.checkbox(column, value=checked):
            if column not in st.session_state.selected_columns:
                st.session_state.selected_columns.append(column)
        else:
            if column in st.session_state.selected_columns:
                st.session_state.selected_columns.remove(column)

# Filtrar el DataFrame según las columnas seleccionadas
filtered_df = df_merged[st.session_state.selected_columns]

# Mostrar el DataFrame filtrado
st.write("DataFrame filtrado:")
st.dataframe(filtered_df)