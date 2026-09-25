import time

WINDOW_SECONDS = 60
MAX_REQUESTS = 10

_requests = {}


def check_rate_limit(client_ip):
    now = time.time()
    timestamps = [t for t in _requests.get(client_ip, []) if now - t < WINDOW_SECONDS]
    if len(timestamps) >= MAX_REQUESTS:
        return False
    timestamps.append(now)
    _requests[client_ip] = timestamps
    return True
