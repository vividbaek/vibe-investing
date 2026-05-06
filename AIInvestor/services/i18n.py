"""Language detection and localized strings.

Telegram delivers the user's UI language in `update.effective_user.language_code`
(e.g. "ko", "en-US", "ja", "zh-Hans"). We support four languages and fall back
to English for everything else. Users can switch via /lang or the inline keyboard.
"""

from __future__ import annotations

from dataclasses import dataclass

SUPPORTED = ("ko", "en", "ja", "zh")
DEFAULT = "en"


def normalize_language(code: str | None) -> str:
    if not code:
        return DEFAULT
    head = code.lower().split("-")[0]
    if head in SUPPORTED:
        return head
    return DEFAULT


@dataclass(frozen=True)
class _Bundle:
    greeting: str
    intro: str
    language_switch_hint: str
    persona_prompt: str
    persona_buffett: str
    persona_dalio: str
    persona_wood: str
    persona_set: str
    report_offer: str
    report_yes: str
    report_skip: str
    interest_prompt: str
    interest_preset_btn: list[tuple[str, str]]
    interest_custom_btn: str
    interest_done_btn: str
    interest_saved: str
    interest_saved_with_tickers: str
    free_query_invite: str
    persona_changed: str
    lang_changed: str
    disclaimer: str
    unknown_input: str
    error_market_data: str
    error_llm: str
    forget_prompt: str
    forget_yes: str
    forget_no: str
    forget_done: str
    forget_cancelled: str
    policy: str
    feedback_usage: str
    feedback_thanks: str
    feedback_error: str
    ticker_not_found: str
    intent_unrecognized: str
    deeper_analysis_offer: str
    deeper_analysis_yes: str
    deeper_analysis_no: str
    short_disclaimer: str
    risk_notice: str


