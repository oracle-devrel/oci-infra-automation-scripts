import io
import json
import logging
import oci
from fdk import response

# Get Resource Principal Credentials
signer = oci.auth.signers.get_resource_principals_signer()

identity_client = oci.identity.IdentityClient(config={}, signer=signer)

def process_users(user,identity_domains_client,tag_namespace,manage_capability,execution_mode):
   change_in_capability = {}
   tag_capability = {}
   user_ocid = user.ocid
   tags = {}
   if hasattr(user,"urn_ietf_params_scim_schemas_oracle_idcs_extension_oci_tags"):
      if hasattr(user.urn_ietf_params_scim_schemas_oracle_idcs_extension_oci_tags,"defined_tags"):
         tags = user.urn_ietf_params_scim_schemas_oracle_idcs_extension_oci_tags.defined_tags
   for tag in tags:
      if tag.namespace == tag_namespace:
         tag_capability.update({tag.key: tag.value})

   capabilities = user.urn_ietf_params_scim_schemas_oracle_idcs_extension_capabilities_user
   attribute_dict = capabilities.attribute_map

   # Loop through input configuration
   for tag_key in manage_capability:
      key = "can_use_" + tag_key
      if ("disable" in execution_mode.lower()) and ((getattr(capabilities, key)) and (not tag_key in tag_capability.keys())):
         # print("changing value " + tag_key)
         change_in_capability.update({attribute_dict[key]: False})
      # Uncomment below line to enable capability through this script
      elif ("enable" in execution_mode.lower()) and ((not getattr(capabilities,key)) and (tag_key in tag_capability.keys())):
         change_in_capability.update({attribute_dict[key] : True})

   if change_in_capability:
      logging.getLogger().info(f'Change in capability for user {user.user_name}')
      patch_ops = oci.identity_domains.models.PatchOp()
      patch_ops.schemas = ["urn:ietf:params:scim:api:messages:2.0:PatchOp"]

      patch_ops_operations = []
      for k, v in change_in_capability.items():
         patch_ops_operations.append(oci.identity_domains.models.Operations(
            op="REPLACE",
            path="urn:ietf:params:scim:schemas:oracle:idcs:extension:capabilities:User:" + k,
            value=v
         )
         )
      patch_ops.operations = patch_ops_operations
      identity_domains_client.patch_user(user_id=user_ocid, patch_op=patch_ops)


def handler(ctx, data: io.BytesIO=None):
   try:
      # Extracting values from triggered OCI event
      domain_endpoints = []
      payload = False
      cfg = ctx.Config()
      manage_capability = cfg["manage_capability"].split(",")
      execution_mode = cfg["execution_mode"].strip()
      tag_namespace = cfg["tag_namespace"].strip()

      try:
         body = json.loads(data.getvalue())
         user_ocid = str(body["data"]["resourceId"]).lstrip()
         details = body["data"]["additionalDetails"]
         domain_ocid = str(details["domainId"]).lstrip()
         domain_ocids= [domain_ocid]
         payload = True
         logging.getLogger().info(f'Fixing capabilities for new user {user_ocid} ')
      except Exception as ex:
         logging.getLogger().info(ex)
         domain_ocids = cfg["domain_ocids"].split(",")

      for ocid in domain_ocids:
         logging.getLogger().info(f'Processing domain ocid {str(ocid)} ')
         domain_data = identity_client.get_domain(domain_id=ocid).data
         url = domain_data.url
         domain_endpoint = (url.split(":443"))[0]
         domain_endpoints.append(domain_endpoint)

      for domain_endpoint in domain_endpoints:

         identity_domains_client = oci.identity_domains.IdentityDomainsClient(config={}, signer=signer,
                                                                           service_endpoint=domain_endpoint
                                                                           )

         if payload:
            users = [identity_domains_client.get_user(user_ocid).data]
         else:
            list_users_response = identity_domains_client.list_users()
            users = list_users_response.data.resources
            while list_users_response.has_next_page:
               list_users_response = identity_domains_client.list_users(page=list_users_response.next_page)
               users.extend(list_users_response.data.resources)
         count = 0

         for user in users:
            process_users(user, identity_domains_client,tag_namespace,manage_capability,execution_mode)
            count += 1

      logging.getLogger().info(f'Processed {str(count)} users....')


   except (Exception, ValueError) as ex:
      logging.getLogger().info('error parsing json payload: ' + str(ex))

   return response.Response(ctx, response_data=json.dumps({"message": "success"}),headers={"Content-Type": "application/json"})