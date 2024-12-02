import time
from datetime import datetime, timedelta
from asyncua.sync import Server
import pandas as pd

if __name__ == "__main__":

    excel = "cincominutales-rambla-poyo.xlsx"
    datos = pd.read_excel(excel)
    datos.columns = ['Fecha', 'Caudal', 'Estado']
    datos['Fecha'] = pd.to_datetime(datos['Fecha'], errors='coerce')
    datos = datos.dropna(subset=['Fecha'])

    datos_caudal= list(zip(datos['Fecha'], datos['Caudal'], datos['Estado']))  # tupla de de fecha y datos

    servidor = Server()
    servidor.set_endpoint("opc.tcp://localhost:4840/servidor_caudal/")

    uri = "http://www.f4l1.es/server_cau"
    idx = servidor.register_namespace(uri)

    obj_caudal = servidor.nodes.objects.add_object(idx, "caudal")

    variable_caudal_dato = obj_caudal.add_variable(idx, "DatosCaudal", datos_caudal[0][2])
    variable_caudal_dato.set_writable()

    variable_caudal_hora = obj_caudal.add_variable(idx, "HoraCaudal",
                                                             datos_caudal[0][1].timestamp())
    variable_caudal_hora.set_writable()

    servidor.start()

    try:
        cont_list = 0
        while True:
            hora, data = datos_caudal[cont_list]
            data = float(data)

            variable_caudal_hora.write_value(hora.timestamp())
            variable_caudal_dato.write_value(data)

            cont_list += 1

            time.sleep(1)
    finally:
        servidor.stop()
