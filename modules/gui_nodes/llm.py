import yaml
from modules.executors import get_gui_parsers

class GuiNodeParser:

    def __init__(self):
        self.parsers_list = get_gui_parsers()
        self.parsers_list = [el() for el in self.parsers_list]
        parsers_map = {}
        for el in self.parsers_list:
            for t in el.node_types:
                parsers_map[t] = el
        self.parsers_map = parsers_map
        

    def parse_generic(self ,old_config ,links):
        new_config = {}
        new_config["type"] = old_config["type"]
        properties = old_config.get("properties", {})
        parameters = properties.get("parameters", {})
        parameters = yaml.safe_load(parameters)

        for i, el in enumerate(parameters.get("init" ,[])):
            if isinstance(el, dict):
                if len(el) > 0:
                    val = list(el.keys())
                    parameters["init"][i] = "{" + str(val[0]) + "}"
                else:
                    parameters["init"][i] = "{}"
                pass

        if parameters:
            for vel in parameters:
                new_config[vel] = parameters[vel]


        old_inputs = old_config.get("inputs", [])
        new_inputs = [str(el["link"]) if el["link"] else None for el in old_inputs]
        new_inputs = [links[el] if el else None for el in new_inputs]
        new_inputs = [str(el[1]) + "[" + str(el[2]) + "]" if el else None for el in new_inputs]
        val_exec = []
        for vel in new_inputs:
            if not vel:
                break
            val_exec.append(vel)
        new_config["exec"] = val_exec
        return new_config

    def _calc_exec(self ,old_inputs ,links):

        new_inputs = [str(el["link"]) if el["link"] else None for el in old_inputs]
        new_inputs = [links[el] if el else None for el in new_inputs]
        new_inputs = [str(el[1]) + "[" + str(el[2]) + "]" if el else None for el in new_inputs]
        val_exec = []
        for vel in new_inputs:
            if not vel:
                break
            val_exec.append(vel)
        return val_exec



    def parse_file(self ,old_config ,links):
        new_config = {}
        new_config["type"] = "file"
        properties = old_config.get("properties", {})
        template = properties.get("filename", "")
        new_config["init"] = [template]
        conf = properties.get("config", "")
        conf = yaml.safe_load(conf)
        if conf:
            new_config["conf"] = conf
        old_inputs = old_config.get("inputs", [])
        new_config["exec"] = self._calc_exec(old_inputs ,links)
        return new_config

    def parse_list(self ,old_config ,links):
        new_config = {}
        new_config["type"] = "list"
        properties = old_config.get("properties", {})
        template = properties.get("parameters", [])
        new_config["init"] = template

        old_inputs = old_config.get("inputs", [])
        new_config["exec"] = self._calc_exec(old_inputs ,links)
        return new_config

    def parse_connection(self ,old_config ,links):
        new_config = {}
        new_config["type"] = "copy"
        new_config["conf"] = {"subtype" :"input"}
        properties = old_config.get("properties", {})
        subtype = properties.get("subtype", "input")
        if subtype == "output":
            new_config["conf"]["subtype"] = "output"

        old_inputs = old_config.get("inputs", [])
        new_config["exec"] = self._calc_exec(old_inputs ,links)
        return new_config

    def parse_watch(self ,old_config ,links):
        new_config = {}
        new_config["type"] = "copy"

        old_inputs = old_config.get("inputs", [])
        new_config["exec"] = self._calc_exec(old_inputs ,links)
        return new_config

    def parse_scraper(self ,old_config ,links):
        new_config = {}
        new_config["type"] = "exec"

        properties = old_config.get("properties", {})
        address = properties.get("address")
        new_config["init"] = ["python3", "extras/scraper/scrape.py", address]

        old_inputs = old_config.get("inputs", [])
        new_config["exec"] = self._calc_exec(old_inputs ,links)
        return new_config

    def parse_pdf(self ,old_config ,links):
        new_config = {}
        new_config["type"] = "exec"

        properties = old_config.get("properties", {})
        address = properties.get("address")
        new_config["init"] = ["python3", "extras/parse_pdf.py", address]

        old_inputs = old_config.get("inputs", [])
        new_config["exec"] = self._calc_exec(old_inputs ,links)
        return new_config

    def parse_history(self ,old_config ,links):
        new_config = {}
        new_config["type"] = "list"
        properties = old_config.get("properties", {})
        template = properties.get("parameters", [])
        t = ""
        for i ,v in enumerate(template):
            if i == 0:
                t += "{p:system}\n" + v + "{p:eom}\n\n"
            elif i % 2:
                t += "{p:user}\n" + v + "{p:eom}\n\n"
            else:
                t += "{p:assistant}\n" + v + "{p:eom}\n\n"

        new_config["init"] = [t]

        old_inputs = old_config.get("inputs", [])
        new_config["exec"] = []
        return new_config

    def parse_input(self ,old_config ,links):
        new_config = {}
        new_config["type"] = "constant"
        properties = old_config.get("properties", {})
        parameters = properties.get("parameters", "")
        new_config["init"] = [parameters]

        old_inputs = old_config.get("inputs", [])
        new_inputs = [str(el["link"]) if el["link"] else None for el in old_inputs]
        new_inputs = [links[el] if el else None for el in new_inputs]
        new_inputs = [str(el[1]) + "[" + str(el[2]) + "]" if el else None for el in new_inputs]
        val_exec = []
        for vel in new_inputs:
            if not vel:
                break
            val_exec.append(vel)
        new_config["exec"] = val_exec
        return new_config

    def parse_python(self ,old_config ,links):
        new_config = {}
        new_config["type"] = "python"
        properties = old_config.get("properties", {})
        parameters = properties.get("parameters", "")
        new_config["init"] = [parameters]

        old_inputs = old_config.get("inputs", [])
        new_config["exec"] = self._calc_exec(old_inputs, links)
        return new_config

    def parse_tts(self ,old_config ,links):
        new_config = {}
        new_config["type"] = "tts"
        properties = old_config.get("properties", {})
        language = properties.get("language", "it")
        new_config["conf"] = {"lang": language}

        old_inputs = old_config.get("inputs", [])
        new_config["exec"] = self._calc_exec(old_inputs, links)
        return new_config

    def parse_variable(self ,old_config ,links):
        new_config = {}
        new_config["type"] = "variable"
        properties = old_config.get("properties", {})
        parameters = properties.get("parameters", "")

        new_config["conf"] = {"name" :properties["identifier"] ,"value" :properties["parameters"]}

        old_inputs = old_config.get("inputs", [])
        new_inputs = [str(el["link"]) if el["link"] else None for el in old_inputs]
        new_inputs = [links[el] if el else None for el in new_inputs]
        new_inputs = [str(el[1]) + "[" + str(el[2]) + "]" if el else None for el in new_inputs]
        val_exec = []
        for vel in new_inputs:
            if not vel:
                break
            val_exec.append(vel)
        new_config["exec"] = val_exec
        return new_config

    def parse_node(self ,old_config ,links):

        new_config = {}
        new_config["type"] = old_config["type"]
        node_type = old_config["type"].split("/")[-1]
        
        if node_type in self.parsers_map:
            old_inputs = old_config.get("inputs", [])
            new_inputs = [str(el["link"]) if el["link"] else None for el in old_inputs]
            new_inputs = [links[el] if el else None for el in new_inputs]
            old_config["inputs"] = new_inputs
            
            res = self.parsers_map[node_type].parse_node(old_config)
            
            return res
        if node_type in ["generic_node"]:
            return self.parse_generic(old_config ,links)
        if old_config["type"] in ["llm/input"]:
            return self.parse_input(old_config ,links)
        if node_type in ["virtual_sink" ,"virtual_source"]:
            return self.parse_virtual(old_config ,links)
        if old_config["type"].startswith("llm/watch"):
            return None

        if node_type in ["file"]:
            return self.parse_file(old_config ,links)
        if old_config["type"].startswith("llm/list"):
            return self.parse_list(old_config ,links)
        if old_config["type"].startswith("llm/chat_history"):
            return self.parse_history(old_config ,links)
        if node_type in ["variable"]:
            return self.parse_variable(old_config, links)
        if node_type in ["connection"]:
            return self.parse_connection(old_config ,links)
        if node_type in ["web_scraper"]:
            return self.parse_scraper(old_config ,links)
        if node_type in ["pdf_parser"]:
            return self.parse_pdf(old_config ,links)
        if node_type in ["watch"]:
            return self.parse_watch(old_config ,links)
        if node_type in ["python_sandbox"]:
            return self.parse_python(old_config ,links)
        if node_type in ["tts"]:
            return self.parse_tts(old_config ,links)
        return None

    def postprocess_nodes(self,new_nodes):

        for el in self.parsers_list:
            el.postprocess_nodes(new_nodes)


