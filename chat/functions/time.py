#!/usr/bin/env python3
import datetime

current_time = datetime.datetime.now().time()
friendly_time = current_time.strftime("%I:%M %p")

print(friendly_time)
