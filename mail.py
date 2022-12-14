import smtplib, ssl
import siaas_aux
import platform
from datetime import datetime
from email.utils import formataddr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

smtp_email = "jpdsa@iscte-iul.pt"
receiver_email = "joao.pedro.seara@gmail.com,joao_pedro_seara@hotmail.com"
receiver_email = "joao.pedro.seara@gmail.com"
smtp_pwd = "VtSwPnF7!0"
smtp_server = "smtp.office365.com"
smtp_tls_port = 25


message = MIMEMultipart("alternative")
message["Subject"] = "SIAAS Report from "+datetime.now().strftime('%Y-%m-%d at %H:%M')
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

# Turn these into plain/html MIMEText objects
part1 = MIMEText(text, "plain")
part2 = MIMEText(html, "html")

# Add HTML/plain-text parts to MIMEMultipart message
# The email client will try to render the last part first
message.attach(part1)
message.attach(part2)

# Create secure connection with server and send email
context = ssl.create_default_context()
with smtplib.SMTP(smtp_server, smtp_tls_port) as server:
    server.starttls(context=context)
    server.login(smtp_email, smtp_pwd)
    server.sendmail(
        smtp_email, receiver_email_list, message.as_string()
    )
