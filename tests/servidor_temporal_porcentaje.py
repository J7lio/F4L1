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
        if str(node) == "ns=2;i=4": # porcentaje_dia
            try:
                porcentaje_dia = float(val)
                actualizar_hora = True
            except ValueError:
                print("Error: Valor del delta_tiempo no es valido")

        if str(node) == "ns=2;i=5": # delta_tiempo
            try:
                delta_tiempo = float(val)
            except ValueError:
                print("Error: Valor del delta_tiempo no es valido")
                return

        if str(node) == "ns=2;i=6": # duracion_simulada_dia
            try:
                duracion_simulada_dia = float(val)
            except ValueError:
                print("Error: Valor del delta_tiempo no es valido")
                return


def cambiar_hora():
    tiempo_del_dia = timedelta(days=1*porcentaje_dia)
    hora_nueva = fecha_hora_obj + tiempo_del_dia
    return hora_nueva


if __name__ == "__main__":
    servidor = Server()
    servidor.set_endpoint("opc.tcp://localhost:4840/f4l1/servidor_temporal/")

    uri = "http://www.f4l1.es/server/temporal"
    idx = servidor.register_namespace(uri)

    obj_hora = servidor.nodes.objects.add_object(idx, "ServidorTemporal")

    hora_numerica = obj_hora.add_variable(idx, "HoraSimuladaNumerica", datetime.now().timestamp())
    hora_numerica.set_writable()
    hora_texto = obj_hora.add_variable(idx, "HoraSimuladaTexto", "00:00:00")
    hora_texto.set_writable()

    # Variables para cambiar la hora y el ritmo de simulación
    var_porcentaje_del_dia_29 = obj_hora.add_variable(idx, "PorcentajeDelDia29", porcentaje_dia)
    var_porcentaje_del_dia_29.set_writable()

    var_delta_tiempo = obj_hora.add_variable(idx, "DeltaTiempo", delta_tiempo)
    var_delta_tiempo.set_writable()

    var_duracion_simulada_dia = obj_hora.add_variable(idx, "DuracionSimuladaDia", duracion_simulada_dia)
    var_duracion_simulada_dia.set_writable()

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

            incremento_tiempo = timedelta(seconds=delta_tiempo)
            tiempo_espera = delta_tiempo * duracion_simulada_dia / 86400
            print(f"tiempo_espera: {tiempo_espera}, delta_tiempo: {delta_tiempo}, duracion_simulada_dia {duracion_simulada_dia}")
            time.sleep(tiempo_espera)

            hora_simulada += incremento_tiempo
    finally:
        servidor.stop()
