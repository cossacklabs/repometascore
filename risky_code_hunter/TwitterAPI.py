import asyncio
import json

import aiohttp


class TwitterAPI:
    twitter_guest_token: str
    twitter_token_Lock: asyncio.Lock
    __session: aiohttp.ClientSession

    def __init__(self, session=None):
        self.twitter_guest_token = str()
        self.twitter_token_Lock = asyncio.Lock()
        if session:
            self.__session = session
        else:
            self.__session = aiohttp.ClientSession()

    async def getTwitterGuestToken(self):
        response = await self.asyncRequest(
            method='POST',
            url='https://api.twitter.com/1.1/guest/activate.json',
            headers={
                'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs'
                                 '%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA '
            }
        )
        result = await response.json()
        return result['guest_token']

    async def getTwitterToken(self):
        async with self.twitter_token_Lock:
            if isinstance(self.twitter_guest_token, str) and self.twitter_guest_token:
                return self.twitter_guest_token
            self.twitter_guest_token = await self.getTwitterGuestToken()
        return self.twitter_guest_token

    async def getTwitterAccountInfo(self, twitter_username):
        twitter_token = await self.getTwitterToken()
        url = 'https://twitter.com/i/api/graphql/Bhlf1dYJ3bYCKmLfeEQ31A/UserByScreenName'
        headers = {
            'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs'
                             '%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            'x-guest-token': twitter_token
        }
        parameters = {'variables': json.dumps(
            {
                'screen_name': twitter_username,
                'withSafetyModeUserFields': False,
                'withSuperFollowsUserFields': True
            }
        )}
        response = await self.asyncRequest(method='GET', url=url, headers=headers, params=parameters)
        result = await response.json()
        return result

    async def asyncRequest(self, method, url, params=None, data=None, headers=None):
        retry = 0
        while True:
            retry += 1
            async with self.__session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data
            ) as resp:
                await resp.read()
                if resp.status == 404:
                    raise Exception(
                        "Error, 404 status!\n"
                        f"Cannot find info on such url: {url}\n"
                        f"Status code: {resp.status}\n"
                        f"Response:\n{await resp.text()}"
                    )
                elif resp.status == 401:
                    raise Exception(
                        "Your github token is not valid. Github returned err validation code!\n"
                        f"Status code: {resp.status}\n"
                        f"Response:\n{await resp.text()}"
                    )
                elif resp.status != 200:
                    raise Exception(
                        f"Non-predicted response from server\n"
                        f"Requested URL: {url}\n"
                        f"Requested params: {params}\n"
                        f"Status code: {resp.status}\n"
                        f"Response:\n{await resp.text()}"
                    )
                break
        return resp
