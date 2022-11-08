import streamlit as st
import re
import json
import numpy as np
import math as mt
import pandas as pd
import pytz
import mysql.connector as sql
import requests
from datetime import datetime 
from dateutil.relativedelta import relativedelta
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup
from price_parser import Price
from multiprocessing.dummy import Pool

#-----------------------------------------------------------------------------#
# Precio de compra
#-----------------------------------------------------------------------------#
def precio_compra(inputvar):
    #inputvar = {'precio_venta':400000000,'areaconstruida':85,'admon':320000,'ganancia':0.06,'comision_compra':0.003,'comision_venta':0.003,'nmonths':6,'provisionmt2':100000,'pinturamt2':13000}
    
    ganancia        = 0.06 # (6%)
    comision_compra = 0.003 # (0.3%)
    comision_venta  = 0.003 # (0.3%)
    nmonths         = 6
    provisionmt2    = 100000  # Para reparaciones / colchon financiero
    pinturamt2      = 13000
    remodelacion    = 0
    IVA             = 0.19
    p1              = None
    admon           = None
    areaconstruida  = None
    
    if 'precio_venta' in inputvar and inputvar['precio_venta'] is not None and inputvar['precio_venta']>0:
        p1 = inputvar['precio_venta']
    if 'ganancia' in inputvar and inputvar['ganancia'] is not None and inputvar['ganancia']>0 and inputvar['ganancia']<100: 
        ganancia = inputvar['ganancia']
    if 'areaconstruida' in inputvar and inputvar['areaconstruida'] is not None and inputvar['areaconstruida']>0:
        areaconstruida = inputvar['areaconstruida']
    if 'nmonths' in inputvar and inputvar['nmonths'] is not None and inputvar['nmonths']>0: 
        nmonths = inputvar['nmonths']
    if 'admon' in inputvar and inputvar['admon'] is not None and inputvar['admon']>0: 
        admon = inputvar['admon']*1.1 # Es usual que reporten un menor valor de la administracion
    else:
        admon = 5500*areaconstruida
    if 'pinturamt2' in inputvar: 
        pinturamt2 = inputvar['pinturamt2']
    if 'provisionmt2' in inputvar: 
        provisionmt2 = inputvar['provisionmt2']
    if 'remodelacion' in inputvar and inputvar['remodelacion'] is not None and inputvar['remodelacion']>0:
        remodelacion = inputvar['remodelacion']
    
    PRECIO_GANANCIA  = p1/(1+ganancia)
    GN_VENTA         = 164000+0.0033*p1  # (regresion)
    COMISION_VENTA   = comision_venta*p1
    PINTURA          = pinturamt2*(1+IVA)*areaconstruida
    ADMON            = admon*nmonths
    PROVISION        = provisionmt2*areaconstruida
    X                = PRECIO_GANANCIA-GN_VENTA-COMISION_VENTA-PINTURA-ADMON-PROVISION-remodelacion
    preciocompra     = (X-57000)/(1+(0.0262+comision_compra))
    preciocompra     = np.round(preciocompra, int(-(mt.floor(mt.log10(preciocompra))-2)))
    gn_compra        = 57000+0.0262*preciocompra
    gn_compra        = np.round(gn_compra, int(-(mt.floor(mt.log10(gn_compra))-2)))
    gn_venta         = np.round(GN_VENTA, int(-(mt.floor(mt.log10(GN_VENTA))-2)))
    COMISION_COMPRA  = (preciocompra*comision_compra)
    retorno_bruto_esperado = p1/preciocompra-1
    retorno_neto_esperado  = (p1-COMISION_COMPRA-COMISION_VENTA-PINTURA-ADMON-PROVISION)/preciocompra-1
    return {'precio_venta':p1,'preciocompra':preciocompra,'retorno_bruto_esperado':retorno_bruto_esperado,'retorno_neto_esperado':retorno_neto_esperado,'gn_compra':gn_compra,'gn_venta':gn_venta,'comisiones':COMISION_VENTA+COMISION_COMPRA,'otros_gastos':PINTURA+ADMON+PROVISION+remodelacion}   

