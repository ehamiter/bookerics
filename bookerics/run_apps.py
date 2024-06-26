import subprocess


def run_apps():
    uvicorn_process = subprocess.Popen(
        [
            "poetry",
            "run",
            "uvicorn",
            "bookerics.main:app",
            "--reload",
            "--port",
            "8080",
        ]
    )
    sqlite_web_process = subprocess.Popen(
        ["poetry", "run", "sqlite_web", "bookerics.db", "-p", "8888", "-x"]
    )

    uvicorn_process.wait()
    sqlite_web_process.wait()


if __name__ == "__main__":
    run_apps()
