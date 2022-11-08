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

@st.cache
def get_id_inmueble_list(x):
    condicion = ''
    if x:
        condicion = ' WHERE activo=1'
    db_connection  = sql.connect(user=user, password=password, host=host, database=database)
    datainmuebles  = pd.read_sql(f"SELECT id as id_inmueble,direccion_formato,nombre_conjunto FROM {database}.app_callcenter_inbound {condicion}" , con=db_connection)
    db_connection.close()
    datainmuebles = datainmuebles.sort_values(by='id_inmueble',ascending=True)
    return datainmuebles

@st.cache
def get_id_inmueble_cuentas(id_inmueble):
    db_connection  = sql.connect(user=user, password=password, host=host, database=database)
    datacuentas    = pd.read_sql(f"SELECT * FROM  {database}.app_pm_cuentas WHERE id_inmueble='{id_inmueble}'" , con=db_connection)
    db_connection.close()
    return datacuentas

@st.cache
def get_inmueble_caracteristicas(id_inmueble):
    db_connection       = sql.connect(user=user, password=password, host=host, database=database)
    datacaracteristicas = pd.read_sql(f"SELECT * FROM  {database}.data_stock_inmuebles_caracteristicas WHERE id_inmueble='{id_inmueble}'" , con=db_connection)
    db_connection.close()
    return datacaracteristicas

@st.cache
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

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
        
