import csv
from datetime import datetime
import asyncio
from asyncua import Client, Node, ua
from asyncua.sync import Server

# Configuración de archivos y servidor
endpoint_temporal = "opc.tcp://localhost:4840/freeopcua/servidor_temporal/"
endpoint_pluviometro = "opc.tcp://localhost:4841/f4l1/servidor_pluviometro/"
uri_pluviometro = "http://www.f4l1.es/server/pluviometro"
ruta_xml = "../modelos_datos/modelo_datos_total.xml"
ruta_csv_pluviometro = "../data/PluviómetroChiva_29octubre2024.csv"


# Funciones auxiliares
def leer_csv(ruta_csv):
    """
    Lee un archivo CSV y devuelve una lista de diccionarios con los datos.
    """
    with open(ruta_csv, "r") as archivo_csv:
        lector_csv = csv.DictReader(archivo_csv)
        return [fila for fila in lector_csv]


class Pluviometro:
    """
    Clase para manejar la suscripción y publicación de datos del pluviómetro.
    """
    def __init__(self):
        """
        Inicializa el manejador con los datos de lluvia y la configuración del servidor.
        """
        self.datos_lluvia = leer_csv(ruta_csv_pluviometro)

        # Configuración del servidor OPC UA
        self.servidor = Server()
        self.servidor.set_endpoint(endpoint_pluviometro)
        idx = self.servidor.register_namespace(uri_pluviometro)

        # Importar el modelo de datos
        self.servidor.import_xml(ruta_xml)

        # Obtener referencias a las variables importadas
        self.obj_pluviometro = self.servidor.nodes.objects.get_child([f"{idx}:Pluviometro"])
        self.variable_pluviometro_dato = self.obj_pluviometro.get_child([f"{idx}:DatosPluviometro"])
        self.variable_estado_sensor = self.obj_pluviometro.get_child([f"{idx}:EstadoSensorPluviometro"])

        self.servidor.start()

    @classmethod
    async def crea_pluviometro(cls):
        """
        Fábrica asincrónica para crear una instancia de Pluviometro con la configuración inicial.
        """
        # Configuración del cliente OPC UA
        client = Client(url=endpoint_temporal)
        await client.connect()
        idx = await client.get_namespace_index(uri="http://www.f4l1.es/server/temporal")
        var = await client.nodes.objects.get_child(f"{idx}:ServidorTemporal/{idx}:HoraSimuladaNumerica")

        # Crear instancia de Pluviometro
        pluviometro = cls()

        # Crear una suscripción
        pluviometro.subscription = await client.create_subscription(100, pluviometro)

        # Suscribirse a cambios de datos
        await pluviometro.subscription.subscribe_data_change(var)

        # Retornar el pluviometro y el cliente
        return pluviometro, client

    def leer_valor_por_hora(self, fecha):
        """
        Busca y devuelve el valor de lluvia correspondiente a la fecha pasada.
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
        """
        Publica el dato de lluvia en la variable correspondiente.
        """
        if self.variable_pluviometro_dato:
            self.variable_pluviometro_dato.write_value(dato)

    def publicar_error(self, dato):
        """
        Publica el estado del sensor de lluvia (si está funcionando o no).
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
        dato_lluvia = self.leer_valor_por_hora(hora_str)
        print("Hora:", hora_str, "Publicando dato:", dato_lluvia)
        self.publicar_lluvia(dato_lluvia)
        self.publicar_error(dato_lluvia)


async def main():
    """
    Función principal para la ejecución del cliente y suscripción.
    """
    # Crear una instancia de Pluviometro utilizando la fábrica asincrónica
    pluviometro, client = await Pluviometro.crea_pluviometro()

    try:
        while True:
            await asyncio.sleep(1)  # Mantener vivo el bucle de eventos
    finally:
        await client.disconnect()  # Desconectar el cliente al finalizar


if __name__ == "__main__":
    asyncio.run(main())
