import requests
import yaml
import os.path

SERVER_ADDR = "http://localhost:5000/api"
DOC_ROOT = "./doc/"
DOC_TEMPLATE = {
    "responses": {
        "200": {
            "content": {
                "application/vnd.mason+json": {
                    "example": {}
                }
            }
        }
    }
}
endPointName = "insights"
resp_json = requests.get(SERVER_ADDR + "/insights/?usr=test3").json()
DOC_TEMPLATE["responses"]["200"]["content"]["application/vnd.mason+json"]["example"] = resp_json
with open(os.path.join(DOC_ROOT, f"{endPointName}/get.yml"), "w") as target:
    target.write(yaml.dump(DOC_TEMPLATE, default_flow_style=False))