_KO = _Bundle(
    greeting="안녕하세요, AI Investor 입니다.",
    intro=(
        "당신만의 투자 멘토 페르소나로 매일 미국 시황(NASDAQ / S&P 500)을 해설해 드립니다.\n\n"
        "• 데이터 출처: Yahoo Finance (yfinance)\n"
        "• AI 모델: DeepSeek\n"
        "• ⚠ 본 챗봇은 실수할 수 있으며, 어떤 응답도 투자 자문이 아닙니다.\n"
        "• ⚠ 모든 투자 판단과 그 결과에 대한 책임은 전적으로 본인에게 있습니다."
    ),
    language_switch_hint=(
        "현재 한국어로 대화 중입니다. 다른 언어로 전환하려면 /lang 을 입력하세요. "
        "(English / 日本語 / 中文 / 한국어 지원)"
    ),
    persona_prompt="투자 멘토 페르소나를 선택해 주세요:",
    persona_buffett="Warren Buffett (장기 가치)",
    persona_dalio="Ray Dalio (매크로/올웨더)",
    persona_wood="Cathie Wood (혁신 성장)",
    persona_set="✓ {persona} 로 설정되었습니다.",
    report_offer="오늘의 시황 리포트가 준비되어 있습니다. 받아보시겠어요?",
    report_yes="예, 보기",
    report_skip="건너뛰기",
    interest_prompt=(
        "주로 어떤 분야나 종목에 투자하시나요?\n"
        "버튼을 눌러 선택하시거나, 자유롭게 입력해 주세요 (예: \"AI 반도체\", \"NVDA TSLA AAPL\")."
    ),
    interest_preset_btn=[
        ("AI 반도체", "interest:ai_chip"),
        ("빅테크", "interest:bigtech"),
        ("배당주", "interest:dividend"),
        ("ETF", "interest:etf"),
        ("BTC 관련주", "interest:btc"),
        ("원자재/에너지", "interest:energy"),
        ("헬스케어", "interest:health"),
    ],
    interest_custom_btn="✏ 직접 입력",
    interest_done_btn="✅ 완료",
    interest_saved="관심 분야를 저장했습니다: {tags}",
    interest_saved_with_tickers="관심 분야를 저장했습니다.\n• 분야: {tags}\n• 종목: {tickers}",
    free_query_invite="궁금한 주식이나 지금 시장 상황이 궁금하세요? 종목 티커나 자유 질문을 보내 주세요.",
    persona_changed="✓ {persona} 로 페르소나가 변경됐습니다.{interests}",
    lang_changed="✓ 언어가 한국어로 변경되었습니다.",
    disclaimer="본 응답은 투자 자문이 아닙니다.",
    unknown_input="이해하지 못했어요. /help 를 입력하시면 명령 목록을 볼 수 있습니다.",
    error_market_data="지금 시장 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.",
    error_llm="지금 답변을 생성하지 못했습니다. 잠시 후 다시 시도해 주세요.",
    forget_prompt="저장된 페르소나·관심사·언어 설정을 모두 삭제할까요? 이 작업은 되돌릴 수 없습니다.",
    forget_yes="네, 모두 삭제",
    forget_no="취소",
    forget_done="✓ 저장된 데이터를 모두 삭제했습니다. /start 로 다시 시작할 수 있습니다.",
    forget_cancelled="삭제를 취소했습니다.",
    policy=(
        "📋 데이터 처리 및 면책 안내\n\n"
        "• 본 챗봇은 실수할 수 있으며, 어떤 응답도 투자 자문이 아닙니다.\n"
        "• 모든 투자 판단과 그 결과에 대한 책임은 전적으로 본인에게 있습니다.\n\n"
        "데이터 출처:\n"
        "• 시세·펀더멘털: Yahoo Finance (yfinance)\n"
        "• AI 응답: DeepSeek (deepseek-chat / deepseek-reasoner)\n\n"
        "저장되는 정보:\n"
        "• 페르소나, 언어, 관심 분야·종목 (서비스 운영 목적)\n"
        "• 텔레그램 ID 는 SHA-256 익명화되어 anon_user_id 로만 보관\n"
        "• 원시 ID·이름·연락처·IP 는 저장하지 않음\n\n"
        "권리:\n"
        "• /forget 으로 저장된 데이터를 즉시 삭제할 수 있습니다.\n"
        "• /lang 으로 언제든 언어를 변경할 수 있습니다.\n"
        "• /persona 로 페르소나를 변경해도 관심사는 보존됩니다."
    ),
    feedback_usage="피드백을 함께 보내주세요.\n예시: /feedback 응답이 너무 길어요 / 피드백 좋네요!",
    feedback_thanks="감사합니다. 의견이 운영자에게 전달되었습니다. 🙏",
    feedback_error="죄송합니다. 의견 전송에 실패했습니다. 잠시 후 다시 시도해 주세요.",
    ticker_not_found="'{q}' 종목을 찾지 못했어요. 정확한 티커(예: AAPL) 또는 회사명(예: 애플)을 보내주세요.",
    intent_unrecognized="어떤 종목이나 ETF가 궁금하신가요? 예: NVDA, 테슬라, QQQ\n‘추천/비교/포트폴리오’ 같은 자연어 요청은 곧 지원될 예정입니다.",
    deeper_analysis_offer="더 전문적인 {persona} 페르소나의 의견이 필요하신가요?\n\n⏱ 예 선택 시 5초 이상 소요됩니다.",
    deeper_analysis_yes="✅ 예, 받기",
    deeper_analysis_no="아니요, 괜찮아요",
    short_disclaimer="ℹ 본 응답은 투자 자문이 아닙니다.",
    risk_notice=(
        "⚠ 이 서비스는 주식 매매를 권장하지 않으며, 실제 투자는 전문가의 상담이 필요합니다.\n"
        "AI는 환각 및 오류가 있을 수 있으며, 모든 투자 판단의 책임은 본인에게 있습니다."
    ),
)

