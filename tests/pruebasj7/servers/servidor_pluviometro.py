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
        self.ruta_csv_pluviometro = "../data/PluviómetroChiva_29octubre2024.csv"
        self.datos_lluvia = leer_csv(self.ruta_csv_pluviometro)

        self.servidor = Server()
        self.servidor.set_endpoint("opc.tcp://localhost:4841/f4l1/servidor_pluviometro/")

        uri = "http://www.f4l1.es/server/pluviometro"
        idx = self.servidor.register_namespace(uri)

        # Importar modelo desde XML
        ruta_xml = "../modelos_datos/modelo_datos_total.xml"
        importar_modelo_desde_xml(self.servidor, ruta_xml)

        # Obtener referencias a las variables importadas
        self.obj_pluviometro = self.servidor.nodes.objects.get_child([f"{idx}:Pluviometro"])
        self.variable_pluviometro_dato = self.obj_pluviometro.get_child([f"{idx}:DatosPluviometro"])
        self.variable_estado_sensor = self.obj_pluviometro.get_child([f"{idx}:EstadoSensorPluviometro"])

        self.servidor.start()

    def leer_valor_por_hora(self, fecha):
        """
        Lee un valor de self.datos_lluvia segun la fecha pasada por argumento
        """
        data = None
        for row in self.datos_lluvia:
            if row['Fecha'] == fecha:
                data = row['Lluvia']
                break

        if data == "":
            data = "Fallo Sensor"
        elif data is None:
            data = "Hora No Registrada"

        return data

    def publicar_lluvia(self, dato):
        self.variable_pluviometro_dato.write_value(dato)
        print("Publicando dato: ", dato)

    def publicar_error(self, dato):
        if dato == "Fallo Sensor" or dato == "Hora No Registrada":
            self.variable_estado_sensor.write_value(False)
        else:
            self.variable_estado_sensor.write_value(True)

    def datachange_notification(self, node: Node, val, data):
        """
        Callback for asyncua Subscription.
        This method will be called when the Client received a data change message from the Server.
        """
        hora_str = datetime.fromtimestamp(val).strftime("%d-%m-%y %#H:%M")
        dato_lluvia = self.leer_valor_por_hora(hora_str)
        self.publicar_lluvia(dato_lluvia)
        self.publicar_error(dato_lluvia)


async def main():
    """
    Main task of this Client-Subscription example.
    """
    client = Client(url="opc.tcp://localhost:4840/freeopcua/servidor_temporal/")
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