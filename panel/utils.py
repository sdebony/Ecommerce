#MAnejo de conexion SOAP
from zeep import Client
from zeep.transports import Transport
from requests.auth import HTTPBasicAuth

import requests
from xml.etree import ElementTree as ET

def consultar_costo_envio(peso_total, volumen_total, cp_origen, cp_destino, cant_paquetes, valor_declarado, cuit, operativa):
    url = "http://webservice.oca.com.ar/ePak_Tracking_TEST/Oep_TrackEPak.asmx"
    headers = {'Content-Type': 'text/xml; charset=utf-8'}

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

