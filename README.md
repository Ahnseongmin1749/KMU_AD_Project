# SNS Hate-Speech Mitigation & Counter-Speech System

본 프로젝트는 AI 기술을 활용하여 SNS 상의 무분별한 혐오 표현 및 갈등을 탐지하고, 이에 대응하는 중립적·이성적 반박 댓글을 생성 및 자동화하는 파이프라인 아키텍처입니다.

## 🛠️ 의존성 라이브러리 및 핵심 모듈 기능 요약

프로젝트 구동 및 구현을 위해 설치하는 6가지 오픈소스 라이브러리의 상세 역할과 기능 정의는 다음과 같습니다.

| 라이브러리명 | 아키텍처 내 담당 모듈 | 핵심 기능 및 정체 |
| :--- | :--- | :--- |
| **`playwright`** | **Module 1**<br>(Data Ingestion) | **비동기 웹 브라우저 자동화 및 동적 크롤링 도구**<br>유튜브, 인스타그램 등 스크롤 다운이나 버튼 클릭이 필요한 동적 자바스크립트 렌더링 페이지에서 실시간 댓글 트래픽과 컨텐츠 데이터를 봇 제재를 우회하여 고속 수집합니다. |
| **`transformers`** | **Module 2**<br>(Context Evaluation) | **Hugging Face의 사전 학습(Pre-trained) NLP 모델 엔진**<br>한국어 댓글 및 악플 분석에 특화된 딥러닝 모델(`KcELECTRA`)을 로드하여, 수집된 텍스트의 맥락(Context Vector)을 분석하고 혐오 점수(Hate Score)를 연산합니다. |
| **`torch`** | **Module 2**<br>(AI Core Backend) | **PyTorch 인공지능 연산 프레임워크**<br>`transformers` 알고리즘이 내부적으로 컴퓨터의 CPU/GPU 자원을 사용하여 텍스트 분류 및 신경망 연산을 수행할 수 있도록 지원하는 핵심 인프라 백엔드입니다. |
| **`langchain`** | **Module 3**<br>(Counter-Speech RAG) | **LLM 기반 애플리케이션 빌딩 프레임워크**<br>외부 팩트체크 데이터베이스(Fact-check DB)에서 필요한 정보를 검색한 뒤, 이를 생성형 AI 모델과 결합하여 논리적 구조를 만드는 **RAG(검색 증강 생성) 파이프라인**을 설계하고 통제합니다. |
| **`langchain-openai`**| **Module 3**<br>(LLM Generator) | **OpenAI API 연동 모듈**<br>LangChain 아키텍처 위에서 OpenAI의 고성능 거대 언어 모델(GPT-4o 등)을 호출하여, 시스템 프롬프트에 튜닝된 '감정이 배제된 정중한 중립 반박문'을 실제로 생성합니다. |
| **`python-dotenv`** | **보안 및 환경설정** | **환경 변수(.env) 로드 파일 관리 도구**<br>OpenAI API Key 등 깃허브에 노출되면 안 되는 민감한 보안 자격 증명을 로컬 `.env` 파일에서 안전하게 읽어와 소스 코드 내에 주입합니다. |

---

## 🚀 설치 및 구동 방법

### 1. 환경 설정 및 라이브러리 설치
터미널 환경에서 프로젝트에 필요한 외부 모듈을 일괄 설치합니다.
```bash
python -m pip install playwright transformers torch langchain langchain-openai python-dotenv
