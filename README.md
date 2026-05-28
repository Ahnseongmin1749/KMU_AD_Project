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

### 2. 크롤러 브라우저 바이너리 다운로드
playwright 모듈의 웹 브라우저 인스턴스 제어를 위해 아래 명령어를 추가로 실행합니다.
```bash
playwright install

3. 시스템 실행
```bash
python main.py

# SNS Hate-Speech Mitigation & Counter-Speech System

본 프로젝트는 AI 기술을 활용하여 SNS 상의 무분별한 혐오 표현 및 갈등을 탐지하고, 이에 대응하는 중립적·이성적 반박 댓글을 생성 및 자동화하는 파이프라인 아키텍처입니다.

---

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

## 🧩 모듈별 상세 아키텍처 및 흐름 (Architecture Flow)

본 시스템은 데이터 수집부터 최종 액션까지 총 4개의 독립된 기능적 파이프라인(모듈)으로 구성되어 유기적으로 동작합니다.

### 1. Module 1: Data Ingestion (crawler.py)
* **목적**: 분석 대상이 되는 SNS 플랫폼의 실시간 텍스트 트래픽 확보
* **주요 기능**:
  * 타겟 URL(유튜브 동영상, 인스타그램 포스트 등) 인터페이스 접속 자동화
  * 동적 스크롤 제어를 통한 비동기 댓글 레이어 로딩 및 렌더링 대응
  * 플랫폼별 봇 탐지 정책을 우회하기 위한 휴먼 라이크(Human-like) 무작위 딜레이 메커니즘 적용
* **데이터 흐름**: `Target URL` ➔ `Playwright Engine` ➔ `Raw Text Data 추출`

### 2. Module 2: Context Evaluation Encoder (detector.py)
* **목적**: 수집된 원본 데이터 내의 혐오 표현 및 갈등 유발 요소 정밀 판독
* **주요 기능**:
  * 자연어 처리(NLP) 임베딩 모델을 활용한 문장의 언어 맥락 분석
  * 딥러닝 기반 텍스트 분류 알고리즘(`KcELECTRA`)을 통한 지능형 혐오 수치(Hate Score) 연산
  * 설정된 임계치(τ)를 기반으로 단순 일상 댓글과 선동형 혐오 댓글을 분리하는 Decision Gate 역할 수행
* **데이터 흐름**: `Raw Text Data` ➔ `NLP Embedding` ➔ `Hate Score 판정 (Target 선별)`

### 3. Module 3: Counter-Speech Generator (generator.py)
* **목적**: 감정적 동조를 배제하고 확증 편향을 완화할 수 있는 이성적 대응문 생성
* **주요 기능**:
  * 신뢰성 있는 외부 지식 베이스(Fact-check DB)와 연동하는 **RAG(검색 증강 생성)** 아키텍처 구현
  * OpenAI API를 결합하여 팩트 기반의 객관적인 검증 정보 추출
  * 시스템 프롬프트 제어를 통해 조롱이나 비하가 배제된 정중하고 논리적인 '중립 반박문(Counter-Speech)' 빌드
* **데이터 흐름**: `Target 혐오 댓글` + `Fact-Context` ➔ `LLM 파이프라인` ➔ `중립 반박문 생성`

### 4. Module 4: Automated Macro Agent (poster.py)
* **목적**: 생성된 건강한 여론 데이터를 플랫폼에 안전하게 환원 및 도배 방지
* **주요 기능**:
  * 탐지
