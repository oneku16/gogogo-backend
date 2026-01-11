from .base import Settings


class CloudinarySettings(Settings):
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str


cloudinary_settings = CloudinarySettings()  # type: ignore[call-arg]
