

### notifier.py
from plyer import notification

def send_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        app_name='Asset Signal Bot',
        timeout=10
    )

