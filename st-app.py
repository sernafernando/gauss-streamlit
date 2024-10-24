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

# Aplicamos la función y formateamos el resultado.
df_merged['MarkUp'] = df_merged.apply(markupear, axis=1)
df_merged['MarkUp'] = df_merged['MarkUp'].apply(lambda x: f"{x:.2f}%")


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
total_limpio = df_merged['Limpio'].sum()
total_costo = df_merged['costo_total_iva'].sum()
total_comision = df_merged['Comisión en pesos'].sum()
total_markup = ((total_limpio / total_costo)-1)*100

totales = {
    "Total Limpio": f"{total_limpio:.2f}",
    "Total Costo": f"{total_costo:.2f}",
    "Total Comisión": f"{total_comision:.2f}",
    "Total Markup": f"{total_markup:.2f}%"
}

# Crear gráficos para los totales
def display_totals(totales):
    cols = st.columns(len(totales))
    for col, (title, value) in zip(cols, totales.items()):
        with col:
            with st.container(border=True):
                    st.metric(title, value)  # Muestra la métrica
            #   st.bar_chart([total_limpio, total_costo, total_comision], use_container_width=True)  # Gráfico de barras

# Mostrar totales en la aplicación
st.subheader("Total periodo")
display_totals(totales)

# Visualización del contenido

# Línea separadora
st.markdown("---")

# Resultado final
#df_merged

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
    end_date = st.date_input("Fecha final:", value=df_merged['Fecha'].max())

# Filtrar el DataFrame en base a las fechas seleccionadas
df_filter = df_filter[(df_filter['Fecha'] >= pd.to_datetime(start_date)) & 
                      (df_filter['Fecha'] <= pd.to_datetime(end_date))]

filtro_monto_total = df_filter['Monto_Total'].sum()

# Formatear los totales
total_limpio_filtered = df_filter['Limpio'].sum()
total_costo_filtered = df_filter['costo_total_iva'].sum()
total_comision_filtered = df_filter['Comisión en pesos'].sum()
total_markup_filtered = ((total_limpio_filtered / total_costo_filtered)-1)*100

totales_filtered = {
    "Total Limpio": f"{total_limpio_filtered:.2f}",
    "Total Costo": f"{total_costo_filtered:.2f}",
    "Total Comisión": f"{total_comision_filtered:.2f}",
    "Total Markup": f"{total_markup_filtered:.2f}%"
}

# Crear gráficos para los totales
def display_totals_filtered(totales):
    cols = st.columns(len(totales))
    for col, (title, value) in zip(cols, totales.items()):
        with col:
            with st.container(border=True):
                    st.metric(title, value)  # Muestra la métrica
            #   st.bar_chart([total_limpio, total_costo, total_comision], use_container_width=True)  # Gráfico de barras

# Mostrar totales en la aplicación
st.subheader("Total filtro")
display_totals(totales_filtered)

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