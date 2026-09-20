SCALE_MIN = 1
SCALE_MAX = 5

# 「起業の科学」（田所雅之）のリーンスタートアップ検証プロセス
# （ペインの質 → CPF → PSF → 市場・収益性の定量分析 → PMF）に沿ったルーブリック。
BUSINESS_RUBRIC_CRITERIA = [
    {
        "id": "pain_quality",
        "name": "ペインの質・課題の深さ（Whom/Occasion/Painkillerかビタミンか）",
        "description": (
            "5=誰が(Whom)・どんな時に(Occasion)感じる痛みかが具体的で、"
            "既存の代替手段より優れた「痛み止め（Painkiller）」であることが示されている／"
            "3=課題はあるが「痛み止め」か「ビタミン剤（あれば嬉しい程度）」かの見極めが弱い／"
            "1=誰のどんな痛みかが不明、または対価を払う理由が見えない"
        ),
    },
    {
        "id": "cpf_validation",
        "name": "顧客・課題の検証度（CPF: Customer Problem Fit）",
        "description": (
            "5=顧客インタビューなど一次情報に基づき、想定顧客が実際にその課題を抱えていることが"
            "具体的な人数・発言とともに検証されている／"
            "3=検証への言及はあるが人数や手法が不明確／"
            "1=顧客への検証が行われていない、または想像のみで語られている"
        ),
    },
    {
        "id": "psf_validation",
        "name": "解決策の検証度（PSF: Problem Solution Fit）",
        "description": (
            "5=MVPやプロトタイプを用いた検証により、解決策が課題を実際に解決できることが"
            "具体的な結果とともに示されている／"
            "3=解決策の検証はあるが定性的・限定的／"
            "1=解決策が机上の議論にとどまり検証されていない"
        ),
    },
    {
        "id": "market_sizing_economics",
        "name": "市場・収益性の定量分析（TAM/SAM/SOM・Unit Economics）",
        "description": (
            "5=TAM/SAM/SOMが具体的な根拠とともに算出され、LTV/CACなど1顧客あたりの経済性も"
            "現実的な数値で示されている／"
            "3=市場規模や収益性への言及はあるが算出根拠が粗い／"
            "1=市場規模・収益性の定量的な分析がない"
        ),
    },
    {
        "id": "pmf_growth_potential",
        "name": "市場適合・グロース可能性（PMF兆候）",
        "description": (
            "5=継続利用率・口コミ・リピート購入など、プロダクトが市場に受け入れられている兆候が"
            "具体的に示され、今後のスケール戦略も描かれている／"
            "3=市場適合の兆候への言及はあるが根拠が弱い／"
            "1=市場適合やスケールへの言及がない"
        ),
    },
    {
        "id": "team_execution",
        "name": "チームの実行力",
        "description": (
            "5=事業に必要な専門性・実績が明確でチーム体制に説得力がある／"
            "3=チーム紹介はあるが実行力の裏付けが弱い／"
            "1=チームについて触れられていない"
        ),
    },
    {
        "id": "presentation_clarity",
        "name": "プレゼンの分かりやすさ・訴求力",
        "description": (
            "5=構成が論理的で、聞き手を惹きつける展開・話し方になっている／"
            "3=概ね分かりやすいが冗長・構成が弱い部分がある／"
            "1=構成が分かりにくい、または要点が伝わらない"
        ),
    },
]

# 業界・テーマを問わない汎用ピッチ審査ルーブリック
# （ビジネスモデルや収益性を前提としない、課題〜実現可能性〜インパクト〜検証〜実行力〜伝達力の観点）。
GENERAL_RUBRIC_CRITERIA = [
    {
        "id": "problem_clarity",
        "name": "課題の明確さ・意義",
        "description": (
            "5=解決しようとしている課題・ニーズが具体的で、その重要性が伝わる／"
            "3=課題は述べられているが重要性の裏付けが弱い／"
            "1=課題が曖昧、または誰のための取り組みか不明"
        ),
    },
    {
        "id": "solution_originality",
        "name": "解決策・アイデアの独自性と有効性",
        "description": (
            "5=既存の取り組みとの違いが明確で、課題解決への筋道が具体的かつ説得力がある／"
            "3=解決策はあるが独自性や効果の裏付けが弱い／"
            "1=解決策が課題と結びついていない、または既存の取り組みと差がない"
        ),
    },
    {
        "id": "feasibility_roadmap",
        "name": "実現可能性・実行計画",
        "description": (
            "5=実現までの具体的なステップ・スケジュール・必要なリソースが示されている／"
            "3=大まかな計画はあるが時期や必要資源など具体性に欠ける／"
            "1=実現に向けた計画への言及がない"
        ),
    },
    {
        "id": "impact_significance",
        "name": "インパクト・意義の大きさ",
        "description": (
            "5=取り組みが実現した際に及ぶ影響の範囲・規模が具体的に示されている／"
            "3=意義への言及はあるが影響の規模感が不明確／"
            "1=インパクトへの言及がない"
        ),
    },
    {
        "id": "evidence_validation",
        "name": "検証・裏付けの質",
        "description": (
            "5=データ・実験・ヒアリングなど具体的な根拠に基づいて主張が裏付けられている／"
            "3=根拠の提示はあるが弱い、または部分的／"
            "1=主張を裏付ける検証・データがない"
        ),
    },
    {
        "id": "team_execution",
        "name": "実行体制・チームの実行力",
        "description": (
            "5=取り組みに必要な専門性・実績が明確で、体制に説得力がある／"
            "3=体制の紹介はあるが実行力の裏付けが弱い／"
            "1=実行体制について触れられていない"
        ),
    },
    {
        "id": "presentation_clarity",
        "name": "プレゼンの分かりやすさ・訴求力",
        "description": (
            "5=構成が論理的で、聞き手を惹きつける展開・話し方になっている／"
            "3=概ね分かりやすいが冗長・構成が弱い部分がある／"
            "1=構成が分かりにくい、または要点が伝わらない"
        ),
    },
]

RUBRIC_MODES = {
    "business": {
        "label": "ビジネスコンテスト向け（起業の科学ベース）",
        "criteria": BUSINESS_RUBRIC_CRITERIA,
    },
    "general": {
        "label": "汎用ピッチ審査",
        "criteria": GENERAL_RUBRIC_CRITERIA,
    },
}

DEFAULT_MODE = "business"


def get_rubric_criteria(mode: str) -> list[dict]:
    if mode not in RUBRIC_MODES:
        raise ValueError(f"unknown rubric mode: {mode}")
    return RUBRIC_MODES[mode]["criteria"]


def get_rubric_label(mode: str) -> str:
    if mode not in RUBRIC_MODES:
        raise ValueError(f"unknown rubric mode: {mode}")
    return RUBRIC_MODES[mode]["label"]


def compute_overall_score(criterion_scores: list[int], mode: str) -> int:
    max_total = len(get_rubric_criteria(mode)) * SCALE_MAX
    return round(sum(criterion_scores) / max_total * 100)
