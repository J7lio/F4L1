import time
from datetime import datetime, timedelta
from asyncua.sync import Server

delta_tiempo = 300 # 5 minutos
duracion_simulada_dia = 100 # 10 minutos

fecha_hora_inicio_str = "29-10-24 0:00"
hora_simulada = None

# Convertir la cadena a un objeto datetime
fecha_hora_obj = datetime.strptime(fecha_hora_inicio_str, "%d-%m-%y %H:%M")

if __name__ == "__main__":
    servidor = Server()
    servidor.set_endpoint("opc.tcp://0.0.0.0:4840/servidor_temporal/")

    uri = "http://www.f4l1.es/server"
    idx = servidor.register_namespace(uri)

    obj_hora = servidor.nodes.objects.add_object(idx, "ServidorTemporal")
    
    hora_numerica = obj_hora.add_variable(idx, "HoraSimuladaNumerica", datetime.now().timestamp())
    hora_numerica.set_writable()
    hora_texto = obj_hora.add_variable(idx, "HoraSimuladaTexto", "00:00:00")
    hora_texto.set_writable()

    servidor.start()

    try:
        hora_simulada = fecha_hora_obj
        incremento_tiempo = timedelta(seconds=delta_tiempo)

        while True:
            tiempo_espera = delta_tiempo * duracion_simulada_dia / 86400
            time.sleep(tiempo_espera)
            hora_simulada += incremento_tiempo
            
            hora_numerica.write_value(hora_simulada.timestamp())

            fecha_hora_str = hora_simulada.strftime("%d de %b %H:%M:%S")
            hora_texto.write_value(fecha_hora_str)
    finally:
        servidor.stop()
