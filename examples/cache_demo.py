import asyncio
import time

from risky_code_hunter.cache import Cache


async def add_after_5sec_sleep(cache, id):
    start = time.time()
    is_present, result = await cache.get_and_await("key", create_new_awaitable=True)
    if is_present:
        print(f"I'm #{id}. I was waiting for it {time.time() - start}. Result: {result}")
    else:
        print(f"Everyone waits only for me (#{id}) to fill value into cache")
        await asyncio.sleep(5)
        result = "someResult"
        await cache.set("key", result)


async def impatient_get_function(cache):
    await asyncio.sleep(4.0)
    print("impatient_get_function: ", await cache.get("key", None))


async def impatient_pop_function(cache):
    await asyncio.sleep(2.5)
    await cache.pop("key", None)


async def impatient_function(cache):
    await asyncio.sleep(2)
    print(
        "I was sleeping for 2 seconds, but now I'm in hurry and will fill cache key with my own value! And those"
        " functions should awake with my own value! In total they would sleep (3 seconds). But only after 1 more"
        " second of sleeping :)")
    await asyncio.sleep(1)
    print("I'm very impatient and adding value.")
    await cache.set("key", "badValue")


async def function_with_timeout(cache):
    try:
        is_present, result = await cache.get_and_await("key", create_new_awaitable=True, timeout=2.0)
    except asyncio.TimeoutError:
        await cache.set("key", "timeout_value")


async def scenario_1():
    cache = Cache()
    tasks = [
        add_after_5sec_sleep(cache, 0),
        add_after_5sec_sleep(cache, 1),
        add_after_5sec_sleep(cache, 2),
        add_after_5sec_sleep(cache, 3),
        add_after_5sec_sleep(cache, 4),
        add_after_5sec_sleep(cache, 5),
        add_after_5sec_sleep(cache, 6),
        add_after_5sec_sleep(cache, 7),
        add_after_5sec_sleep(cache, 8),
    ]
    tasks_results = await asyncio.gather(*tasks)


async def scenario_2():
    cache = Cache()
    tasks = [
        add_after_5sec_sleep(cache, 0),
        add_after_5sec_sleep(cache, 1),
        add_after_5sec_sleep(cache, 2),
        add_after_5sec_sleep(cache, 3),
        add_after_5sec_sleep(cache, 4),
        add_after_5sec_sleep(cache, 5),
        impatient_function(cache),
        add_after_5sec_sleep(cache, 6),
        add_after_5sec_sleep(cache, 7),
        add_after_5sec_sleep(cache, 8),
    ]
    tasks_results = await asyncio.gather(*tasks)


async def scenario_3():
    cache = Cache()
    tasks = [
        add_after_5sec_sleep(cache, 0),
        add_after_5sec_sleep(cache, 1),
        add_after_5sec_sleep(cache, 2),
        add_after_5sec_sleep(cache, 3),
        add_after_5sec_sleep(cache, 4),
        add_after_5sec_sleep(cache, 5),
        impatient_pop_function(cache),
        add_after_5sec_sleep(cache, 6),
        add_after_5sec_sleep(cache, 7),
        add_after_5sec_sleep(cache, 8),
    ]
    tasks_results = await asyncio.gather(*tasks)


async def scenario_4():
    cache = Cache()
    tasks = [
        add_after_5sec_sleep(cache, 0),
        add_after_5sec_sleep(cache, 1),
        add_after_5sec_sleep(cache, 2),
        add_after_5sec_sleep(cache, 3),
        add_after_5sec_sleep(cache, 4),
        add_after_5sec_sleep(cache, 5),
        function_with_timeout(cache),
        add_after_5sec_sleep(cache, 6),
        add_after_5sec_sleep(cache, 7),
        add_after_5sec_sleep(cache, 8),
    ]
    tasks_results = await asyncio.gather(*tasks)


async def scenario_5():
    cache = Cache()
    tasks = [
        add_after_5sec_sleep(cache, 0),
        add_after_5sec_sleep(cache, 1),
        add_after_5sec_sleep(cache, 2),
        add_after_5sec_sleep(cache, 3),
        add_after_5sec_sleep(cache, 4),
        add_after_5sec_sleep(cache, 5),
        impatient_get_function(cache),
        add_after_5sec_sleep(cache, 6),
        add_after_5sec_sleep(cache, 7),
        add_after_5sec_sleep(cache, 8),
    ]
    tasks_results = await asyncio.gather(*tasks)


async def main():
    print("Scenario 1")
    await scenario_1()
    print("Scenario 2")
    await scenario_2()
    print("Scenario 3")
    await scenario_3()
    print("Scenario 4")
    await scenario_4()
    print("Scenario 5")
    await scenario_5()

if __name__ == "__main__":
    asyncio.run(main())
