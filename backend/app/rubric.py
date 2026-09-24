SCALE_MIN = 1
SCALE_MAX = 5

# Each criterion's "levels" is an ordered list of 5 descriptions (low to high),
# used both as the Jev Score primitive's `criteria` argument and to give
# Claude the same rubric context when writing per-criterion comments.

# 「起業の科学」（田所雅之）のリーンスタートアップ検証プロセス
# （ペインの質 → CPF → PSF → 市場・収益性の定量分析 → PMF）に沿ったルーブリック。
BUSINESS_RUBRIC_CRITERIA = [
    {
        "id": "pain_quality",
        "name": "ペインの質・課題の深さ（Whom/Occasion/Painkillerかビタミンか）",
        "levels": [
            "誰のどんな痛みかが不明、または対価を払う理由が見えない",
            "課題は述べられているが、誰の・どんな場面の痛みかが曖昧",
            "誰が・どんな時に感じる痛みかは分かるが、切実さの裏付けが弱い",
            "誰が・どんな時に感じる痛みかが具体的で、一定の切実さが伝わる",
            "誰が・どんな時に感じる痛みかが具体的で、既存の代替手段より優れた「痛み止め（Painkiller）」であることが示されている",
        ],
    },
    {
        "id": "cpf_validation",
        "name": "顧客・課題の検証度（CPF: Customer Problem Fit）",
        "levels": [
            "顧客への検証が行われていない、または想像のみで語られている",
            "検証への言及はあるが、手法や人数が全く不明",
            "検証への言及はあるが人数や手法が不明確",
            "一定数の顧客インタビュー等の検証があるが、具体性や深掘りが弱い",
            "顧客インタビューなど一次情報に基づき、想定顧客が実際にその課題を抱えていることが具体的な人数・発言とともに検証されている",
        ],
    },
    {
        "id": "psf_validation",
        "name": "解決策の検証度（PSF: Problem Solution Fit）",
        "levels": [
            "解決策が机上の議論にとどまり検証されていない",
            "解決策への言及はあるが検証の形跡がない",
            "解決策の検証はあるが定性的・限定的",
            "MVP等での検証はあるが、結果の裏付けがやや弱い",
            "MVPやプロトタイプを用いた検証により、解決策が課題を実際に解決できることが具体的な結果とともに示されている",
        ],
    },
    {
        "id": "market_sizing_economics",
        "name": "市場・収益性の定量分析（TAM/SAM/SOM・Unit Economics）",
        "levels": [
            "市場規模・収益性の定量的な分析がない",
            "市場規模や収益性への言及はあるが数字が一切ない",
            "市場規模や収益性への言及はあるが算出根拠が粗い",
            "TAM/SAM/SOMまたはUnit Economicsのどちらかは示されているが、もう一方が弱い",
            "TAM/SAM/SOMが具体的な根拠とともに算出され、LTV/CACなど1顧客あたりの経済性も現実的な数値で示されている",
        ],
    },
    {
        "id": "pmf_growth_potential",
        "name": "市場適合・グロース可能性（PMF兆候）",
        "levels": [
            "市場適合やスケールへの言及がない",
            "市場適合への言及はあるが根拠が全くない",
            "市場適合の兆候への言及はあるが根拠が弱い",
            "継続利用や口コミ等の兆候はあるが、スケール戦略の具体性がやや弱い",
            "継続利用率・口コミ・リピート購入など、プロダクトが市場に受け入れられている兆候が具体的に示され、今後のスケール戦略も描かれている",
        ],
    },
    {
        "id": "team_execution",
        "name": "チームの実行力",
        "levels": [
            "チームについて触れられていない",
            "チームメンバーの紹介はあるが、専門性や役割が不明",
            "チーム紹介はあるが実行力の裏付けが弱い",
            "専門性や役割は示されているが、実績の裏付けがやや弱い",
            "事業に必要な専門性・実績が明確でチーム体制に説得力がある",
        ],
    },
    {
        "id": "presentation_clarity",
        "name": "プレゼンの分かりやすさ・訴求力",
        "levels": [
            "構成が分かりにくい、または要点が伝わらない",
            "要点は伝わるが構成が場当たり的",
            "概ね分かりやすいが冗長・構成が弱い部分がある",
            "構成は論理的だが、訴求力や聞き手を惹きつける工夫がやや弱い",
            "構成が論理的で、聞き手を惹きつける展開・話し方になっている",
        ],
    },
]

