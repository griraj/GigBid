import asyncio
import os
from mcp.server.fastmcp import FastMCP

mcp=FastMCP('pool-test')

@mcp.tool()
async def process(delay:float=0)->int:
    await asyncio.sleep(delay)
    return os.getpid()

if __name__=='__main__':mcp.run()
