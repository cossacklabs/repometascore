import asyncio
import functools
import threading
from typing import Dict


async def wait(lock:asyncio.Lock):
    await lock.acquire()
    return



class AsyncLocker:
    __mainLock: threading.Lock
    __dictLoopsLocks: Dict[asyncio.AbstractEventLoop, asyncio.Lock]
    __allLocks: bool

    def __init__(self):
        self.__mainLock = threading.Lock()
        self.__dictLoopsLocks = {}
        self.__allLocks = False

    # May use threading.Lock because vital zone
    # and can be passed relatively fast
    async def __createLock(self, loop: asyncio.AbstractEventLoop) -> asyncio.Lock:
        if not isinstance(loop, asyncio.AbstractEventLoop):
            raise Exception("No such loop provided")
        with self.__mainLock:
            lock = self.__dictLoopsLocks.get(loop)
            if lock:
                return lock
            lock = asyncio.Lock()
            if self.__allLocks:
                if not lock.locked():
                    try:
                        await lock.acquire()
                    except RuntimeError:
                        pass
            self.__dictLoopsLocks[loop] = lock
        return lock

    async def __getLock(self, loop: asyncio.AbstractEventLoop) -> asyncio.Lock | None:
        if not isinstance(loop, asyncio.AbstractEventLoop):
            raise Exception("No such loop provided")
        if loop.is_closed():
            await self.__dictLoopsLocks.pop(loop)
            return
        # To not interrupt every time
        lock = self.__dictLoopsLocks.get(loop)
        if lock:
            return lock
        # We need to create it
        lock = await self.__createLock(loop)
        return lock

    async def turnOnAllLocks(self):
        orig_loop = asyncio.events.get_event_loop()
        while True:
            lock = await self.__getLock(orig_loop)
            await lock.acquire()
            with self.__mainLock:
                if self.__allLocks:
                    continue
                self.__allLocks = True
                for loop, lock in self.__dictLoopsLocks.copy().items():
                    if loop.is_closed():
                        self.__dictLoopsLocks.pop(loop)
                        continue
                    if not lock.locked():
                        try:
                            await lock.acquire()
                        except RuntimeError:
                            continue
            break

    async def turnOffAllLocks(self):
        if not self.__allLocks:
            return
        with self.__mainLock:
            if not self.__allLocks:
                return
            self.__allLocks = False
            for loop, lock in self.__dictLoopsLocks.copy().items():
                if loop.is_closed():
                    self.__dictLoopsLocks.pop(loop)
                    continue
                if lock.locked():
                    lock.release()

    async def lockLoop(self, loop: asyncio.AbstractEventLoop):
        if not isinstance(loop, asyncio.AbstractEventLoop):
            raise Exception("No such loop provided")
        lock = await self.__getLock(loop)
        if lock and not lock.locked():
            await lock.acquire()

    async def unlockLoop(self, loop: asyncio.AbstractEventLoop):
        if not isinstance(loop, asyncio.AbstractEventLoop):
            raise Exception("No such loop provided")
        if self.__allLocks:
            return
        with self.__mainLock:
            if self.__allLocks:
                return
            lock = await self.__getLock(loop)
            if lock and lock.locked():
                lock.release()

    async def lockCurrentLoop(self):
        loop = asyncio.events.get_event_loop()
        lock = await self.__getLock(loop)
        await lock.acquire()

    async def unlockCurrentLoop(self):
        loop = asyncio.events.get_event_loop()
        if self.__allLocks:
            return
        with self.__mainLock:
            if self.__allLocks:
                return
            lock = await self.__getLock(loop)
            if lock and lock.locked():
                lock.release()
