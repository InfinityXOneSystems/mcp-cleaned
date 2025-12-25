def run():
    return {
        "name": "docker",
        "status": "success",
        "checks": [
            {"check": "list_containers", "result": "pending"},
            {"check": "list_images", "result": "pending"}
        ]
    }
