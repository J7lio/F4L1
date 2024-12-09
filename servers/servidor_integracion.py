import asyncio
import time
from datetime import datetime
from asyncua.sync import Server
from asyncua import Client, Node

cambio_hora = False
hora = ""
lluvia = 0
caudal = 0

class SubscriptionHandler:
    def __init__(self, client_name):
        self.client_name = client_name



    def datachange_notification(self, node: Node, val, data):
        global hora, lluvia, caudal, cambio_hora
        # print(f"{self.client_name} - Data change on node: {node} val: {val}")
        if self.client_name == "Client Temporal":
            hora = val
            cambio_hora = True
        elif self.client_name == "Client Pluviometro":
            lluvia = val
        elif self.client_name == "Client Caudal":
            caudal = val


async def client_task(client_name, server_url, namespace,  array_variable_path):
    global handler
    async with Client(url=server_url) as client:
        idx = await client.get_namespace_index(namespace)

        separator = "/" + str(idx) + ":"
        variable_path = str(idx) + ":" + separator.join(array_variable_path) #Para que tenga el formato idx:p1/idx:p2

        variable = await client.nodes.objects.get_child(variable_path)
        handler = SubscriptionHandler(client_name)
        subscription = await client.create_subscription(100, handler)
        await subscription.subscribe_data_change(variable)
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


async def imprimir_variables():
    global hora, lluvia, caudal, cambio_hora
    global variable_dato_pluviometro, hora_texto_temporal, variable_dato_caudal, estado_sistema_alerta

    while True:
        if cambio_hora:
            lluvia_float = transformar_a_float(lluvia)
            caudal_float = transformar_a_float(caudal)

            if (lluvia_float > 4.14) and (caudal_float > 45.000 or caudal_float == -1.0):
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

            cambio_hora = False
        await asyncio.sleep(0.1)


async def main():
    global cambio_hora, variable_dato_pluviometro, hora_texto_temporal, variable_dato_caudal, estado_sistema_alerta
    # Crear y arrancar el servidor una sola vez
    servidor_integracion = Server()
    servidor_integracion.set_endpoint("opc.tcp://localhost:4843/f4l1/servidor_integracion/")
    uri = "http://www.f4l1.es/server/integracion"
    idx = servidor_integracion.register_namespace(uri)
    obj_integracion = servidor_integracion.nodes.objects.add_object(idx, "Integracion")

    # Crear variables en el servidor
    variable_dato_pluviometro = obj_integracion.add_variable(idx, "DatosPluviometroIntegracion", 0.0)
    variable_dato_pluviometro.set_writable()

    hora_texto_temporal = obj_integracion.add_variable(idx, "HoraTemporal", "00:00:00")
    hora_texto_temporal.set_writable()

    variable_dato_caudal = obj_integracion.add_variable(idx, "DatosCaudalIntegracion", 0.0)
    variable_dato_caudal.set_writable()

    estado_sistema_alerta = obj_integracion.add_variable(idx, "EstadoSistemaAlerta", "")
    estado_sistema_alerta.set_writable()

    servidor_integracion.start()

    url_servidor_temporal = "opc.tcp://localhost:4840/f4l1/servidor_temporal/"
    url_servidor_pluviometro = "opc.tcp://localhost:4841/f4l1/servidor_pluviometro/"
    url_servidor_caudal = "opc.tcp://localhost:4842/f4l1/servidor_caudal/"
    tasks = [
        client_task("Client Temporal", url_servidor_temporal,
                    "http://www.f4l1.es/server/temporal" ,["ServidorTemporal", "HoraSimuladaTexto"]),
        client_task("Client Pluviometro", url_servidor_pluviometro,
                    "http://www.f4l1.es/server/pluviometro" ,["Pluviometro", "DatosPluviometro"]),
        client_task("Client Caudal", url_servidor_caudal,
                    "http://www.f4l1.es/server/caudal" ,["Caudal", "DatosCaudal"]),
    ]
    await asyncio.gather(*tasks, imprimir_variables())



if __name__ == "__main__":
    asyncio.run(main())