#-----------------------------------------------------------------------------#
# dir2coddir
#-----------------------------------------------------------------------------#
def coddir(x):
    result = x
    try: result = prefijo(x) + getnewdir(x)
    except:pass
    return result

def getdirformat(x):
    # x    = 'carrera 19a # 103A - 62'
    result = ''
    x      = x.lower()
    x      = re.sub(r'[^0-9a-zA-Z]',' ', x).split(' ')
    for u in range(len(x)):
        i=x[u]
        try: i = i.replace(' ','').strip().lower()
        except: pass
        try:
            float(re.sub(r'[^0-9]',' ', i))
            result = result +'+'+i
        except:
            if i!='': result = result + i
        try:
            if len(re.sub(r'[^+]','',result))>=3:
                try:
                    if 'sur'  in x[u+1]:  result= result + 'sur'
                    if 'este' in x[u+1]:  result= result + 'este'
                except: pass
                break
        except: pass
    return result

def getnewdir(x):
    result = None
    try:
        x      = getdirformat(x).split('+')[1:]
        result = ''
        for i in x:
            result = result + '+' + re.sub(r'[^0-9]','', i)+''.join([''.join(sorted(re.sub(r'[^a-zA-Z]','', i)))])
    except: pass
    if result=='': result = None
    return result

def prefijo(x):
    result = None
    m      = re.search("\d", x).start()
    x      = x[:m].strip()
    prefijos = {'D':{'d','diagonal','dg', 'diag', 'dg.', 'diag.', 'dig'},
                'T':{'t','transv', 'tranv', 'tv', 'tr', 'tv.', 'tr.', 'tranv.', 'transv.', 'transversal', 'tranversal'},
                'C':{'c','avenida calle','avenida cll','avenida cl','calle', 'cl', 'cll', 'cl.', 'cll.', 'ac', 'a calle', 'av calle', 'av cll', 'a cll'},
                'AK':{'avenida carrera','avenida cr','avenida kr','ak', 'av cr', 'av carrera', 'av cra'},
                'K':{'k','carrera', 'cr', 'cra', 'cr.', 'cra.', 'kr', 'kr.', 'kra.', 'kra'},
                'A':{'av','avenida'}}
    for key, values in prefijos.items():
        if x.lower() in values:
            result = key
            break
    return result

