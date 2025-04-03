from pyatlan.client.atlan import AtlanClient
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    atlan_base_url: str = "ATLAN_BASE_URL"
    atlan_api_key: str = "ATLAN_API_KEY"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

    @property
    def atlan_client(self) -> AtlanClient:
        return AtlanClient(
            base_url=self.atlan_base_url, api_key=self.atlan_api_key
        )
