from modules.executors.common import BaseGuiParser


class ListParserNode(BaseGuiParser):
    node_types = ["list"]

    def parse_node(self, old_config):
        new_config = {}
        new_config["type"] = "list"
        properties = old_config.get("properties", {})
        template = properties.get("parameters", [])
        new_config["init"] = template

        old_inputs = old_config.get("inputs", [])
        new_config["exec"] = self._calc_exec(old_inputs)

        return new_config

    def postprocess_nodes(self, new_nodes):
        pass
