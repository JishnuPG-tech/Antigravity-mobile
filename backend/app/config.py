import os
import tempfile


class Settings:
    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN")
        self.authorized_users = os.getenv("AUTHORIZED_USERS", "")
        self.upload_limit = int(os.getenv("UPLOAD_LIMIT", "104857600"))
        
        path = os.getenv("WORKSPACE_PATH", "/data/workspaces")
        try:
            os.makedirs(path, exist_ok=True)
            test_file = os.path.join(path, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            self.workspace_path = path
        except Exception:
            self.workspace_path = os.path.join(tempfile.gettempdir(), "workspaces")
            os.makedirs(self.workspace_path, exist_ok=True)


settings = Settings()
