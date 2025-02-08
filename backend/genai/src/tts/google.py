from google.cloud import texttospeech

# TTS settings
AUDIO_ENCODING = "MP3"
LANGUAGE_CODE = "ja-JP"
VOICE_NAME = "ja-JP-Neural2-B"
# 微調整対象のパラメータ
EFFECTS_PROFILE_ID = ["handset-class-device"]
SPEAKING_RATE = 1.1  # speed
PITCH = 0.0
VOLUME_GAIN_DB = 0.0

# use python sdk
# see: https://github.com/googleapis/google-cloud-python/tree/main/packages/google-cloud-texttospeech/docs
# example: https://github.com/GoogleCloudPlatform/python-docs-samples/tree/main/texttospeech/snippets
client = texttospeech.TextToSpeechClient()

voice = texttospeech.VoiceSelectionParams(
    language_code=LANGUAGE_CODE,
    name=VOICE_NAME,
)

audio_config = texttospeech.AudioConfig(
    audio_encoding=AUDIO_ENCODING,
    effects_profile_id=EFFECTS_PROFILE_ID,
    pitch=PITCH,
    speaking_rate=SPEAKING_RATE,
    volume_gain_db=VOLUME_GAIN_DB,
)


def synthesize(text: str):
    # 改行は不正な文字として扱われるため、スペースに変換
    text = text.replace("\n", " ")
    # tabもスペースに変換
    text = text.replace("\t", " ")

    synthesis_input = texttospeech.SynthesisInput(text=text)
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return response


if __name__ == "__main__":
    text = """はい、皆さんこんにちは！ラジオパーソナリティのミーホです。
今日のテーマは「創造性と伝統、未来を彩る二つの光」です。

最近、AIが生成する画像がすごいですよね。まるでプロのイラストレーターが描いたような作品も、簡単に作れちゃう時代になりました。でも、そこでふと思うんです。「じゃあ、人が描くイラストの価値って、これからどうなっていくんだろう？」って。

そんな疑問に答えてくれるかもしれない一冊が、「AI生成画像にまけない イラストの描きかた」です。この本は、AIにはできない、人にしか描けないイラストの魅力を教えてくれます。著者の榎本事務所さんは、長年イラストの世界で活躍されてきた方。その経験から、AI時代でも生き残るためのヒントを伝授してくれるんです。

一方、グローバルな視点に目を向けてみましょう。世界中の経営幹部たちが、今、日本の伝統文化に熱い視線を送っているのをご存知ですか？

「世界の経営幹部はなぜ日本に感化されるのか」という本には、その理由が詳しく書かれています。茶道、武道、禅…、日本の伝統文化には、ビジネスに通じる深い叡智が隠されているんです。高津尚志さんをはじめとする著者の方々は、その叡智を解き明かし、これからのビジネスのあり方を提案しています。

創造性と伝統。一見すると対照的な二つの要素ですが、どちらも未来を彩る光になるはずです。AIの進化に負けない創造性を磨き、日本の伝統文化から学びを得る。この二つの視点を持つことで、私たちはより豊かな未来を切り開けるのではないでしょうか。

それでは、今日の放送はここまで。また次回、お耳にかかりましょう！"""

    response = synthesize(text)
    with open("tts_output_3.mp3", "wb") as out:
        out.write(response.audio_content)
        print("音声ファイルを保存しました。")
