import asyncio
import struct
import time
import io

ORDER_FORMAT = '<QQdIcc2x'
ORDER_STRUCT = struct.Struct(ORDER_FORMAT)

async def firehose(num_orders: int, buffer: io.BytesIO):
    timestamp = int(time.time() * 1000)
    order_id = 1000000
    price = 45000.50
    size = 100
    side = b'B'
    order_type = b'L'
    
    start_time = time.perf_counter()

    for i in range(num_orders):
        buffer.write(ORDER_STRUCT.pack(
            timestamp,
            order_id + i,
            price,
            size,
            side,
            order_type
        ))

        if i % 10000 == 0:
            await asyncio.sleep(0)

    end_time = time.perf_counter()
    duration = end_time - start_time
    writes_per_sec = num_orders / duration
    
    return duration, writes_per_sec
