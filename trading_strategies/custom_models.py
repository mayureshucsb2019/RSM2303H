from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    """
    Represents authentication details for API requests.
    This has been configured to pull in details from env file.
    """

    username: str = Field(..., title="API Username")
    password: str = Field(..., title="API Password")
    server: str = Field(..., title="Server Address")
    port: int = Field(..., title="Server Port")

    def __getitem__(self, item):
        return getattr(self, item)
