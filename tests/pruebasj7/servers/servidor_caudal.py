import csv
from datetime import datetime
import asyncio
from asyncua import Client, Node, ua
from asyncua.sync import Server


def leer_csv(ruta_csv):
    with open(ruta_csv, "r") as archivo_csv:
        lector_csv = csv.DictReader(archivo_csv)  # Lee las filas como diccionarios
        return [fila for fila in lector_csv]  # Devuelve las filas del csv en una lista de diccionarios


def importar_modelo_desde_xml(servidor, ruta_xml):
    servidor.import_xml(ruta_xml)


class SubscriptionHandler:
    """
    The SubscriptionHandler is used to handle the data that is received for the subscription.
    """


    def __init__(self):
        self.ruta_csv_caudal = "../data/cincominutales_modificado.csv"
        self.datos_caudal = leer_csv(self.ruta_csv_caudal)

        self.servidor = Server()
        self.servidor.set_endpoint("opc.tcp://localhost:4842/f4l1/servidor_caudal/")

        uri = "http://www.f4l1.es/server/caudal"
        idx = self.servidor.register_namespace(uri)

        ruta_xml = "modelo_caudal.xml"
        importar_modelo_desde_xml(self.servidor, ruta_xml)

        self.obj_caudal = self.servidor.nodes.objects.get_child([f"{idx}:Caudal"])
        self.variable_caudal_dato = self.obj_caudal.get_child([f"{idx}:DatosCaudal"])
        self.variable_estado_sensor = self.obj_caudal.get_child([f"{idx}:EstadoSensor"])

        self.servidor.start()


    def leer_valor_por_hora(self, fecha):
        """
        Lee un valor de self.datos_lluvia segun la fecha pasada por argumento
        """
        data = None
        for row in self.datos_caudal:
            if row['Fecha'] == fecha:
                data = row['Caudal']
                break

        if data == "":
            data = "Fallo Sensor"
        elif data is None:
            data = "Hora No Registrada"

        return data


    def publicar_caudal(self, dato):
        self.variable_caudal_dato.write_value(dato)
        print("Dato registrado: ", dato)



    def datachange_notification(self, node: Node, val, data):
        """
        Callback for asyncua Subscription.
        This method will be called when the Client received a data change message from the Server.
        """
        hora_str = datetime.fromtimestamp(val).strftime("%d-%m-%y %#H:%M")
        dato_caudal = self.leer_valor_por_hora(hora_str)
        self.publicar_caudal(dato_caudal)


async def main():
    """
    Main task of this Client-Subscription example.
    """
    client = Client(url="opc.tcp://localhost:4840/servidor_temporal/")
    async with client:
        idx = await client.get_namespace_index(uri="http://www.f4l1.es/server/temporal")
        var = await client.nodes.objects.get_child(f"{idx}:ServidorTemporal/{idx}:HoraSimuladaNumerica")
        handler = SubscriptionHandler()
        # We create a Client Subscription.
        subscription = await client.create_subscription(100, handler)

        await subscription.subscribe_data_change(var)
        try:
            while True:
                await asyncio.sleep(1)  # Keep the event loop alive
        finally:
            await subscription.delete()  # Cleanup on exit


if __name__ == "__main__":
    asyncio.run(main())