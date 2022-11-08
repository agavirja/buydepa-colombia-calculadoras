import streamlit as st
import pandas as pd
import mysql.connector as sql

# streamlit run D:\Dropbox\Empresa\Buydepa\COLOMBIA\DESARROLLO\streamlit\calculadora\ejecutable.py
# https://streamlit.io/
# pipreqs --encoding utf-8 "D:\Dropbox\Empresa\Buydepa\COLOMBIA\DESARROLLO\streamlit\calculadora"
# https://share.streamlit.io/
# cuenta de github - agavirja
    
user     = st.secrets["buydepauser"]
password = st.secrets["buydepapass"]
host     = st.secrets["buydepahost"]
database = st.secrets["buydepadatabase"]
    
def get_id_inmueble_list(x):
    user     = st.secrets["buydepauser"]
    password = st.secrets["buydepapass"]
    host     = st.secrets["buydepahost"]
    database = st.secrets["buydepadatabase"]
    condicion = ''
    if x:
        condicion = ' WHERE activo=1'
    db_connection  = sql.connect(user=user, password=password, host=host, database=database)
    datainmuebles  = pd.read_sql(f"SELECT id as id_inmueble,direccion_formato,nombre_conjunto FROM {database}.app_callcenter_inbound {condicion}" , con=db_connection)
    db_connection.close()
    datainmuebles = datainmuebles.sort_values(by='id_inmueble',ascending=True)
    return datainmuebles


st.title('Calculadoras Buydepa Colombia')
#-----------------------------------------------------------------------------#
# Precio de compra
#-----------------------------------------------------------------------------#
with st.expander("nueva forma de calcular"):
    st.text('cambio a la funcion')
    data = get_id_inmueble_list(True)
    st.write(data.head())
            