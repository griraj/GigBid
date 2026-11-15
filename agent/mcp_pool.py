"""Persistent MCP actors: one owner task per session, no automatic write replay."""
import asyncio
import atexit
import concurrent.futures
import hashlib
import json
import threading
from contextlib import AsyncExitStack


class SessionWorker:
    def __init__(self,parameters):
        self.parameters=parameters
        self.ready=threading.Event()
        self.closed=False
        self.thread=threading.Thread(target=self._run,daemon=True,name='gigbid-mcp')
        self.thread.start()

    def _run(self):
        asyncio.run(self._serve())

    async def _serve(self):
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client
        self.loop=asyncio.get_running_loop();self.queue=asyncio.Queue();self.ready.set()
        while True:
            request=await self.queue.get()
            if request is None:return
            if request[0].cancelled():continue
            try:
                async with AsyncExitStack() as stack:
                    async with asyncio.timeout(request[3]):
                        read,write=await stack.enter_async_context(stdio_client(self.parameters))
                        session=await stack.enter_async_context(ClientSession(read,write))
                        await session.initialize()
                    while request is not None:
                        future,name,arguments,timeout,metadata=request
                        if not future.cancelled():
                            try:
                                result=await asyncio.wait_for(session.call_tool(name,arguments,meta=metadata),timeout)
                            except Exception as exc:
                                if not future.done():
                                    error=TimeoutError('MCP call timed out; not retried') if isinstance(exc,TimeoutError) else RuntimeError('MCP session interrupted; call was not retried')
                                    future.set_exception(error)
                                raise
                            if not future.done():future.set_result(result)
                        request=await self.queue.get()
                    return
            except Exception:
                if request is not None and not request[0].done():
                    request[0].set_exception(RuntimeError('MCP server unavailable; call was not retried'))

    def call(self,name,arguments,timeout,metadata):
        if self.closed:raise RuntimeError('MCP worker closed')
        if not self.ready.wait(timeout):raise TimeoutError('MCP worker startup timed out')
        future=concurrent.futures.Future()
        self.loop.call_soon_threadsafe(self.queue.put_nowait,(future,name,arguments,timeout,metadata))
        try:return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            future.cancel()
            raise TimeoutError('MCP timeout; result unknown, no automatic retry') from None

    def close(self):
        self.closed=True
        if self.ready.is_set() and self.thread.is_alive():
            self.loop.call_soon_threadsafe(self.queue.put_nowait,None)


_workers={}
_lock=threading.Lock()


def get_worker(parameters):
    relevant={key:value for key,value in (parameters.env or {}).items()
        if key.startswith('GIGBID_') and key!='GIGBID_TRACE_ID'}
    fingerprint=hashlib.sha256(json.dumps([parameters.command,parameters.args,relevant],sort_keys=True).encode()).hexdigest()
    with _lock:
        worker=_workers.get(fingerprint)
        if worker is None or worker.closed or not worker.thread.is_alive():
            if len(_workers)>=6:
                _,old=_workers.popitem();old.close()
            worker=SessionWorker(parameters);_workers[fingerprint]=worker
        return worker


def close_workers():
    with _lock:
        workers=list(_workers.values());_workers.clear()
    for worker in workers:worker.close()
    for worker in workers:worker.thread.join(timeout=3)


atexit.register(close_workers)
