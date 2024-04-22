import io
import json
import logging
import oci
import base64
from fdk import response
from Cryptodome.PublicKey import RSA

# Get Resource Principal Credentials
signer = oci.auth.signers.get_resource_principals_signer()

# Initialize client
identity_client = oci.identity.IdentityClient(config={}, signer=signer)
onsclient = oci.ons.NotificationDataPlaneClient(config={}, signer=signer)
vault_client = oci.vault.VaultsClient(config={}, signer=signer)

# Get tenancy id and name
tenancy_data = identity_client.get_tenancy(tenancy_id=signer.tenancy_id).data
t_name = str(tenancy_data.name)
t_id = signer.tenancy_id

# Get secret OCID from comments
def get_secret_ocids(comments_items,find_name):
    secret_ocid = ""
    for comment in comments_items:
        if comment.split(":")[0] == find_name:
            secret_ocid = comment.split(":")[1]
    return secret_ocid

# Function to store secret in OCI vault 
def update_secret(vault_client,secret_id,new_value):
    # Base64 encode
    new_token_ascii = new_value.encode("ascii")
    base64_bytes = base64.b64encode(new_token_ascii)
    base64_string = base64_bytes.decode("ascii")

    # Create new version of secret
    vault_client.update_secret(secret_id=secret_id,update_secret_details=oci.vault.models.UpdateSecretDetails(secret_content=oci.vault.models.Base64SecretContentDetails(content_type="BASE64", content=base64_string)))

def handler(ctx, data: io.BytesIO=None):
    try:
        cfg = ctx.Config()
        ons_topic = cfg["ons_topic"]
        body = json.loads(data.getvalue())
        
        # Get common parameters values
        e_time = str(body["eventTime"]).lstrip()
        problem_name = str(body["data"]["additionalDetails"]["problemName"]).lstrip()
        status = "NOT RESOLVED"
        resource_name = str(body["data"]["resourceName"]).lstrip()
        user_ocid = str(body["data"]["additionalDetails"]["problemAdditionalDetails"]["User OCID"]).lstrip()
        target_resource_name = str(body["data"]["additionalDetails"]["resourceName"]).lstrip()
        target_resource_id = str(body["data"]["additionalDetails"]["resourceId"]).lstrip()
        risk_level = str(body["data"]["additionalDetails"]["riskLevel"]).lstrip()
        comments = str(body["data"]["additionalDetails"]["problemAdditionalDetails"]["comments"]).lstrip()
        comments_items = comments.split(",")
        additional_details = "\r\r\nAction : Closure comments was not in required format hence, no action by automation."
        
        try:
            # Check Problem Type
            if problem_name == "PASSWORD_TOO_OLD":
                identity_client.create_or_reset_ui_password(user_id=user_ocid)
                additional_details = "\r\r\nAction : Your password has been reset by the System Administrator as per password policy rotation. Please set new password by clicking on forgot password from OCI console. "
                status = "RESOLVED"

            elif problem_name == "AUTH_TOKEN_TOO_OLD":
                auth_secret_ocid = get_secret_ocids(comments_items,"auth_secret_ocid")
                if auth_secret_ocid != "":
                    # Delete existing auth token
                    identity_client.delete_auth_token(user_id=user_ocid, auth_token_id=target_resource_id)
                    # Create new auth token
                    create_auth_token_response = identity_client.create_auth_token(
                    create_auth_token_details=oci.identity.models.CreateAuthTokenDetails(description=target_resource_name),user_id=user_ocid).data
                    new_value = create_auth_token_response.token
                    # Store new auth token in vault secret
                    update_secret(vault_client,auth_secret_ocid,new_value)
                    additional_details = '\r\nAuth Token - Secret OCID : ' + auth_secret_ocid
                    status = "RESOLVED"

            elif problem_name == "SECRET_KEY_TOO_OLD":
                access_id_secret_ocid = get_secret_ocids(comments_items, "accesskey_secret_ocid")
                secret_key_secret_ocid = get_secret_ocids(comments_items, "secretkey_secret_ocid")
                if access_id_secret_ocid != "" and secret_key_secret_ocid != "":
                    # Delete existing customer secrete key
                    delete_secret_key_response = identity_client.delete_customer_secret_key(user_ocid, target_resource_id).data
                    # Create new customer secret key
                    create_customer_secret_key_response = identity_client.create_customer_secret_key(create_customer_secret_key_details=oci.identity.models.CreateCustomerSecretKeyDetails(display_name=target_resource_name),user_id=user_ocid).data
                    new_secret_key = str(create_customer_secret_key_response.key)
                    new_access_key_id = str(create_customer_secret_key_response.id)
                    # Store new customer secret key in vault secret
                    update_secret(vault_client,secret_key_secret_ocid,new_secret_key)
                    update_secret(vault_client,access_id_secret_ocid,new_access_key_id)
                    additional_details = '\r\nAccess Key - Secret OCID : ' + access_id_secret_ocid + \
                           '\r\nSecret Key - Secret OCID : ' + secret_key_secret_ocid
                    status = "RESOLVED"

            elif problem_name == "API_KEY_TOO_OLD":
                key_fingerprint = target_resource_id.split("/")[2]
                api_secret_ocid = get_secret_ocids(comments_items,"api_secret_ocid")
                if api_secret_ocid != "":
                    key = RSA.generate(2048)
                    key_private = key.exportKey()
                    pubkey = key.publickey()
                    key_public = pubkey.exportKey()
                    # Delete existing API key
                    delete_api_key_response = identity_client.delete_api_key(user_id=user_ocid,fingerprint=key_fingerprint)
                    # Upload new public API key in OCI for the user
                    upload_api_key_response = identity_client.upload_api_key(user_id=user_ocid,
                                                                             create_api_key_details=oci.identity.models.CreateApiKeyDetails(
                                                                                 key=key_public.decode()))
                    # Store content of new private key in vault secret
                    update_secret(vault_client,api_secret_ocid,key_private.decode())
                    additional_details = '\r\nSecret OCID for private API key : ' + api_secret_ocid
                    status = "RESOLVED"
        except Exception as e:
            additional_details = '\r\r\n Error: '+ str(e)

        # Message Body Customization, it can be updated as per need
        line_head = 'Oracle Cloud Notification' + '\n====================='
        message_body = line_head + \
                       '\r\r\nProblem Name : ' + problem_name + \
                       '\r\r\nRisk Level : ' + risk_level + \
                       '\r\nEvent Time : ' + e_time + \
                       '\r\nTenancy Name : ' + t_name + \
                       '\r\nTenancy ID : ' + t_id + \
                       '\r\r\nAdditional Details : ' + '\n-------------------------' \
                       '\r\nResource Name : ' + target_resource_name + \
                       '\r\nResource ID : ' + target_resource_id + \
                       '\r\nResource User OCID : ' + user_ocid + ' ' + additional_details

        # Message Title
        message_title = 'Problem : ' + resource_name + ' | ' + status +' by automation '

        # Message Detail
        message_details = oci.ons.models.MessageDetails(body=message_body, title=message_title)
        
        # Publish message to ONS
        onsclient.publish_message(ons_topic, message_details)

    except (Exception, ValueError) as ex:
        logging.getLogger().info('error parsing json payload: ' + str(ex))
        
    return response.Response(ctx, response_data=json.dumps({"message": "success"}),headers={"Content-Type": "application/json"})
