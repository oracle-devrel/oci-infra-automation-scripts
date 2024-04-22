# This is a sample python script to post disk utilization custom metric to oci monitoring.
# Command: python disk_usage.py
   
import oci,psutil,datetime
from pytz import timezone
   
# initialize service client with OCI python SDK
signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
monitoring_client = oci.monitoring.MonitoringClient(config={}, signer=signer, service_endpoint="https://telemetry-ingestion.ap-mumbai-1.oraclecloud.com")
   
# get disk usage with psutil
disk = psutil.disk_usage('/')
disk_usage=disk.percent
print(disk_usage)
   
times_stamp = datetime.datetime.now(timezone('UTC'))
   
# post custom metric to oci monitoring
# replace "compartment_ocid“ with your compartmet ocid and srv01 with your compute instance
post_metric_data_response = monitoring_client.post_metric_data(
   post_metric_data_details=oci.monitoring.models.PostMetricDataDetails(
      metric_data=[
            oci.monitoring.models.MetricDataDetails(
               namespace="custom_metrics",
               compartment_id="your_compartment_ocid",
               name="disk_usage",
               dimensions={'resourceDisplayName': 'srv01'},
               datapoints=[
                  oci.monitoring.models.Datapoint(
                        timestamp=datetime.datetime.strftime(
                           times_stamp,"%Y-%m-%dT%H:%M:%S.%fZ"),
                        value=disk_usage)]
               )]
   )
)
   
# Get the data from response
print(post_metric_data_response.data)
