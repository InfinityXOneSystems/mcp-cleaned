"""
Background Build Runner
Submits `gcloud builds submit` repeatedly (with a cooldown) so builds run asynchronously.
Use carefully — this will submit source archives to Cloud Build and may count towards quota.
"""

import os
import subprocess
import time

PROJECT = os.environ.get("GCP_PROJECT", "infinity-x-one-systems")
CLOUDBUILD_CONFIG = "cloudbuild.yaml"
COOLDOWN = int(os.environ.get("BUILD_COOLDOWN_SECONDS", "60"))


def submit_build():
    cmd = [
        "gcloud",
        "builds",
        "submit",
        "--config",
        CLOUDBUILD_CONFIG,
        "--project",
        PROJECT,
        "--quiet",
    ]
    print("Submitting build...")
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        print("Build submit output:")
        print(proc.stdout)
        return proc.returncode
    except Exception as e:
        print("Build submission failed:", e)
        return 2


if __name__ == "__main__":
    while True:
        code = submit_build()
        if code == 0:
            print("Build submitted successfully. Sleeping for", COOLDOWN, "seconds")
        else:
            print("Build submit returned code", code, "— will retry after cooldown")
        time.sleep(COOLDOWN)
