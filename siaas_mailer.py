import smtplib, ssl
import csv
import siaas_aux
import platform
import pprint
import os
import sys
from pathlib import Path
from datetime import datetime
from email.utils import formataddr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

smtp_email = "siaas.iscte@gmail.com"
receiver_email = "joao.pedro.seara@gmail.com,joao_pedro_seara@hotmail.com"
receiver_email = "joao.pedro.seara@gmail.com"
receiver_email = "siaas.iscte@gmail.com"
smtp_pwd = "mdbnifhmquaexxka"
smtp_server = "smtp.gmail.com"
smtp_tls_port = "587"

# Generate global variables from the configuration file
config_dict = siaas_aux.get_config_from_configs_db(convert_to_string=True)
MONGO_USER = None
MONGO_PWD = None
MONGO_HOST = None
MONGO_PORT = None
MONGO_DB = None
MONGO_COLLECTION = None
for config_name in config_dict.keys():
    if config_name.upper() == "MONGO_USER":
        MONGO_USER = config_dict[config_name]
    if config_name.upper() == "MONGO_PWD":
        MONGO_PWD = config_dict[config_name]
    if config_name.upper() == "MONGO_HOST":
        MONGO_HOST = config_dict[config_name]
    if config_name.upper() == "MONGO_PORT":
        MONGO_PORT = config_dict[config_name]
    if config_name.upper() == "MONGO_DB":
        MONGO_DB = config_dict[config_name]
    if config_name.upper() == "MONGO_COLLECTION":
        MONGO_COLLECTION = config_dict[config_name]

if len(MONGO_PORT or '') > 0:
    mongo_host_port = MONGO_HOST+":"+MONGO_PORT
else:
    mongo_host_port = MONGO_HOST
db_collection = siaas_aux.connect_mongodb_collection(
    MONGO_USER, MONGO_PWD, mongo_host_port, MONGO_DB, MONGO_COLLECTION)


out_dict=siaas_aux.get_dict_current_agent_data(db_collection, agent_uid=None, module="portscanner")
out_dict_str=pprint.pformat(out_dict)

file_to_write="./tmp/siaas_report_"+datetime.now().strftime('%Y%m%d%H%M%S')+".csv"
os.makedirs(os.path.dirname(os.path.join(sys.path[0], file_to_write)), exist_ok=True)
with open(file_to_write, 'w') as f:
    #w = csv.DictWriter(f, out_dict.keys())
    #w.writeheader()
    #w.writerow(out_dict)
    w = csv.writer(f)
    w.writerows(out_dict.items())

#print(out_dict_str)

message = MIMEMultipart("alternative")
message["Subject"] = "SIAAS Report from "+datetime.utcnow().strftime('%Y-%m-%d at %H:%M')+" "+datetime.now().astimezone().tzname()
#message["From"] = smtp_email
message["From"] = formataddr(("SIAAS ("+platform.node().split('.', 1)[0]+")", smtp_email))
message["To"] = receiver_email

receiver_email_list = receiver_email.lstrip().rstrip().split(',')

# Create the plain-text and HTML version of your message
text = """\
Hi,
How are you?
Real Python has many great tutorials:
www.realpython.com"""
html = """\
<html>
  <body>
    <p>Hi,<br>
       How are you?<br>
       <a href="http://www.realpython.com">Real Python</a> 
       has many great tutorials.
    </p>
  </body>
</html>
"""
output = out_dict_str

# Turn these into plain/html MIMEText objects
part1 = MIMEText(text, "plain")
part2 = MIMEText(html, "html")
part3 = MIMEText(output, "plain")

# Add HTML/plain-text parts to MIMEMultipart message
# The email client will try to render the last part first
message.attach(part1)
message.attach(part2)
message.attach(part3)

with open(file_to_write, "r") as file:
  part = MIMEApplication(
  file.read(),
  Name=os.path.basename(file_to_write)
  )
part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(file_to_write)
message.attach(part)

# Create secure connection with server and send email
context = ssl.create_default_context()
with smtplib.SMTP(smtp_server, smtp_tls_port) as server:
    server.starttls(context=context)
    server.login(smtp_email, smtp_pwd)
    server.sendmail(
        smtp_email, receiver_email_list, message.as_string()
    )

Path(file_to_write).unlink(missing_ok=True)
