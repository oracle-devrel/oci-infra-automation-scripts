# python script for sending SMTP configuration with Oracle Cloud Infrastructure Email Delivery
import io
import json
import logging
import oci
from fdk import response
import smtplib
import email.utils
import ssl
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase

# Get Resource Principal Credentials
signer = oci.auth.signers.get_resource_principals_signer()

# Get instance principal context
secret_client = oci.secrets.SecretsClient(config={}, signer=signer)
identity_client = oci.identity.IdentityClient(config={}, signer=signer)
tenancy_data = identity_client.get_tenancy(tenancy_id=signer.tenancy_id).data
t_name = str(tenancy_data.name)
t_id = signer.tenancy_id

# Retrieve secret
def read_secret_value(secret_client, secret_id):
   response = secret_client.get_secret_bundle(secret_id)
   base64_Secret_content = response.data.secret_bundle_content.content
   base64_secret_bytes = base64_Secret_content.encode('ascii')
   base64_message_bytes = base64.b64decode(base64_secret_bytes)
   secret_content = base64_message_bytes.decode('ascii')
   return secret_content

# Sender name
sendername = 'noreply'

# If you're using Email Delivery in a different region, replace the HOST value with an appropriate SMTP endpoint.
# Use port 25 or 587 to connect to the SMTP endpoint.
port = 587

# Reading company logo information in base64 encoded
with open("companylogo.png", "rb") as image_file:
   image_data = base64.b64encode(image_file.read())
image_data = '<img src="data:image/png;base64,'+str(image_data)[2:]+'" alt="company logo" />'

def handler(ctx, data: io.BytesIO=None):
   try:
      # Extracting function config values
      cfg = ctx.Config()
      smtp_user = cfg["smtpuser"]
      host = cfg["host"]
      sender = cfg["sender"]
      smtp_defrec = cfg["defaultrecipient"]
      smtp_pass = cfg["smtppass"]

      # Secrets from vault
      smtp_pass = read_secret_value(secret_client, secret_id=smtp_pass )

      # Extracting values from triggered OCI event
      body = json.loads(data.getvalue())
      e_Type = body.get("eventType")
      e_time = body.get("eventTime")
      r_name = body["data"]["resourceName"]
      c_id = body["data"]["compartmentId"]
      c_name = body["data"]["compartmentName"]
      r_id = body["data"]["resourceId"]
      add_detail = ""

      try:
            # Extracting additional details from OCI event
            details = body["data"]["additionalDetails"]
            for key, value in details.items():
               add_detail = add_detail+str(key)+' : '+str(value)+'<br>'
      except (Exception, ValueError) as ex:
            add_detail = "Additional details not available for this OCI event"

      try:
            # Extracting recepient details if available in OCI event
            recipient = body["data"]["definedTags"]["custom"]["recipient"]
      except Exception as e:
            recipient = smtp_defrec

      # Extract event type
      e_Type = e_Type.split('com.oraclecloud.')[1]

      # Extract region name
      r_id = r_id.split('.')[3]

      # The subject line of the email.
      SUBJECT = 'Event | '+ r_name + ' | ' + e_Type + ' | ' + e_time

      BODY_HTML = """\
      <html>
         <head></head>
         <body>
         """ +str(image_data)+ """
         <h2>Oracle Cloud Notification</h2>
         <hr>
         <b>Event Time : </b>""" +str(e_time)+ """
         <br>
         <b>Event Type : </b>""" +str(e_Type)+ """
         <br>
         <b>Tenancy Name : </b>""" +str(t_name)+ """
         <br>
         <b>Tenancy ID : </b>""" +str(t_id)+ """
         <hr>
         <b>Resource Name : </b>""" +str(r_name)+ """
         <br>
         <b>Region Name : </b>""" +str(r_id)+ """
         <br>
         <b>Compartment ID : </b>""" +str(c_id)+ """
         <br>
         <b>Compartment Name : </b>""" +str(c_name)+ """
         <hr>
         <b>Details : </b><br>""" +str(add_detail)+ """
         <hr>
      <br>
      <p>
      Thank you, <br>
      The OCI team <br><br><br>
      Please do not reply directly to this email. This mailbox is not monitored. If you have any questions regarding this notification, contact your account administrator. <br>
      </p>
      </body>
      </html>
      """

      # create message container
      msg = MIMEMultipart()
      msg['Subject'] = SUBJECT
      msg['From'] = email.utils.formataddr((sendername, sender))
      msg['To'] = recipient

      # Attach HTML body for email
      msg.attach(MIMEText(BODY_HTML, 'html'))

      # Attach JSON payload as attachement
      attach_file = json.dumps(body,indent=2)
      payload = MIMEBase('application', 'octate-stream')
      payload.set_payload(attach_file)
      payload.add_header('Content-Disposition', 'attachment', filename='event_output.json')
      msg.attach(payload)

      # Try to send the message.
      server = smtplib.SMTP(host, port)
      server.ehlo()
      # most python runtimes default to a set of trusted public CAs that will include the CA used by OCI Email Delivery.
      # However, on platforms lacking that default (or with an outdated set of CAs), customers may need to provide a capath that includes our public CA.
      server.starttls(context=ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=None, capath=None))
      # smtplib docs recommend calling ehlo() before & after starttls()
      server.ehlo()
      server.login(smtp_user, smtp_pass)

      # our requirement is that SENDER is the same as From address set previously
      server.sendmail(sender, recipient, msg.as_string())
      server.close()
      # Display an error message if something goes wrong.
   except (Exception, ValueError) as ex:
      logging.getLogger().info('error parsing json payload: ' + str(ex))

   return response.Response(ctx, response_data=json.dumps({"message": "success"}),headers={"Content-Type": "application/json"})
