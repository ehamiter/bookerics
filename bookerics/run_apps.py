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
    uvicorn_process.wait()


if __name__ == "__main__":
    run_apps()
