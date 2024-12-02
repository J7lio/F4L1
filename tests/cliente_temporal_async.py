from asyncua.sync import Client
import time

class SubHandler:
    def datachange_notification(self, node, val, data):
        print(f"Variable actualizada: {node} - Nuevo valor: {val}")

if __name__ == "__main__":
    url = "opc.tcp://localhost:4840/servidor_temporal/"

    with Client(url) as client:
        print("Conectado al servidor OPC UA")

        # Obtener el nodo base del servidor
        root = client.nodes.root
        objects = client.nodes.objects
        print("Root y Objects obtenidos.")

        # Buscar el nodo del objeto "ServidorTemporal"
        uri = "http://www.f4l1.es/server"
        idx = 2
        servidor_temporal = objects.get_child([f"{idx}:ServidorTemporal"])

        # Obtener las variables
        hora_numerica = servidor_temporal.get_child([f"{idx}:HoraSimuladaNumerica"])
        hora_texto = servidor_temporal.get_child([f"{idx}:HoraSimuladaTexto"])

        print("Variables obtenidas:")
        print(f" - {hora_numerica}")
        print(f" - {hora_texto}")

        # Crear un manejador de suscripciones
        handler = SubHandler()
        subscription = client.create_subscription(100, handler)

        # Suscribirse a las variables
        subscription.subscribe_data_change(hora_numerica)
        subscription.subscribe_data_change(hora_texto)

        print("Suscripción creada. Monitoreando actualizaciones...")

        try:
            while True:
                time.sleep(5)  # Mantener el cliente activo
        except KeyboardInterrupt:
            print("Cliente detenido.")
