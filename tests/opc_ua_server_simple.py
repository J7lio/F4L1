import time
from asyncua.sync import Server

if __name__ == "__main__":
    servidor = Server()
    servidor.set_endpoint(("opc.tcp://0.0.0.0:4840/f4l1/server/"))
    uri = "http://www.f4l1.es/server"
    idx = servidor.register_namespace(uri)
    mi_obj = servidor.nodes.objects.add_object(idx, "Objeto_Test_1")
    mi_var = mi_obj.add_variable(idx, "miNumeroQueQuieroDibujar", -10.0)
    mi_var.set_writable()
    servidor.start()

    try:
        contador = 0
        while True:
            time.sleep(1)
            contador = mi_var.read_value()
            contador += 0.1
            mi_var.write_value(contador)
    finally:
        servidor.stop()