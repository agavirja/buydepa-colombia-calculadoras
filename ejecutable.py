import streamlit as st
import re
import pandas as pd
import mysql.connector as sql
from datetime import datetime 
from sidefunctions import precio_compra, get_data_market, get_data_recorrido, coddir

# streamlit run D:\Dropbox\Empresa\Buydepa\COLOMBIA\DESARROLLO\streamlit\calculadora\ejecutable.py
# https://streamlit.io/
# pipreqs --encoding utf-8 "D:\Dropbox\Empresa\Buydepa\COLOMBIA\DESARROLLO\streamlit\calculadora"
# https://share.streamlit.io/
# cuenta de github - agavirja
    
user     = st.secrets["buydepauser"]
password = st.secrets["buydepapass"]
host     = st.secrets["buydepahost"]
database = st.secrets["buydepadatabase"]


st.title('Calculadoras Buydepa Colombia')
#-----------------------------------------------------------------------------#
# Precio de compra
#-----------------------------------------------------------------------------#
with st.expander("Calcular precio de compra"):
    st.text('Calcular el precio de compra de acuerdo al precio de venta del inmueble')
    precioventa = st.text_input('Precio al que se vende el inmueble')
    try:    
        precioventa = float(precioventa)
        valor       = f'${precioventa:,.0f}'
        st.write(valor)
    except: precioventa = None

    areaconstruida = st.slider('Area construida',min_value=30,max_value=150,value=50)
    adminsitracion = st.text_input('Valor de la adminsitracion','')
    try:    
        adminsitracion = float(adminsitracion)
        valor          = f'${adminsitracion:,.0f}'
        st.write(valor)
    except: adminsitracion = None
    
    remodelacion = st.text_input('Gastos de remodelacion','')
    try:    
        remodelacion = float(remodelacion)
        valor        = f'${remodelacion:,.0f}'
        st.write(valor)
    except: remodelacion = None 

    meses = st.slider('Meses maximos para la venta',min_value=1,max_value=24,value=6)

    try:    areaconstruida = float(areaconstruida)
    except: areaconstruida = None
    try:    meses = int(meses)
    except: meses = None 
    inputvar = {'precio_venta':precioventa,'areaconstruida':areaconstruida,'admon':adminsitracion,'nmonths':meses,'remodelacion':remodelacion}

    idcontinue = True
    for i in [precioventa,areaconstruida]:
        if idcontinue:
            if i is None or i=='':
                idcontinue = False
    if idcontinue:
        resultado  = precio_compra(inputvar)
        col1,col2  = st.columns(2)        
        col1.text('Precio de compra: ')
        valor = resultado['preciocompra']
        valor = f'${valor:,.0f}'
        col2.write(valor)
        col1.text('Retorno bruto esperado: ')
        col2.write("{:.2%}".format(resultado['retorno_bruto_esperado']))
        col1.text('Retorno neto esperado: ')
        col2.write("{:.2%}".format(resultado['retorno_neto_esperado']))
        col1.text('Gastos notariales al comprar: ')
        valor = resultado['gn_compra']
        valor = f'${valor:,.0f}'
        col2.write(valor)
        col1.text('Gastos notariales al vender: ')
        valor = resultado['gn_venta']
        valor = f'${valor:,.0f}'
        col2.write(valor)
        col1.text('Comisiones: ')
        valor = resultado['comisiones']
        valor = f'${valor:,.0f}'
        col2.write(valor)
        col1.text('Otros gastos estimados: ')
        valor = resultado['otros_gastos']
        valor = f'${valor:,.0f}'
        col2.write(valor)