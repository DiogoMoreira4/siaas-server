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
report_type = "vuln_only" # all, vuln_only, exploit_only

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
new_dict={}

if report_type.lower() == "all":
    new_dict = out_dict
else:
    try:
        for a in out_dict.keys():
            for b in out_dict[a].keys():
                if b == "portscanner":
                    for c in out_dict[a][b].keys():
                        for d in out_dict[a][b][c].keys():
                            if d == "last_check":
                                if a not in new_dict.keys():
                                    new_dict[a]={}
                                if b not in new_dict[a].keys():
                                    new_dict[a][b]={}
                                if c not in new_dict[a][b].keys():
                                    new_dict[a][b][c]={}
                                new_dict[a][b][c]["last_check"] = out_dict[a][b][c]["last_check"]
                            if d == "scanned_ports":
                                for e in out_dict[a][b][c][d].keys():
                                    for f in out_dict[a][b][c][d][e].keys():
                                        if f == "scan_results":
                                            for g in out_dict[a][b][c][d][e][f].keys():
                                                for h in out_dict[a][b][c][d][e][f][g].keys():
                                                    if "vulners" in h or "vulscan" in h:
                                                        if report_type.lower() == "vuln_only":
                                                            if a not in new_dict.keys():
                                                                 new_dict[a]={}
                                                            if b not in new_dict[a].keys():
                                                                 new_dict[a][b]={}
                                                            if c not in new_dict[a][b].keys():
                                                                 new_dict[a][b][c]={}
                                                            if d not in new_dict[a][b][c].keys():
                                                                 new_dict[a][b][c][d]={}
                                                            if e not in new_dict[a][b][c][d].keys():
                                                                 new_dict[a][b][c][d][e]={}
                                                            if f not in new_dict[a][b][c][d][e].keys():
                                                                 new_dict[a][b][c][d][e][f]={}
                                                            if g not in new_dict[a][b][c][d][e][f].keys():
                                                                new_dict[a][b][c][d][e][f][g]={}
                                                            new_dict[a][b][c][d][e][f][g][h]=out_dict[a][b][c][d][e][f][g][h]
                                                        else: # exploit_only (default)
                                                            for i in out_dict[a][b][c][d][e][f][g][h].keys():
                                                                for j in out_dict[a][b][c][d][e][f][g][h][i].keys():
                                                                    if "siaas_exploit_tag" in out_dict[a][b][c][d][e][f][g][h][i][j]:
                                                                        if a not in new_dict.keys():
                                                                            new_dict[a]={}
                                                                        if b not in new_dict[a].keys():
                                                                            new_dict[a][b]={}
                                                                        if c not in new_dict[a][b].keys():
                                                                            new_dict[a][b][c]={}
                                                                        if d not in new_dict[a][b][c].keys():
                                                                            new_dict[a][b][c][d]={}
                                                                        if e not in new_dict[a][b][c][d].keys():
                                                                            new_dict[a][b][c][d][e]={}
                                                                        if f not in new_dict[a][b][c][d][e].keys():
                                                                            new_dict[a][b][c][d][e][f]={}
                                                                        if g not in new_dict[a][b][c][d][e][f].keys():
                                                                            new_dict[a][b][c][d][e][f][g]={}
                                                                        if h not in new_dict[a][b][c][d][e][f][g].keys():
                                                                            new_dict[a][b][c][d][e][f][g][h]={}
                                                                        if i not in new_dict[a][b][c][d][e][f][g][h].keys():
                                                                            new_dict[a][b][c][d][e][f][g][h][i]={}
                                                                        new_dict[a][b][c][d][e][f][g][h][i][j]=out_dict[a][b][c][d][e][f][g][h][i][j]

    except Exception as e:
        print(str(e))

if len(new_dict) == 0:
    new_dict_str = "No results available."
else:
    new_dict_str=pprint.pformat(new_dict, width=999)
#print(new_dict_str)

file_to_write="./tmp/siaas_report_"+datetime.now().strftime('%Y%m%d%H%M%S')+".csv"
os.makedirs(os.path.dirname(os.path.join(sys.path[0], file_to_write)), exist_ok=True)
with open(file_to_write, 'w') as f:
    #w = csv.DictWriter(f, new_dict.keys())
    #w.writeheader()
    #w.writerow(new_dict)
    w = csv.writer(f)
    w.writerows(new_dict.items())

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
output = new_dict_str

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

if len(new_dict) > 0:
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