#-----------------------------------------------------------------------------#
# Actualizar caracteristicas de un inmueble
#-----------------------------------------------------------------------------# 
with st.expander("Actualizar o modificar variables de un inmueble"):
    datainmuebles =  get_id_inmueble_list(False)
    datainmuebles['combinacion'] = datainmuebles['id_inmueble'].astype(str)+'-'+datainmuebles['direccion_formato'].astype(str)+'-'+datainmuebles['nombre_conjunto'].astype(str)
    combinacion = st.selectbox('ID Inmueble',options=datainmuebles['combinacion'].to_list())
    id_inmueble = datainmuebles[datainmuebles['combinacion']==combinacion]['id_inmueble'].iloc[0]
    datacaracteristicas = get_inmueble_caracteristicas(id_inmueble)
    variables           = [x for x in ['tipoinmueble','nombre_conjunto','areaconstruida','areaprivada','habitaciones','banos','garajes','depositos','estrato','piso','antiguedad','ascensores','numerodeniveles','valoradministracion','latitud','longitud','conjunto_unidades','ph','chip','matricula','cedula_catastral','avaluocatastral','impuestopredial','total_parqueaderos','total_depositos','numero_sotanos','porteria','circuito_cerrado','lobby','salon_comunal','parque_infantil','terraza','sauna','turco','jacuzzi','cancha_multiple','cancha_baloncesto','cancha_voleibol','cancha_futbol','cancha_tenis','cancha_squash','salon_juegos','gimnasio','zona_bbq','sala_cine','piscina'] if x in datacaracteristicas]
    datacaracteristicas = datacaracteristicas[variables]
    
    principales       = st.container()
    catastrales       = st.container()
    amenities         = st.container()
    cambios_variables = st.container()
    originvar         = datacaracteristicas.iloc[0].to_dict()
    
    for i in ['habitaciones','banos','garajes','depositos','estrato','piso','antiguedad','ascensores','numerodeniveles','conjunto_unidades','total_parqueaderos','total_depositos','numero_sotanos']:
        if isinstance(originvar[i],int) is False:
            originvar[i] = 0
            
    for i in ['areaconstruida','areaprivada','valoradministracion','latitud','longitud','avaluocatastral','impuestopredial']:
        if isinstance(originvar[i],int) is False and isinstance(originvar[i],float) is False:
            originvar[i] = 0
     
    for i in ['porteria','circuito_cerrado','lobby','salon_comunal','parque_infantil','terraza','sauna','turco','jacuzzi','cancha_multiple','cancha_baloncesto','cancha_voleibol','cancha_futbol','cancha_tenis','cancha_squash','salon_juegos','gimnasio','zona_bbq','sala_cine','piscina']:
        if 'Si' in originvar[i]: originvar[i] = True
        else: originvar[i] = False
        
    with  principales:
        st.text('Caracteristicas principales:')
        col1, col2      = st.columns(2)
        tipoinmueble    = col1.text_input('Tipo de inmueble',value=originvar['tipoinmueble'])
        nombre_conjunto = col2.text_input('Nombre del conjunto',value=originvar['nombre_conjunto'])
        areaconstruida  = col1.number_input('Área construida', min_value=0.0, max_value=150.0, value=originvar['areaconstruida'], step=1.0)
        areaprivada     = col2.number_input('Área privada', min_value=0.0, max_value=150.0, value=originvar['areaprivada'], step=1.0)
        habitaciones    = col1.number_input('Habitaciones', min_value=1, max_value=4, value=originvar['habitaciones'], step=1)
        banos           = col2.number_input('Baños', min_value=1, max_value=5, value=originvar['banos'], step=1)
        garajes         = col1.number_input('Garajes', min_value=0, max_value=4, value=originvar['garajes'], step=1)
        depositos       = col2.number_input('Depósitos', min_value=0, max_value=4, value=originvar['depositos'], step=1)
        estrato         = col1.number_input('Estrato', min_value=1, max_value=6, value=originvar['estrato'], step=1)
        piso            = col2.number_input('Piso', min_value=1, max_value=30, value=originvar['piso'], step=1)
        antiguedad      = col1.number_input('Antiguedad', min_value=0, max_value=50, value=originvar['antiguedad'], step=1)
        ascensores      = col2.number_input('Ascensores', min_value=0, max_value=8, value=originvar['ascensores'], step=1)
        numerodeniveles = col1.number_input('Número de niveles', min_value=1, max_value=4, value=originvar['numerodeniveles'], step=1)
        valoradministracion  = col2.number_input('Valor administración', min_value=50000.0, max_value=1000000.0, value=originvar['valoradministracion'], step=10000.0)
        #latitud              = col1.text_input('Latitud', value=originvar['latitud'])
        #longitud             = col2.text_input('Longitud', value=originvar['longitud'])
        #try: latitud = float(latitud)
        #except: pass
        #try: longitud = float(longitud)
        #except: pass    
        latitud  = originvar['latitud']
        longitud = originvar['longitud']
    
    with  catastrales:
        st.text('Identificacion catastral:')
        col1, col2       = st.columns(2)
        chip             = col1.text_input('Chip',value=originvar['chip'])
        matricula        = col2.text_input('Mátricula inmobiliaria',value=originvar['matricula'])
        cedula_catastral = col1.text_input('Cédula catastral',value=originvar['cedula_catastral'])
        ph               = col2.selectbox('Propiedad horizontal',options=['S','N'])
        avaluocatastral  = col1.number_input('Avalúo catastral', min_value=150000000.0, max_value=800000000.0, value=originvar['avaluocatastral'], step=10000000.0)
        impuestopredial  = col2.number_input('Impuesto predial', min_value=400000.0, max_value=10000000.0, value=originvar['impuestopredial'], step=100000.0)

    with  amenities:
        st.text('Amenities del edificio:')
        col1, col2, col3, col4      = st.columns(4)
        conjunto_unidades  = col1.number_input('# unidades en el conjunto', min_value=1, max_value=2000, value=originvar['conjunto_unidades'], step=1)
        total_parqueaderos = col2.number_input('Total parqueaderos', min_value=0, max_value=2000, value=originvar['total_parqueaderos'], step=1)
        total_depositos    = col3.number_input('Total depósitos', min_value=0, max_value=2000, value=originvar['total_depositos'], step=1)
        numero_sotanos     = col4.number_input('N[umero de sotanos', min_value=0, max_value=8, value=originvar['numero_sotanos'], step=1)
        
        porteria          =  col1.checkbox('porteria', value=originvar['porteria'])
        circuito_cerrado  =  col2.checkbox('Circuito cerrado', value=originvar['circuito_cerrado'])
        lobby             =  col3.checkbox('lobby', value=originvar['lobby'])
        salon_comunal     =  col4.checkbox('Salón comunal', value=originvar['salon_comunal'])
        parque_infantil   =  col1.checkbox('Parque infantil', value=originvar['parque_infantil'])
        terraza           =  col2.checkbox('Terraza', value=originvar['terraza'])
        sauna             =  col3.checkbox('Sauna', value=originvar['sauna'])
        turco             =  col4.checkbox('Turco', value=originvar['turco'])
        jacuzzi           =  col1.checkbox('Jacuzzi', value=originvar['jacuzzi'])
        cancha_multiple   =  col2.checkbox('Cancha múltiple', value=originvar['cancha_multiple'])
        cancha_baloncesto =  col3.checkbox('Cancha baloncesto', value=originvar['cancha_baloncesto'])
        cancha_voleibol   =  col4.checkbox('Cancha voleibol', value=originvar['cancha_voleibol'])
        cancha_futbol     =  col1.checkbox('Cancha futbol', value=originvar['cancha_futbol'])
        cancha_tenis      =  col2.checkbox('Cancha tenis', value=originvar['cancha_tenis'])
        cancha_squash     =  col3.checkbox('Cancha squash', value=originvar['cancha_squash'])
        salon_juegos      =  col4.checkbox('Salón juegos', value=originvar['salon_juegos'])
        gimnasio          =  col1.checkbox('Gimnasio', value=originvar['gimnasio'])
        zona_bbq          =  col2.checkbox('Zona bbq', value=originvar['zona_bbq'])
        sala_cine         =  col3.checkbox('Sala cine', value=originvar['sala_cine'])
        piscina           =  col4.checkbox('Piscina', value=originvar['piscina'])

    with cambios_variables:
        newinputvar = {'tipoinmueble':tipoinmueble,'nombre_conjunto':nombre_conjunto,'areaconstruida':areaconstruida,'areaprivada':areaprivada,'habitaciones':habitaciones,'banos':banos,'garajes':garajes,'depositos':depositos,'estrato':estrato,'piso':piso,'antiguedad':antiguedad,'ascensores':ascensores,'numerodeniveles':numerodeniveles,'latitud':latitud,'longitud':longitud,'valoradministracion':valoradministracion,'chip':chip,'matricula':matricula,'cedula_catastral':cedula_catastral,'ph':ph,'avaluocatastral':avaluocatastral,'impuestopredial':impuestopredial,'conjunto_unidades':conjunto_unidades,'total_parqueaderos':total_parqueaderos,'total_depositos':total_depositos,'numero_sotanos':numero_sotanos,'porteria':porteria,'circuito_cerrado':circuito_cerrado,'lobby':lobby,'salon_comunal':salon_comunal,'parque_infantil':parque_infantil,'terraza':terraza,'sauna':sauna,'turco':turco,'jacuzzi':jacuzzi,'cancha_multiple':cancha_multiple,'cancha_baloncesto':cancha_baloncesto,'cancha_voleibol':cancha_voleibol,'cancha_futbol':cancha_futbol,'cancha_tenis':cancha_tenis,'cancha_squash':cancha_squash,'salon_juegos':salon_juegos,'gimnasio':gimnasio,'zona_bbq':zona_bbq,'sala_cine':sala_cine,'piscina':piscina}
        for i in ['porteria','circuito_cerrado','lobby','salon_comunal','parque_infantil','terraza','sauna','turco','jacuzzi','cancha_multiple','cancha_baloncesto','cancha_voleibol','cancha_futbol','cancha_tenis','cancha_squash','salon_juegos','gimnasio','zona_bbq','sala_cine','piscina']:
            if i in newinputvar and newinputvar[i] is True: newinputvar[i] = 'Si'
            else: newinputvar[i] = 'No'
        inputvar = datacaracteristicas.iloc[0].to_dict()
        
        varchange = {}
        for key,values in newinputvar.items():
            if key in inputvar:
                if newinputvar[key]!=inputvar[key]:
                    varchange.update({key:values})
            
        if varchange!={}:
            st.text('Se van a realizar estos cambios en las variables del inmueble')
            st.write(varchange)
            if st.button('Estoy seguro de los cambios'):
                condicion  = ''
                for key,values in varchange.items(): condicion = condicion + f", `{key}`='{values}'"
                condicion   = condicion + f" WHERE `id_inmueble`='{id_inmueble}'"
                condicion   = condicion.strip(',')
                condicion   = condicion.replace("'nan'","NULL").replace("'none'","NULL").replace("'None'","NULL").replace("'NaT'","NULL").replace("'nat'","NULL")
                db_connection = sql.connect(user=user, password=password, host=host, database=database)
                cursor        = db_connection.cursor()
                cursor.execute(f"""UPDATE colombia.data_stock_inmuebles_caracteristicas SET {condicion} """)
                db_connection.commit()
                db_connection.close()                  
                st.write('Cambios guardados con exito')

