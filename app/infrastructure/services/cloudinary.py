import base64
import hashlib
import time
import typing

import httpx
from loguru import logger

from app.configurations import cloudinary_settings
from app.domain.interfaces.media_service import IMediaService

__all__ = [
    'CloudinaryService',
]


class CloudinaryService(IMediaService):
    def __init__(self) -> None:
        self.cloud_name = cloudinary_settings.CLOUDINARY_CLOUD_NAME
        self.api_key = cloudinary_settings.CLOUDINARY_API_KEY
        self.api_secret = cloudinary_settings.CLOUDINARY_API_SECRET
        self.base_url = f'https://api.cloudinary.com/v1_1/{self.cloud_name}/'
        self.client = httpx.AsyncClient()

    async def close(self):
        await self.client.aclose()

    def generate_signature(self, params: dict[str, typing.Any]) -> str:
        params_to_sign = {
            k: v for k, v in params.items()
            if k not in [
                'file', 'cloud_name', 'resource_type', 'api_key'
            ]
        }

        sorted_params = sorted(params_to_sign.items())
        params_string = '&'.join(
            [f"{k}={v}" for k, v in sorted_params]
        )

        string_to_sign = params_string + self.api_secret

        return hashlib.sha1(string_to_sign.encode()).hexdigest()

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> dict:
        url = self.base_url + endpoint
        logger.info(f'{method=}, url={url}')
        response = await self.client.request(
            method=method.upper(),
            url=url,
            **kwargs
        )
        response.raise_for_status()
        return response.json()

    async def get_asset_details(self, public_id: str, resource_type: str = 'image') -> str:
        auth = base64.b64encode(f'{self.api_key}:{self.api_secret}'.encode()).decode()
        endpoint = f'resources/{resource_type}/upload/{public_id}'
        headers = {
            'Authorization': f'Basic {auth}'
        }
        logger.info(f'Requesting media for public ID: {public_id}, type: {resource_type}')

        response = await self._request(
            method='GET',
            endpoint=endpoint,
            headers=headers,
        )
        return response['url']

    async def upload_file(
        self,
        public_id: str,
        file_bytes: bytes,
    ):
        data = {
            'public_id': public_id,
            'timestamp': int(time.time())
        }
        signature = self.generate_signature(data)
        data.update({'signature': signature, 'api_key': self.api_key})

        files = {
            'file': ('upload.png', file_bytes),
        }

        return await self._request(
            method='POST',
            endpoint='image/upload/',
            data=data,
            files=files,
        )
