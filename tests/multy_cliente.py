import asyncio
import time
from datetime import datetime

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


async def imprimir_variables():
    """
    Tarea principal para imprimir las variables leídas en un bucle.
    """
    global hora, lluvia, caudal, cambio_hora
    while True:
        if cambio_hora:
            print(f"Hora: {datetime.fromtimestamp(hora)}, Lluvia: {lluvia}, Caudal: {caudal}")
            cambio_hora = False
        await asyncio.sleep(0.1)  # Ajusta el intervalo según sea necesario


async def main():
    global cambio_hora
    url_servidor_temporal = "opc.tcp://localhost:4840/f4l1/servidor_temporal/"
    url_servidor_pluviometro = "opc.tcp://localhost:4841/f4l1/servidor_pluviometro/"
    url_servidor_caudal = "opc.tcp://localhost:4842/f4l1/servidor_caudal/"
    tasks = [
        client_task("Client Temporal", url_servidor_temporal,
                    "http://www.f4l1.es/server/temporal" ,["ServidorTemporal", "HoraSimuladaNumerica"]),
        client_task("Client Pluviometro", url_servidor_pluviometro,
                    "http://www.f4l1.es/server/pluviometro" ,["Pluviometro", "DatosPluviometro"]),
        client_task("Client Caudal", url_servidor_caudal,
                    "http://www.f4l1.es/server/caudal" ,["Caudal", "DatosCaudal"]),
    ]
    await asyncio.gather(*tasks, imprimir_variables())



if __name__ == "__main__":
    asyncio.run(main())