#-----------------------------------------------------------------------------#
# Comparables del conjunto, zona, recorrido, etc
#-----------------------------------------------------------------------------# 
with st.expander("Consultar inmuebles en oferta en el mismo edificio, zona u otros ibuyers"):
    ciudad       = st.selectbox('ID Inmueble:',options=['Bogota'])
    formulario   = st.columns(4)
    tipovia      = formulario[0].selectbox('Tipo via',options=['CL','KR','TR','DG'])
    complemento1 = formulario[1].text_input('Complemento 1')
    complemento2 = formulario[2].text_input('Complemento 2')
    complemento3 = formulario[3].text_input('Complemento 3')
    complemento1 = re.sub(r'\s+',' ',re.sub('[^0-9a-zA-Z]',' ',complemento1))
    complemento2 = re.sub(r'\s+',' ',complemento2)
    complemento3 = re.sub(r'\s+',' ',complemento3)
    direccion_formato = f'{tipovia} {complemento1} {complemento2} {complemento3}, {ciudad}'
    st.write(direccion_formato)
    
    tipoinmueble    = st.text_input('Tipo de inmueble ',value='Apartamento')
    col1, col2      = st.columns(2)
    areaconstruida  = col1.slider('Área construida ', min_value=1, max_value=150, value=50, step=1)
    antiguedad      = col2.slider('Antiguedad ', min_value=0, max_value=50, value=5, step=1)
    habitaciones    = col1.selectbox('Habitaciones ', options=[1,2,3,4])
    banos           = col2.selectbox('Baños ', options=[1,2,3,4,5])
    garajes         = col1.selectbox('Garajes ', options=[0,1,2,3])
    estrato         = col2.selectbox('Estrato ', options=[1,2,3,4,5,6])
    latitud         = col1.text_input('Latitud' )
    longitud        = col2.text_input('Longitud ')
    try: latitud = float(latitud)
    except: pass
    try: longitud = float(longitud)
    except: pass
    fcoddir  = coddir(direccion_formato)
    inputvar = {'tipoinmueble':tipoinmueble,'direccion':direccion_formato,'areaconstruida':areaconstruida,'antiguedad':antiguedad,'habitaciones':habitaciones,'banos':banos,'garajes':garajes,'estrato':estrato,'latitud':latitud,'longitud':longitud}
    if len(re.sub('[^+]','',fcoddir))>=3:
        if st.button('Comparables'):
            data = get_data_market(inputvar)
            if data.empty is False:
                for j in ['valorventa','valorarriendo']:
                    idd = data[f'{j}_new'].notnull()
                    if sum(idd): data.loc[idd,j] = data.loc[idd,f'{j}_new']
                    data[f'{j}mt2'] = data[j]/data['areaconstruida']
                data.drop(columns=[x for x in ['valorventa_new','valorarriendo_new','valormt2_venta','valormt2_renta'] if x in data],inplace=True)
                variables = [x for x in ["direccion",	"fecha_inicial",	"tipoinmueble",	"tiponegocio",	"estrato",	"areaconstruida",	"habitaciones",	"garajes",	"tiempodeconstruido",	"valorventa",	"valorventamt2",	"valorarriendo",	"valorarriendomt2",	"latitud",	"longitud",	"descripcion",	"url"] if x in data]
                data      = data[variables]
                st.write(data.head())
                csv = convert_df(data)
                col1,col2 = st.columns(2)
                col2.download_button(
                   "Descargar Data Comparables",
                   csv,
                   "data-comparables.csv",
                   "text/csv",
                   key='download-csv'
                )
                
        if st.button('Ventanas en oferta'):
            inputvar = {'direccion':direccion_formato}
            data     = get_data_recorrido(inputvar)
            if data.empty is False:
                st.write(data.head())
                csv = convert_df(data)
                col1,col2 = st.columns(2)
                col2.download_button(
                   "Descargar Data Recorrido",
                   csv,
                   "data-recorrido.csv",
                   "text/csv",
                   key='download-csv'
                )