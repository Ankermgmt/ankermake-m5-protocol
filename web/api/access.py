from flask import Blueprint


router = Blueprint("access", __name__)


@router.get("/oneshot_token")
def access_oneshot_token():
    return {
        "result": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    }


@router.get("/user")
def access_user():
    return {
        "result": {
            "username": "_TRUSTED_USER_",
            "source": "moonraker",
            "created_on": 0.0
        }
    }


@router.get("/users/list")
def access_users_list():
    return {
        "result": {
            "users": []
        }
    }


@router.get("/api_key")
def access_api_key():
    return {
        "result": "00000000000000000000000000000000"
    }
