import asyncio
import time
from functools import partial, wraps
from typing import Dict, Any, List
from urllib.parse import urlparse

import aiodns
import pycares
import whois

from .abstract_api import AbstractAPI

# set function defaults
# def whois(self, query, hostname, flags, many_results=False, quiet=False) =>
#   => def whois(self, query, hostname, flags, many_results=False, quiet=True)
whois.NICClient.whois.__defaults__ = (False, True)


def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        partial_func = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, partial_func)
    return run


class DomainInfo(AbstractAPI):
    retry_times: int
    dns_resolver: aiodns.DNSResolver

    def __init__(self, session=None, config=None, retry_times=6, verbose: int = 0):
        super().__init__(session=session, config=config, verbose=verbose)
        self.retry_times = retry_times
        self.dns_resolver = aiodns.DNSResolver()
        return

    async def initialize_tokens(self) -> bool:
        return True

    def create_response_handlers(self) -> Dict:
        result = {
            self.UNPREDICTED_RESPONSE_HANDLER_INDEX: self.handle_unpredicted_response,
            200: self.handle_response_200,
        }
        return result

    @staticmethod
    def get_domain(url) -> str:
        return str(urlparse(url).hostname).lower()

    async def get_domain_info(self, domain: str) -> Dict:
        domain = self.get_domain(domain)
        try:
            # set timeout to 180 as getting whois info takes too much time
            is_result_present, cached_result = await self._cache.get_and_await(
                domain, create_new_awaitable=True, timeout=180
            )
        except asyncio.TimeoutError:
            is_result_present = False
        if is_result_present:
            return cached_result
        result = {'location': []}
        ip = await self.get_ip_by_domain(domain)
        if ip:
            tasks = [
                self.retry_sync_func(whois.whois, url=domain, flags=whois.NICClient.WHOIS_RECURSE),
                self.retry_sync_func(whois.whois, url=ip, flags=whois.NICClient.WHOIS_RECURSE),
            ]
            whois_results = await asyncio.gather(*tasks)
            for whois_res in whois_results:
                result['location'].extend(self.get_location_info_from_whois(whois_res))
        await self._cache.set(domain, result)
        return result

    @async_wrap
    def retry_sync_func(self, func, *args, **kwargs) -> Any:
        retry_num = 0
        result = None
        while retry_num < self.retry_times:
            retry_num += 1
            try:
                result = func(*args, **kwargs)
                if result.text[:22] == "Socket not responding:":
                    time.sleep(self.request_limit_timeout(retry_num))
                    continue
                break
            # Known whois parser and package errors. Can be showed with verbose level >= 4
            except (NotImplementedError, AttributeError, ConnectionResetError, KeyboardInterrupt,
                    whois.parser.PywhoisError) as exception:
                self.print(f"DomainInfo.retry_sync_func({func.__name__}, {args}, {kwargs})."
                           f" Raised an exception: \n{exception}", verbose_level=4)
                return None
            # Unknown whois parser and package errors. Can be showed with verbose level >= 4
            except Exception as exception:
                time.sleep(self.request_limit_timeout(retry_num))
                self.print(f"DomainInfo.retry_sync_func({func.__name__}, {args}, {kwargs})."
                           f" Raised an exception: \n{exception}", verbose_level=4)
                continue
        return result

    def get_location_info_from_whois(self, whois_res: whois.WhoisEntry) -> List:
        if isinstance(whois_res, whois.WhoisEntry):
            pass
        elif isinstance(whois_res, whois.dict):
            pass
        else:
            return []
        pattern_list = [
            'address',
            'city',
            'state',
            'country',
            'registrar'
        ]
        result = []
        for key, value in whois_res.items():
            if isinstance(value, str) and value:
                for pattern in pattern_list:
                    if pattern in key:
                        result.append(value)
        return result

    async def get_ip_by_domain(self, domain):
        try:
            ipv4: List[pycares.ares_query_a_result] = await self.dns_resolver.query(domain, "A")
        except aiodns.error.DNSError:
            return str()
        if ipv4:
            return ipv4[0].host
        return str()
