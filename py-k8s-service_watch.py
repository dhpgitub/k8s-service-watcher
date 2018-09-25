#
# This script watches for changes to Kubernetes services.
# It was inspired by the article https://medium.com/programming-kubernetes/building-stuff-with-the-kubernetes-api-part-3-using-python-aea5ab16f627
import os
from kubernetes.config.config_exception import ConfigException
import requests
from kubernetes import client, config, watch
import logging
# from consul import Consul
# Consul.Agent.Service()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(threadName)s - %(levelname)s - %(message)s')

# set the Consul agent URL and other variables
consul_url = "http://servicemesh-consul:8500"
datacenter = "dev"

control_plane_host = "servicemesh-consul"
control_plane_ip = "servicemesh-consul"
kube_Config_File = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'k8s-config', 'k8s-servicewatch-servicemesh-conf'))
def main(k8s_context=None):
    # setup the namespace
    ns = os.getenv("K8S_NAMESPACE")
    if ns is None:
        ns = ""

    # configure client
    config.load_kube_config(config_file=kube_Config_File)
    api = client.CoreV1Api()

    # Setup new watch
    w = watch.Watch()
    logging.info(f"Watching for Kubernetes services for all namespaces")

    for item in w.stream(api.list_service_for_all_namespaces, timeout_seconds=0):
        svc = item['object']
        # get the metadata labels
        labels = svc.metadata.labels
        # look for a label named "registerWithMesh"
        if (labels.get('app',None) if labels else []) == 'servicemesh1':
            register_flag = True
        elif(labels.get('registerWithMesh',None) if labels else []) == "true":
            register_flag = True
        else:
            register_flag = False
        # notify consul about the service
        logging.info(f"service type is {item.get('type')}, {svc.metadata.name}, {register_flag} and {svc.spec.type}")
        try:
            ext_ip = svc.status.load_balancer.ingress[0].ip
        except TypeError as err:
            logging.info("External IP not set for LoadBalancer service")
            ext_ip = None
        if register_flag == True and svc.spec.type in ("NodePort", "ClusterIP"):         
            notify_consul(svc, item['type'], labels)
        elif register_flag == True and svc.spec.type in ("LoadBalancer"):
            if not (ext_ip is None):
                logging.info(f"external ip is not null: {ext_ip}")
                notify_consul(svc, item['type'], labels)
            else:
                logging.info(f"external ip is null: {ext_ip}")
        else:
            logging.info(f"watch stream for new events")

# Notify the Consul agent
def notify_consul(service, action, labels):
    if service.spec.type in("NodePort", "ClusterIP", "LoadBalancer"):
        ports = service.spec.ports
        for port in ports:
            #			print "Port", port
            full_name = service.metadata.namespace + "-" + service.metadata.name + "-" +  (port.name if port.name else "")
            if action == 'ADDED':
                # if action == 'DELETED':
                logging.info(f"Registering new service {full_name}")
                # full_consul_url = consul_url + "/v1/catalog/register"
                full_consul_url = consul_url + "/v1/agent/service/register"
                # determine which port to use depending on the service port type
                if service.spec.type == "NodePort":
                    final_host = service.metadata.name + "." + service.metadata.namespace
                    final_address = service.metadata.name + "." + service.metadata.namespace
                # final_port = port.node_port
                    final_port = port.port
                if service.spec.type == "ClusterIP":
                    final_host = service.spec.cluster_ip + "." + service.metadata.namespace
                    final_address = service.spec.cluster_ip + "." + service.metadata.namespace
                    final_port = port.port
                if service.spec.type == "LoadBalancer":
                    final_host = service.status.load_balancer.ingress[0].ip
                    final_address = service.status.load_balancer.ingress[0].ip
                    final_port = port.port

                consul_json = {
                    "ID": full_name,
                    "Name": full_name,
                    "Tags": [service.metadata.namespace],
                    "Address": final_address,
                    "Port": final_port,
                    "EnableTagOverride": False,
                    "Check": {"DeregisterCriticalServiceAfter": "90m",
                              "HTTP": f"http://{final_address}:{final_port}/{ 'actuator/' if labels.get('framework',None) == 'spring_boot' else ''}health",
                              "Interval": "90s"
                              }
                }
                logging.info(f"request {full_consul_url} {consul_json}")
                html_headers = {"Content-Type": "application/json", "Accept": "application/json"}
                response = requests.put(full_consul_url, json=consul_json, headers=html_headers)
                logging.info(response.status_code)
                if response.status_code != 200:
                    logging.info(f"Status: {response.status_code} Headers: {response.headers} Response content: {response.text}")
            if action == "MODIFIED":
                logging.info(f"Registering new modified {full_name}")
                if service.spec.type == "LoadBalancer":
                    final_host = service.status.load_balancer.ingress[0].ip
                    final_address = service.status.load_balancer.ingress[0].ip
                    final_port = port.port
                consul_json = {
                    "ID": full_name,
                    "Name": full_name,
                    "Tags": [service.metadata.namespace],
                    "Address": final_address,
                    "Port": final_port,
                    "EnableTagOverride": False,
                    "Check": {"DeregisterCriticalServiceAfter": "90m",
                              "HTTP": f"http://{final_address}:{final_port}/health",
                              "Interval": "90s"
                              }
                }
                logging.info(f"request {full_consul_url} {consul_json}")
                html_headers = {"Content-Type": "application/json", "Accept": "application/json"}
                response = requests.put(full_consul_url, json=consul_json, headers=html_headers)
                logging.info(response.status_code)
                if response.status_code != 200:
                    logging.info(
                        f"Status: {response.status_code} Headers: {response.headers} Response content: {response.text}")

            if action == 'DELETED':
                # if action == 'ADDED':
                serviceID = full_name
                logging.info(f"Deregistering {serviceID}")
                full_consul_url = consul_url + "/v1/agent/service/deregister/" + serviceID
                # assemble the Consul API payload
                logging.info(full_consul_url)
                response = requests.put(full_consul_url)
                logging.info(response.status_code)
                if response.status_code != 200:
                    logging.info('Status:', response.status_code, 'Headers:', response.headers, 'Response content:',
                                 response.text)
    else:
        logging.info("Skipping service", service.metadata.name, "becuase it is not a NodePort service type")


if __name__ == '__main__':
    while True:
        logging.info("starting service watcher")
        main()
        logging.info("service watcher stream timed-out and restarting new watchstream")
        
