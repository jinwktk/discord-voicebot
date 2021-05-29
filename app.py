import MeCab
import json
import discord
import os
import os
from os.path import join, dirname
from dotenv import load_dotenv
import subprocess
from pydub import AudioSegment

class CommonModule:
    def load_json(self, file):
        with open(file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        return json_data

class NLP:
    def __init__(self):
        self.cm = CommonModule()

    def morphological_analysis(self, text, keyword='-Ochasen'):
        words = []
        tagger = MeCab.Tagger(keyword)
        result = tagger.parse(text)
        result = result.split('\n')
        result = result[:-2]

        for word in result:
            temp = word.split('\t')
            word_info = {
                'surface': temp[0],
                'kana': temp[1],
                'base': temp[2],
                'pos': temp[3],
                'conjugation': temp[4],
                'form': temp[5]
            }
            words.append(word_info)
        return words

    def evaluate_pn_ja_wordlist(self, wordlist, word_pn_dictpath=None):
        if word_pn_dictpath is None:
            word_pn_dict = self.cm.load_json('pn_ja.json')
        else:
            word_pn_dict = self.cm.load_json(word_pn_dictpath)

        pn_value = 0
        for word in wordlist:
            pn_value += self.evaluate_pn_ja_word(word, word_pn_dict)

        return pn_value

    def evaluate_pn_ja_word(self, word, word_pn_dict:dict):
        if type(word) is dict:
            word = word['base']
        elif type(word) is str:
            pass
        else:
            raise TypeError

        if word in word_pn_dict.keys():
            pn_value = float(word_pn_dict[word]['value'])
            return pn_value
        return 0

    def analysis_emotion(self, text):
            split_words = self.morphological_analysis(text, "-Ochasen")
            pn_value = self.evaluate_pn_ja_wordlist(split_words)
            if pn_value > 0.5:
                emotion = 'happy'
            elif pn_value < -1.0:
                emotion = 'angry'
            elif pn_value < -0.5:
                emotion = 'sad'
            else:
                emotion = 'normal'
            return emotion

class VoiceChannel:
    def __init__(self):
        self.conf = {
            "voice_configs": {
                "htsvoice_resource": "./voice/",
                "jtalk_dict": "./dic"
            }
        }


    def make_by_jtalk(self, text, filepath='voice_message', voicetype='mei', emotion='normal'):
        
        with open('input.txt','w',encoding='shift_jis') as file:
            file.write(text)
        
        htsvoice = {
            'mei': {
                'normal': ['-m', os.path.join(self.conf['voice_configs']['htsvoice_resource'], 'mei/mei_normal.htsvoice')],
                'angry': ['-m', os.path.join(self.conf['voice_configs']['htsvoice_resource'], 'mei/mei_angry.htsvoice')],
                'bashful': ['-m', os.path.join(self.conf['voice_configs']['htsvoice_resource'], 'mei/mei_bashful.htsvoice')],
                'happy': ['-m', os.path.join(self.conf['voice_configs']['htsvoice_resource'], 'mei/mei_happy.htsvoice')],
                'sad': ['-m', os.path.join(self.conf['voice_configs']['htsvoice_resource'], 'mei/mei_sad.htsvoice')]
            },
            # 'm100': {
            #     'normal': ['-m', os.path.join(self.conf['voice_configs']['htsvoice_resource'], 'm100/nitech_jp_atr503_m001.htsvoice')]
            # },
            # 'tohoku-f01': {
            #     'normal': ['-m', os.path.join(self.conf['voice_configs']['htsvoice_resource'], 'htsvoice-tohoku-f01-master/tohoku-f01-neutral.htsvoice')],
            #     'angry': ['-m', os.path.join(self.conf['voice_configs']['htsvoice_resource'], 'htsvoice-tohoku-f01-master/tohoku-f01-angry.htsvoice')],
            #     'happy': ['-m', os.path.join(self.conf['voice_configs']['htsvoice_resource'], 'htsvoice-tohoku-f01-master/tohoku-f01-happy.htsvoice')],
            #     'sad': ['-m', os.path.join(self.conf['voice_configs']['htsvoice_resource'], 'htsvoice-tohoku-f01-master/tohoku-f01-sad.htsvoice')]
            # }
        }

        open_jtalk = ['./bin/open_jtalk']
        mech = ['-x', self.conf['voice_configs']['jtalk_dict']]
        speed = ['-r', '0.75']
        tone = ['-fm', '-3']
        outwav = ['-ow', filepath+'.wav']
        inputtxt = ['input.txt']
        cmd = open_jtalk + mech + htsvoice[voicetype][emotion] + speed + tone + outwav + inputtxt
        c = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        c.stdin.write(text.encode())
        c.stdin.close()
        c.wait()
        audio_segment = AudioSegment.from_wav(filepath+'.wav')
        os.remove(filepath+'.wav')
        audio_segment.export(filepath+'.mp3', format='mp3')
        return filepath+'.mp3'

client = discord.Client()

voice = None
volume = None

@client.event
async def on_ready():
    # 起動時の処理
    print('Bot is wake up.')

@client.event
async def on_message(message):
    nlp = NLP()
    vc = VoiceChannel()
    # テキストチャンネルにメッセージが送信されたときの処理
    global voice, volume, read_mode

    if voice is True and volume is None:
            source = discord.PCMVolumeTransformer(voice.source)
            volume = source.volume

    if client.user != message.author:
        text = message.content
        if text == '.s':
            channel = message.author.voice.channel
            voice = await channel.connect()
            await message.channel.send('ボイスチャンネルにログインしました')
        elif text == '.e':
            await voice.disconnect()
            await message.channel.send('ボイスチャンネルからログアウトしました')
        elif text == '!status':
            if voice.is_connected():
                await message.channel.send('ボイスチャンネルに接続中です')
        elif text == '!volume_up':
            volume += 0.1
            await message.channel.send('音量を上げました')
        elif text == '!volume_down':
            volume -= 0.1
            await message.channel.send('音量を下げました')
        elif text == '!bye':
            await client.close()
        # elif text == '!read_mode_on':
        #     read_mode = True
        #     await message.channel.send('読み上げモードをオンにしました')
        # elif text == '!read_mode_off':
        #     read_mode = False
        #     await message.channel.send('読み上げモードをオフにしました')
        else:
            # if read_mode:
            emotion = nlp.analysis_emotion(text)
            voice_file = vc.make_by_jtalk(text, "voice_massage", emotion=emotion)
            audio_source = discord.FFmpegPCMAudio(voice_file)
            voice.play(audio_source)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

client.run(os.environ.get("DISCORD_TOKEN"))