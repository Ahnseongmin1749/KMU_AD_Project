import os
from transformers import pipeline

HATE_KEYWORDS = [
    "죽어", "꺼져", "병신", "멍청", "혐오", "쓰레기", "벌레", "추방",
    "열등", "재앙", "없애", "박멸", "범죄자", "XX들", "놈들"
]

POSITIVE_LABEL_HINTS = ("hate", "toxic", "offensive", "abuse", "insult", "toxin")
NEGATIVE_LABEL_HINTS = ("non", "neutral", "clean", "normal", "safe", "none")

THEME_KEYWORDS = {
    "politics": ["정치", "좌파", "우파", "보수", "진보", "정부", "대통령", "국회"],
    "gender": ["남자", "여자", "페미", "한남", "한녀", "성별", "미소지니", "미소andry"],
    "region": ["지역", "지방", "서울", "경상", "전라", "충청", "강원", "제주"],
    "race_nationality": ["외국인", "이민", "난민", "인종", "국적", "동남아", "중국인", "흑인"],
    "religion": ["종교", "기독교", "불교", "이슬람", "천주교", "개신교"],
    "class_age": ["노인", "꼰대", "MZ", "급식", "세대", "서민", "부자", "가난"],
}

# 한국어 텍스트 및 댓글 혐오 표현 분류에 특화된 오픈소스 pre-trained 모델 로드
# 모델이 최초 실행될 때 자동으로 다운로드됩니다.
DEFAULT_HATE_MODEL = os.getenv("HATE_MODEL_NAME", "unitary/multilingual-toxic-xlm-roberta")
FALLBACK_MODEL = "beomi/KcELECTRA-base"

print(f"[Module 2] 혐오 탐지 AI 모델 로드 중... ({DEFAULT_HATE_MODEL})")
try:
    hate_classifier = pipeline(
        "text-classification",
        model=DEFAULT_HATE_MODEL,
        tokenizer=DEFAULT_HATE_MODEL
    )
except Exception as e:
    print(f"[Module 2] 기본 모델 로드 실패: {e}")
    print(f"[Module 2] 폴백 모델로 전환: {FALLBACK_MODEL}")
    hate_classifier = pipeline(
        "text-classification",
        model=FALLBACK_MODEL,
        tokenizer=FALLBACK_MODEL
    )


def _normalize_label(label: str) -> str:
    return str(label).strip().lower().replace("-", "_")


def _keyword_features(text: str) -> tuple[list, float]:
    lowered = text.lower()
    hit_tokens = [token for token in HATE_KEYWORDS if token.lower() in lowered]
    hit_count = len(hit_tokens)
    # 키워드 히트 수에 따라 최대 0.25까지 가산
    return hit_tokens, min(0.25, 0.08 * hit_count)


def _classify_theme(text: str) -> tuple[str, list]:
    lowered = text.lower()
    scores = {}
    matches = {}
    for theme, keywords in THEME_KEYWORDS.items():
        hit_terms = [kw for kw in keywords if kw.lower() in lowered]
        if hit_terms:
            scores[theme] = len(hit_terms)
            matches[theme] = hit_terms

    if not scores:
        return "general", []

    best_theme = max(scores, key=scores.get)
    return best_theme, matches.get(best_theme, [])


def _extract_hate_score(prediction_output) -> float:
    # pipeline(top_k=None) 반환 형태를 표준화
    if isinstance(prediction_output, list) and prediction_output and isinstance(prediction_output[0], list):
        scores_list = prediction_output[0]
    elif isinstance(prediction_output, list):
        scores_list = prediction_output
    else:
        scores_list = [prediction_output]

    label_scores = {}
    for item in scores_list:
        label = _normalize_label(item.get("label", ""))
        score = float(item.get("score", 0.0))
        label_scores[label] = score

    # 명시적 혐오 라벨 우선
    positive_scores = [
        score for label, score in label_scores.items()
        if any(hint in label for hint in POSITIVE_LABEL_HINTS)
    ]
    if positive_scores:
        return max(positive_scores)

    # 비혐오 라벨만 있는 경우 역변환
    negative_scores = [
        score for label, score in label_scores.items()
        if any(hint in label for hint in NEGATIVE_LABEL_HINTS)
    ]
    if negative_scores:
        return 1.0 - max(negative_scores)

    # 일반 binary 분류에서 LABEL_1을 혐오 클래스로 가정
    if "label_1" in label_scores:
        return label_scores["label_1"]
    if "label_0" in label_scores:
        return 1.0 - label_scores["label_0"]

    # 라벨 정보를 알 수 없으면 보수적으로 최고 점수 사용
    return max(label_scores.values()) if label_scores else 0.0


def evaluate_hate_speech(comment_obj: dict, threshold: float = 0.62) -> dict:
    """
    수집된 댓글의 맥락(Context Vector)을 분석하여 공격성, 편향성, 모욕성을 다중 라벨링합니다.
    Hate Score가 설정된 임계치(τ) 이상일 경우 '대응 타겟' 큐로 적재합니다.
    """
    text = comment_obj["raw_text"]

    # AI 모델을 통한 감성 및 혐오 판단 점수 계산
    prediction = hate_classifier(text, top_k=None, truncation=True, max_length=256)
    model_score = _extract_hate_score(prediction)
    keyword_hits, keyword_boost = _keyword_features(text)
    hate_score = min(1.0, model_score + keyword_boost)
    theme, theme_terms = _classify_theme(text)
    
    comment_obj["hate_score"] = hate_score
    comment_obj["theme"] = theme
    comment_obj["theme_terms"] = theme_terms
    comment_obj["rationale"] = {
        "model_score": round(model_score, 4),
        "keyword_boost": round(keyword_boost, 4),
        "keyword_hits": keyword_hits,
        "theme_terms": theme_terms,
        "threshold": threshold,
        "final_score": round(hate_score, 4),
    }
    
    # Decision Gate: 임계치(τ) 판단 알고리즘
    if hate_score >= threshold:
        comment_obj["decision"] = "TARGET_REJECT"
        comment_obj["decision_reason"] = (
            f"score={hate_score:.2f} (model={model_score:.2f} + keyword={keyword_boost:.2f}) >= {threshold:.2f}"
        )
        print(
            f"🚨 [Module 2] 혐오 댓글 감지 (점수: {hate_score:.2f}, 주제: {theme}): "
            f"{text[:20]}..."
        )
    else:
        comment_obj["decision"] = "PASS"
        comment_obj["decision_reason"] = (
            f"score={hate_score:.2f} (model={model_score:.2f} + keyword={keyword_boost:.2f}) < {threshold:.2f}"
        )
        print(f"[Module 2] 일반 댓글 판정 (점수: {hate_score:.2f}): {text[:20]}...")
        
    return comment_obj