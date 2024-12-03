import asyncio
from asyncua import Client, Node, ua


class SubscriptionHandler:
    """
    The SubscriptionHandler is used to handle the data that is received for the subscription.
    """
    def datachange_notification(self, node: Node, val, data):
        """
        Callback for asyncua Subscription.
        This method will be called when the Client received a data change message from the Server.
        """
        print(f"datachange_notification node:{node} val:{val}")


async def main():
    """
    Main task of this Client-Subscription example.
    """
    client = Client(url="opc.tcp://localhost:4840/servidor_temporal/")
    async with client:
        idx = await client.get_namespace_index(uri="http://www.f4l1.es/server")
        var = await client.nodes.objects.get_child(f"{idx}:ServidorTemporal/{idx}:HoraSimuladaTexto")
        handler = SubscriptionHandler()
        # We create a Client Subscription.
        subscription = await client.create_subscription(100, handler)

        # We subscribe to data changes for two nodes (variables).
        await subscription.subscribe_data_change(var)
        # We let the subscription run for ten seconds
        try:
            while True:
                await asyncio.sleep(1)  # Keep the event loop alive
        finally:
            await subscription.delete()  # Cleanup on exit


if __name__ == "__main__":
    asyncio.run(main())