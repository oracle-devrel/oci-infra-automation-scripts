import io
import json
import logging
import oci
from fdk import response
import smtplib
import datetime
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase

# Get Resource Principal Credentials
signer = oci.auth.signers.get_resource_principals_signer()

# Create required client object
identity_client = oci.identity.IdentityClient(config={}, signer=signer)
secret_client = oci.secrets.SecretsClient(config={}, signer=signer)
onsclient = oci.ons.NotificationDataPlaneClient(config={}, signer=signer)

# Fetch tenancy information
tenancy_data = identity_client.get_tenancy(tenancy_id=signer.tenancy_id).data
t_name = str(tenancy_data.name)
t_id = signer.tenancy_id

# Retrieve secret
def read_secret_value(secret_client, secret_id):
   response = secret_client.get_secret_bundle(secret_id).data
   base64_Secret_content = response.secret_bundle_content.content
   base64_secret_bytes = base64_Secret_content.encode('ascii')
   base64_message_bytes = base64.b64decode(base64_secret_bytes)
   secret_content = base64_message_bytes.decode('ascii')
   return secret_content

def reset_body_html(image_data):
    BODY_HTML = """<html>
                            <head>
                               <style>
                                  table, th, td {
                                  border: 1px solid black;
                                  border-collapse: collapse;
                                  }
                               </style>
                            </head>
                            <body>
                               """ + str(image_data)
    return BODY_HTML

def append_body_html(BODY_HTML,domain_name,user_name,type,identifier,severity,created_time,expiry_date):
    
    if severity == "Expired":
        BODY_HTML += f'''
                            <tr>
                                <td>{domain_name}</td>
                                <td>{user_name}</td>
                                <td>{type}</td>
                                <td>{identifier}</td>
                                <td style="color:red">{severity}</td>
                                <td>{created_time}</td>
                                <td>{expiry_date}</td>
                                </tr>
                            '''
    else:
        BODY_HTML += f'''
                            <tr>
                                <td>{domain_name}</td>
                                <td>{user_name}</td>
                                <td>{type}</td>
                                <td>{identifier}</td>
                                <td>{severity}</td>
                                <td>{created_time}</td>
                                <td>{expiry_date}</td>
                                </tr>
                            '''
    return BODY_HTML

# Sender name
sendername = 'noreply'

# Reading company logo information in base64 encoded
with open("companylogo.png", "rb") as image_file:
   image_data = base64.b64encode(image_file.read())

image_data = '<img src="data:image/png;base64,'+str(image_data)[2:]+'" alt="company logo" />'

def send_email(subject,secret_client,cfg,BODY_HTML,report_data,recipient,report_day=False):
    # create message container
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['To'] = recipient

    # Extracting function config values
    smtp_user = cfg["smtpuser"]
    host = cfg["host"]
    port = cfg["port"]
    msg['From'] = cfg["sender"]

    # Secrets from vault
    secret_pass_id = cfg["smtppass"]
    smtp_pass = read_secret_value(secret_client, secret_id=secret_pass_id)

    if report_day:
        BODY_HTML = reset_body_html(image_data)
        BODY_HTML += """ 
                <br><br>Dear <b>Security Administrator</b>,
                <br>
                <p>Please refer attached list of users with IAM secret identifiers either going to or expired.<br><br>
                Tenancy : <b>""" + str(t_name) + """ </b><br><br>                
                Review the list of users and request them to rotate the secrets, or follow the exception process.<br><br>
                <b>Action for users:</b><br>                           
                    1.  Log on OCI console.<br>
                    2.	Open the Profile menu and click My profile.<br>
                    3.  In the Resources section at the bottom left, click required secret i.e., API Keys, Auth Token, Customer secret key etc.<br><br>

                Please do not reply directly to this email. This mailbox is not monitored. If you have any questions regarding this notification, contact your account administrator. <br>
                </p>
            </body>
            </html>
        """
        msg.attach(MIMEText(BODY_HTML, 'html'))
        # Attach csv payload as attachement
        attach_file = report_data
        payload = MIMEBase('application', 'octate-stream')
        payload.set_payload(attach_file)
        payload.add_header('Content-Disposition', 'attachment', filename='user_credential_report.csv')
        msg.attach(payload)

    else:
        # Attach HTML body for email
        msg.attach(MIMEText(BODY_HTML, 'html'))

    # Send the message
    server = smtplib.SMTP(host, port)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(smtp_user, smtp_pass)
    server.sendmail(msg["From"], msg["To"].split(","), msg.as_string())
    #server.send_message(msg)
    server.close()

