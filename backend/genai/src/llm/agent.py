import os

import litellm
import weave
from lmnr import Laminar as L
from lmnr import observe
from smolagents import LiteLLMModel, ToolCallingAgent

from src.llm.config import INSTRUCTION_PROMPT

if os.getenv("CI") == "true":
    # CI 環境では weave と Laminar を初期化しない
    pass
else:
    weave.init(project_name=os.getenv("WEAVE_PROJECT_NAME", ""))
    L.initialize(project_api_key=os.getenv("LMNR_PROJECT_API_KEY"))


def _get_agent() -> ToolCallingAgent:
    # use smolagents as llm agent
    # see: https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models#gemini-models
    model_id = "gemini-2.0-flash-001"
    model = LiteLLMModel(
        model_id,
        temperature=0.08,
        seed=42,
    )
    agent = ToolCallingAgent(
        tools=[],
        model=model,
        prompt_templates={
            "system_prompt": INSTRUCTION_PROMPT,
        },
        max_steps=5,
    )
    return agent


def call_agent(agent: ToolCallingAgent, text: str) -> str:
    return agent.run(task=text, stream=False)


if __name__ == "__main__":
    agent = _get_agent()
    dataset = """
This XML file does not appear to have any style information associated with it. The document tree is shown below.
<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/" version="2.0" data-google-analytics-opt-out="">
<script async="false" src="chrome-extension://nmniboccheadcclilkfkonokbcoceced/js/vendor.js"/>
<script async="false" src="chrome-extension://nmniboccheadcclilkfkonokbcoceced/js/injected/proxy-injected-providers.js"/>
<channel>
<title>国立国会図書館サーチRSS - 検索</title>
<link>https://ndlsearch.ndl.go.jp/search?cs=bib&from=0&size=10&sort=published:desc&f-ht=ndl&f-ht=library&f-repository=R100000137&f-doc_style=digital&f-doc_style=paper&f-mt=dtbook&f-mt=dbook</link>
<atom:link href="https://ndlsearch.ndl.go.jp/rss/ndls/bib.xml" rel="self" type="application/rss+xml"/>
<description/>
<lastBuildDate>Sun, 09 Feb 2025 00:00:00 +0900</lastBuildDate>
<item>
<title>AI生成画像にまけない イラストの描きかた / 榎本事務所 著・文・その他</title>
<link>https://ndlsearch.ndl.go.jp/books/R100000137-I9784798073972</link>
<description>榎本事務所 著・文・その他. AI生成画像にまけない イラストの描きかた. 秀和システム; 秀和システム. ISBN:9784798073972</description>
<guid isPermaLink="true">https://ndlsearch.ndl.go.jp/books/R100000137-I9784798073972</guid>
<category>図書</category>
<pubDate>Wed, 05 Feb 2025 18:37:00 +0900</pubDate>
</item>
<item>
<title>医人たちの春 / 藤城　龍三郎 著・文・その他</title>
<link>https://ndlsearch.ndl.go.jp/books/R100000137-I9784866771465</link>
<description>藤城　龍三郎 著・文・その他. 医人たちの春. 講談社エディトリアル; 講談社エディトリアル. ISBN:9784866771465</description>
<guid isPermaLink="true">https://ndlsearch.ndl.go.jp/books/R100000137-I9784866771465</guid>
<category>図書</category>
<pubDate>Wed, 01 May 2024 00:25:00 +0900</pubDate>
</item>
<item>
<title>縁切りエマ【単話】 11 / とらふぐ 原著ほか</title>
<link>https://ndlsearch.ndl.go.jp/books/R100000137-I09D154490010d0000000</link>
<description>とらふぐ 原著; 今井康絵 イラスト; 伊藤征章 企画・原案. 縁切りエマ【単話】 11. 小学館, ビッグコミックススペシャル</description>
<guid isPermaLink="true">https://ndlsearch.ndl.go.jp/books/R100000137-I09D154490010d0000000</guid>
<category>図書</category>
<category>電子書籍・電子雑誌</category>
<pubDate>Tue, 04 Feb 2025 18:54:00 +0900</pubDate>
</item>
<item>
<title>底辺ハンターが【リターン】スキルで現代最強 : 前世の知識と死に戻りを駆使して、人類最速レベルアップ ２ / 萩鵜アキ 著・文・その他ほか</title>
<link>https://ndlsearch.ndl.go.jp/books/R100000137-I9784824201126</link>
<description>萩鵜アキ 著・文・その他; gunkan イラスト. 底辺ハンターが【リターン】スキルで現代最強 : 前世の知識と死に戻りを駆使して、人類最速レベルアップ ２. 一二三書房; 一二三書房, サーガフォレスト. ISBN:9784824201126</description>
<guid isPermaLink="true">https://ndlsearch.ndl.go.jp/books/R100000137-I9784824201126</guid>
<category>図書</category>
<pubDate>Thu, 30 Jan 2025 18:37:00 +0900</pubDate>
</item>
<item>
<title>地雷ちゃんは愛されたい！ / ゆいみす イラスト</title>
<link>https://ndlsearch.ndl.go.jp/books/R100000137-I9784049158472</link>
<description>ゆいみす イラスト. 地雷ちゃんは愛されたい！. ＫＡＤＯＫＡＷＡ; ＫＡＤＯＫＡＷＡ. ISBN:9784049158472</description>
<guid isPermaLink="true">https://ndlsearch.ndl.go.jp/books/R100000137-I9784049158472</guid>
<category>図書</category>
<pubDate>Wed, 15 Jan 2025 19:08:00 +0900</pubDate>
</item>
<item>
<title>光が死んだ夏　7　ラバーストラップ付き限定版 7 / モクモク　れん 著・文・その他</title>
<link>https://ndlsearch.ndl.go.jp/books/R100000137-I9784041156834</link>
<description>モクモク　れん 著・文・その他. 光が死んだ夏　7　ラバーストラップ付き限定版 7. ＫＡＤＯＫＡＷＡ; ＫＡＤＯＫＡＷＡ, 角川コミックス・エース. ISBN:9784041156834</description>
<guid isPermaLink="true">https://ndlsearch.ndl.go.jp/books/R100000137-I9784041156834</guid>
<category>図書</category>
<pubDate>Sun, 22 Dec 2024 18:37:00 +0900</pubDate>
</item>
<item>
<title>光が死んだ夏　7 7 / モクモク　れん 著・文・その他</title>
<link>https://ndlsearch.ndl.go.jp/books/R100000137-I9784041156827</link>
<description>モクモク　れん 著・文・その他. 光が死んだ夏　7 7. ＫＡＤＯＫＡＷＡ; ＫＡＤＯＫＡＷＡ, 角川コミックス・エース. ISBN:9784041156827</description>
<guid isPermaLink="true">https://ndlsearch.ndl.go.jp/books/R100000137-I9784041156827</guid>
<category>図書</category>
<pubDate>Sun, 19 Jan 2025 18:24:00 +0900</pubDate>
</item>
<item>
<title>凸解析―理論と応用 / 田中　久稔 翻訳ほか</title>
<link>https://ndlsearch.ndl.go.jp/books/R100000137-I9784621310618</link>
<description>田中　久稔 翻訳; 丸山 徹 翻訳. 凸解析―理論と応用. 丸善出版, 数理と経済. ISBN:9784621310618</description>
<guid isPermaLink="true">https://ndlsearch.ndl.go.jp/books/R100000137-I9784621310618</guid>
<category>図書</category>
<pubDate>Thu, 23 Jan 2025 00:29:00 +0900</pubDate>
</item>
<item>
<title>観月ありさ写真集　『タイトル未定』 / 観月 ありさ 著・文・その他ほか</title>
<link>https://ndlsearch.ndl.go.jp/books/R100000137-I9784065360385</link>
<description>観月 ありさ 著・文・その他; 中村 和孝 写真. 観月ありさ写真集　『タイトル未定』. 講談社. ISBN:9784065360385</description>
<guid isPermaLink="true">https://ndlsearch.ndl.go.jp/books/R100000137-I9784065360385</guid>
<category>図書</category>
<pubDate>Thu, 26 Sep 2024 18:39:00 +0900</pubDate>
</item>
<item>
<title>世界の経営幹部はなぜ日本に感化されるのか : 伝統文化の叡智に学ぶビジネスの未来 / 高津尚志 編集ほか</title>
<link>https://ndlsearch.ndl.go.jp/books/R100000137-I9784296119288</link>
<description>高津尚志 編集; 高津尚志 著・文・その他. 世界の経営幹部はなぜ日本に感化されるのか : 伝統文化の叡智に学ぶビジネスの未来. 日経BP　日本経済新聞出版; 日経BPマーケティング. ISBN:9784296119288</description>
<guid isPermaLink="true">https://ndlsearch.ndl.go.jp/books/R100000137-I9784296119288</guid>
<category>図書</category>
<pubDate>Wed, 29 Jan 2025 00:23:00 +0900</pubDate>
</item>
</channel>
</rss>
"""
    text = "dataset: " + dataset
    result = call_agent(agent, text)
    print(result)
