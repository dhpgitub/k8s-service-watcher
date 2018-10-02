class Consul_payload:
    def __init__(self, ID=None, Name=None, Address=None, Tags=[], port=None, deregisterCriticalServiceAfter="90s", interval="90s"):
        self.Name = Name
        self.ID = Name
        self.Address = Address
        self.Port = port
        self.Tags = Tags
        self.EnableTagOverride = False
        self.Check = {'DeregisterCriticalServiceAfter': deregisterCriticalServiceAfter,
                      'HTTP': f"http://{self.Address}:{self.Port}/health",
                      "Interval": interval
                      }

    def setCheck(self, deregisterCriticalServiceAfter="90s", interval="90s", health=""):
        self.Check = {'DeregisterCriticalServiceAfter': deregisterCriticalServiceAfter,
                      'HTTP': f"http://{self.Address}:{self.Port}/{health}",
                       "Interval": interval
                     }