def get_body_html(identity_domains_client,BODY_HTML,domain_name,credential_check,user_name,user_email,resource,resource_id,type,cfg,except_user,report_data):
    report_date = str(datetime.datetime.strftime(datetime.datetime.now(), "%Y-%b-%d"))
    identifier = resource_id
    created_time = datetime.datetime.strptime((resource.meta).created, "%Y-%m-%dT%H:%M:%S.%fZ")
    warning_date = created_time + datetime.timedelta(days=int(cfg["warning_in_days"]))
    critical_date = created_time + datetime.timedelta(days=int(cfg["critical_in_days"]))
    expiry_date = created_time + datetime.timedelta(days=int(cfg["expiry_in_days"]))
    created_time = str(created_time.strftime("%Y-%b-%d"))
    severity = ""
    if expiry_date < datetime.datetime.now():
        credential_check = False
        severity = "Expired"

        # Delete the credential
        user_to_check = str(user_name)+"@"+str(domain_name)
        if user_to_check.lower() not in except_user:
            logging.getLogger().info(f'Deleting {resource.id}  {type} for {user_name} in {domain_name} domain')
            if type == "api_key":
                identity_domains_client.delete_api_key(resource.id)
            elif type == "auth_token":
                identity_domains_client.delete_auth_token(resource.id)
            elif type == "customer_secret_key":
                identity_domains_client.delete_customer_secret_key(resource.id)

    elif critical_date < datetime.datetime.now():
        credential_check = False
        severity = "Critical"

    elif warning_date < datetime.datetime.now():
        credential_check = False
        severity = "Warning"

    expiry_date = str(expiry_date.strftime("%Y-%b-%d"))
    if severity != "":
        BODY_HTML = append_body_html(BODY_HTML, domain_name, user_name, type, identifier, severity, created_time, expiry_date )
        if not credential_check:
            report_data += f'\n"{report_date}","{domain_name}","{user_name}","{user_email}","{type}","{identifier}","{severity}","{created_time}","{expiry_date}"'

    return BODY_HTML,credential_check,report_data