#-----------------------------------------------------------------------------#
# Precio de compra
#-----------------------------------------------------------------------------#
def get_data_market(inputvar):
    # Caracteristicas del inmueble
    metros                = 300
    area                  = inputvar['areaconstruida']
    areamin               = area*0.95
    areamax               = area*1.05
    habitaciones          = inputvar['habitaciones']
    banos                 = inputvar['banos']
    garajes               = inputvar['garajes']
    estrato               = inputvar['estrato']
    tipoinmueble          = inputvar['tipoinmueble']
    todaynum              = datetime.now(tz=pytz.timezone('America/Bogota'))
    fechainicial_conjunto = todaynum+relativedelta(months=-12)
    fechainicial_conjunto = fechainicial_conjunto.strftime("%Y-%m-%d")
    fcoddir               = coddir(inputvar['direccion'])
    fechainicial_market   = todaynum+relativedelta(months=-6)
    fechainicial_market   = fechainicial_market.strftime("%Y-%m-%d")
    latitud               = inputvar['latitud']
    longitud              = inputvar['longitud']
    
    # Bases de datos
    user          = st.secrets["prinanmasteruser"]
    password      = st.secrets["prinanpass"]
    host          = st.secrets["prinanhost"]
    database      = st.secrets["prinandatabase"]
    db_connection = sql.connect(user=user, password=password, host=host, database=database)
    dane           = pd.read_sql(f"SELECT dpto_ccdgo,mpio_ccdgo,setu_ccnct,secu_ccnct FROM {database}.SAE_dane WHERE  st_contains(geometry, POINT({longitud}, {latitud}))", con=db_connection)
    consultabarrio = ''
    if dane.empty is False:
        inputvar.update(dane.iloc[0].to_dict())
        mpio_ccdgo = inputvar['mpio_ccdgo']
        setu_ccnct = inputvar['setu_ccnct']
        consultabarrio = f" mpio_ccdgo='{mpio_ccdgo}' AND setu_ccnct='{setu_ccnct}' AND "
        
    datastock = [pd.read_sql(f"SELECT areaconstruida,descripcion,direccion,estrato,fecha_inicial,fuente,garajes,habitaciones,id_tabla,latitud,longitud,tiempodeconstruido,tipoinmueble,tiponegocio,url,valorarriendo,valorventa FROM {database}.4M_stockdata WHERE tipoinmueble='{tipoinmueble}' AND coddir='{fcoddir}' AND fecha_inicial>='{fechainicial_conjunto}' AND  (areaconstruida>={areamin} AND areaconstruida<={areamax}) AND  url like '%bogota%'" , con=db_connection),
                 pd.read_sql(f"SELECT areaconstruida,descripcion,direccion,estrato,fecha_inicial,fuente,garajes,habitaciones,id_tabla,latitud,longitud,tiempodeconstruido,tipoinmueble,tiponegocio,url,valorarriendo,valorventa FROM {database}.4M_stockdata WHERE  {consultabarrio} tipoinmueble='{tipoinmueble}' AND (areaconstruida>={areamin} AND areaconstruida<={areamax}) AND estrato={estrato} AND habitaciones={habitaciones} AND banos={banos} AND garajes={garajes} AND fecha_inicial>='{fechainicial_market}' AND ST_Distance_Sphere(geometry, POINT({longitud},{latitud}))<={metros}" , con=db_connection)]    
    
    data = datastock[0].append(datastock[1])
    if data.empty is False:
        data['latitud']        = latitud
        data['longitud']       = longitud
        data['id']             = range(len(data))
        dataupdate             = urlupdate(data)
        data                   = data.merge(dataupdate,on='id',how='left',validate='1:1')
        data.drop(columns=[ 'areaconstruida_new','imagenes_new'],inplace=True)
        data['valormt2_venta'] = data['valorventa']/data['areaconstruida']
        data['valormt2_renta'] = data['valorarriendo']/data['areaconstruida']
        data = duplicated_description(data)
    return data

#-----------------------------------------------------------------------------#
# Eliminar registros con descripcion similar o igual
#-----------------------------------------------------------------------------#  
def duplicated_description(b):
    b                 = b.drop_duplicates(subset='descripcion',keep='first')
    b['descnew']      = b['descripcion'].apply(lambda x: re.sub(r'\s+',' ',x.lower()))
    b['index']        = b.index
    b.index           = range(len(b))
    b['isduplicated'] = 0
    b['coddup']       = None
    for i in range(len(b)):
        coddup  = b['index'].iloc[i]
        compare = b['descnew'].iloc[i]
        idd     = b['descnew'].apply(lambda x: fuzz.partial_ratio(compare,x))>=85
        idd.loc[i] = False
        idj        = b['index'].isin(b['coddup'].unique())
        idd  = (idd) & (b['isduplicated']==0) & (~idj)
        if sum(idd)>0:
            b.loc[idd,'isduplicated'] = 1
            b.loc[idd,'coddup']       = coddup
    b.index = b['index'] 
    b       = b[b['isduplicated']==0]
    b.drop(columns=['index','isduplicated','coddup','descnew'],inplace=True)
    return b

#-----------------------------------------------------------------------------#
# url update
#-----------------------------------------------------------------------------#
def urlupdate(data):  
    pool           = Pool(10)
    futures        = []
    datafinal = pd.DataFrame()
    for i in range(len(data)):  
        inputvar = data.iloc[i].to_dict()
        futures.append(pool.apply_async(fuenteupdate,args = (inputvar, )))
    #for future in tqdm(futures):
    for future in futures:
        try: datafinal = datafinal.append([future.get()])
        except: pass
    datafinal.index = range(len(datafinal))
    return datafinal
    
