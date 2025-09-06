import sys

from piper import PiperVoice
from piper.voice import AudioChunk
from piper.download_voices import VOICES_JSON,download_voice
from urllib.request import urlopen

from pathlib import Path
import logging
import os
import wave
import io
import json
#python3 -m modules.executors.tts.parla |aplay -r 16000 -f S16_LE -t raw -

PIPER_DIR = os.path.dirname(__file__)

class EngineTTS:
    def __init__(self):
        self.download_dir = PIPER_DIR
        self.synthesizer = None

    def load_voice(self, language):

        if os.path.exists(PIPER_DIR + "/voices.json"):
            with open(PIPER_DIR + "/voices.json") as f:
                voices_s = f.read()
                all_voices = json.loads(voices_s)
        else:
            with urlopen(VOICES_JSON) as response:
                all_voices = json.loads(response.fp.read())
                with open(PIPER_DIR + "/voices.json", "w") as f:
                    f.write(json.dumps(all_voices, indent=4))
        filtered_voices = [el for el in all_voices if el.startswith(language)]
        selected_voice = filtered_voices[0]
        #ensure_voice_exists(selected_voice,[self.download_dir],self.download_dir,all_voices)
        self.selected_voice = selected_voice
        download_voice(selected_voice,Path(self.download_dir))
        self.synthesizer = PiperVoice.load(self.download_dir + "/" + selected_voice + ".onnx", config_path=None, use_cuda=False)
        
        return selected_voice

    def read_line(self, text):
        synthesize_args = {'speaker_id': None, 'length_scale': None, 'noise_scale': None, 'noise_w': None, 'sentence_silence': 0.7}
        audio_stream = self.synthesizer.synthesize_stream_raw(line, **synthesize_args)
        
        return audio_stream
    
    def read_text(self,text,sentence_silence=0.8):
        sentence_phonemes = self.synthesizer.phonemize(text)
        num_silence_samples = int(sentence_silence * self.synthesizer.config.sample_rate)
        silence_bytes = bytes(num_silence_samples * 2)
        synthesize_args = {'speaker_id': None, 'length_scale': None, 'noise_scale': None, 'noise_w': None}
        for phonemes in sentence_phonemes:
            #print("processing: ", "".join(phonemes), file=sys.stderr)
            phoneme_ids = self.synthesizer.phonemes_to_ids(phonemes)
            yield self.synthesizer.phoneme_ids_to_audio(phoneme_ids) + silence_bytes

    def phonemize(self,text):
        sentence_phonemes = self.synthesizer.phonemize(text)
        return sentence_phonemes

    def read_phonemized_to_buffer(self,phonemes,sentence_silence=0.8):
        num_silence_samples = int(sentence_silence * self.synthesizer.config.sample_rate)
        silence_bytes = bytes(num_silence_samples * 2)
        synthesize_args = {'speaker_id': None, 'length_scale': None, 'noise_scale': None, 'noise_w': None}
        phoneme_ids = self.synthesizer.phonemes_to_ids(phonemes)
        audio_floats = self.synthesizer.phoneme_ids_to_audio(phoneme_ids)

        audio_chunk = AudioChunk(
                sample_rate=self.synthesizer.config.sample_rate,
                sample_width=2,
                sample_channels=1,
                audio_float_array=audio_floats,
            )

        with io.BytesIO() as dest, wave.open(dest, "wb") as f:
            f.setnchannels(1)
            # 2 bytes per sample.
            f.setsampwidth(2)
            f.setframerate(self.synthesizer.config.sample_rate)
            f.writeframes(audio_chunk.audio_int16_bytes)
            f.writeframes(silence_bytes)
            val = dest.getvalue()
        return val

    def read_text_to_buffers(self,line,sentence_silence=0.8):
        for audio_bytes in self.read_text(line):
            with io.BytesIO() as dest, wave.open(dest, "wb") as f:
                f.setnchannels(1)
                # 2 bytes per sample.
                f.setsampwidth(2)
                f.setframerate(self.synthesizer.config.sample_rate)
                f.writeframes(audio_bytes)
                val = dest.getvalue()
            yield val

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    engine = EngineTTS()
    selected_voice = engine.load_voice("it_IT-riccardo-x_low")

    lines = [
        "Da decenni il Libano fa i conti con una situazione politica, economica e sociale molto precaria, e al momento il paese non avrebbe i soldi né le risorse necessarie per rispondere a un’emergenza di questa portata. La situazione è diventata ancora più instabile in seguito all’uccisione da parte di Israele di Hassan Nasrallah, il leader del gruppo militare e politico libanese Hezbollah, avvenuta venerdì scorso con un bombardamento sulla capitale Beirut. "
        ]

    line = "Innaffiare le piante è un elemento cruciale per la loro crescita e sopravvivenza, poiché l'acqua è essenziale per tutte le funzioni vitali delle piante. L'acqua permette alle piante di trasportare i nutrienti dal suolo fino alle loro parti superiori, facilitando il processo di fotosintesi. Inoltre, aiuta a mantenere la struttura flessibile e rigida della pianta, permettendole di rimanere eretta. Senza una idratazione adeguata, le piante possono soffrire di stress idrico, che può portare a foglie secche e ammaccate, crescita rallentata, e in casi estremi, alla morte della pianta. Pertanto, è importante capire e rispettare i bisogni idrici specifici di ogni tipo di pianta per garantire la loro salute e la loro fioritura."

    #lines = ["Hello! How can I assist you today?"]

    for audio_bytes in engine.read_text(line):
        with io.BytesIO() as dest, wave.open(dest, "wb") as f:
            f.setnchannels(1)
            # 2 bytes per sample.
            f.setsampwidth(2)
            f.setframerate(16000)

            sys.stdout.buffer.write(audio_bytes)
            sys.stdout.buffer.flush()

            f.writeframes(audio_bytes)


            with open("/tmp/file.wav","wb") as f:
              val = dest.getvalue()
              f.write(val)