import pytest

import src.tts.google as tts_google


# ダミーのレスポンスオブジェクト
class DummyResponse:
    def __init__(self, audio_content):
        self.audio_content = audio_content


# ダミー関数（キーワード引数として受け取る）
def dummy_synthesize_speech(*, input, voice, audio_config):
    # input.text 内に改行やタブが含まれていないことを検証
    assert "\n" not in input.text, "改行が除去されていません"
    assert "\t" not in input.text, "タブが除去されていません"

    # 期待するテキストに変換されているか確認
    expected_text = "Hello World Test"
    assert input.text == expected_text, (
        f"期待値 '{expected_text}' ではなく、'{input.text}' が入力されています"
    )

    # ダミーの音声データを返す
    return DummyResponse(audio_content=b"dummy audio content")


def test_synthesize(monkeypatch):
    # google モジュール内で定義されている client.synthesize_speech をダミー関数に差し替え
    monkeypatch.setattr(tts_google.client, "synthesize_speech", dummy_synthesize_speech)

    # テスト用の入力テキスト（改行とタブを含む）
    input_text = "Hello\nWorld\tTest"

    # synthesize 関数を呼び出す
    response = tts_google.synthesize(input_text)

    # レスポンスの audio_content がダミーの値と一致することを検証
    assert response.audio_content == b"dummy audio content"
