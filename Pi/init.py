from Pi.main import HUB_DOMAIN
import random
import string
import os

PI_ID = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
# HUB_DOMAIN = "github.com/dhruv0000"


path = "~/.RAP"
try:
    os.mkdir(path)
except OSError as error:
    print(error)

with open("~/.RAP/PI.env", "w") as f:
    f.write("PI_ID=" + PI_ID)
    f.write("HUB_DOMAIN=" + HUB_DOMAIN)

# fetch main.py ans save in ~/.RAP
# https://www.stuffaboutcode.com/2012/06/raspberry-pi-run-program-at-start-up.html
# /etc/init.d/ Make a on power on => run python3 main.py

# get domain/init
# init.bat
# ./init.bat
# put PI_ID -> id.env
# POST request with PI_ID


# get main.py
# daemon changes
