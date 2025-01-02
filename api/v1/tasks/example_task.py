"""from api.v1.app import celery


def send_email(user_email, message):
    return (user_email, message)

def get_user_by_id(user_id):
    return user_id

@celery.task
def send_welcome_email(user_id: str):
    
    Celery task to send a welcome email to the user.
    
    user = get_user_by_id(user_id)  # Assume a function that fetches user info
    send_email(user.email, "Welcome to QuizyPal!")  # Assume a function to send email
    return f"Welcome email sent to {user.email}"""
