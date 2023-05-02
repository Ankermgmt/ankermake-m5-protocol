def os_platform(os_family: str):
    if os_family.startswith('Mac OS'):
        return 'macos'
    if os_family.startswith('Windows'):
        return 'windows'
    if os_family.__contains__('Linux'):
        return 'linux'
    else:
        return None


def login_path(platform: str):
    if platform == 'macos':
        return '~/Library/Application Support/AnkerMake/AnkerMake_64bit_fp/login.json'
    if platform == 'windows':
        return r'%LOCALAPPDATA%\Ankermake\AnkerMake_64bit_fp\login.json'
    else:
        return 'Unsupported OS: You must supply path to login.json'
    