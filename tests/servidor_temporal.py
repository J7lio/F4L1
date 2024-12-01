import time
from datetime import datetime, timedelta
from asyncua.sync import Server

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
        hora_actual = datetime.now()
        incremento_tiempo = timedelta(seconds=1)

        while True:
            time.sleep(1)
            hora_actual += incremento_tiempo
            
            hora_numerica.write_value(hora_actual.timestamp())
            
            hora_texto.write_value(hora_actual.strftime('%H:%M:%S'))
    finally:
        servidor.stop()
