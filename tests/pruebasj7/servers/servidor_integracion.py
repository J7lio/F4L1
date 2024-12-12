import asyncio
import time
from datetime import datetime

from asyncua.sync import Server
from asyncua import Client, Node
from collections import deque


cambio_hora = False
hora = ""
lluvia = 0
estado_pluviometro = False
caudal = 0
estado_caudal = False

class SubscriptionHandler:
    def __init__(self, client_name):
        self.client_name = client_name

    def datachange_notification(self, node, val, data):
        global cambio_hora, hora, lluvia, estado_pluviometro, caudal, estado_caudal
        # print(f"La variable '{node}' cambió a {val}")
        # Aquí puedes manejar los cambios de las variables específicas
        if str(node) == "ns=2;s=HoraSimuladaTexto":  # HoraSimuladaTexto
            hora = val
            cambio_hora = True
        if str(node) == "ns=2;s=DatosPluviometro":  # DatosPluviometro
            lluvia = val
        if str(node) == "ns=2;s=EstadoSensorPluviometro":  # EstadoSensorPluviometro
            estado_pluviometro = val
        if str(node) == "ns=2;s=DatosCaudal":  # DatosCaudal
            caudal = val
        if str(node) == "ns=2;s=EstadoSensorCaudal":  # EstadoSensorCaudal
            estado_caudal = val


async def client_task(server_url, namespace,  array_variables_path):
    async with Client(url=server_url) as client:
        variables = []
        for paths in array_variables_path:
            idx = await client.get_namespace_index(namespace)

            separator = "/" + str(idx) + ":"
            variable_path = str(idx) + ":" + separator.join(paths) #Para que tenga el formato idx:p1/idx:p2

            variable = await client.nodes.objects.get_child(variable_path)
            print(variable)
            variables.append(variable)
        handler = SubscriptionHandler("paco")
        subscription = await client.create_subscription(100, handler)
        await subscription.subscribe_data_change(variables)
        try:
            while True:
                await asyncio.sleep(1)  # Mantén la conexión activa
        finally:
            await subscription.delete()


def transformar_a_float(var):
    try:
        var = float(var.replace(',', '.'))
    except ValueError:
        return -1.0

    return var


def hay_alerta(cola_lluvias, caudal):
    if -1.0 in cola_lluvias or caudal == -1.0:  # Si hay fallo en alguno de los sensores
        return True
    elif sum(cola_lluvias) > 50:                # Si se superan los 50 mm/h
        print("Alarma por lluvia:", cola_lluvias)
        return True
    elif caudal > 150:                          # Si se supera el caudal de 150m^3/s
        print("Alarma caudal:", caudal)
        return True
    else:
        return False


async def imprimir_variables():
    global hora, lluvia, caudal, cambio_hora
    global variable_dato_pluviometro, hora_texto_temporal, variable_dato_caudal, estado_sistema_alerta

    cola_lluvias = deque(maxlen=12) # Como la lluvia va cada 5 minutos para conseguir las precipitaciones por hora cogemos las ultimas 60/5 = 12

    while True:
        if cambio_hora:
            time.sleep(0.1) # Margen para evitar leer datos anteriores

            lluvia_float = transformar_a_float(lluvia)
            caudal_float = transformar_a_float(caudal)

            cola_lluvias.append(lluvia_float)

            if hay_alerta(cola_lluvias, caudal_float):
                estado_alerta = "ESTADO DE ALERTA"
            else:
                estado_alerta = "NO ALERTA"

            #print(type(hora))
            print(f"Hora : {hora}, Pluviometro : {lluvia}, Caudal : {caudal}  -> Estado : {estado_alerta}")
            #dssfdsfesfdfdf
            variable_dato_pluviometro.write_value(lluvia_float)
            hora_texto_temporal.write_value(hora)
            variable_dato_caudal.write_value(caudal_float)
            estado_sistema_alerta.write_value(estado_alerta)
            estado_sensor_pluviometro.write_value(estado_pluviometro)
            estado_sensor_caudal.write_value(estado_caudal)

            cambio_hora = False
        await asyncio.sleep(0.1)


def importar_modelo_desde_xml(servidor, ruta_xml):
    servidor.import_xml(ruta_xml)


async def main():
    global cambio_hora, variable_dato_pluviometro, hora_texto_temporal, variable_dato_caudal, estado_sistema_alerta, estado_sensor_pluviometro, estado_sensor_caudal
    # Crear y arrancar el servidor una sola vez
    servidor_integracion = Server()
    servidor_integracion.set_endpoint("opc.tcp://localhost:4843/f4l1/servidor_integracion/")
    uri = "http://www.f4l1.es/server/integracion"
    idx = servidor_integracion.register_namespace(uri)

    ruta_xml = "../modelos_datos/modelo_integracion.xml"
    importar_modelo_desde_xml(servidor_integracion, ruta_xml)

    obj_integracion = servidor_integracion.nodes.objects.get_child([f"{idx}:Integracion"])

    hora_texto_temporal = obj_integracion.get_child([f"{idx}:HoraTemporal"])
    variable_dato_pluviometro = obj_integracion.get_child([f"{idx}:DatosPluviometroIntegracion"])
    variable_dato_caudal = obj_integracion.get_child([f"{idx}:DatosCaudalIntegracion"])
    estado_sistema_alerta = obj_integracion.get_child([f"{idx}:EstadoSistemaAlerta"])
    estado_sensor_pluviometro = obj_integracion.get_child([f"{idx}:EstadoSensorPluviometroIntegracion"])
    estado_sensor_caudal = obj_integracion.get_child([f"{idx}:EstadoSensorCaudalIntegracion"])



    servidor_integracion.start()

    url_servidor_temporal = "opc.tcp://localhost:4840/f4l1/servidor_temporal/"
    url_servidor_pluviometro = "opc.tcp://localhost:4841/f4l1/servidor_pluviometro/"
    url_servidor_caudal = "opc.tcp://localhost:4842/f4l1/servidor_caudal/"
    tasks = [
        client_task(url_servidor_temporal,
                    "http://www.f4l1.es/server/temporal" ,[["ServidorTemporal", "HoraSimuladaTexto"]]),
        client_task(url_servidor_pluviometro,
                    "http://www.f4l1.es/server/pluviometro" ,[["Pluviometro", "DatosPluviometro"], ["Pluviometro", "EstadoSensorPluviometro"]]),
        client_task(url_servidor_caudal,
                    "http://www.f4l1.es/server/caudal" ,[["Caudal", "DatosCaudal"], ["Caudal", "EstadoSensorCaudal"]]),
    ]
    await asyncio.gather(*tasks, imprimir_variables())


#Definir las variables globales
variable_dato_pluviometro = None
hora_texto_temporal = None
variable_dato_caudal = None
estado_sistema_alerta = None
estado_sensor_pluviometro = None
estado_sensor_caudal = None


if __name__ == "__main__":
    asyncio.run(main())