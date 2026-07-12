WAKE_MODE = "wake"
CONTINUOUS_MODE = "continuous"
VALID_RECORD_MODES = {WAKE_MODE, CONTINUOUS_MODE}


def get_record_config(config):
    return config.get("source", {}).get("record", {})


def get_record_mode(config):
    mode = str(get_record_config(config).get("mode", WAKE_MODE)).strip().lower()
    return mode if mode in VALID_RECORD_MODES else WAKE_MODE


def is_recording_enabled(config):
    return bool(get_record_config(config).get("enabled", False))


def is_continuous_mode(config):
    return get_record_mode(config) == CONTINUOUS_MODE


def disable_unbound_continuous_recording(config):
    if not is_continuous_mode(config) or not is_recording_enabled(config):
        return False
    get_record_config(config)["enabled"] = False
    return True
