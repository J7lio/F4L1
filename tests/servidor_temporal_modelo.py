import time
from datetime import datetime, timedelta
from asyncua.sync import Server

delta_tiempo = 300  # 5 minutos
duracion_simulada_dia = 600  # 1 minutos

fecha_hora_inicio_str = "29-10-24 0:00"

# Convertir la cadena a un objeto datetime
fecha_hora_obj = datetime.strptime(fecha_hora_inicio_str, "%d-%m-%y %H:%M")

def importar_modelo_desde_xml(servidor, ruta_xml):
    """
    Importa un modelo OPC UA desde un archivo XML.
    """
    servidor.import_xml(ruta_xml)

if __name__ == "__main__":
    servidor = Server()
    servidor.set_endpoint("opc.tcp://localhost:4840/f4l1/servidor_temporal/")

    uri = "http://www.f4l1.es/server/temporal"
    idx = servidor.register_namespace(uri)

    # Importar modelo desde XML
    ruta_xml = "modelo_temporal.xml"
    importar_modelo_desde_xml(servidor, ruta_xml)

    # Obtener referencias a las variables importadas
    objeto_temporal = servidor.nodes.objects.get_child([f"{idx}:ServidorTemporal"])
    hora_numerica = objeto_temporal.get_child([f"{idx}:HoraSimuladaNumerica"])
    hora_texto = objeto_temporal.get_child([f"{idx}:HoraSimuladaTexto"])

    servidor.start()

    try:
        hora_simulada = fecha_hora_obj
        incremento_tiempo = timedelta(seconds=delta_tiempo)

        while True:
            tiempo_espera = delta_tiempo * duracion_simulada_dia / 86400
            time.sleep(tiempo_espera)

            hora_simulada += incremento_tiempo

            # Actualizar valores de las variables
            hora_numerica.write_value(hora_simulada.timestamp())

            fecha_hora_str = hora_simulada.strftime("%d de %b %H:%M:%S")
            hora_texto.write_value(fecha_hora_str)
            print("Hora simulada:", fecha_hora_str)
    finally:
        servidor.stop()