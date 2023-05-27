from jsonrpc import dispatcher

from ....jsondb import JsonDatabase


database = JsonDatabase("db.json")
database.load()


@dispatcher.add_method(name="server.database.post_item")
def server_database_post_item(namespace, key, value):
    database.set(f"{namespace}.{key}", value)
    return {
        "namespace": namespace,
        "key": key,
        "value": value
    }


@dispatcher.add_method(name="server.database.delete_item")
def server_database_delete_item(namespace, key):
    name = f"{namespace}.{key}"
    value = database.get(name)
    database.delete(name)
    return {
        "namespace": namespace,
        "key": key,
        "value": value,
    }


@dispatcher.add_method(name="server.database.get_item")
def server_database_get_item(namespace, key=None):
    if key:
        value = database.get(f"{namespace}.{key}")
    else:
        value = database.get(namespace)

    return {
        "namespace": namespace,
        "key": key,
        "value": value
    }


@dispatcher.add_method(name="server.database.list")
def server_database_list(root=None):
    return {
        "namespaces": list(database.db.keys())
    }
