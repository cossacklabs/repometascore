import asyncio
import asyncwhois
import socket
from functools import partial, wraps
from typing import Dict, Any, List

import httpx
from asyncwhois import DomainLookup, NumberLookup


def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        partial_func = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, partial_func)
    return run


class DomainInfo:
    retryTimes: int
    timeout: float
    __httpx_client: httpx.AsyncClient

    def __init__(self, retryTimes=5):
        self.retryTimes = retryTimes
        self.timeout = 1.0
        self.__httpx_client = httpx.AsyncClient(follow_redirects=True, timeout=self.timeout)
        return

    async def getDomainInfo(self, domain: str) -> Dict:
        result = {'location': []}

        if domain.find("://") != -1:
            domain = domain[domain.find("://") + 3:]
        if domain.find("/") != -1:
            domain = domain[:domain.find("/")]
        ip = await self.getIpByDomain(domain)
        if isinstance(ip, str) and ip:
            tasks = [
                asyncio.ensure_future(
                    self.retryAsyncFunc(asyncwhois.aio_whois_domain, domain=domain, timeout=self.timeout)
                ),
                asyncio.ensure_future(
                    self.retryAsyncFunc(asyncwhois.aio_rdap_domain, domain=domain, httpx_client=self.__httpx_client)
                ),
                asyncio.ensure_future(
                    self.retryAsyncFunc(asyncwhois.aio_whois_ipv4, ipv4=ip, timeout=self.timeout)
                ),
                asyncio.ensure_future(
                    self.retryAsyncFunc(asyncwhois.aio_rdap_ipv4, ipv4=ip, httpx_client=self.__httpx_client)
                )
            ]
            whois_results = list(await asyncio.gather(*tasks))
            for whois_res in whois_results:
                result['location'].extend(await self.getLocationInfoFromWhois(whois_res))
        return result

    async def retryAsyncFunc(self, func, *args, **kwargs) -> Any:
        retryNum = 0
        result = None
        while retryNum < self.retryTimes:
            retryNum += 1
            try:
                result = await func(*args, **kwargs)
                break
            except asyncio.TimeoutError as e:
                # print("Timeout", func.__name__, kwargs.get('domain', kwargs.get('ipv4')))
                return None
            except NotImplementedError as e:
                # print(e, func.__name__, kwargs.get('domain', kwargs.get('ipv4')))
                return None
            except httpx.ConnectTimeout as e:
                # print("Connect Timeout", e, func.__name__, kwargs.get('domain', kwargs.get('ipv4')))
                return None
            except AttributeError as e:
                # print("Attribute Error", e, func.__name__, kwargs.get('domain', kwargs.get('ipv4')))
                return None
            except ConnectionResetError as e:
                # print("Connection Reset Error", e, func.__name__, kwargs.get('domain', kwargs.get('ipv4')))
                return None
            except httpx.ReadTimeout as e:
                # print("Read Timeout", e, func.__name__, kwargs.get('domain', kwargs.get('ipv4')))
                return None
            except Exception as e:
                # print(e, func.__name__, kwargs.get('domain', kwargs.get('ipv4')))
                continue
        return result

    async def getLocationInfoFromWhois(self, whois) -> List:
        if isinstance(whois, DomainLookup) or isinstance(whois, NumberLookup):
            if isinstance(whois.parser_output, Dict):
                parsed = whois.parser_output
            elif isinstance(whois.query_output, Dict):
                parsed = whois.query_output
            else:
                return []
        else:
            return []
        patternList = [
            'address',
            'city',
            'state',
            'country',
            'registrar'
        ]
        result = []
        for key, value in parsed.items():
            if isinstance(value, str) and value:
                for pattern in patternList:
                    if pattern in key:
                        result.append(value)
        return result

    @async_wrap
    def getIpByDomain(self, domain) -> str:
        try:
            ip = socket.gethostbyname(domain)
        except Exception:
            ip = str()
        return ip
