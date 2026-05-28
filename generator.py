import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# .env 파일에 저장된 OPENAI_API_KEY 로드
load_dotenv()

THEME_GUIDE = {
    "politics": "정책 근거와 제도 맥락을 강조해 과열된 진영 프레임을 완화하세요.",
    "gender": "성별 일반화의 오류를 짚고 상호존중 관점으로 전환하세요.",
    "region": "지역 집단 일반화를 피하고 개인 단위 판단 원칙을 강조하세요.",
    "race_nationality": "국적/인종 일반화의 위험성과 사실 기반 판단을 강조하세요.",
    "religion": "신념의 자유와 타인 권리의 균형을 차분히 설명하세요.",
    "class_age": "세대/계층 낙인을 피하고 구조적 요인을 분리해 설명하세요.",
    "general": "감정적 표현을 줄이고 검증 가능한 사실 중심으로 안내하세요.",
}

LOCAL_FALLBACK_PREFIX = {
    "politics": "정책 논의는 진영 비난보다 근거 비교가 더 생산적입니다.",
    "gender": "성별 전체를 일반화하면 문제 해결이 어려워집니다.",
    "region": "지역 전체를 하나로 묶어 단정하기보다 개인 단위 사실 확인이 필요합니다.",
    "race_nationality": "국적이나 인종을 근거로 단정하면 오해와 갈등이 커질 수 있습니다.",
    "religion": "신념 차이는 비난보다 상호 존중과 사실 검증으로 다루는 편이 좋습니다.",
    "class_age": "세대나 계층 전체를 낙인찍기보다 구체적 원인을 분리해 보는 것이 좋습니다.",
    "general": "감정적 단정보다 검증 가능한 근거를 중심으로 대화하는 것이 안전합니다.",
}


def _local_fallback_counter_speech(hate_comment_text: str, theme: str, repeated_count: int) -> str:
    prefix = LOCAL_FALLBACK_PREFIX.get(theme, LOCAL_FALLBACK_PREFIX["general"])
    spread_line = (
        "같은 주장 반복이 갈등을 키울 수 있어, 표현 수위를 낮추고 사실 중심으로 정리해 주세요."
        if repeated_count > 1
        else "표현 수위를 조금 낮추고 구체적 근거를 함께 제시해 주시면 논의에 도움이 됩니다."
    )
    return f"{prefix} {spread_line}"

def generate_counter_speech(hate_comment_text: str, theme: str = "general", repeated_count: int = 1) -> str:
    """
    RAG Engine 구조를 모사하여 팩트 데이터베이스를 참조한 후,
    Fine-tuned LLM을 통해 감정을 철저히 배제한 중립적이고 이성적인 반박 댓글을 생성합니다.
    """
    if not os.getenv("OPENAI_API_KEY"):
        fallback = _local_fallback_counter_speech(
            hate_comment_text=hate_comment_text,
            theme=theme,
            repeated_count=repeated_count,
        )
        print("[Module 3] OPENAI_API_KEY 미설정: 로컬 폴백 반박문 생성 로직 사용")
        print(f"🤖 [Module 3] 반박문 생성 완료(Local Fallback): {fallback}")
        return fallback

    # 가상의 Fact-check DB 검색 메커니즘 (RAG Knowledge Base 역할)
    # 실제 구현 시 ChromaDB의 similarity_search 결과가 들어갈 영역
    mock_fact_context = (
        "통계청 조사 결과에 따르면, 해당 집단의 실제 범죄율 및 사회적 비용 야기 비율은 "
        "일반 집단과 통계적으로 유의미한 차이가 없으며 오히려 감소 추세에 있음이 검증되었습니다."
    )
    
    # 1. 대형 언어 모델 아키텍처 선언 (온도를 낮춰 이성적이고 일관된 문장 생성 강제)
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0.2)
    theme_instruction = THEME_GUIDE.get(theme, THEME_GUIDE["general"])
    mode_instruction = (
        "반복 선동 패턴이 관측된 상황이므로, 댓글 확산을 낮추는 톤으로 오해를 바로잡아라."
        if repeated_count > 1
        else ""
    )
    
    # 2. 역할과 제약 조건을 엄격하게 주입하는 프롬프트 엔지니어링 설계
    system_prompt = (
        "너는 인터넷 여론의 무분별한 극단화와 혐오 확산을 방지하는 이성적인 커뮤니티 중재자 AI다.\n"
        "제공되는 [객관적 팩트]에만 철저히 기반하여, 감정을 완전히 배제하고 논리적 오류를 점잖게 지적하는 "
        "중립적인 반박 댓글(Counter-Speech)을 한국어로 단 1줄(짧고 간결하게)로 작성해라.\n"
        "상대방을 비난하거나 조롱하지 말고, 존댓말을 사용하여 신뢰감을 주도록 해라.\n"
        f"[주제별 가이드] {theme_instruction}\n"
        f"[확산 억제 모드] {mode_instruction}"
    )
    
    user_prompt = (
        "[객관적 팩트]: {context}\n"
        "[탐지 주제]: {theme}\n"
        "[반복 관측 횟수]: {repeated_count}\n"
        "[인터넷 혐오 댓글]: {hate_comment}\n\n"
        "정화용 대응 댓글:"
    )
    
    # LangChain 파이프라인 구성
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", user_prompt)
    ])
    
    # 3. Chain 실행 및 결과 반환
    chain = prompt_template | llm
    try:
        response = chain.invoke({
            "context": mock_fact_context,
            "theme": theme,
            "repeated_count": repeated_count,
            "hate_comment": hate_comment_text
        })
        counter_speech = response.content.strip()
        print(f"🤖 [Module 3] 반박문 생성 완료: {counter_speech}")
        return counter_speech
    except Exception as e:
        # 쿼터 초과(429) 또는 일시적인 API 장애 시 파이프라인 중단 없이 폴백으로 진행
        fallback = _local_fallback_counter_speech(
            hate_comment_text=hate_comment_text,
            theme=theme,
            repeated_count=repeated_count,
        )
        print(f"[Module 3] API 생성 실패로 로컬 폴백 사용: {e}")
        print(f"🤖 [Module 3] 반박문 생성 완료(Local Fallback): {fallback}")
        return fallback