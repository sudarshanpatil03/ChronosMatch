import asyncio
import struct
import time
import io

ORDER_FORMAT = '<QQdIcc2x'
ORDER_STRUCT = struct.Struct(ORDER_FORMAT)
