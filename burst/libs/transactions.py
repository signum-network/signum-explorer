def get_message(attachment: bytes) -> str:
    txt = str(attachment).split('\\')[-1][3:-1]
    return txt
