import requests
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(threadName)s - %(levelname)s - %(message)s')

def consul_deregister_all(consul_host = None):
    logging.info("Retrieving list of all registered services")
    response = requests.get(consul_host + "/v1/agent/services")
    if response.status_code != 200:
        logging.info('Status:', response.status_code, 'Headers:', response.headers, 'Response content:',
                     response.text)
    response = response.json()
    all_consul_svc = list(response.keys())
    for svc in all_consul_svc:
        response = requests.put(consul_host + "/v1/agent/service/deregister/" + svc)
        if response.status_code != 200:
            logging.info('Status:', response.status_code, 'Headers:', response.headers, 'Response content:',
                         response.text)
        else:
            logging.info(f"Deregisterd service {svc}")

