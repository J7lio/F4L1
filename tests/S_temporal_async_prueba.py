import asyncio
import logging
from datetime import datetime, timedelta
from asyncua import Server


async def main():
    _logger = logging.getLogger(__name__)
    server = Server()
    server._application_uri = "urn:f4l1.servers:tiempo_simulado"
    await server.init()
    server.set_endpoint("opc.tcp://localhost:4840/freeopcua/servidor_temporal/")

    uri = "http://www.f4l1.es/server/temporal"
    idx = await server.register_namespace(uri)

    sim_time_obj = await server.nodes.objects.add_object(idx, "ServidorTemporal")
    sim_time_var = await sim_time_obj.add_variable(idx, "HoraSimulada", "29-10-24 00:00")
    sim_time_timestamp = await sim_time_obj.add_variable(idx, "HoraSimuladaTimestamp", 0.0)
    await sim_time_var.set_writable()
    await sim_time_timestamp.set_writable()

    simulated_time = datetime(2024, 10, 29, 0, 0)
    time_step = timedelta(minutes=5)  # Incremento de 5 minutos simulados
    real_step_duration = 1  # 1 segundo entre cada actualización de la hora

    _logger.info("Servidor temporal OPC UA iniciado.")
    async with server:
        while True:
            simulated_time += time_step
            formatted_time = simulated_time.strftime('%d-%m-%y %H:%M')  # Convertir a formato del csv
            _logger.info("Hora simulada actualizada: %s", formatted_time)
            await sim_time_var.write_value(formatted_time)
            await sim_time_timestamp.write_value(simulated_time.timestamp())

            await asyncio.sleep(real_step_duration)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
