from .prompt_parser import parse_raw, check_special_tokens, parse_graphllm
from modules.formatter.high_level.formatter_graphllm import RendererGraphLLM
import re

## questa è la parte che non ha bisongno di conoscere il modello

class MultimodalPromptException(Exception):
    pass

class PromptBuilder:

    def __init__(self):

        self.sysprompt = None
        self.custom_default_sysprompt =  False
        self.updated_sysprompt = False
        self.messages = []
        self.last_message = None
        self.serialize_format = "GraphLLM"
        self.reset()


    @staticmethod
    def _check_special_tokens(m):
        is_raw = check_special_tokens(m)
        return is_raw

    def set_param(self,name,val):
        if name == "sysprompt":
             self.sysprompt = val
             self.reset()

    def set_serialize_format(self,format):
        self.serialize_format = format

    def __getattr__(self, attr):
        serialized = self.__str__()
        bar = getattr(serialized, attr)
        return bar

    def _build(self,formatter):
        multimodal_inputs = [el for el in self.messages if isinstance(el["content"],list)]
        if len(multimodal_inputs) > 0:
            raise MultimodalPromptException("Multimodal input not supported by this client")

        text_prompt = formatter.build_prompt(self.messages)
        print(text_prompt, end="")
        return text_prompt

    def to_string(self,format=None):
        if format is None:
            serialize_format = self.serialize_format.lower()
        else:
            serialize_format=format.lower()

        if serialize_format == "graphllm":
            renderer = RendererGraphLLM()
            text_prompt = renderer.build_prompt_j(self.messages)
        elif serialize_format == "text" or serialize_format == "last":
            if self.messages[-1]["role"] == "assistant" and self.last_message is not None:
                text_prompt = self.last_message
            else:
                text_prompt = self.messages[-1]["content"]
        else:
            text_prompt = str(self.messages)

        return text_prompt

    def reset(self):
        self.messages = []
        self.last_message = None
        if self.sysprompt:
            self.messages.append({"role":"system","content":self.sysprompt})
        self.first_prompt = True

    def set_from_raw(self,message):
        self.messages = parse_raw(message)

    def _parse_user_message(self,message_raw, variables):
        role = message_raw["role"]
        content_raw = message_raw["content"]
        content = content_raw

        content_split = re.split(r'({i:[^}]{1,100}})',content_raw)
        content_split = [{"type": "text", "text": el} for el in content_split]
        for el in content_split[1::2]:
            text = el["text"]
            varname = text[3:-1]
            if varname in variables:
                del el["text"]
                el["type"] = "image_url"
                el["image_url"] = {"url": variables[varname]["content"]}
        if len([el for el in content_split if el["type"] != "text"])> 0:
            # merge text_blocks
            for i, el in enumerate(content_split):
                if i == 0:
                    continue
                if content_split[i]["type"] == "text" and content_split[i-1]["type"] == "text":
                    content_split[i]["content"] = content_split[i-1]["content"] + content_split[i]["content"]
                    content_split[i - 1]["content"] = ""

            # remove empty text blocks
            content_split = [el for el in content_split if el["type"] != "text" or el["text"] != "" ]
            content = content_split

        parsed = {"role": role, "content": content}
        return parsed

    def add_request(self, message,role="user",variables={}):
        m = message
        is_raw = self._check_special_tokens(m)
        is_graphllm = message.lstrip().startswith("{p:") or message.lstrip().startswith("{r:")

        if is_graphllm:
            parsed = parse_graphllm(message)
        elif is_raw:
            try:
                parsed = parse_raw(message)
            except:
                parsed = [{"role":"raw","content":str(m)}]
        else:
            parsed = [{"role":role,"content":str(m)}]

        for el in parsed:
            if el["role"] == "raw":
                self.messages = [el]
            elif el["role"] == "system":
                if len(self.messages) > 0 and self.messages[0]["role"] == "system":
                    self.messages[0] = el
                else:
                    self.messages.insert(0,el)
            elif el["role"] == "user":
                message = self._parse_user_message(el,variables)
                self.messages.append(message)
            else:
                self.messages.append(el)

        return self.messages

    def add_response(self,message,role = "assistant"):
        if(self.messages[-1]["role"] == "assistant" and role == "assistant"):
            self.messages[-1]["content"] = self.messages[-1]["content"]  + str(message)
        else:
            self.messages.append({"role":role,"content":str(message)})
        self.last_message = message
        return self.messages

    def get_messages(self):
        return self.messages



if __name__ == "__main__":
    a = PromptBuilder()
    f = open("test/raw.txt","r")
    message = f.read()
    f.close()
    a.set_from_raw(message)
