from core.session_manager import SessionManager


def test_session_create(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKSPACE_PATH", str(tmp_path))
    # Prevent actual tmux calls in test environment by stubbing subprocess.run
    class Dummy:
        def __init__(self):
            self.returncode = 0
            self.stdout = ""

    def fake_run(*args, **kwargs):
        return Dummy()

    monkeypatch.setattr("subprocess.run", fake_run)
    sm = SessionManager()
    sm.ensure_session("testuser")
    out = sm.capture_output("testuser")
    assert isinstance(out, str)
