#MAnejo de conexion SOAP
#from zeep import Client
#from zeep.transports import Transport
#from requests.auth import HTTPBasicAuth

from django.conf import settings


import requests
#from xml.etree import ElementTree as ET
import xml.etree.ElementTree as ET

def consultar_costo_envio(peso_total, volumen_total, cp_origen, cp_destino, cant_paquetes, valor_declarado, cuit, operativa):
    url = "http://webservice.oca.com.ar/ePak_Tracking/Oep_TrackEPak.asmx"
    headers = {'Content-Type': 'text/xml; charset=utf-8'}

    print("consultar_costo_envio")

    # Construir el XML del request
    body = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:oca="#Oca_e_Pak">
       <soapenv:Header/>
       <soapenv:Body>
          <oca:Tarifar_Envio_Corporativo>
             <oca:PesoTotal>{peso_total}</oca:PesoTotal>
             <oca:VolumenTotal>{volumen_total}</oca:VolumenTotal>
             <oca:CodigoPostalOrigen>{cp_origen}</oca:CodigoPostalOrigen>
             <oca:CodigoPostalDestino>{cp_destino}</oca:CodigoPostalDestino>
             <oca:CantidadPaquetes>{cant_paquetes}</oca:CantidadPaquetes>
             <oca:ValorDeclarado>{valor_declarado}</oca:ValorDeclarado>
             <oca:Cuit>{cuit}</oca:Cuit>
             <oca:Operativa>{operativa}</oca:Operativa>
          </oca:Tarifar_Envio_Corporativo>
       </soapenv:Body>
    </soapenv:Envelope>
    """

    # Enviar la solicitud SOAP
    response = requests.post(url, data=body, headers=headers)

    if response.status_code == 200:
        # Parsear el XML de respuesta
        root = ET.fromstring(response.content)
        precio = root.find('.//Precio').text
        total = root.find('.//Total').text
        plazo_entrega = root.find('.//PlazoEntrega').text

        return {
            'Precio': precio,
            'Total': total,
            'PlazoEntrega': plazo_entrega
        }
    else:
        raise Exception(f"Error al consultar OCA: {response.status_code}")

def oca_consultar_costo_envio_by_cart(peso,cp_destino,tipo_envio):
          #https://webservice.oca.com.ar/oep_tracking/Oep_Track.asmx
          
    url = "http://webservice.oca.com.ar/ePak_Tracking/Oep_TrackEPak.asmx"
    headers = {'Content-Type': 'text/xml; charset=utf-8'}


    print("consultar_costo_envio_by_cart")
    OCA_CP_ORIGEN = settings.OCA_CP_ORIGEN
    OCA_OPERATIVA_ED = settings.OCA_OPERATIVA_ED 
    OCA_OPERATIVA_ES = settings.OCA_OPERATIVA_ES
    OCA_CUIT = settings.OCA_CUIT
    OCA_VALOR_DECLARADO = settings.OCA_VALOR_DECLARADO
    OCA_VOLUMETRIA_TOTAL = settings.OCA_VOLUMETRIA_TOTAL

    peso_total=peso
    volumen_total=OCA_VOLUMETRIA_TOTAL
    cp_origen=OCA_CP_ORIGEN
    cant_paquetes=1
    valor_declarado=OCA_VALOR_DECLARADO
    cuit=OCA_CUIT
    if tipo_envio==1:       
        operativa=OCA_OPERATIVA_ED  #Envio a Domicilio
    else:
        operativa=OCA_OPERATIVA_ES  #Envio a Sucursal


    # Construir el XML del request
    body = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:oca="#Oca_e_Pak">
       <soapenv:Header/>
       <soapenv:Body>
          <oca:Tarifar_Envio_Corporativo>
             <oca:PesoTotal>{peso_total}</oca:PesoTotal>
             <oca:VolumenTotal>{volumen_total}</oca:VolumenTotal>
             <oca:CodigoPostalOrigen>{cp_origen}</oca:CodigoPostalOrigen>
             <oca:CodigoPostalDestino>{cp_destino}</oca:CodigoPostalDestino>
             <oca:CantidadPaquetes>{cant_paquetes}</oca:CantidadPaquetes>
             <oca:ValorDeclarado>{valor_declarado}</oca:ValorDeclarado>
             <oca:Cuit>{cuit}</oca:Cuit>
             <oca:Operativa>{operativa}</oca:Operativa>
          </oca:Tarifar_Envio_Corporativo>
       </soapenv:Body>
    </soapenv:Envelope>
    """

    # Enviar la solicitud SOAP
    response = requests.post(url, data=body, headers=headers)

    if response.status_code == 200:
        # Parsear el XML de respuesta
        root = ET.fromstring(response.content)
        precio = root.find('.//Precio').text
        total = root.find('.//Total').text
        plazo_entrega = root.find('.//PlazoEntrega').text

        return {
            'Precio': precio,
            'Total': total,
            'PlazoEntrega': plazo_entrega
        }
    else:
        raise Exception(f"Error al consultar OCA: {response.status_code}")


def consultar_sucursal_bycp(cp_destino,dir_id_2):
    url = "http://webservice.oca.com.ar/ePak_Tracking/Oep_TrackEPak.asmx"
    headers = {'Content-Type': 'text/xml; charset=utf-8'}

    print("FNC: consultar_sucursal_bycp")

    # Construir el XML del request
    body = f"""    
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:oca="#Oca_e_Pak">
        <soapenv:Header/>
        <soapenv:Body>
        <oca:GetCentrosImposicionConServiciosByCP>
        <oca:CodigoPostal>{cp_destino}</oca:CodigoPostal>
        </oca:GetCentrosImposicionConServiciosByCP>
        </soapenv:Body>
        </soapenv:Envelope>
    """

    # Enviar la solicitud SOAP
    response = requests.post(url, data=body, headers=headers)

    
    if response.status_code == 200:
        # Parsear el XML de respuesta
        root = ET.fromstring(response.content.decode('utf-8'))

        # Buscamos los centros de imposición dentro de la respuesta
        # Aquí estamos buscando el elemento Centro directamente
        centros = root.findall('.//CentrosDeImposicion/Centro')  # Utilizamos .// para buscar en cualquier lugar dentro del XML

        
        # Extraemos los datos de cada centro
        centros_info = []
        for centro in centros:
            centro_data = {
                'IdCentroImposicion': centro.findtext('IdCentroImposicion'),
                'Sigla': centro.findtext('Sigla'),
                'Sucursal': centro.findtext('Sucursal'),
                'Calle': centro.findtext('Calle'),
                'Numero': centro.findtext('Numero'),
                'Localidad': centro.findtext('Localidad'),
                'CodigoPostal': centro.findtext('CodigoPostal'),
                'Provincia': centro.findtext('Provincia'),
                'Telefono': centro.findtext('Telefono'),
                'Latitud': centro.findtext('Latitud'),
                'Longitud': centro.findtext('Longitud'),
                'TipoAgencia': centro.findtext('TipoAgencia'),
                'HorarioAtencion': centro.findtext('HorarioAtencion'),
                'dir_id_2':dir_id_2,
               
            }

            # Servicios
            servicios = centro.findall('Servicios/Servicio')
            centro_data['Servicios'] = [{'IdTipoServicio': s.findtext('IdTipoServicio'), 'ServicioDesc': s.findtext('ServicioDesc')} for s in servicios]

            centros_info.append(centro_data)

       
        return {'centro_data': centros_info}

    else:
        raise Exception(f"Error al consultar OCA: {response.status_code}")
