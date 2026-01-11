from typing import Protocol, Any


class IMediaService(Protocol):
    async def upload_file(self, public_id: str, file_bytes: bytes) -> dict[str, Any]:
        ...

    async def get_asset_details(self, public_id: str, resource_type: str = 'image') -> str:
        ...
