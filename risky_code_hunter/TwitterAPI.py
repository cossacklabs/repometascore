import aiohttp
import json
from typing import Dict

from .AbstractAPI import AbstractAPI
from .HTTP_METHOD import HTTP_METHOD


class TwitterAPI(AbstractAPI):
    twitter_guest_token: str

    def __init__(self, session: aiohttp.ClientSession = None, config: Dict = None):
        super().__init__(session=session, config=config)
        self.twitter_guest_token = str()

    def initializeRequestMap(self):
        self._mappedResponseStatuses[-1] = self.nonPredictedResponse
        self._mappedResponseStatuses[200] = self.response200
        self._mappedResponseStatuses[401] = self.response401
        self._mappedResponseStatuses[404] = self.response404
        return

    async def initializeTokens(self) -> None:
        print("Getting Twitter Guest Token")
        self.twitter_guest_token = await self.getTwitterGuestToken()
        print("Successfully Retrieved Twitter Guest Token")
        return

    async def response200(self, **kwargs):
        return False

    async def response401(self, resp, **kwargs):
        raise Exception(
            "Your guest token is not valid. Twitter returned err validation code!\n"
            f"Status code: {resp.status}\n"
            f"Response:\n{await resp.text()}"
        )
        return False

    async def response404(self, url, resp, **kwargs):
        raise Exception(
            "Error, 404 status!\n"
            f"Cannot find info on such url: {url}\n"
            f"Status code: {resp.status}\n"
            f"Response:\n{await resp.text()}"
        )
        return False

    # To get Twitter guest token
    # we need to make request on special url and get + activate our
    # freshly created guest token. It has expiration time, fewer than 24 hours,
    # but greater than 8 hours. Thus we can work with one guest token
    # Response structure: json
    # { 'guest_token': GUEST_TOKEN }
    async def getTwitterGuestToken(self) -> str:
        response = await self.asyncRequest(
            method=HTTP_METHOD.POST,
            url='https://api.twitter.com/1.1/guest/activate.json',
            headers={
                'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs'
                                 '%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA '
            }
        )
        result = await response.json()
        return result['guest_token']

    # to get succesfull response from twitter API
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
    #                "description":"나는야 장난기 넘치는, 20+n살 먹은 예측불가 토끼라구요!☆\n// \uD83C\uDFC6 칭호: '보급형 알쓸신잡' 보유 중\n// \uD83D\uDC64 ENFP-T\n// \uD83C\uDF10 한국어, English\n// \uD83D\uDCDE 디코 서버 '토끼와 악동들' 운영 중\n// \uD83D\uDC8F @pudding1221\uD83D\uDC95",
    #                "entities":{
    #                   "description":{
    #                      "urls":[
    #
    #                      ]
    #                   },
    #                   "url":{
    #                      "urls":[
    #                         {
    #                            "display_url":"youtube.com/channel/UCO8cY…",
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
    #                "location":"예쁜 말이 필요하시거나 사는게 힘들다면 디엠주세요 :D",
    #                "name":"악동분홍토끼",
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
    async def getTwitterAccountInfo(self, twitter_username) -> Dict:
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
        response = await self.asyncRequest(method=HTTP_METHOD.GET, url=url, headers=headers, params=parameters)
        result = await response.json()
        return result
