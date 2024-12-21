import time
from datetime import datetime, timedelta
from asyncua.sync import Server

# Configuración de archivos y servidor
ENDPOINT_TEMPORAL = "opc.tcp://localhost:4840/f4l1/servidor_temporal/"
URI_TEMPORAL = "http://www.f4l1.es/server/temporal"
RUTA_XML = "../modelos_datos/modelo_datos_total.xml"  # Ruta del archivo XML de datos del modelo


# Configuración de la fecha y hora inicial
fecha_hora_inicio_str = "29-10-24 0:00"  # Fecha y hora inicial en formato de cadena
fecha_hora_inicio_obj = datetime.strptime(fecha_hora_inicio_str, "%d-%m-%y %H:%M")  # Objeto datetime correspondiente

# Variables globales para manejar las subscripciones
actualizar_hora = False  # Bandera para habilitar o deshabilitar la actualización de la hora
porcentaje_dia = 0.0  # Porcentaje del día que ha transcurrido
delta_tiempo = 300  # Variación de tiempo entre pasos en segundos (5 minutos por defecto)
duracion_simulada_dia = 600  # Duración de un día simulado en segundos (10 minutos por defecto)


class ManejadorCambios:
    """
    Clase que gestiona los eventos de cambio de datos de las variables en el servidor OPC UA.
    """
    def datachange_notification(self, node, val, data):
        global delta_tiempo, duracion_simulada_dia, porcentaje_dia, actualizar_hora
        print(f"La variable '{node}' cambió a {val}")
        if str(node) == "ns=2;s=PorcentajeDelDia29": # porcentaje_dia
            try:
                porcentaje_dia = float(val)
                actualizar_hora = True
            except ValueError:
                print("Error: Valor del delta_tiempo no es valido")

        if str(node) == "ns=2;s=DeltaTiempo": # delta_tiempo
            try:
                delta_tiempo = float(val)
            except ValueError:
                print("Error: Valor del delta_tiempo no es valido")
                return

        if str(node) == "ns=2;s=DuracionSimuladaDia": # duracion_simulada_dia
            try:
                duracion_simulada_dia = float(val)
            except ValueError:
                print("Error: Valor del delta_tiempo no es valido")
                return


def calcular_hora_nueva():
    """
    Calcula la nueva hora simulada basada en el porcentaje del día transcurrido,
    ajustando para evitar segundos sobrantes.
    """
    tiempo_del_dia = timedelta(days=porcentaje_dia)
    hora_nueva = fecha_hora_inicio_obj + tiempo_del_dia
    segundos_sobrantes = (hora_nueva.minute * 60 + hora_nueva.second) % 300
    hora_nueva -= timedelta(seconds=segundos_sobrantes, microseconds=hora_nueva.microsecond)
    return hora_nueva


def calcular_porcentaje_dia(fecha_hora):
    """
    Calcula la diferencia en porcentaje de la fecha pasada y la inicial(dia 29 0:00)
    """
    dia_29_obj = datetime.strptime(fecha_hora_inicio_str, "%d-%m-%y %H:%M")
    diff_dia_segundos = fecha_hora.timestamp() - dia_29_obj.timestamp()
    return diff_dia_segundos / 86400


def configurar_servidor(endpoint, uri):
    """
    Configura y devuelve el servidor OPC UA junto con las referencias a las variables.
    """
    servidor = Server()
    servidor.set_endpoint(endpoint)

    idx = servidor.register_namespace(uri)

    # Importar modelo de datos desde el XML
    servidor.import_xml(RUTA_XML)

    # Obtener referencias a las variables importadas
    objeto_temporal = servidor.nodes.objects.get_child([f"{idx}:ServidorTemporal"])
    variables = {
        "hora_numerica": objeto_temporal.get_child([f"{idx}:HoraSimuladaNumerica"]),
        "hora_texto": objeto_temporal.get_child([f"{idx}:HoraSimuladaTexto"]),
        "porcentaje_del_dia_29": objeto_temporal.get_child([f"{idx}:PorcentajeDelDia29"]),
        "delta_tiempo": objeto_temporal.get_child([f"{idx}:DeltaTiempo"]),
        "duracion_simulada_dia": objeto_temporal.get_child([f"{idx}:DuracionSimuladaDia"]),
    }

    return servidor, variables


def iniciar_suscripcion(servidor, variables):
    """
    Inicia las suscripciones a las variables relevantes del servidor para gestionar cambios.
    """
    handler = ManejadorCambios()
    sub = servidor.create_subscription(500, handler)
    sub.subscribe_data_change([
        variables["delta_tiempo"],
        variables["duracion_simulada_dia"],
        variables["porcentaje_del_dia_29"]
    ])


def ejecutar_bucle_principal(variables):
    """
    Ejecuta el bucle principal de la simulación, actualizando las variables del servidor.
    """
    global actualizar_hora
    try:
        hora_simulada = fecha_hora_inicio_obj

        while True:
            if actualizar_hora:
                hora_simulada = calcular_hora_nueva()
                actualizar_hora = False

            # Actualizar las variables en el servidor
            variables["hora_numerica"].write_value(hora_simulada.timestamp())
            variables["hora_texto"].write_value(hora_simulada.strftime("%d de %b %H:%M:%S"))

            incremento_tiempo = timedelta(seconds=delta_tiempo)
            hora_simulada += incremento_tiempo

            tiempo_espera = delta_tiempo * duracion_simulada_dia / 86400
            time.sleep(tiempo_espera)

    finally:
        servidor.stop()

if __name__ == "__main__":
    # Configura y arranca el servidor
    servidor, variables = configurar_servidor(ENDPOINT_TEMPORAL, URI_TEMPORAL)
    servidor.start()

    # Inicia las suscripciones y ejecuta el bucle principal
    iniciar_suscripcion(servidor, variables)
    ejecutar_bucle_principal(variables)
