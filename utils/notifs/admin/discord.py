import requests

THEMES = {
    "danger": {
        "color": 16711680,
        "title": "Bad News!"
    },
    "success": {
        "color": 3319890,
        "title": "Good News!"
    },
    "info": {
        "color": 4360176,
        "title": "Info"
    }
}

BOT_NAMES = {
    "signup": {
        "name": "Sign Up Bot",
        "wh": "https://discord.com/api/webhooks/1348654119497502760/OTdiiw7AuVa_NlM4Hd6C3c40vOLD0hPwzooIGxUbxg66WVjhHg_zz25lBOxconqyKHzo"
    },
    "sub": {
        "name": "Subscription Bot",
        "wh": "https://discord.com/api/webhooks/1348654163675840643/JUE04NJtElp46PCX8RZL3Rvcf2d5lj3HJ7lMypksovBw2of5g6xGIWV-QovJodnlViGG"
    },
    "err": {
        "name": "Error Reporting Bot",
        "wh": "https://discord.com/api/webhooks/1348654205220421764/wZcWA4LHt85brWzIA-s-zvLV8_wbUA757j1ooWyBEkXopvqTe-YeRPO7dRQv_T1IcNLc"
    },
    "start-shut": {
        "name": "Startup and Shutdown bot",
        "wh": "https://discord.com/api/webhooks/1348654259096522762/zuLl5KrAC9OC_wQ7pDNY7kpIitTyynhI9I4m48KEztsJ29xoEz5ZeDMyenJ0JHhvNIcm"
    },
    "integration-create": {
        "name": "Integration Create",
        "wh": "https://discord.com/api/webhooks/1348654309910253619/95NYPHIgVUWgYsn64VdhnGyn9sGU-lZy-v8VthMdVNoeqr_zzNfnqDaxvTY0Iy3M9nAs"
    },
    "integration-requests": {
        "name": "Integration Requests",
        "wh": "https://discord.com/api/webhooks/1346990674368528397/4cP_6I1RoRsQ5yUKAZMQRKMOrm4FoOzVFcLQR7GJQLe_C7oOD4RWHAUE74KDz_gsCrrD"
    },
}


def send_discord_message(bot, theme, content, image=None):
    try:
        data = {
            "username": BOT_NAMES[bot]["name"],
            "embeds": [{
                "title": THEMES[theme]["title"],
                "description": content,
                "color": THEMES[theme]["color"],
            }
            ],
        }
        if image is not None:
            data["image"] = image

        requests.post(BOT_NAMES[bot]["wh"], json=data)
    except:
        print("DISCORD MESSAGE FAILED")
        pass
