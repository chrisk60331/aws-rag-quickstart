import json
import os

import requests


def lambda_handler(event, context):
    host = os.environ["ECS_HOST_IP"]
    delete = int(os.environ["DELETE"])  # boolean
    response = requests.post(
        "http://" + host + "/pdf_file",
        data=json.dumps(
            {
                "event": {
                    "unique_ids": ["apple/www.apple.com_2024-08-27-22-43-46.pdf"]
                }
            }
        ),
    )
    docs = []
    try:
        docs = json.loads(response.content.decode()).get("docs_list")
    except:
        pass
    if not docs:
        response = requests.put(
            "http://" + host + "/pdf_file",
            data=json.dumps(
                {
                    "event": {
                        "unique_id": "apple/www.apple.com_2024-08-27-22-43-46.pdf",
                        "file_path": "apple/www.apple.com_2024-08-27-22-43-46.pdf",
                    }
                }
            ),
        )
        print(vars(response))
    response = requests.post(
        "http://" + host + "/chat",
        data=json.dumps(
            {
                "event": {
                    "unique_ids": [
                        "apple/www.apple.com_2024-08-27-22-43-46.pdf"
                    ],
                    "question": "Find all instances of apple logo in the docs",
                }
            }
        ),
    )
    print(vars(response))
    if delete:
        response = requests.delete(
            "http://" + host + "/pdf_file",
            data=json.dumps(
                {
                    "event": {
                        "unique_id": "apple/www.apple.com_2024-08-27-22-43-46.pdf",
                        "file_path": "apple/www.apple.com_2024-08-27-22-43-46.pdf",
                    }
                }
            ),
        )
        print(vars(response))
    return "ok"


if __name__ == "__main__":
    lambda_handler({}, {})
