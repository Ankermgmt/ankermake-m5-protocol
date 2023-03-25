def json_key_value(str):
    if not "=" in str:
        raise ValueError("Invalid 'key=value' argument")
    key, value = str.split("=", 1)
    try:
        return key, int(value)
    except:
        try:
            return key, float(value)
        except:
            return key, value
