import requests, logging, time, os
from kubernetes import client, config, watch
from consul_reg_payload import Consul_payload

wait_time = int(os.environ.get("wait_time",60))
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(threadName)s - %(levelname)s - %(message)s')
# set the Consul agent URL and other variables
consul_url = "http://servicemesh-consul:8500"
datacenter = "dev"

control_plane_host = "servicemesh-consul"
control_plane_ip = "servicemesh-consul"

def consul_get_all_svc(consul_host = None):
    logging.info("Retrieving list of all registered services")
    response = requests.get(consul_host + "/v1/catalog/services")
    if response.status_code != 200:
        logging.info('Status:', response.status_code, 'Headers:', response.headers, 'Response content:',
                     response.text)
        return {'services': []}
    else:
        response = response.json()
        return {'services': list(response.keys()).remove('consul')}

def main():
    consul_svcs = consul_get_all_svc(consul_host=consul_url).get('services')
    config.load_incluster_config()
    api = client.CoreV1Api()
    all_endpoints = api.list_endpoints_for_all_namespaces().items
    payload = Consul_payload(Name='default-ms-name-normalization-all-ops')
    k8s_svcs = []
    for i in all_endpoints:
        labels = i.metadata.labels
        if (labels.get('registerWithMesh', None) if not(labels is None) else []) == "true":
            register_flag = True
        else:
            register_flag = False
        if register_flag and (not i.subsets is None):
            tags = [v for k, v in labels.items() if k in ['app', 'appLanguage', 'framework']]
            for port in i.subsets[0].ports:
                full_name = i.metadata.namespace + "-" + i.metadata.name + "-" + (
                    port.name if port.name else "")
                k8s_svcs.append(full_name)
                svc = [{'Service': full_name, 'Address': d.ip, 'Port': port.port, 'ID': d.target_ref.uid}
                       for d in i.subsets[0].addresses]
                for s in svc:
                    payload.Name = s['Service']
                    payload.Address = s['Address']
                    payload.ID = s['ID']
                    payload.Port = s['Port']
                    payload.Tags = tags
                    payload.setCheck(health=f"{ 'actuator/' if labels.get('framework',None) == 'spring_boot' else ''}health")
                    html_headers = {"Content-Type": "application/json", "Accept": "application/json"}
                    response = requests.put(url=consul_url + "/v1/agent/service/register", json=payload.__dict__, headers=html_headers)
                    logging.info(f"{'Skipping service ' + full_name + ' error from Consul' if response.status_code!=200 else 'Registered service '+ full_name}")

    # Deregister all services from Consul that are not running in k8s
    if consul_svcs:
        for service in consul_svcs:
            if service not in k8s_svcs:
                response = requests.put(consul_url + "/v1/agent/service/deregister/" + service)
                logging.info(
                    f"{'Skipping service ' + service + ' error from Consul' if response.status_code!=200 else 'Deregistered service ' + service}")


if __name__ == '__main__':
    while True:
        main()
        time.sleep(60)
