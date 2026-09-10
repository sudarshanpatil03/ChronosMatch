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
