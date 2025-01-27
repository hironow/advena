import os

import google.auth as gauth
import weave
from livekit.plugins import google as livekit_google
from lmnr import Laminar as L
from lmnr import observe

# see: https://docs.livekit.io/agents/integrations/google/#gemini-llm
llm = livekit_google.LLM(
    model="gemini-2.0-flash-exp",
    candidate_count=1,
    temperature=0.08,
    vertexai=True,
    tool_choice="auto",  # NOTE: 動的に変えたい required, none
)

tts = livekit_google.TTS(
    language="ja-JP",
    gender="female",
    voice_name="ja-JP-Neural2-B",  # use Neural2 voice type: ja-JP-Neural2-C, ja-JP-Neural2-D see: https://cloud.google.com/text-to-speech/docs/voices
    encoding="linear16",
    effects_profile_id="large-automotive-class-device",
    sample_rate=24000,
    pitch=0,
    speaking_rate=1.0,
)

stt = livekit_google.STT(
    languages="ja-JP",
    detect_language=True,
    interim_results=True,
    punctuate=True,
    spoken_punctuation=True,
    model="chirp_2",
    sample_rate=16000,
    keywords=[
        ("mi-ho", 24.0),  # 仮設定
    ],
)

model = livekit_google.beta.realtime.RealtimeModel(
    model="gemini-2.0-flash-exp",
    voice="Charon",
    modalities=["TEXT", "AUDIO"],
    enable_user_audio_transcription=True,
    enable_agent_audio_transcription=True,
    vertexai=True,
    candidate_count=1,
    temperature=0.08,
    instructions="You are a helpful assistant",
)


@weave.op()
@observe()
def main():
    print("Hello from genai!")


if __name__ == "__main__":
    weave.init(project_name=os.getenv("WEAVE_PROJECT_NAME"))
    L.initialize(project_api_key=os.getenv("LMNR_PROJECT_API_KEY"))

    # see: https://github.com/googleapis/google-auth-library-python/blob/main/google/auth/_default.py#L577-L595
    credentials, project_id = gauth.default()
    # print("credentials", credentials)
    print("project_id", project_id)

    main()
