import csv
from datetime import datetime
import asyncio
from asyncua import Client, Node, ua
from asyncua.sync import Server

# Configuración de archivos y servidor
ENDPOINT_TEMPORAL = "opc.tcp://localhost:4840/servidor_temporal/"
ENDPOINT_CAUDAL = "opc.tcp://localhost:4842/f4l1/servidor_caudal/"
URI_TEMPORAL = "http://www.f4l1.es/server/temporal"
URI_CAUDAL = "http://www.f4l1.es/server/caudal"
RUTA_XML = "../modelos_datos/modelo_datos_total.xml"
RUTA_CSV_CAUDAL = "../data/cincominutales_modificado.csv"


# Funciones auxiliares
def leer_csv(ruta_csv):
    """
    Lee un archivo CSV y devuelve una lista de diccionarios con los datos.
    """
    with open(ruta_csv, "r") as archivo_csv:
        lector_csv = csv.DictReader(archivo_csv)
        return [fila for fila in lector_csv]


class Caudal:
    """
    Clase para manejar la suscripción y publicación de datos de caudal.
    """
    def __init__(self):
        """
        Inicializa el manejador con los datos de caudal y la configuración del servidor.
        """
        self.datos_caudal = leer_csv(RUTA_CSV_CAUDAL)

        # Configuración del servidor OPC UA
        self.servidor = Server()
        self.servidor.set_endpoint(ENDPOINT_CAUDAL)
        idx = self.servidor.register_namespace(URI_CAUDAL)

        # Importar el modelo de datos
        self.servidor.import_xml(RUTA_XML)

        # Obtener referencias a las variables importadas
        self.obj_caudal = self.servidor.nodes.objects.get_child([f"{idx}:Caudal"])
        self.variable_caudal_dato = self.obj_caudal.get_child([f"{idx}:DatosCaudal"])
        self.variable_estado_sensor = self.obj_caudal.get_child([f"{idx}:EstadoSensorCaudal"])

        self.servidor.start()

    @classmethod
    async def crea_caudal(cls):
        """
        Fábrica asincrónica para crear una instancia de Caudal con la configuración inicial.
        """
        # Configuración del cliente OPC UA
        client = Client(url=ENDPOINT_TEMPORAL)
        await client.connect()
        idx = await client.get_namespace_index(uri=URI_TEMPORAL)
        var = await client.nodes.objects.get_child(f"{idx}:ServidorTemporal/{idx}:HoraSimuladaNumerica")

        # Crear instancia de Caudal
        caudal = cls()

        # Crear una suscripción
        caudal.subscription = await client.create_subscription(100, caudal)

        # Suscribirse a cambios de datos
        await caudal.subscription.subscribe_data_change(var)

        # Retornar el caudal y el cliente
        return caudal, client

    def leer_valor_por_hora(self, fecha):
        """
        Busca y devuelve el valor de caudal correspondiente a la fecha pasada.
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
        """
        Publica el dato de caudal en la variable correspondiente.
        """
        if self.variable_caudal_dato:
            self.variable_caudal_dato.write_value(dato)

    def publicar_error(self, dato):
        """
        Publica el estado del sensor de caudal (si está funcionando o no).
        """
        if self.variable_estado_sensor:
            if dato == "Fallo Sensor" or dato == "Hora No Registrada":
                self.variable_estado_sensor.write_value(False)
            else:
                self.variable_estado_sensor.write_value(True)

    def datachange_notification(self, node: Node, val, data):
        """
        Callback que maneja los cambios de datos recibidos desde el servidor.
        """
        hora_str = datetime.fromtimestamp(val).strftime("%d-%m-%y %#H:%M")
        dato_caudal = self.leer_valor_por_hora(hora_str)
        print("Hora:", hora_str, "Publicando dato:", dato_caudal)
        self.publicar_caudal(dato_caudal)
        self.publicar_error(dato_caudal)


async def main():
    """
    Función principal para la ejecución del cliente y suscripción.
    """
    # Crear una instancia de Caudal utilizando la fábrica asincrónica
    caudal, client = await Caudal.crea_caudal()

    try:
        while True:
            await asyncio.sleep(1)  # Mantener vivo el bucle de eventos
    finally:
        await client.disconnect()  # Desconectar el cliente al finalizar


if __name__ == "__main__":
    asyncio.run(main())