def fuenteupdate(inputvar): 
    result = {'activo':0,'id':inputvar['id'],'valorventa_new':None,'valorarriendo_new':None,'areaconstruida_new':None,'imagenes_new':''}
    if 'fuente' in inputvar:
        if   inputvar['fuente']=='M2': result = M2(inputvar)  
        elif inputvar['fuente']=='FR': result = FR(inputvar)
        elif inputvar['fuente']=='CC': result = CC(inputvar)
        elif inputvar['fuente']=='PP': result = PP(inputvar)
    return result 

# Metrocuadrado
def M2(inputvar):
    
    headers_getinmueble = {'authority':'www.metrocuadrado.com',
                         'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                         'accept-encoding':'gzip, deflate, br',
                         'cookie':'visid_incap_434661=hjhD3pTOTImpvPDHBbVMIU5M6V4AAAAAQUIPAAAAAACkDZw6A2qwPXxaO7VyvF5F; incap_ses_988_434661=cMapWeC51msf8YPo0RS2DU5M6V4AAAAAIhV77ejUakC/84UMYyzM0g==',
                         'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
                         'x-api-key':'P1MfFHfQMOtL16Zpg36NcntJYCLFm8FqFfudnavl',
                         }
    isactive     = False
    today        = datetime.now(tz=pytz.timezone('America/Bogota')).strftime("%Y-%m-%d %H:%M:%S")
    result       = {'activo':0,'id':inputvar['id'],'valorventa_new':None,'valorarriendo_new':None,'areaconstruida_new':None,'imagenes_new':''}
    url          = inputvar['url']
    r            = requests.get(url,headers=headers_getinmueble,timeout=30,verify=False)
    soup         = BeautifulSoup(r.text,'html.parser')
    try:
        try:    z = json.loads(soup.find_all('script',type='application/json')[0].getText)['props']['initialProps']['pageProps']['realEstate']
        except: z = json.loads(soup.find_all('script',type='application/json')[0].next_element)['props']['initialProps']['pageProps']['realEstate']
        try:    
            result.update({'valorventa_new':float(z['salePrice'])})
            isactive = True
        except: pass
        try:
            result.update({'areaconstruida_new':float(z['areac'])})
            isactive = True
        except: pass
        try:    
            result.update({'valorarriendo_new':float(z['rentPrice'])})
            isactive = True
        except: pass
    except: pass
    try:
        imagenes = []
        for i in z['images']: 
            imagenes.append(i['image'])
        result['imagenes_new'] = json.dumps(imagenes)
    except: pass
    if isactive: result['activo'] = 1    
    return result
        
# Finca Raíz
def FR(inputvar):
    isactive     = False
    today        = datetime.now(tz=pytz.timezone('America/Bogota')).strftime("%Y-%m-%d %H:%M:%S")
    result       = {'activo':0,'id':inputvar['id'],'valorventa_new':None,'valorarriendo_new':None,'areaconstruida_new':None,'imagenes_new':''}
    url          = inputvar['url']
    r            = requests.get(url,timeout=30)
    soup         = BeautifulSoup(r.text,'html.parser')
    try: 
        datajson = json.loads(soup.find(['script'], {'type': 'application/json'}).next_element)
        for i in ['venta','arriendo']:
            if i in datajson['props']['pageProps']['offer']['name'].lower(): 
                try:
                    result[f'valor{i}_new'] = Price.fromstring(str(datajson['props']['pageProps']['price'])).amount_float
                    isactive = True
                except: pass
        result['areaconstruida_new'] = float(datajson['props']['pageProps']['area'])
        isactive = True
        result['imagenes_new'] = json.dumps(datajson['props']['pageProps']['media']['photos'])
    except: pass
    if isactive: result['activo'] = 1
    return result
                
