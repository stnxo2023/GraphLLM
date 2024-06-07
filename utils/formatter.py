from .parser import parse_raw, check_special_tokens
from transformers import AutoTokenizer
import copy

class Formatter:
    def __init__(self):
        self.hf_formatter = None

    def load_hf_model(self,model_name):

        if model_name.lower().startswith("phi"):
            tokenizer_path = "tokenizers/phi"
        elif model_name.lower().startswith("glm"):
            tokenizer_path = "tokenizers/glm-chat"
        elif model_name.lower().startswith("qwen2"):
            tokenizer_path = "tokenizers/Qwen2"
        else:
            return None
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, trust_remote_code=True)
        self.tokenizer = tokenizer
        return tokenizer

    def load_custom_model(self,model_name):
#        print("Model name:",model_name)
        formatter={}
        formatter["enable_system"] = True
        if model_name.find("c4ai-command-r") >= 0:
            formatter={}
            formatter["bos"]=""
            formatter["bor"]="<|START_OF_TURN_TOKEN|><|"
            formatter["eor"]="_TOKEN|>"

            formatter["eom"]="<|END_OF_TURN_TOKEN|>"

            formatter["system_name"]="SYSTEM"
            formatter["user_name"]="USER"
            formatter["assistant_name"]="CHATBOT"


            formatter["enable_system"] = False
            formatter["roles"] = ["raw","user","assistant"]
        elif model_name.lower().find("yuan") >= 0:
            formatter={}
            formatter["bos"]=""
            formatter["bos"]=""
            formatter["bor"]=""
            formatter["eor"]=""

            formatter["eom"]="\n"

            formatter["system_name"]=""
            formatter["user_name"]="Instruction: "
            formatter["assistant_name"]="Response:\n"
            formatter["role_string"] = {"user":"","assistant":"","system":""}
            formatter["role_eom"] = {"user":"<sep>","assistant":"","system":"\n"} 
            formatter["enable_system"] = False
            formatter["roles"] = ["raw","system","user","assistant"]
        elif model_name.lower().find("platypus-yi") >= 0:
            formatter={}
            formatter["bos"]=""
            formatter["bos"]=""
            formatter["bor"]=""
            formatter["eor"]=""

            formatter["eom"]="\n"

            formatter["system_name"]="system"
            formatter["user_name"]="user"
            formatter["assistant_name"]="assistant"
            formatter["role_string"] = {"user":"USER: ","assistant":"ASSISTANT: ","system":""}
            formatter["role_eom"] = {"user":"\n","assistant":"\n","system":"\n"} 

            formatter["enable_system"] = True
            formatter["roles"] = ["raw","system","user","assistant"]
        elif model_name.lower().find("deepseek") >= 0:
            formatter={}
            formatter["bos"]="<｜begin▁of▁sentence｜>"
            formatter["bor"]=""
            formatter["eor"]=""

            formatter["eom"]="\n"

            formatter["system_name"]="system"
            formatter["user_name"]="user"
            formatter["assistant_name"]="assistant"
            formatter["role_string"] = {"user":"User: ","assistant":"Assistant: ","system":""}
            formatter["role_eom"] = {"user":"\n\n","assistant":"<｜end▁of▁sentence｜>","system":"\n\n"} 

            formatter["enable_system"] = True
            formatter["roles"] = ["raw","system","user","assistant"]
        elif model_name.lower().startswith("internlm"):
            formatter={}
            formatter["bos"]="<s>"
            formatter["bor"]="<|im_start|>"
            formatter["eor"]="\n"

            formatter["eom"]="<|im_end|>\n"

            formatter["system_name"]="system"
            formatter["user_name"]="user"
            formatter["assistant_name"]="assistant"
            #formatter["role_string"] = {"user":"<|im_start|>user\n","assistant":"<|im_start|>assistant\n","system":""}
            #formatter["role_eom"] = {"user":"<|im_end|>\n","assistant":"<|im_end|>\n","system":""} 

            formatter["enable_system"] = True
            formatter["roles"] = ["raw","system","user","assistant"]
        elif model_name.lower().startswith("yi") or model_name.lower().startswith("faro"):
            formatter={}
            formatter["bos"]="<|startoftext|>"
            formatter["bos"]=""
            formatter["bor"]="<|im_start|>"
            formatter["eor"]="\n"

            formatter["eom"]="<|im_end|>\n"

            formatter["system_name"]="system"
            formatter["user_name"]="user"
            formatter["assistant_name"]="assistant"
            #formatter["role_string"] = {"user":"<|im_start|>user\n","assistant":"<|im_start|>assistant\n","system":""}
            #formatter["role_eom"] = {"user":"<|im_end|>\n","assistant":"<|im_end|>\n","system":""} 

            formatter["enable_system"] = True
            formatter["roles"] = ["raw","system","user","assistant"]
        elif model_name.lower().startswith("wizardlm"):
            formatter={}
            formatter["bos"]=""
            formatter["bos"]=""
            formatter["bor"]=""
            formatter["eor"]=""

            formatter["eom"]="\n"

            formatter["system_name"]="system"
            formatter["user_name"]="user"
            formatter["assistant_name"]="assistant"
            formatter["role_string"] = {"user":"USER: ","assistant":"ASSISTANT: ","system":""}
            formatter["role_eom"] = {"user":" ","assistant":"</s>","system":" "} 

            formatter["enable_system"] = True
            formatter["roles"] = ["raw","system","user","assistant"]
        elif model_name.lower().startswith("mistral") or model_name.lower().startswith("mixtral"):
            formatter={}
            formatter["bos"]=""
            formatter["bor"]=""
            formatter["eor"]=""

            formatter["eom"]=""

            formatter["system_name"]="system"
            formatter["user_name"]="user"
            formatter["assistant_name"]="assistant"
            formatter["role_string"] = {"user":"[INST]_","assistant":"","system":"[INST]"}
            formatter["role_eom"] = {"user":"[/INST]","assistant":"","system":"[/INST]"} 

            formatter["enable_system"] = False
            formatter["roles"] = ["raw","user","assistant"]
        elif model_name.startswith("gemma"):
            formatter={}
            formatter["bos"]=""
            formatter["bor"]="<start_of_turn>"
            formatter["eor"]="\n"

            formatter["eom"]="""<end_of_turn>\n"""
            formatter["system_name"]="user"
            formatter["user_name"]="user"
            formatter["assistant_name"]="model"

            formatter["enable_system"] = False
            formatter["roles"] = ["raw","user","assistant"]
        elif model_name.lower().startswith("phi"):
            formatter={}
            formatter["bos"]="<s>"
            if model_name.lower().find("medium") >= 0:
                formatter["bos"]="<s>"
            formatter["bor"]="<|"
            formatter["eor"]="|>\n"
            formatter["lf"] = "<0x0A>"
            formatter["eom"]="""<|end|>\n"""
            formatter["system_name"]="user"
            formatter["user_name"]="user"
            formatter["assistant_name"]="assistant"

            formatter["enable_system"] = False
            formatter["roles"] = ["raw","user","assistant"]
            formatter["role_eom"] = {"user":"<|end|>\n","assistant":"<|end|>\n","system":"\n\n"}
        else: #llama

            formatter["bos"]="<|begin_of_text|>" ##non capisco
            #formatter["bos"]=""
            formatter["bor"]="<|start_header_id|>"
            formatter["eor"]="<|end_header_id|>\n\n"

            formatter["eom"]="""<|eot_id|>"""
            #formatter["row"]=formatter["row1"] + formatter["row2"]
            formatter["roles"] = ["raw","system", "user","assistant"]
            formatter["system_name"]="system"
            formatter["user_name"]="user"
            formatter["assistant_name"]="assistant"

        return formatter

    def load_model(self,model_name):
        self.hf_formatter = self.load_hf_model(model_name)
        self.f = self.load_custom_model(model_name)

    def build_hf_prompt(self,messages,force_system=False):
        # se il primo è raw, allora salva così com'è
        #     se il secondo è presente e assistant, appendi senza preamble?
        # se l'ultimo è raw o assistant allora non mettere il generation token
        # se l'ultimo è raw o assistant non mettere eom
        # se il primo è system e manca il system, allora attaccalo al primo
        messages = copy.deepcopy(messages)
        has_system = True
        try:
            has_system = self.tokenizer.chat_template.find("system") >= 0
        except:
            pass

        if messages[0]["role"] == "system" and not has_system:
            messages[0]["role"] = "user"
            if len(messages) > 1:
                messages[1]["content"] = messages[0]["content"]+"\n\n" + messages[1]["content"]
                messages = messages[1:]

        assistant_prompt = None
        if messages[-1]["role"] == "assistant":
            assistant_prompt = messages[-1]["content"]
            messages = messages[:-1]

        raw_prompt = None
        if messages[0]["role"] == "raw":
            raw_prompt = messages[0]["content"]
            #messages = messages[1:]

        if raw_prompt is None:
            input_string = self.tokenizer.apply_chat_template(messages, add_special_tokens=True, add_generation_prompt=True, tokenize=False)
        else:
            if len(messages) == 1:
                input_string = raw_prompt
            else:
                assistant_response = messages[1]["content"]
                placeholder_string="<<<<|>>>>PLACEHOLDER<<<|>>>"
                messages[0]["role"] ="user"
                messages[0]["content"]="AAAA"
                messages[1]["content"]=placeholder_string
                input_string = self.tokenizer.apply_chat_template(messages, add_special_tokens=True, add_generation_prompt=True, tokenize=False)

                el = input_string.find(placeholder_string)+len(placeholder_string)
                input_string = raw_prompt + assistant_response+input_string[el:]

        if assistant_prompt is not None:
            input_string = input_string + assistant_prompt

        return input_string

    def apply_format_templates(self, prompt):
        formatter = self.f
        a = prompt
        system_name = "system"
        if not formatter["enable_system"]:
            system_name = "user"
        a = a.replace("{p:bos}\n",formatter["bos"])
        a = a.replace("{p:bos}",formatter["bos"])
        a = a.replace("\n{p:system}\n",formatter["bor"]+formatter["system_name"]+formatter["eor"])
        a = a.replace("{p:eom}\n",formatter["eom"])
        a = a.replace("\n{p:user}\n",formatter["bor"]+formatter["user_name"]+formatter["eor"])
        a = a.replace("\n{p:assistant}\n",formatter["bor"]+formatter["assistant_name"]+formatter["eor"])
        return a
    
    def build_prompt(self,messages,force_system=False):
        if self.hf_formatter is not None:
            return self.build_hf_prompt(messages)


        formatter = self.f
        skip_bos = False
        skip_final = False
        modifiers = [ {"skip_preamble":False,"skip_postamble":False} for el in messages]

        if messages[0]["role"] == "raw":
            skip_bos = True
            if len(messages) > 1 and messages[1]["role"] == "assistant":
                modifiers[1]["skip_preamble"] = True
        if messages[-1]["role"] == "raw" or messages[-1]["role"] == "assistant":
            skip_final = True
        if messages[-1]["role"] == "assistant":
            modifiers[-1]["skip_postamble"] = True
            skip_postamble = len(messages) - 1
        if messages[0]["role"] == "system" and len(messages) > 1 and force_system:
            #modifiers[0]["skip_postamble"] = True
            modifiers[1]["skip_preamble"] = True

        prompt=""
        if not skip_bos:
            prompt = formatter["bos"]
        skip_last = False
        for i in range(len(messages)):
            el = messages[i]
            if el["role"] not in formatter["roles"]:
                if el["role"] == "system" and force_system:
                     pass
                else:
                     continue

            if el["role"] == "raw":
                val = self.apply_format_templates(el["content"])
                #print(val,end="")
                prompt = prompt + val
            else:
                if not modifiers[i]["skip_preamble"]:
                    if "role_string" in formatter:
                         prompt = prompt + formatter["role_string"][el["role"]]
                    else:
                         role_name = formatter["assistant_name"] if el["role"] == "assistant" else el["role"]
                         role_name = formatter["system_name"] if el["role"] == "system" else role_name
                         role_name = formatter["user_name"] if el["role"] == "user" else role_name
                         prompt = prompt + formatter["bor"] + role_name + formatter["eor"]
                prompt = prompt + el["content"]
                if not modifiers[i]["skip_postamble"]:
                    if "role_eom" in formatter:
                        prompt = prompt + formatter["role_eom"][el["role"]]
                    else:
                        prompt = prompt + formatter["eom"]
        if not skip_final:
            if "role_string" in formatter:
                prompt = prompt + formatter["role_string"]["assistant"]
            else:
                prompt = prompt + formatter["bor"] + formatter["assistant_name"] + formatter["eor"]
        if "lf" in formatter:
            pass
            #prompt = prompt.replace("\n",formatter["lf"])
