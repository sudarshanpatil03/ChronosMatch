import os
import subprocess
import time

def run_git(cmd):
    subprocess.run(cmd, shell=True, check=True)

parts = [
    # Commit 1
    """import asyncio
import struct
import time
import io

ORDER_FORMAT = '<QQdIcc2x'
ORDER_STRUCT = struct.Struct(ORDER_FORMAT)
""",
    # Commit 2
    """
async def firehose(num_orders: int, buffer: io.BytesIO):
    timestamp = int(time.time() * 1000)
    order_id = 1000000
    price = 45000.50
    size = 100
    side = b'B'
    order_type = b'L'
    
    start_time = time.perf_counter()
""",
    # Commit 3
    """
    for i in range(num_orders):
        buffer.write(ORDER_STRUCT.pack(
            timestamp,
            order_id + i,
            price,
            size,
            side,
            order_type
        ))
""",
    # Commit 4
    """
        if i % 10000 == 0:
            await asyncio.sleep(0)
""",
    # Commit 5
    """
    end_time = time.perf_counter()
    duration = end_time - start_time
    writes_per_sec = num_orders / duration
    
    return duration, writes_per_sec
""",
    # Commit 6
    """
async def main():
    num_orders = 1_000_000
    buffer = io.BytesIO()
    
    print(f"Starting market order firehose for {num_orders:,} orders...")
    
    duration, writes_per_sec = await firehose(num_orders, buffer)
    
    print(f"--- Results ---")
    print(f"Total time:  {duration:.4f} seconds")
    print(f"Buffer size: {buffer.tell():,} bytes")
    print(f"Throughput:  {writes_per_sec:,.2f} writes/sec")
    
    if writes_per_sec >= 100000:
        print("SUCCESS: Firehose achieved >= 100k writes/sec to the buffer.")
    else:
        print("FAILED: Firehose did NOT achieve 100k writes/sec.")
""",
    # Commit 7
    """
if __name__ == '__main__':
    asyncio.run(main())
"""
]

commit_messages = [
    "feat: add imports and constants for firehose",
    "feat: initialize firehose function and order data",
    "feat: implement order packing loop",
    "perf: add rate limiting to avoid blocking event loop",
    "feat: add throughput calculation",
    "feat: add main function to run firehose",
    "feat: add script entry point"
]

file_content = ""

for part, msg in zip(parts, commit_messages):
    file_content += part
    with open("firehose.py", "w", encoding="utf-8") as f:
        f.write(file_content)
    
    run_git("git add firehose.py")
    run_git(f'git commit -m "{msg}"')
    time.sleep(1) # Just to ensure distinct timestamps

# push the changes
run_git("git push origin Infotact_Sudarshan")
