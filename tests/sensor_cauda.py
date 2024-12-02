import time
from datetime import datetime, timedelta
from asyncua.sync import Server
import pandas as pd

if __name__ == "__main__":

    excel = "PluviómetroChiva_29octubre2024.xlsx"
    datos = pd.read_excel(excel)
    datos.columns = ['Fecha', 'Datos']
    datos['Fecha'] = pd.to_datetime(datos['Fecha'], errors='coerce')
    datos = datos.dropna(subset=['Fecha'])

    datos_pluviometro = list(zip(datos['Fecha'], datos['Datos']))  # tupla de de fecha y datos

    servidor = Server()
    servidor.set_endpoint("opc.tcp://localhost:4840/servidor_pluviometro/")

    uri = "http://www.f4l1.es/server_plu"
    idx = servidor.register_namespace(uri)

    obj_pluviometro = servidor.nodes.objects.add_object(idx, "pluviometro")

    variable_pluviometro_dato = obj_pluviometro.add_variable(idx, "DatosPluviometro", datos_pluviometro[0][1])
    variable_pluviometro_dato.set_writable()

    variable_pluviometro_hora = obj_pluviometro.add_variable(idx, "HoraPluviometro",
                                                             datos_pluviometro[0][0].timestamp())
    variable_pluviometro_hora.set_writable()

    servidor.start()

    try:
        cont_list = 0
        while True:
            hora, data = datos_pluviometro[cont_list]
            data = float(data)

            variable_pluviometro_hora.write_value(hora.timestamp())
            variable_pluviometro_dato.write_value(data)

            cont_list += 1

            time.sleep(1)
    finally:
        servidor.stop()
