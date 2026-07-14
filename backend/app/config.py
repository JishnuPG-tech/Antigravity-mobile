import os


class Settings:
    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN")
        self.authorized_users = os.getenv("AUTHORIZED_USERS", "")
        self.workspace_path = os.getenv("WORKSPACE_PATH", "/data/workspaces")
        self.upload_limit = int(os.getenv("UPLOAD_LIMIT", "104857600"))


settings = Settings()
