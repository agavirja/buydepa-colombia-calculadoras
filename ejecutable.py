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

def get_id_inmueble_list(x):
    condicion = ''
    if x:
        condicion = ' WHERE activo=1'
    db_connection  = sql.connect(user=user, password=password, host=host, database=database)
    datainmuebles  = pd.read_sql(f"SELECT id as id_inmueble,direccion_formato,nombre_conjunto FROM {database}.app_callcenter_inbound {condicion}" , con=db_connection)
    db_connection.close()
    datainmuebles = datainmuebles.sort_values(by='id_inmueble',ascending=True)
    return datainmuebles

def get_id_inmueble_cuentas(id_inmueble):
    db_connection  = sql.connect(user=user, password=password, host=host, database=database)
    datacuentas    = pd.read_sql(f"SELECT * FROM  {database}.app_pm_cuentas WHERE id_inmueble='{id_inmueble}'" , con=db_connection)
    db_connection.close()
    return datacuentas

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
        
#-----------------------------------------------------------------------------#
# Precio de venta
#-----------------------------------------------------------------------------# 
with st.expander("¿Cuál es el margen de ganancia de acuerdo a la oferta de venta?"):
    datainmuebles =  get_id_inmueble_list(True)
    datainmuebles['combinacion'] = datainmuebles['id_inmueble'].astype(str)+'-'+datainmuebles['direccion_formato'].astype(str)+'-'+datainmuebles['nombre_conjunto'].astype(str)
    combinacion   = st.selectbox('ID Inmueble',options=datainmuebles['combinacion'].to_list())
    precioventa   = st.text_input('¿Cuál sería el precio de venta?','')
    try:    precioventa = float(precioventa)
    except: precioventa = 0
    comision_venta = st.slider('¿Comisión en la venta?',min_value=0.0,max_value=3.0,step=0.1,value=0.3)
    comision_venta = comision_venta/100
    st.write("{:.1%}".format(comision_venta))
    
    if precioventa==0:
        priceminvalue = 0
        pricemaxvalue = 1
        step          = 1
    else:
        priceminvalue = int(precioventa*0.85)
        pricemaxvalue = int(precioventa*1.15)
        step          = 1000000 
    precioventa   = st.slider('Simular diferentes precios de venta',min_value=priceminvalue,max_value=pricemaxvalue,step=step,value=int(precioventa))
    try:    
        precioventa = float(precioventa)
        valor       = f'${precioventa:,.0f}'
        st.write(valor)
    except: precioventa = 0
    
    datapaso = datainmuebles[datainmuebles['combinacion']==combinacion]
    if datapaso.empty is False:
        id_inmueble = datapaso['id_inmueble'].iloc[0]
        datacuentas = get_id_inmueble_cuentas(id_inmueble)
        if len(datacuentas[datacuentas['concepto']=='PRECIO COMPRA'])==1:
            preciocompra     = datacuentas[datacuentas['concepto']=='PRECIO COMPRA']['valor'].iloc[0]
            try:    gastos   = float(datacuentas[datacuentas['tipo']=='GASTO']['valor'].sum())
            except: gastos   = 0
            try:    ingresos = float(datacuentas[datacuentas['tipo']=='INGRESO']['valor'].sum())
            except: ingresos = 0
            gastosnotariales = 164000+0.0033*precioventa
            comisionventa    = comision_venta*precioventa
            totalgastos      = gastos + gastosnotariales + comisionventa
            totalingresos    = precioventa+ingresos
            neto             = totalingresos-totalgastos
            retornoneto      = neto/preciocompra
            retornobruto     = precioventa/preciocompra-1
            diasmarket       = ''
            try: 
                fechacompra = datacuentas[datacuentas['concepto']=='PRECIO COMPRA']['fecha_pago'].iloc[0]
                diasmarket  = datetime.now()-fechacompra
                diasmarket  = str(int(diasmarket.days))
                fechacompra = fechacompra.strftime('%Y-%m-%d')+ ' (yy/mm/dd)'
            except: fechacompra = ''
            
            col1,col2 = st.columns(2)
            col1.write('Fecha de compra')
            col2.write(fechacompra)
            col1.write('Dias en el mercado')
            col2.write(diasmarket)
            col1.write('Precio de compra')
            valor = f'${preciocompra:,.0f}'
            col2.write(valor)
            col1.write('Precio de venta')
            valor = f'${precioventa:,.0f}'
            col2.write(valor)
            col1.write('Total gastos')
            valor = f'${totalgastos:,.0f}'
            col2.write(valor)
            col1.write('Total ingresos')
            valor = f'${ingresos:,.0f}'
            col2.write(valor)          
            col1.write('Neto')
            valor = f'${neto:,.0f}'
            col2.write(valor)            
            col1.write('Retorno neto')
            col2.write("{:.2%}".format(retornoneto))                        
            col1.write('Retorno bruto')
            col2.write("{:.2%}".format(retornobruto))
            
        else: st.write('No hay precio de compra registrado en la base de datos de property management para el inmueble y no se puede calcular la ganancia')