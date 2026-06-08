import json
import os

STATE_FILE = "monitoring_state.json"


def load_history():

    if not os.path.exists(STATE_FILE):
        return {}

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:
        return {}