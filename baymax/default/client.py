from functools import partial
from json import dumps as json_dumps
from typing import Any, Dict, List, Mapping, Optional, Union

import aiohttp

from ..base import BaseHttpClient
from ..markups import MarkupJSONEncoder


class AIOHttpClient(BaseHttpClient):
    """
    Http client implementation using aiohttp.
    """

    form_data_type = aiohttp.formdata.FormData

    async def request(
        self,
        endpoint: str,
        params: Optional[Mapping[str, str]] = None,
        data: Any = None,
        json: Any = None,
        headers: Optional[Mapping[str, str]] = None,
        **kwargs: Any
    ) -> Union[Dict[str, str], List[Any], str, int, float, bool]:
        async with aiohttp.ClientSession(
            json_serialize=partial(json_dumps, cls=MarkupJSONEncoder)
        ) as client:

            async with client.post(
                self.get_api_url(endpoint),
                params=params,
                data=data,
                json=json,
                headers=headers,
                **kwargs
            ) as response:
                # TODO: Handle errors
                return await response.json()