# 業界・テーマを問わない汎用ピッチ審査ルーブリック
# （ビジネスモデルや収益性を前提としない、課題〜実現可能性〜インパクト〜検証〜実行力〜伝達力の観点）。
GENERAL_RUBRIC_CRITERIA = [
    {
        "id": "problem_clarity",
        "name": "課題の明確さ・意義",
        "levels": [
            "課題が曖昧、または誰のための取り組みか不明",
            "課題への言及はあるが重要性が全く伝わらない",
            "課題は述べられているが重要性の裏付けが弱い",
            "課題は具体的だが、重要性の裏付けがやや弱い",
            "解決しようとしている課題・ニーズが具体的で、その重要性が伝わる",
        ],
    },
    {
        "id": "solution_originality",
        "name": "解決策・アイデアの独自性と有効性",
        "levels": [
            "解決策が課題と結びついていない、または既存の取り組みと差がない",
            "解決策はあるが独自性が全く示されていない",
            "解決策はあるが独自性や効果の裏付けが弱い",
            "独自性は示されているが、効果の裏付けがやや弱い",
            "既存の取り組みとの違いが明確で、課題解決への筋道が具体的かつ説得力がある",
        ],
    },
    {
        "id": "feasibility_roadmap",
        "name": "実現可能性・実行計画",
        "levels": [
            "実現に向けた計画への言及がない",
            "計画への言及はあるが具体性が全くない",
            "大まかな計画はあるが時期や必要資源など具体性に欠ける",
            "計画はあるが、時期またはリソースのどちらかの具体性がやや弱い",
            "実現までの具体的なステップ・スケジュール・必要なリソースが示されている",
        ],
    },
    {
        "id": "impact_significance",
        "name": "インパクト・意義の大きさ",
        "levels": [
            "インパクトへの言及がない",
            "インパクトへの言及はあるが規模感が全く示されていない",
            "意義への言及はあるが影響の規模感が不明確",
            "影響の範囲は示されているが、規模の具体性がやや弱い",
            "取り組みが実現した際に及ぶ影響の範囲・規模が具体的に示されている",
        ],
    },
    {
        "id": "evidence_validation",
        "name": "検証・裏付けの質",
        "levels": [
            "主張を裏付ける検証・データがない",
            "根拠への言及はあるが具体性が全くない",
            "根拠の提示はあるが弱い、または部分的",
            "データや実験への言及はあるが、裏付けの厳密さがやや弱い",
            "データ・実験・ヒアリングなど具体的な根拠に基づいて主張が裏付けられている",
        ],
    },
    {
        "id": "team_execution",
        "name": "実行体制・チームの実行力",
        "levels": [
            "実行体制について触れられていない",
            "体制の紹介はあるが専門性・役割が不明",
            "体制の紹介はあるが実行力の裏付けが弱い",
            "専門性は示されているが、実績の裏付けがやや弱い",
            "取り組みに必要な専門性・実績が明確で、体制に説得力がある",
        ],
    },
    {
        "id": "presentation_clarity",
        "name": "プレゼンの分かりやすさ・訴求力",
        "levels": [
            "構成が分かりにくい、または要点が伝わらない",
            "要点は伝わるが構成が場当たり的",
            "概ね分かりやすいが冗長・構成が弱い部分がある",
            "構成は論理的だが、訴求力や聞き手を惹きつける工夫がやや弱い",
            "構成が論理的で、聞き手を惹きつける展開・話し方になっている",
        ],
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


def compute_overall_score(criterion_scores: list[float], mode: str) -> int:
    max_total = len(get_rubric_criteria(mode)) * SCALE_MAX
    return round(sum(criterion_scores) / max_total * 100)
