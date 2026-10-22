# SCRIPT: RING-VIDEO-VOICE-01
# Narration for "The ring keeps two books" in Kokoro, voice am_michael. One WAV per segment.
import json, os, soundfile as sf
from kokoro_onnx import Kokoro
HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.environ.get('KOKORO_DIR', os.path.join(HERE, 'models'))  # kokoro-v1.0.onnx and voices-v1.0.bin
os.makedirs(os.path.join(HERE, 'voice'), exist_ok=True)
K = Kokoro(os.path.join(MODELS, 'kokoro-v1.0.onnx'), os.path.join(MODELS, 'voices-v1.0.bin'))
SEG = {
 's1': "Here is a ring of five sites. Every edge keeps two books: the connection book, in amber, and its opposite, in cyan.",
 's2': "Each edge holds a fixed budget of eight, so the band never changes width. Only the split between the two books can move.",
 's3': "Now a twist is wound into the ring, and the connection book fills on every edge.",
 's4': "At a twist of pi, the two windings tie. From here on, the lowest state is the other winding, and the floor marker jumps ahead.",
 's5': "But the field keeps the winding it started with, so its book climbs away from the floor.",
 's6': "Until it cannot hold. The field slips one full winding, and in this run, the whole slip lands on a single edge.",
 's7': "Then it settles back onto the floor. The slip is kept as a record, in the winding.",
 's8': "The two books, the budget and the floor come from Jeromie Beasley's paper, Non-normality is connection energy. Every frame is drawn from equations.",
}
out = {}
for k, text in SEG.items():
    audio, sr = K.create(text, voice='am_michael', speed=1.0, lang='en-us')
    sf.write(os.path.join(HERE, 'voice', '%s.wav' % k), audio, sr)
    out[k] = {'text': text, 'sec': len(audio) / sr, 'sr': sr}
    print(k, round(len(audio) / sr, 2))
json.dump(out, open(os.path.join(HERE, 'voice', 'segments.json'), 'w'), indent=1)
