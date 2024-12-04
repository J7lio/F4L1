import csv
from datetime import datetime
import asyncio
from asyncua import Client, Node, ua, Server  # Usamos AsyncServer para operaciones asincrónicas

def leer_csv(ruta_csv):
    with open(ruta_csv, "r") as archivo_csv:
        lector_csv = csv.DictReader(archivo_csv)  # Lee las filas como diccionarios
        return [fila for fila in lector_csv]  # Devuelve las filas del CSV en una lista de diccionarios

class SubscriptionHandler:
    """
    El SubscriptionHandler maneja los datos que se reciben para la suscripción.
    """

    def __init__(self):
        self.ruta_csv_caudal = "../data/cincominutales_modificado.csv"
        self.datos_caudal = leer_csv(self.ruta_csv_caudal)

        self.servidor = Server()  # Usamos AsyncServer para operaciones asincrónicas
        self.servidor.set_endpoint("opc.tcp://localhost:4842/f4l1/servidor_caudal/")



    async def iniciar_servidor(self):
        uri = "http://www.f4l1.es/server/caudal"
        idx = await self.servidor.register_namespace(uri)

        self.obj_caudal = await self.servidor.nodes.objects.add_object(idx, "Caudal")

        self.variable_caudal_dato = await self.obj_caudal.add_variable(idx, "DatosCaudal", "NoData")
        await self.variable_caudal_dato.set_writable()


    def leer_valor_por_hora(self, fecha):
        """
        Lee un valor de self.datos_caudal según la fecha pasada por argumento.
        """
        data = None
        for row in self.datos_caudal:
            if row['Fecha'] == fecha:
                data = row['Caudal']
                if data == "":
                    data = "Fallo en el Sensor"
                else:
                    print(f'Fecha: {fecha}')
        if data is None:
            print(f"Fecha {fecha} no registrada")
        return data

    async def publicar_caudal(self, dato):
        await self.variable_caudal_dato.write_value(dato)
        print("Dato registrado: ", dato)

    async def datachange_notification(self, node: Node, val, data):
        """
        Callback para la suscripción asincrónica.
        Este método se llamará cuando el cliente reciba un mensaje de cambio de datos desde el servidor.
        """
        hora_str = datetime.fromtimestamp(val).strftime("%d-%m-%y %#H:%M")
        dato_caudal = self.leer_valor_por_hora(hora_str)
        if dato_caudal is None:
            print("ERROR: Hora No registrada")
            return
        self.publicar_caudal(dato_caudal)


async def main():
    """
    Tarea principal de este ejemplo Cliente-Suscripción.
    """
    client = Client(url="opc.tcp://localhost:4840/servidor_temporal/")
    async with client:
        idx = await client.get_namespace_index(uri="http://www.f4l1.es/server/temporal")
        var = await client.nodes.objects.get_child(f"{idx}:ServidorTemporal/{idx}:HoraSimuladaTimestamp")
        handler = SubscriptionHandler()
        await handler.iniciar_servidor()
        # Creamos una suscripción asincrónica del cliente
        subscription = await client.create_subscription(100, handler)

        await subscription.subscribe_data_change(var)
        try:
            while True:
                await asyncio.sleep(1)  # Mantén el bucle de eventos activo
        finally:
            await subscription.delete()  # Limpiar al salir

# Ejecutar la función principal
if __name__ == "__main__":
    asyncio.run(main())
