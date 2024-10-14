from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Set

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str

    USE_RANDOM_DELAY_IN_RUN: bool = True
    RANDOM_DELAY_IN_RUN: list[int] = [0, 36000]

    REF_CODE: str = 'onetime6434058521'
    MINI_SLEEP: list[int] = [7, 20]
    TASK_SLEEP: list[int] = [25, 50]
    MAX_SPIN_PER_CYCLE: int = 5
    SLEEP_TIME: list[int] = [21000, 32000]
    BLACKLIST: Set[str] = {'stars_purchase', 'invite_3_friends', 'transaction', 'boost', 'subscribe'}


settings = Settings()
