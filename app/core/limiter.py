from slowapi import Limiter
from slowapi.util import get_remote_address

# IP manzil bo'yicha cheklaydi. Redis o'rniga xotirada saqlaydi -
# bitta serverli kichik loyihalar uchun yetarli.
limiter = Limiter(key_func=get_remote_address)
