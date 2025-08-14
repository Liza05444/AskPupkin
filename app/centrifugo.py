import requests
from django.conf import settings
import jwt
import time

def generate_token(user_id):
    token = jwt.encode(
        {
            "sub": str(user_id),
            "exp": int(time.time()) + 10 * 60  
        },
        settings.CENTRIFUGO_SECRET,
        algorithm="HS256"
    )
    return token


def publish_to_centrifugo(channel, answer):
    data = {
        "id": answer.id,
        "text": answer.text,
        "author": answer.author.user.username,
        "author_avatar": answer.author.avatar.url,
        "rating": answer.rating,
        "is_correct": answer.is_correct
    }
    url = f"{settings.CENTRIFUGO_URL}/api/publish"
    headers = {
        "Content-type": "application/json",
        "Authorization": f"apikey {settings.CENTRIFUGO_API_KEY}"
    }
    json_data = {
        "channel": channel,
        "data": data
    }
    try:
        response = requests.post(url, json=json_data, headers=headers)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error while publishing to Centrifugo: {e}")
        return None
    