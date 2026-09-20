SCALE_MIN = 1
SCALE_MAX = 5

# 「起業の科学」（田所雅之）のリーンスタートアップ検証プロセス
# （ペインの質 → CPF → PSF → 市場・収益性の定量分析 → PMF）に沿ったルーブリック。
RUBRIC_CRITERIA = [
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

MAX_TOTAL_SCORE = len(RUBRIC_CRITERIA) * SCALE_MAX


def compute_overall_score(criterion_scores: list[int]) -> int:
    return round(sum(criterion_scores) / MAX_TOTAL_SCORE * 100)
