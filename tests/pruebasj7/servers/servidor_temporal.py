import time
from datetime import datetime, timedelta
from asyncua.sync import Server

fecha_hora_inicio_str = "29-10-24 0:00"

# Convertir la cadena a un objeto datetime
fecha_hora_obj = datetime.strptime(fecha_hora_inicio_str, "%d-%m-%y %H:%M")

# Variable para poder cambiar la hora del dia
actualizar_hora = False
porcentaje_dia = 0.0
# Variables para controlar la duracion del dia
delta_tiempo = 300 # Default: 5 minutos
duracion_simulada_dia = 600 # Default: 10 minutos


class ManejadorCambios:
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


def cambiar_hora():
    tiempo_del_dia = timedelta(days=1*porcentaje_dia)
    hora_nueva = fecha_hora_obj + tiempo_del_dia

    # Cambiar la hora si no sale multiple de 5 minutos o con segundos, se aproxima hacia abajo
    minutos = hora_nueva.minute
    segundos = hora_nueva.second
    microsecons = hora_nueva.microsecond

    if minutos % 5 != 0:
        minutos_extra = timedelta(minutes=minutos % 5)
        hora_nueva -= minutos_extra
    if segundos != 0 or microsecons != 0:
        hora_nueva -= timedelta(seconds=segundos, microseconds=microsecons)

    return hora_nueva


def importar_modelo_desde_xml(servidor, ruta_xml):
    servidor.import_xml(ruta_xml)


if __name__ == "__main__":
    servidor = Server()
    servidor.set_endpoint("opc.tcp://localhost:4840/f4l1/servidor_temporal/")

    uri = "http://www.f4l1.es/server/temporal"
    idx = servidor.register_namespace(uri)

    # Importar modelo desde XML
    ruta_xml = "../modelos_datos/modelo_datos_total.xml"
    importar_modelo_desde_xml(servidor, ruta_xml)

    # Obtener referencias a las variables importadas
    objeto_temporal = servidor.nodes.objects.get_child([f"{idx}:ServidorTemporal"])
    hora_numerica = objeto_temporal.get_child([f"{idx}:HoraSimuladaNumerica"])
    hora_texto = objeto_temporal.get_child([f"{idx}:HoraSimuladaTexto"])
    var_porcentaje_del_dia_29 = objeto_temporal.get_child([f"{idx}:PorcentajeDelDia29"])
    var_delta_tiempo = objeto_temporal.get_child([f"{idx}:DeltaTiempo"])
    var_duracion_simulada_dia = objeto_temporal.get_child([f"{idx}:DuracionSimuladaDia"])

    servidor.start()

    handler = ManejadorCambios()
    sub = servidor.create_subscription(500, handler)
    sub.subscribe_data_change([var_delta_tiempo, var_duracion_simulada_dia, var_porcentaje_del_dia_29])

    try:
        # iniciar la hora inicial
        hora_simulada = fecha_hora_obj

        while True:
            if actualizar_hora:
                hora_simulada = cambiar_hora()
                actualizar_hora = False

            hora_numerica.write_value(hora_simulada.timestamp())

            fecha_hora_str = hora_simulada.strftime("%d de %b %H:%M:%S")
            hora_texto.write_value(fecha_hora_str)
            print("Hora simulada:", fecha_hora_str)

            dia_29_str = "29-10-24 0:00"
            dia_29_obj = datetime.strptime(fecha_hora_inicio_str, "%d-%m-%y %H:%M")

            diff_dia_segundos = hora_simulada.timestamp() - dia_29_obj.timestamp()
            porcentaje_dia = diff_dia_segundos / 86400

            var_porcentaje_del_dia_29.write_value(porcentaje_dia)

            incremento_tiempo = timedelta(seconds=delta_tiempo)
            tiempo_espera = delta_tiempo * duracion_simulada_dia / 86400
            print(f"tiempo_espera: {tiempo_espera}, delta_tiempo: {delta_tiempo}, duracion_simulada_dia {duracion_simulada_dia}")
            time.sleep(tiempo_espera)

            hora_simulada += incremento_tiempo
    finally:
        servidor.stop()
