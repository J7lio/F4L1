# Cierra los procesos que usen los puertos [4840, 4841, 4842, 4843], tambien cierra el browser y ns si algo mas

# Cuidao

import subprocess

def kill_ports(ports):
    for port in ports:
        # Ejecutar el comando `netstat` y filtrar el puerto
        cmd = f'netstat -ano | findstr ":{port}"'
        try:
            result = subprocess.check_output(cmd, shell=True, text=True)

            # Extraer el PID de la salida
            lines = result.strip().split("\n")
            for line in lines:
                parts = line.split()
                pid = parts[-1]  # El PID está en la última columna

                # Ejecutar el comando `taskkill`
                kill_cmd = f"taskkill /PID {pid} /F"
                subprocess.run(kill_cmd, shell=True)
                print(f"Proceso con PID {pid} en puerto {port} terminado.")
        except subprocess.CalledProcessError:
            print(f"No se encontró ningún proceso en el puerto {port}.")


# Lista de puertos
puertos = [4840, 4841, 4842, 4843]
kill_ports(puertos)
