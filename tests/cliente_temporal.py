from asyncua.sync import Client
import time

if __name__ == "__main__":
    
    url_servidor = "opc.tcp://localhost:4840/servidor_temporal/"

    
    with Client(url_servidor) as cliente:
        print("Conectado al servidor OPC UA")

        
        root = cliente.nodes.objects

        #buscar ServidorTemporal
        servidor_temporal = root.get_child("2:ServidorTemporal")

        #sus variables de texto y numero
        hora_numerica = servidor_temporal.get_child("2:HoraSimuladaNumerica")  
        hora_texto = servidor_temporal.get_child("2:HoraSimuladaTexto")  
        try:
            while True:
                
                hora_numerica_value = hora_numerica.read_value()
                hora_texto_value = hora_texto.read_value()

                
                print(f"Hora Simulada Numérica: {hora_numerica_value}")
                print(f"Hora Simulada Texto: {hora_texto_value}")

                
                time.sleep(1)

        except KeyboardInterrupt:
            print("Cliente desconectado.")