# Cien cuadras
def CC(inputvar):
    isactive     = False
    today        = datetime.now(tz=pytz.timezone('America/Bogota')).strftime("%Y-%m-%d %H:%M:%S")
    result       = {'activo':0,'id':inputvar['id'],'valorventa_new':None,'valorarriendo_new':None,'areaconstruida_new':None,'imagenes_new':''}
    url          = inputvar['url']
    r            = requests.get(url,timeout=30)
    soup         = BeautifulSoup(r.text,'html.parser')
    try:
        z        = soup.find('script',type='application/json').next_element
        z        = z.replace('&q;','"')
        z        = json.loads(z)
        try: 
            result['valorventa_new'] = z['dataKey']['sellingprice']
            isactive = True
        except: pass
        try: 
            result['valorarriendo_new'] = z['dataKey']['leasefee']
            isactive = True
        except: pass
        try: 
            result['areaconstruida_new'] = z['dataKey']['propertyFeatures']['builtArea']
            isactive = True
        except: pass   
        try: 
            imagenes = []
            for iiter in z['dataKey']['propertyFeatures']['photosPropertyData']:
                imagenes.append(iiter['url'])
            if imagenes!=[]:
                result['imagenes_new'] = imagenes
        except: pass
    except: pass
    if isactive: result['activo'] = 1
    return result

# Properati
def PP(inputvar):
    isactive     = False
    today        = datetime.now(tz=pytz.timezone('America/Bogota')).strftime("%Y-%m-%d %H:%M:%S")
    result       = {'activo':0,'id':inputvar['id'],'valorventa_new':None,'valorarriendo_new':None,'areaconstruida_new':None,'imagenes_new':''}
    url          = inputvar['url']
    r            = requests.get(url,timeout=30)
    soup         = BeautifulSoup(r.text,'html.parser')
    propertyinfo = {}            
    try:
        propertyinfo = json.loads(soup.find_all('script',type="application/json")[0].getText())['props']['pageProps']['property']
        propertyinfo.update({'valorstr':soup.find_all("span", {"class" : re.compile('.*StyledPrice.*')})[0].getText().strip()})
    except: 
        try:
            propertyinfo = json.loads(soup.find_all('script',type="application/json")[0].next_element)['props']['pageProps']['property']
            propertyinfo.update({'valorstr':soup.find_all("span", {"class" : re.compile('.*StyledPrice.*')})[0].getText().strip()})
        except: pass
    
    if 'price' in  propertyinfo:
        if 'amount' in propertyinfo['price']:
            for i in ['arriendo','venta']:
                if i in url.lower(): 
                    try:     
                        result[f'valor{i}_new'] = propertyinfo['price']['amount']
                        isactive = True
                    except: 
                        try: 
                            result[f'valor{i}_new'] = Price.fromstring(str(propertyinfo['valorstr'])).amount_float
                            isactive = True
                        except: pass
    try: 
        imgs = []
        if 'images' in propertyinfo:
            try:
                for j in propertyinfo['images']:
                    try: imgs.append('http'+j['sizes'][list(j['sizes'])[0]]['webp'].split('format(webp)')[1].strip().split('http')[1])
                    except: pass
            except: pass
        if imgs!=[]:    result.update({'imagenes_new': json.dumps(imgs)})
    except: pass
    if isactive: result['activo'] = 1
    return result

#-----------------------------------------------------------------------------#
# Recorrido ventaneros
#-----------------------------------------------------------------------------#
def get_data_recorrido(inputvar):
    # Caracteristicas del inmueble
    fcoddir  = coddir(inputvar['direccion'])
    user     = st.secrets["buydepauser"]
    password = st.secrets["buydepapass"]
    host     = st.secrets["buydepahost"]
    database = st.secrets["buydepadatabase"]
    db_connection = sql.connect(user=user, password=password, host=host, database=database)
    data          = pd.read_sql(f"SELECT fecha_recorrido,nombre_conjunto, direccion_formato, tipo_negocio, telefono1, telefono2, telefono3   FROM {database}.app_recorredor_stock_ventanas WHERE coddir='{fcoddir}'", con=db_connection)
    return data