_EN = _Bundle(
    greeting="Hello, this is AI Investor.",
    intro=(
        "I explain U.S. market action (NASDAQ / S&P 500) in the voice of a famous investor.\n\n"
        "• Data: Yahoo Finance (yfinance)\n"
        "• AI: DeepSeek\n"
        "• ⚠ This chatbot can make mistakes; nothing it says is financial advice.\n"
        "• ⚠ All investment decisions and their consequences are entirely your own responsibility."
    ),
    language_switch_hint=(
        "Speaking English. To switch, send /lang. "
        "(한국어 / English / 日本語 / 中文 supported)"
    ),
    persona_prompt="Choose your investor persona:",
    persona_buffett="Warren Buffett (long-term value)",
    persona_dalio="Ray Dalio (macro / all-weather)",
    persona_wood="Cathie Wood (disruptive growth)",
    persona_set="✓ Set to {persona}.",
    report_offer="Today's market report is ready. Want to see it?",
    report_yes="Yes, show me",
    report_skip="Skip",
    interest_prompt=(
        "What sectors or tickers do you mainly invest in?\n"
        "Tap presets below or type freely (e.g. \"AI chips\", \"NVDA TSLA AAPL\")."
    ),
    interest_preset_btn=[
        ("AI chips", "interest:ai_chip"),
        ("Big Tech", "interest:bigtech"),
        ("Dividends", "interest:dividend"),
        ("ETF", "interest:etf"),
        ("BTC-linked", "interest:btc"),
        ("Energy", "interest:energy"),
        ("Healthcare", "interest:health"),
    ],
    interest_custom_btn="✏ Type custom",
    interest_done_btn="✅ Done",
    interest_saved="Interests saved: {tags}",
    interest_saved_with_tickers="Interests saved.\n• Sectors: {tags}\n• Tickers: {tickers}",
    free_query_invite="Curious about a specific stock or the market right now? Send a ticker or a question.",
    persona_changed="✓ Persona changed to {persona}.{interests}",
    lang_changed="✓ Language switched to English.",
    disclaimer="This is not financial advice.",
    unknown_input="I didn't catch that. Send /help for commands.",
    error_market_data="I couldn't fetch market data right now. Please try again shortly.",
    error_llm="I couldn't generate a response right now. Please try again shortly.",
    forget_prompt="Delete your saved persona, interests, and language settings? This cannot be undone.",
    forget_yes="Yes, delete everything",
    forget_no="Cancel",
    forget_done="✓ Your stored data has been deleted. Send /start to begin again.",
    forget_cancelled="Cancelled.",
    policy=(
        "📋 Data handling & disclaimer\n\n"
        "• This chatbot can make mistakes; nothing it says is financial advice.\n"
        "• All investment decisions and their consequences are entirely your own responsibility.\n\n"
        "Data sources:\n"
        "• Quotes & fundamentals: Yahoo Finance (yfinance)\n"
        "• AI responses: DeepSeek (deepseek-chat / deepseek-reasoner)\n\n"
        "What we store:\n"
        "• Persona, language, interest tags & watchlist tickers (operational)\n"
        "• Your Telegram ID is one-way hashed (SHA-256) to anon_user_id\n"
        "• Raw IDs, names, contact info, and IP are NOT stored\n\n"
        "Your rights:\n"
        "• /forget — delete all stored data immediately\n"
        "• /lang — switch language at any time\n"
        "• /persona — change persona; interests are preserved"
    ),
    feedback_usage="Please include your feedback in the same message.\nExample: /feedback The replies are too long",
    feedback_thanks="Thanks! Your feedback was forwarded to the operator. 🙏",
    feedback_error="Sorry, we couldn't deliver your feedback right now. Please try again shortly.",
    ticker_not_found="I couldn't find '{q}'. Please send a valid ticker (e.g. AAPL) or company name (e.g. Apple).",
    intent_unrecognized="Which stock or ETF would you like to discuss? e.g. NVDA, Tesla, QQQ\nNatural-language asks like 'recommend / compare / portfolio' are coming soon.",
    deeper_analysis_offer="Want a deeper take from the {persona} persona?\n\n⏱ Yes takes 5+ seconds.",
    deeper_analysis_yes="✅ Yes, please",
    deeper_analysis_no="No thanks",
    short_disclaimer="ℹ Not investment advice.",
    risk_notice=(
        "⚠ This service does not recommend buying or selling. Real investment decisions need professional advice.\n"
        "AI may hallucinate or err. You alone bear responsibility for your investment outcomes."
    ),
)