#        print(prompt)
        return prompt
    



## questa è la parte che non ha bisongno di conoscere il modello

class PromptBuilder:
    def __init__(self):
        self.formatter = Formatter()
        self.sysprompt = "You are a helpful assistant"
        self.force_system=False
        self.reset()
    
    def _check_special_tokens(self,m):
        is_raw = check_special_tokens(m)
        return is_raw
 
    def set_param(self,name,val):
        if name== "force_system":
             self.force_system = val

    def _build(self):

        text_prompt = self.formatter.build_prompt(self.messages,force_system=self.force_system)
#        print(text_prompt)
        return text_prompt

    def load_model(self,model_name):
        self.formatter.load_model(model_name)

    def reset(self):
        self.messages = []
        self.messages.append({"role":"system","content":self.sysprompt})
        self.first_prompt = True

    def set_from_raw(self,message):
        self.messages = parse_raw(message)

    def add_request(self, message):
        m = message
        is_raw = self._check_special_tokens(m)

        if  is_raw:
            try:
                self.messages = parse_raw(message)
            except:
                self.messages = [{"role":"raw","content":str(m)}]
        else:
            self.messages.append({"role":"user","content":str(m)})
        #print(self.messages)
        return self.messages

    def add_response(self,message):
        if(self.messages[-1]["role"] == "assistant"):
            self.messages[-1]["content"] = self.messages[-1]["content"]  + str(message)
        else:
            self.messages.append({"role":"assistant","content":str(message)})
        return self.messages
        



if __name__ == "__main__":
    a = PromptBuilder()
    f = open("test/raw.txt","r")
    message = f.read()
    f.close()
    a.set_from_raw(message)
