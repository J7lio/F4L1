import asyncio
from asyncua.sync import Server
from asyncua import Client, Node
from collections import deque


ENDPOINT_INTEGRACION = "opc.tcp://localhost:4843/f4l1/servidor_integracion/"
ENDPOINT_TEMPORAL = "opc.tcp://localhost:4840/f4l1/servidor_temporal/"
ENDPOINT_PLUVIOMETRO = "opc.tcp://localhost:4841/f4l1/servidor_pluviometro/"
ENDPOINT_CAUDAL = "opc.tcp://localhost:4842/f4l1/servidor_caudal/"
URI_INTEGRACION = "http://www.f4l1.es/server/integracion"
URI_TEMPORAL = "http://www.f4l1.es/server/temporal"
URI_PLUVIOMETRO = "http://www.f4l1.es/server/pluviometro"
URI_CAUDAL = "http://www.f4l1.es/server/caudal"
RUTA_XML = "../modelos_datos/modelo_datos_total.xml"



#Variables Globales para actualizar con las subscripciones
cambio_hora = False
hora = ""
lluvia = ""
estado_pluviometro = False
caudal = ""
estado_caudal = False


class SubscriptionHandler:
    def datachange_notification(self, node, val, data):
        global cambio_hora, hora, lluvia, estado_pluviometro, caudal, estado_caudal
        # print(f"La variable '{node}' cambió a {val}")
        # Aquí puedes manejar los cambios de las variables específicas
        if str(node) == "ns=2;s=HoraSimuladaTexto":         # HoraSimuladaTexto
            hora = val
            cambio_hora = True
        if str(node) == "ns=2;s=DatosPluviometro":          # DatosPluviometro
            lluvia = val
        if str(node) == "ns=2;s=EstadoSensorPluviometro":   # EstadoSensorPluviometro
            estado_pluviometro = val
        if str(node) == "ns=2;s=DatosCaudal":               # DatosCaudal
            caudal = val
        if str(node) == "ns=2;s=EstadoSensorCaudal":        # EstadoSensorCaudal
            estado_caudal = val


async def crear_cliente(server_endpoint, namespace,  array_variables_path):
    async with Client(url=server_endpoint) as client:
        variables_cliente = []
        for paths in array_variables_path:
            idx = await client.get_namespace_index(namespace)

            separator = "/" + str(idx) + ":"
            variable_path = str(idx) + ":" + separator.join(paths) #Para que tenga el formato idx:p1/idx:p2

            variable = await client.nodes.objects.get_child(variable_path)
            variables_cliente.append(variable)
        handler = SubscriptionHandler()
        subscription = await client.create_subscription(100, handler)
        await subscription.subscribe_data_change(variables_cliente)
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
    if not estado_pluviometro or not estado_caudal:  # Si hay fallo en alguno de los sensores
        return True
    elif sum(cola_lluvias) > 50:                # Si se superan los 50 mm/h
        return True
    elif caudal > 150:                          # Si se supera el caudal de 150m^3/s
        return True
    else:
        return False


async def imprimir_variables(variables):
    global hora, lluvia, caudal, cambio_hora

    cola_lluvias = deque(maxlen=12) # Como la lluvia va cada 5 minutos para conseguir las precipitaciones por hora cogemos las ultimas 60/5 = 12

    while True:
        if cambio_hora:
            await asyncio.sleep(0.2) # Margen para evitar leer datos anteriores

            lluvia_float = transformar_a_float(lluvia)
            caudal_float = transformar_a_float(caudal)

            cola_lluvias.append(lluvia_float)

            if hay_alerta(cola_lluvias, caudal_float):
                estado_alerta = "ESTADO DE ALERTA"
            else:
                estado_alerta = "NO ALERTA"

            print(f"Hora : {hora}, Pluviometro : {lluvia}, Caudal : {caudal}  -> Estado : {estado_alerta}")

            variables["hora_texto_temporal"].write_value(hora)
            variables["variable_dato_pluviometro"].write_value(lluvia_float)
            variables["variable_dato_caudal"].write_value(caudal_float)
            variables["estado_sensor_pluviometro"].write_value(estado_pluviometro)
            variables["estado_sensor_caudal"].write_value(estado_caudal)
            variables["estado_sistema_alerta"].write_value(estado_alerta)

            cambio_hora = False
        await asyncio.sleep(0.1)


def configurar_servidor_integracion():
    servidor_integracion = Server()
    servidor_integracion.set_endpoint(ENDPOINT_INTEGRACION)
    idx = servidor_integracion.register_namespace(URI_INTEGRACION)
    servidor_integracion.import_xml(RUTA_XML)
    obj_integracion = servidor_integracion.nodes.objects.get_child([f"{idx}:Integracion"])

    variables = {
        "hora_texto_temporal": obj_integracion.get_child([f"{idx}:HoraTemporal"]),
        "variable_dato_pluviometro": obj_integracion.get_child([f"{idx}:DatosPluviometroIntegracion"]),
        "variable_dato_caudal": obj_integracion.get_child([f"{idx}:DatosCaudalIntegracion"]),
        "estado_sistema_alerta": obj_integracion.get_child([f"{idx}:EstadoSistemaAlerta"]),
        "estado_sensor_pluviometro": obj_integracion.get_child([f"{idx}:EstadoSensorPluviometroIntegracion"]),
        "estado_sensor_caudal": obj_integracion.get_child([f"{idx}:EstadoSensorCaudalIntegracion"]),
    }
    return servidor_integracion, variables


async def main():
    servidor_integracion, variables = configurar_servidor_integracion()

    servidor_integracion.start()

    clientes = [
        crear_cliente(ENDPOINT_TEMPORAL, URI_TEMPORAL,
                      [["ServidorTemporal", "HoraSimuladaTexto"]]),
        crear_cliente(ENDPOINT_PLUVIOMETRO, URI_PLUVIOMETRO,
                      [["Pluviometro", "DatosPluviometro"], ["Pluviometro", "EstadoSensorPluviometro"]]),
        crear_cliente(ENDPOINT_CAUDAL, URI_CAUDAL,
                      [["Caudal", "DatosCaudal"], ["Caudal", "EstadoSensorCaudal"]]),
    ]
    await asyncio.gather(*clientes, imprimir_variables(variables))


if __name__ == "__main__":
    asyncio.run(main())