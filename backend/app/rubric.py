SCALE_MIN = 1
SCALE_MAX = 5

RUBRIC_CRITERIA = [
    {
        "id": "problem_clarity",
        "name": "課題の明確さ・切実さ",
        "description": (
            "5=課題が具体的な数値・エピソードで裏付けられ、切実さが伝わる／"
            "3=課題は述べられているが裏付けが弱い／"
            "1=課題が曖昧、または誰の課題か不明"
        ),
    },
    {
        "id": "solution_originality",
        "name": "解決策の独自性・有効性",
        "description": (
            "5=既存手段との違いが明確で、課題解決への筋道が具体的かつ説得力がある／"
            "3=解決策はあるが独自性や効果の裏付けが弱い／"
            "1=解決策が課題と結びついていない、または既存手段と差がない"
        ),
    },
    {
        "id": "market_fit",
        "name": "市場性・ターゲット顧客の妥当性",
        "description": (
            "5=ターゲット顧客像が具体的で、その顧客が対価を払う理由まで示されている／"
            "3=ターゲットには触れているが顧客像や需要の根拠が弱い／"
            "1=誰に向けた事業か分からない"
        ),
    },
    {
        "id": "business_plan_roadmap",
        "name": "事業計画の具体性・実行ロードマップ",
        "description": (
            "5=立ち上げから事業化までのステップ・時期・必要な資源が具体的に示されている／"
            "3=大まかな流れはあるが時期や必要資源など具体性に欠ける／"
            "1=事業計画・実行手順への言及がない"
        ),
    },
    {
        "id": "financial_plan",
        "name": "収支計画・数値の妥当性",
        "description": (
            "5=売上根拠・単価・コスト構造・損益分岐点などの数値が具体的かつ現実的に示されている／"
            "3=収支計画はあるが数値の根拠が弱い、または楽観的すぎる／"
            "1=収支計画・数値への言及がない"
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
