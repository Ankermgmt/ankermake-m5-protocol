import click

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

class EnumType(click.ParamType):
    def __init__(self, enum):
        self.__enum = enum

    def get_missing_message(self, param: "Parameter") -> str:
        return "Choose number or name from:\n{choices}".format(choices="\n".join(f"{e.value:10}: {e.name}" for e in sorted(self.__enum)))

    def convert(self, value, param, ctx):
        try:
            return self.__enum(int(value))
        except:
            try:
                return self.__enum[value]
            except:
                self.fail(self.get_missing_message(param), param, ctx)
