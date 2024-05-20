from .parser import parse_raw

class Formatter:
    def __init__(self):
        pass
    
    def load_model(self,model_name):
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

            #formatter["row"]=formatter["row1"] + formatter["row2"]

            formatter["enable_system"] = False
            formatter["roles"] = ["raw","user","assistant"]
        elif model_name.lower().startswith("yi"):
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
        elif model_name.startswith("gemma"):
            formatter={}
            formatter["bos"]=""
            formatter["bor"]="<start_of_turn>"
            formatter["eor"]="\n"

            formatter["eom"]="""<end_of_turn>\n"""
            
            formatter["system_name"]="user"
            formatter["user_name"]="user"
            formatter["assistant_name"]="model"
            
            #formatter["row"]=formatter["row1"] + formatter["row2"]

            formatter["enable_system"] = False
            formatter["roles"] = ["raw","user","assistant"]
        else:

            formatter["bos"]="<|begin_of_text|>" ##non capisco
            formatter["bor"]="<|start_header_id|>"
            formatter["eor"]="<|end_header_id|>\n\n"

            formatter["eom"]="""<|eot_id|>"""
            #formatter["row"]=formatter["row1"] + formatter["row2"]
            formatter["roles"] = ["raw","system", "user","assistant"]
            
            formatter["system_name"]="system"
            formatter["user_name"]="user"
            formatter["assistant_name"]="assistant"
        self.f = formatter
        return formatter
    
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
    
    def build_prompt(self,messages):
        formatter = self.f
        skip_bos = False
        skip_final = False
        skip_preamble = -1
        skip_postamble = -1

        if messages[0]["role"] == "raw":
            skip_bos = True
            if len(messages) > 1 and messages[1]["role"] == "assistant":
                skip_preamble = 1
        if messages[-1]["role"] == "raw" or messages[-1]["role"] == "assistant":
            skip_final = True
        if messages[-1]["role"] == "assistant":
            skip_postamble = len(messages) - 1

        prompt=""
        if not skip_bos:
            prompt = formatter["bos"]
        skip_last = False
        for i in range(len(messages)):
            el = messages[i]
            if el["role"] not in formatter["roles"]:
                continue

            if el["role"] == "raw":
                val = self.apply_format_templates(el["content"])
                #print(val,end="")
                prompt = prompt + val
            else:
                if skip_preamble != i:
                    if "role_string" in formatter:
                         prompt = prompt + formatter["role_string"][el["role"]]
                    else:
                         prompt = prompt + formatter["bor"] + (formatter["assistant_name"] if el["role"] == "assistant" else el["role"]) + formatter["eor"]
                prompt = prompt + el["content"]
                if skip_postamble != i:
                    if "role_eom" in formatter:
                        prompt = prompt + formatter["role_eom"][el["role"]]
                    else:
                        prompt = prompt + formatter["eom"]
        if not skip_final:
            if "role_string" in formatter:
                prompt = prompt + formatter["role_string"]["assistant"]
            else:
                prompt = prompt + formatter["bor"] + formatter["assistant_name"] + formatter["eor"]
        #print(prompt)
        return prompt
    



## questa è la parte che non ha bisongno di conoscere il modello
    
class PromptBuilder:
    def __init__(self):
        self.formatter = Formatter()
        self.sysprompt = "You are a helpful assistant"

        self.reset()
    
    def _check_special_tokens(self,m):
        special_tokens = ["{p:bos}","<|START_OF_TURN_TOKEN|>","<BOS_TOKEN>","<|user|>","<|start_header_id|>","{p:user}"]
        is_raw = False
        for el in special_tokens:
            if m.find(el) >= 0:
                is_raw = True
        return is_raw
    
    def _build(self):
        
        text_prompt = self.formatter.build_prompt(self.messages)
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

        #print("-",m)
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