_JA = _Bundle(
    greeting="こんにちは、AI Investor です。",
    intro=(
        "有名投資家のペルソナで毎日の米国市況（NASDAQ / S&P 500）を解説します。\n\n"
        "• データ: Yahoo Finance (yfinance)\n"
        "• AI: DeepSeek\n"
        "• ⚠ 本チャットボットは誤りを含むことがあり、いかなる応答も投資助言ではありません。\n"
        "• ⚠ すべての投資判断とその結果については、ご自身が全責任を負うものとします。"
    ),
    language_switch_hint=(
        "日本語で対話中です。言語を切り替えるには /lang を送信してください。"
        "（한국어 / English / 日本語 / 中文 対応）"
    ),
    persona_prompt="投資メンターのペルソナを選んでください:",
    persona_buffett="ウォーレン・バフェット (長期バリュー)",
    persona_dalio="レイ・ダリオ (マクロ / オールウェザー)",
    persona_wood="キャシー・ウッド (破壊的成長)",
    persona_set="✓ {persona} に設定しました。",
    report_offer="本日の市況レポートをご用意しています。ご覧になりますか?",
    report_yes="はい、見る",
    report_skip="スキップ",
    interest_prompt=(
        "主にどのセクターや銘柄に投資されていますか?\n"
        "ボタンで選択するか、自由にご入力ください (例: \"AI半導体\", \"NVDA TSLA AAPL\")。"
    ),
    interest_preset_btn=[
        ("AI半導体", "interest:ai_chip"),
        ("ビッグテック", "interest:bigtech"),
        ("配当株", "interest:dividend"),
        ("ETF", "interest:etf"),
        ("BTC関連株", "interest:btc"),
        ("エネルギー", "interest:energy"),
        ("ヘルスケア", "interest:health"),
    ],
    interest_custom_btn="✏ 自由入力",
    interest_done_btn="✅ 完了",
    interest_saved="関心分野を保存しました: {tags}",
    interest_saved_with_tickers="関心分野を保存しました。\n• 分野: {tags}\n• 銘柄: {tickers}",
    free_query_invite="気になる銘柄や市場の状況についてお気軽にどうぞ。ティッカーや質問を送ってください。",
    persona_changed="✓ ペルソナを {persona} に変更しました。{interests}",
    lang_changed="✓ 言語を日本語に切り替えました。",
    disclaimer="本回答は投資助言ではありません。",
    unknown_input="理解できませんでした。/help でコマンド一覧を確認できます。",
    error_market_data="市場データを取得できませんでした。しばらくしてから再度お試しください。",
    error_llm="回答を生成できませんでした。しばらくしてから再度お試しください。",
    forget_prompt="保存されたペルソナ・関心分野・言語設定をすべて削除しますか? この操作は取り消せません。",
    forget_yes="はい、すべて削除",
    forget_no="キャンセル",
    forget_done="✓ 保存データを削除しました。/start で再度始められます。",
    forget_cancelled="キャンセルしました。",
    policy=(
        "📋 データの取扱いと免責事項\n\n"
        "• 本チャットボットは誤りを含むことがあり、いかなる応答も投資助言ではありません。\n"
        "• すべての投資判断とその結果については、ご自身が全責任を負うものとします。\n\n"
        "データソース:\n"
        "• 株価・ファンダメンタルズ: Yahoo Finance (yfinance)\n"
        "• AI応答: DeepSeek (deepseek-chat / deepseek-reasoner)\n\n"
        "保存される情報:\n"
        "• ペルソナ、言語、関心分野・銘柄 (サービス運用目的)\n"
        "• Telegram ID は SHA-256 で匿名化された anon_user_id のみ保管\n"
        "• 生の ID・氏名・連絡先・IP は保存されません\n\n"
        "ユーザーの権利:\n"
        "• /forget — 保存データを即時削除\n"
        "• /lang — いつでも言語を切替可能\n"
        "• /persona — ペルソナ変更時も関心分野は保持"
    ),
    feedback_usage="フィードバックを同じメッセージに含めてください。\n例: /feedback 応答が長すぎます",
    feedback_thanks="ありがとうございます。ご意見を運営者に転送しました。 🙏",
    feedback_error="申し訳ありません。フィードバックを送信できませんでした。しばらくしてから再度お試しください。",
    ticker_not_found="'{q}' を見つけられませんでした。正しいティッカー(例: AAPL)または銘柄名(例: アップル)を送信してください。",
    intent_unrecognized="どの銘柄やETFを分析しましょうか? 例: NVDA, テスラ, QQQ\n「推薦/比較/ポートフォリオ」など自然言語は近日対応予定です。",
    deeper_analysis_offer="{persona} ペルソナのより専門的な見解が必要ですか?\n\n⏱ はいを選ぶと5秒以上かかります。",
    deeper_analysis_yes="✅ はい、お願いします",
    deeper_analysis_no="いいえ、結構です",
    short_disclaimer="ℹ 本回答は投資助言ではありません。",
    risk_notice=(
        "⚠ 本サービスは株式の売買を推奨しません。実際の投資判断には専門家への相談が必要です。\n"
        "AIには誤りや幻覚が含まれる可能性があり、投資の責任はすべてご自身にあります。"
    ),
)