def handler(ctx, data: io.BytesIO=None):
    try:
        # Extracting function config values
        cfg = ctx.Config()
        domain_ids = cfg["domain_ocids"]
        except_user_input = cfg["exception_users"].split(",")
        except_user = []
        for item in except_user_input:
            except_user.append(str(item).lower())
        report_requested = False
        if str(cfg["report_requested"]).lower() in ['yes','true']:
            report_requested = True
        weekly_report_day = str(cfg["weekly_report_day"]).lower().split(",")
        #monthly_report_day = str(cfg["monthly_report_day"]).lower().split(",")
        monthly_report_day = str(cfg["monthly_report_day"]).split(",")
        report_recipients = str(cfg['report_recipients'])
        user_email_done = []
        users_map = {}
        report_data = "Report Date,Domain, Username, Email, Type, Identifier, Severity,Created Date,Expiry Date"

        # The subject line of the email.
        SUBJECT = f'NEEDS ATTENTION !!! Your IAM Credentials need to be rotated'

        for domain_id in domain_ids.split(","):
            # Extract domain endpoint
            domain_data = identity_client.get_domain(domain_id=domain_id).data
            url = domain_data.url
            domain_name = domain_data.display_name
            domain_endpoint = (url.split(":443"))[0]

            # Initialize service client with default config file
            identity_domains_client = oci.identity_domains.IdentityDomainsClient(config={}, signer=signer, service_endpoint=domain_endpoint)

            list_users_response = identity_domains_client.list_users(limit=100000).data

            for user in list_users_response.resources:
                user_ocid = user.ocid
                user_name = user.user_name
                user_email = ""
                for email in user.emails:
                    if email.primary:
                        user_email = email.value
                        break
                if user_email not in user_email_done:
                    users_map[user_email] = [{'ocid':user_ocid,'name':user_name,'domain':domain_name,'id_client':identity_domains_client}]
                    user_email_done.append(user_email)
                else:
                    users_map[user_email].append({'ocid':user_ocid,'name':user_name,'domain':domain_name,'id_client':identity_domains_client})

        for key, val in users_map.items():
            BODY_HTML = reset_body_html(image_data)
            BODY_HTML += """ 
                                    <br><br>Dear <b>User</b>,
                                    <br>
                                    <p>Following credentials need attention for tenancy : <b>""" + str(t_name) + """ </b></p>
                                    <br>
                                    <b>Secret Details:</b>
                                    <table style="width:70%">
                                    <tr>
                                        <th>Identity Domain Name</th>
                                        <th> User Name </th>
                                        <th>Secret Type</th>
                                        <th>Identifier</th>
                                        <th>Severity</th>
                                        <th>Creation Date</th>
                                        <th>Expiry Date </th>
                                        </tr>
                            """
            user_email = key
            credential_check = True
            for user in val:
                identity_domains_client = user['id_client']
                user_ocid = user['ocid']
                user_name = user['name']
                domain_name = user['domain']

                # get list of api keys for user
                list_api_keys_response = identity_domains_client.list_api_keys(filter=f'user.ocid eq \"{user_ocid}\"').data
                for api_key in list_api_keys_response.resources:
                    BODY_HTML,credential_check,report_data = get_body_html(identity_domains_client,BODY_HTML,domain_name,credential_check,user_name,user_email,api_key,api_key.fingerprint,"api_key",cfg,except_user,report_data)

                list_auth_tokens_response = identity_domains_client.list_auth_tokens(filter=f'user.ocid eq \"{user_ocid}\"').data
                for auth_token in list_auth_tokens_response.resources:
                    BODY_HTML,credential_check,report_data = get_body_html(identity_domains_client,BODY_HTML,domain_name,credential_check,user_name,user_email,auth_token,auth_token.description,"auth_token",cfg,except_user,report_data)

                list_customer_secret_keys_response = identity_domains_client.list_customer_secret_keys(filter=f'user.ocid eq \"{user_ocid}\"').data
                for csk in list_customer_secret_keys_response.resources:
                    BODY_HTML,credential_check,report_data = get_body_html(identity_domains_client,BODY_HTML,domain_name,credential_check,user_name,user_email,csk,csk.access_key,"customer_secret_key",cfg,except_user,report_data)

                if credential_check:
                    logging.getLogger().info('all credentials for user ' + user_name + ' are healthy')

            if credential_check :
                continue

            # Message Body for notification
            BODY_HTML += """
                </table>
                <p><b>Action:</b><br>                           
                    1.	Log on OCI console.<br>
                    2.	Open the Profile menu and click My profile.<br>
                    3.  In the Resources section at the bottom left, click required secret i.e., API Keys, Auth Token, Customer secret key etc.<br><br>
                    Please update your secret as soon possible to avoid interruption to your access.<br><br>                          

                    For any issue related to OCI IAM secret, please reach out to security helpdesk.<br><br>                         
                    Thank you, <br>
                    Security Helpdesk Team <br><br><br>
                    Please do not reply directly to this email. This mailbox is not monitored. If you have any questions regarding this notification, contact your account administrator. <br>
                </p>
            </body>
            </html>
            """
            #recipient = str(user_email).split(",")
            recipient = str(user_email)
            send_email(SUBJECT,secret_client,cfg,BODY_HTML,"",recipient)

        if report_requested :
            day_today = datetime.datetime.strftime(datetime.datetime.now(),"%A")
            date_today = datetime.datetime.strftime(datetime.datetime.now(),"%d")

            recipient = report_recipients
            for item in weekly_report_day:
                SUBJECT = "IAM secret expiry weekly report of users"
                if item.lower() == day_today.lower():

                    logging.getLogger().info('sending weekly report')
                    send_email(SUBJECT,secret_client,cfg,"",report_data,recipient,True)

            for item in monthly_report_day:
                item = f"{int(item):02d}"

                SUBJECT = "IAM secret expiry monthly report of users"
                if item == date_today:
                    logging.getLogger().info('sending monthly report')
                    send_email(SUBJECT,secret_client,cfg,"",report_data,recipient,True)

    # Display an error message if something goes wrong.
    except (Exception, ValueError) as ex:
      logging.getLogger().info('error parsing json payload: ' + str(ex))

    return response.Response(ctx, response_data=json.dumps({"message": "success"}),headers={"Content-Type": "application/json"})