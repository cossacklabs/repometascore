import asyncio
import json
from typing import Dict

import aiohttp

from .abstract_api import AbstractAPI
from .constants import HTTP_METHOD


class TwitterAPI(AbstractAPI):
    twitter_guest_token: str

    def __init__(self, session: aiohttp.ClientSession = None, config: Dict = None, verbose: int = 0):
        super().__init__(session=session, config=config, verbose=verbose)
        self.twitter_guest_token = str()

    def create_response_handlers(self) -> Dict:
        result = {
            self.UNPREDICTED_RESPONSE_HANDLER_INDEX: self.handle_unpredicted_response,
            200: self.handle_response_200,
            401: self.handle_response_401,
            404: self.handle_response_404,
            429: self.handle_response_429
        }
        return result

    async def initialize_tokens(self) -> bool:
        if self.twitter_guest_token:
            return True
        self.print("Getting twitter guest token")
        self.twitter_guest_token = await self.get_twitter_guest_token()
        self.print("Successfully retrieved twitter guest token")
        return True

    async def handle_response_401(self, resp, **kwargs):
        raise Exception(
            "Your guest token is not valid. Twitter returned err validation code!\n"
            f"Status code: {resp.status}\n"
            f"Response:\n{await resp.text()}"
        )

    async def handle_response_404(self, url, resp, **kwargs):
        raise Exception(
            "Error, 404 status!\n"
            f"Cannot find info on such url: {url}\n"
            f"Status code: {resp.status}\n"
            f"Response:\n{await resp.text()}"
        )

    async def handle_response_429(self, resp, **kwargs):
        return True

    # To get Twitter guest token
    # we need to make request on special url and get + activate our
    # freshly created guest token. It has expiration time, fewer than 24 hours,
    # but greater than 8 hours. Thus, we can work with one guest token
    # Response structure: json
    # { 'guest_token': GUEST_TOKEN }
    async def get_twitter_guest_token(self) -> str:
        response = await self.request(
            method=HTTP_METHOD.POST,
            url='https://api.twitter.com/1.1/guest/activate.json',
            headers={
                'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs'
                                 '%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA '
            }
        )
        result = await response.json()
        return result['guest_token']

    # to get successful response from twitter API
    # we need to get guest_token
    # and init parameters as json-structure in `variables`
    # that json structure needs to consist of 3 fields
    # `screen_name` as twitter username
    # `withSafetyModeUserFields` as boolean. Idk, maybe it has some ties with NSFW content. Can't spot the difference
    # `withSuperFollowsUserFields` as boolean. That field shows if Twitter account has paid content in it.
    # Response structure with data, that would be informational for us:
    # Response type: json
    # Next is a stripped example of json structure only with fields, that can potentially
    # be interesting for us. Anyway not all fields are using in our processing
    # {
    #    "data":{
    #       "user":{
    #          "result":{
    #             "__typename":"User",
    #             "id":"VXNlcjo4MzE3MTUzNjMyMzAzNTU0NTY=",
    #             "rest_id":"831715363230355456",
    #             "legacy":{
    #                "created_at":"Wed Feb 15 04:02:49 +0000 2017",
    #                "default_profile":false,
    #                "default_profile_image":false,
    #                "description":"????????? ????????? ?????????, 20+n??? ?????? ???????????? ???????????????!???\n// \uD83C\uDFC6 ??????: '????????? ????????????' ??????
    #                ???\n// \uD83D\uDC64 ENFP-T\n// \uD83C\uDF10 ?????????, English\n// \uD83D\uDCDE ?????? ?????? '????????? ?????????' ??????
    #                ???\n// \uD83D\uDC8F @pudding1221\uD83D\uDC95",
    #                "entities":{
    #                   "description":{
    #                      "urls":[
    #
    #                      ]
    #                   },
    #                   "url":{
    #                      "urls":[
    #                         {
    #                            "display_url":"youtube.com/channel/UCO8cY???",
    #                            "expanded_url":"https://www.youtube.com/channel/UCO8cYD3Gpey5SfpDZ70nWeQ",
    #                            "url":"https://t.co/3HmpKQgD7e",
    #                            "indices":[
    #                               0,
    #                               23
    #                            ]
    #                         }
    #                      ]
    #                   }
    #                },
    #                "location":"?????? ?????? ?????????????????? ????????? ???????????? ??????????????? :D",
    #                "name":"??????????????????",
    #                "screen_name":"pinkrabbit412",
    #                "url":"https://t.co/3HmpKQgD7e",
    #             },
    #             "professional":{
    #                "rest_id":"1455912413190971405",
    #                "professional_type":"Creator",
    #                "category":[
    #                   {
    #                      "id":959,
    #                      "name":"Gamer"
    #                   }
    #                ]
    #             },
    #             "legacy_extended_profile":{
    #                 Sometimes data as birthday can present here
    #             }
    #          }
    #       }
    #    }
    # }
    # more info about this twitter graphql API:
    # https://stackoverflow.com/questions/65502651/graphql-value-in-twitter-api
    async def get_twitter_account_info(self, twitter_username) -> Dict:
        try:
            # set timeout to 120
            is_result_present, cached_result = await self._cache.get_and_await(
                twitter_username, create_new_awaitable=True, timeout=120
            )
        except asyncio.TimeoutError:
            is_result_present = False
        if is_result_present:
            return cached_result
        url = 'https://twitter.com/i/api/graphql/Bhlf1dYJ3bYCKmLfeEQ31A/UserByScreenName'
        headers = {
            'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs'
                             '%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            'x-guest-token': self.twitter_guest_token
        }
        parameters = {'variables': json.dumps(
            {
                'screen_name': twitter_username,
                'withSafetyModeUserFields': False,
                'withSuperFollowsUserFields': False
            }
        )}
        response = await self.request(method=HTTP_METHOD.GET, url=url, headers=headers, params=parameters)
        result = await response.json()
        await self._cache.set(twitter_username, result)
        return result
