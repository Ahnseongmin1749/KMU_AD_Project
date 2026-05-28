import asyncio
import os
import re
from getpass import getpass
from collections import defaultdict
from crawler import scrape_sns_comments
from detector import evaluate_hate_speech
from generator import generate_counter_speech
from poster import post_counter_speech


def _normalize_theme_key(text: str) -> str:
    cleaned = re.sub(r"[^0-9a-zA-Z가-힣\s]", " ", text.lower())
    tokens = [t for t in cleaned.split() if len(t) >= 2]
    if not tokens:
        return text.strip().lower()[:40]
    return " ".join(tokens[:8])


def _build_propaganda_key(evaluated_item: dict) -> str:
    theme = evaluated_item.get("theme", "general")
    terms = sorted(set(evaluated_item.get("theme_terms", [])))
    if terms:
        return f"{theme}|{'/'.join(terms[:4])}"
    return f"{theme}|{_normalize_theme_key(evaluated_item.get('raw_text', ''))}"


def _print_decision_rationale(evaluated_item: dict) -> None:
    rationale = evaluated_item.get("rationale", {})
    model_score = rationale.get("model_score", 0.0)
    keyword_boost = rationale.get("keyword_boost", 0.0)
    threshold = rationale.get("threshold", 0.0)
    hits = rationale.get("keyword_hits", [])
    theme = evaluated_item.get("theme", "general")
    hit_text = ", ".join(hits[:5]) if hits else "없음"
    print(
        "[판정 근거] "
        f"theme={theme}, model={model_score:.2f}, keyword_boost={keyword_boost:.2f}, "
        f"threshold={threshold:.2f}, hits={hit_text}"
    )
    print(f"[판정식] {evaluated_item.get('decision_reason', '근거 정보 없음')}")

async def main():
    print("=========================================================")
    print("🚀 AI 기반 SNS 혐오 댓글 완화 시스템 파이프라인 가동")
    print("=========================================================")

    # 키를 저장소에 남기지 않기 위해 런타임 입력을 지원합니다.
    if not os.getenv("OPENAI_API_KEY"):
        use_runtime_key = input("OpenAI API 키를 런타임에 입력할까요? (y/N): ").strip().lower()
        if use_runtime_key in ("y", "yes"):
            runtime_key = getpass("OPENAI_API_KEY 입력(화면에 표시되지 않음): ").strip()
            if runtime_key:
                os.environ["OPENAI_API_KEY"] = runtime_key
                print("[보안] 런타임 API 키가 메모리에만 설정되었습니다.")
            else:
                print("[보안] 빈 값이 입력되어 로컬 폴백 생성 모드로 진행합니다.")
        else:
            print("[보안] API 키 없이 실행되어 로컬 폴백 생성 모드로 진행합니다.")
    
    # 실행 시 분석하고자 하는 URL을 입력받습니다.
    target_url = input("분석할 유튜브 영상 URL을 입력하세요: ").strip()
    if not target_url:
        print("[입력 오류] URL이 비어 있습니다. 프로그램을 종료합니다.")
        return

    try:
        max_comments_input = input("수집할 최대 댓글 수를 입력하세요(기본 30): ").strip()
        max_comments = int(max_comments_input) if max_comments_input else 30
        if max_comments <= 0:
            print("[입력 오류] 댓글 수는 1 이상이어야 합니다. 기본값 30을 사용합니다.")
            max_comments = 30
    except ValueError:
        print("[입력 오류] 숫자가 아니어서 기본값 30을 사용합니다.")
        max_comments = 30

    try:
        repeat_threshold_input = input("반복 선동 임계치(동일 계열 댓글 수, 기본 3): ").strip()
        repeat_threshold = int(repeat_threshold_input) if repeat_threshold_input else 3
        if repeat_threshold <= 1:
            print("[입력 오류] 임계치는 2 이상이어야 합니다. 기본값 3을 사용합니다.")
            repeat_threshold = 3
    except ValueError:
        print("[입력 오류] 숫자가 아니어서 반복 선동 임계치 기본값 3을 사용합니다.")
        repeat_threshold = 3
    
    # Step 1: 데이터 수집 (Module 1)
    raw_comments = await scrape_sns_comments(target_url, max_comments=max_comments)

    if not raw_comments:
        print("[Module 1] 수집된 댓글이 없습니다. URL 또는 페이지 공개 상태를 확인해 주세요.")
        return
    
    grouped_hate_comments = defaultdict(list)

    # Step 2~4: 수집된 댓글 순회하며 처리
    for comment_item in raw_comments:
        print("\n---------------------------------------------------------")
        print(f"🔍 원본 댓글 분석 시작: \"{comment_item['raw_text']}\"")
        
        # 혐오 표현 인지 및 탐지 (Module 2)
        evaluated_item = evaluate_hate_speech(comment_item, threshold=0.55)
        _print_decision_rationale(evaluated_item)
        
        # Decision Gate 결과 검증
        if evaluated_item["decision"] == "TARGET_REJECT":
            propaganda_key = _build_propaganda_key(evaluated_item)
            grouped_hate_comments[propaganda_key].append(evaluated_item)

            # RAG 기반 중립 반박문 생성 (Module 3)
            counter_speech = generate_counter_speech(
                evaluated_item["raw_text"],
                theme=evaluated_item.get("theme", "general"),
                repeated_count=1
            )
            print(f"[생성 댓글] {counter_speech}")
            
            # 자동 매크로 포스팅 에이전트 실행 (Module 4)
            posted = post_counter_speech(evaluated_item, counter_speech)
            print(f"[포스팅 결과] {'실제 게시됨' if posted else '드라이런(미게시)'}")
        else:
            print("[Decision Gate] 건전하거나 평범한 댓글입니다. 작업을 패스합니다.")

    # Step 5: 유사 혐오 선동 반복 패턴 감지 시, 추가 반대댓글 1회 생성
    repeated_themes = [
        items for items in grouped_hate_comments.values()
        if len(items) >= repeat_threshold
    ]

    if repeated_themes:
        print("\n=========================================================")
        print("📌 반복 선동 패턴 감지: 추가 반대댓글 생성 단계 실행")
        print("=========================================================")

    for items in repeated_themes:
        representative = max(items, key=lambda x: x.get("hate_score", 0.0))
        repeated_count = len(items)
        theme = representative.get("theme", "general")
        aggregate_prompt = (
            f"다수 유사 댓글에서 반복된 선동성 주장입니다 (관측 {repeated_count}건): "
            f"{representative['raw_text']}"
        )

        extra_counter_speech = generate_counter_speech(
            aggregate_prompt,
            theme=theme,
            repeated_count=repeated_count
        )
        print(f"[반복 패턴 추가 생성 댓글] {extra_counter_speech}")
        posted = post_counter_speech(
            {
                "source_url": representative.get("source_url", target_url),
                "raw_text": aggregate_prompt,
                "hate_score": representative.get("hate_score", 0.0),
                "theme": theme,
                "decision": "TARGET_REJECT"
            },
            extra_counter_speech
        )
        print(f"[포스팅 결과] {'실제 게시됨' if posted else '드라이런(미게시)'}")
        print(
            f"[Pattern 대응] 주제={theme}, 유사 혐오 댓글 {repeated_count}건에 대한 "
            "추가 반대댓글 1건 생성 완료"
        )
            
    print("\n=========================================================")
    print("✅ 모든 분석 및 여론 균형화 작업이 성공적으로 종료되었습니다.")
    print("=========================================================")

if __name__ == "__main__":
    # 비동기 루프 실행
    asyncio.run(main())