_ZH = _Bundle(
    greeting="您好,我是 AI Investor。",
    intro=(
        "我会以著名投资人的角色解读每日美股(NASDAQ / S&P 500)行情。\n\n"
        "• 数据来源: Yahoo Finance (yfinance)\n"
        "• AI: DeepSeek\n"
        "• ⚠ 本聊天机器人可能出错,所有回复均不构成投资建议。\n"
        "• ⚠ 一切投资决策及其后果由您本人完全自行承担。"
    ),
    language_switch_hint=(
        "当前使用中文对话。如需切换语言,请发送 /lang。"
        "(支持 한국어 / English / 日本語 / 中文)"
    ),
    persona_prompt="请选择您的投资导师人设:",
    persona_buffett="沃伦·巴菲特 (长期价值)",
    persona_dalio="瑞·达利欧 (宏观 / 全天候)",
    persona_wood="凯西·伍德 (颠覆性增长)",
    persona_set="✓ 已设置为 {persona}。",
    report_offer="今日的市场报告已准备好,是否查看?",
    report_yes="好的,查看",
    report_skip="跳过",
    interest_prompt=(
        "您主要投资哪些行业或个股?\n"
        "请点击预设或自由输入(例如 \"AI 芯片\", \"NVDA TSLA AAPL\")。"
    ),
    interest_preset_btn=[
        ("AI 芯片", "interest:ai_chip"),
        ("大型科技", "interest:bigtech"),
        ("股息股", "interest:dividend"),
        ("ETF", "interest:etf"),
        ("BTC 概念", "interest:btc"),
        ("能源", "interest:energy"),
        ("医疗", "interest:health"),
    ],
    interest_custom_btn="✏ 自定义输入",
    interest_done_btn="✅ 完成",
    interest_saved="已保存关注领域: {tags}",
    interest_saved_with_tickers="已保存关注领域。\n• 行业: {tags}\n• 个股: {tickers}",
    free_query_invite="想了解某只股票或当前市场吗?请发送股票代码或自由提问。",
    persona_changed="✓ 已将人设切换为 {persona}。{interests}",
    lang_changed="✓ 语言已切换为中文。",
    disclaimer="本回复不构成投资建议。",
    unknown_input="我没理解。发送 /help 查看命令列表。",
    error_market_data="目前无法获取市场数据,请稍后再试。",
    error_llm="目前无法生成回复,请稍后再试。",
    forget_prompt="确认删除已保存的人设、关注领域和语言设置吗? 此操作不可撤销。",
    forget_yes="是,全部删除",
    forget_no="取消",
    forget_done="✓ 已删除您的存储数据。发送 /start 即可重新开始。",
    forget_cancelled="已取消。",
    policy=(
        "📋 数据处理与免责声明\n\n"
        "• 本聊天机器人可能出错,所有回复均不构成投资建议。\n"
        "• 一切投资决策及其后果由您本人完全自行承担。\n\n"
        "数据来源:\n"
        "• 行情与基本面: Yahoo Finance (yfinance)\n"
        "• AI 回复: DeepSeek (deepseek-chat / deepseek-reasoner)\n\n"
        "保存的信息:\n"
        "• 人设、语言、关注领域与股票 (服务运行所需)\n"
        "• Telegram ID 经 SHA-256 单向哈希为 anon_user_id 后保存\n"
        "• 原始 ID、姓名、联系方式、IP 不会被保存\n\n"
        "您的权利:\n"
        "• /forget — 立即删除所存数据\n"
        "• /lang — 随时切换语言\n"
        "• /persona — 切换人设时关注领域将保留"
    ),
    feedback_usage="请将反馈与命令一起发送。\n示例: /feedback 回复太长了",
    feedback_thanks="感谢!您的反馈已转发给运营者。🙏",
    feedback_error="抱歉,反馈发送失败。请稍后再试。",
    ticker_not_found="未找到 '{q}'。请发送正确的代码(例如 AAPL)或公司名(例如 苹果)。",
    intent_unrecognized="您想分析哪只股票或ETF? 例如:NVDA、特斯拉、QQQ\n'推荐/比较/投资组合' 等自然语言查询将很快支持。",
    deeper_analysis_offer="是否需要 {persona} 人设的更深入分析?\n\n⏱ 选择「是」需要5秒以上。",
    deeper_analysis_yes="✅ 是,请分析",
    deeper_analysis_no="不用了",
    short_disclaimer="ℹ 本回复不构成投资建议。",
    risk_notice=(
        "⚠ 本服务不推荐买卖股票,实际投资决策请咨询专业人士。\n"
        "AI 可能出错或产生幻觉,所有投资后果由您本人承担。"
    ),
)

_BUNDLES: dict[str, _Bundle] = {"ko": _KO, "en": _EN, "ja": _JA, "zh": _ZH}


def t(lang: str) -> _Bundle:
    return _BUNDLES.get(lang, _EN)


PERSONA_LANGUAGE_INSTRUCTION: dict[str, str] = {
    "ko": "Always respond in Korean (한국어).",
    "en": "Always respond in English.",
    "ja": "Always respond in Japanese (日本語).",
    "zh": "Always respond in Simplified Chinese (简体中文).",
}
