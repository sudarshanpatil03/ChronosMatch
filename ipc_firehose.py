import asyncio
import struct
import time

ORDER_FORMAT = '<QQdIcc2x'
ORDER_STRUCT = struct.Struct(ORDER_FORMAT)
ORDER_SIZE = ORDER_STRUCT.size

IPC_HOST = '127.0.0.1'
IPC_PORT = 9999

async def mock_ipc_bus(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """
    Mock IPC Bus receiver that consumes the data stream and calculates throughput.
    """
    print("[Bus] IPC Bus Receiver connected.")
    bytes_received = 0
    start_time = time.perf_counter()
    last_report_time = start_time
    
    try:
        while True:
            chunk = await reader.read(ORDER_SIZE * 10000)
            if not chunk:
                break
                
            bytes_received += len(chunk)
            current_time = time.perf_counter()
            
            # Report throughput every 1 second
            if current_time - last_report_time >= 1.0:
                orders_received = bytes_received // ORDER_SIZE
                print(f"[Bus] Throughput: {orders_received:,.0f} orders/sec")
                
                # Reset counters for the next interval
                bytes_received = 0
                last_report_time = current_time
    except asyncio.CancelledError:
        pass
    finally:
        print("[Bus] IPC Bus disconnected.")
        writer.close()
        await writer.wait_closed()

async def start_ipc_bus():
    """Starts the mock IPC bus server."""
    server = await asyncio.start_server(mock_ipc_bus, IPC_HOST, IPC_PORT)
    print(f"[Bus] IPC Bus listening on {IPC_HOST}:{IPC_PORT}")
    return server

async def firehose_client(target_rate_per_sec=100000):
    """
    Blasts mock trade orders into the IPC bus at the specified rate.
    """
    print(f"[Firehose] Connecting to IPC Bus at {IPC_HOST}:{IPC_PORT}...")
    
    # Wait a tiny bit to ensure the server is ready
    await asyncio.sleep(0.5)
    
    try:
        reader, writer = await asyncio.open_connection(IPC_HOST, IPC_PORT)
    except ConnectionRefusedError:
        print("[Firehose] Could not connect to IPC Bus.")
        return

    print(f"[Firehose] Connected! Blasting {target_rate_per_sec:,} orders/sec...")
    
    timestamp = int(time.time() * 1000)
    order_id = 1000000
    price = 45000.50
    size = 100
    side = b'B'
    order_type = b'L'
    
    # Batch writes to improve performance
    batch_size = 25000
    sleep_interval = batch_size / target_rate_per_sec
    
    try:
        while True:
            batch_start_time = time.perf_counter()
            
            # Pack a batch of orders
            batch_data = bytearray()
            for _ in range(batch_size):
                batch_data.extend(ORDER_STRUCT.pack(
                    timestamp,
                    order_id,
                    price,
                    size,
                    side,
                    order_type
                ))
                order_id += 1
                
            # Blast into the IPC bus
            writer.write(batch_data)
            await writer.drain()
            
            # Throttle to maintain the target rate
            elapsed = time.perf_counter() - batch_start_time
            sleep_needed = sleep_interval - elapsed
            if sleep_needed > 0:
                if sleep_needed > 0.015:
                    await asyncio.sleep(sleep_needed)
                else:
                    await asyncio.sleep(0)
                
    except asyncio.CancelledError:
        pass
    finally:
        print("[Firehose] Shutting down...")
        writer.close()
        await writer.wait_closed()

async def main():
    # Start the mock IPC Bus
    bus_server = await start_ipc_bus()
    
    # Start the Firehose client targeting 100,000 writes/sec
    firehose_task = asyncio.create_task(firehose_client(target_rate_per_sec=100000))
    
    try:
        # Run for 10 seconds to demonstrate
        await asyncio.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        firehose_task.cancel()
        bus_server.close()
        await bus_server.wait_closed()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
