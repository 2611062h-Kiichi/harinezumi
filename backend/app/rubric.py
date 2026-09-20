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
        "id": "market_potential",
        "name": "市場規模・成長性",
        "description": (
            "5=市場規模の根拠となるデータがあり、成長性も具体的に示されている／"
            "3=市場規模には触れているが根拠が弱い／"
            "1=市場規模・成長性への言及がない"
        ),
    },
    {
        "id": "business_model",
        "name": "ビジネスモデル・収益性",
        "description": (
            "5=収益構造・単価・コスト構造が具体的で、持続可能性が示されている／"
            "3=収益モデルはあるが数字の裏付けが弱い／"
            "1=どう収益を上げるか説明がない"
        ),
    },
    {
        "id": "traction",
        "name": "トラクション・検証状況",
        "description": (
            "5=顧客の声・利用実績・数値指標など具体的な検証結果が示されている／"
            "3=検証への言及はあるが定性的で数字が弱い／"
            "1=検証・実績への言及が全くない"
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
