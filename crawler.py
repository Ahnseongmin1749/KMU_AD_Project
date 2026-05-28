import asyncio
import os
from playwright.async_api import async_playwright

async def scrape_sns_comments(url: str, max_comments: int = 30) -> list:
    """
    SNS Sources(유튜브/인스타)의 URL을 입력받아 실시간 댓글 트래픽을 수집합니다.
    Selenium보다 가볍고 비동기 처리가 빠른 Playwright를 기반으로 작동합니다.
    """
    comments_data = []
    max_comments = max(1, max_comments)
    
    # 1. 브라우저 구동 (Anti-bot 우회를 위해 headless=True/False 조절 가능)
    async with async_playwright() as p:
        # 디버깅 필요 시 CRAWLER_HEADLESS=false 로 실행하면 브라우저 UI를 확인할 수 있습니다.
        headless = os.getenv("CRAWLER_HEADLESS", "true").lower() != "false"
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        print(f"[Module 1] 타겟 URL 접속 중: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(2500)
        print(f"[Module 1] 실제 이동한 URL: {page.url}")

        # 쿠키 동의/지역 제한 페이지로 리다이렉트되면 댓글을 수집할 수 없습니다.
        if "consent.youtube.com" in page.url:
            print("[Module 1] YouTube 동의 페이지로 이동되었습니다. 브라우저에서 동의 후 재시도해 주세요.")
            await browser.close()
            return []

        if "watch" not in page.url:
            print("[Module 1] watch 페이지가 아닙니다. 일반 YouTube 영상 URL인지 확인해 주세요.")
            await browser.close()
            return []

        # 유튜브 댓글 섹션이 보이도록 먼저 충분히 아래로 이동
        for _ in range(4):
            await page.evaluate("window.scrollBy(0, Math.floor(window.innerHeight * 1.2));")
            await asyncio.sleep(1.0)

        # 댓글 컨테이너 자체가 렌더링될 때까지 대기
        comments_container_selector = "ytd-comments#comments"
        try:
            await page.wait_for_selector(comments_container_selector, timeout=25000)
        except Exception:
            page_text = (await page.content()).lower()
            if "comments are turned off" in page_text or "댓글이 사용 중지" in page_text:
                print("[Module 1] 이 영상은 댓글 기능이 비활성화되어 있습니다.")
            
            print("[Module 1] 댓글 컨테이너(ytd-comments)를 찾지 못했습니다. 영상 공개 상태/연령 제한/지역 제한을 확인해 주세요.")
            await browser.close()
            return []
        
        print("[Module 1] 인간 행동 모사(Human-like) 댓글 스크롤 다운 시작...")
        # 2. 동적 렌더링 대응을 위한 스크롤 루프
        # 유튜브 댓글 로딩 속도에 맞춰 충분히 스크롤합니다.
        comment_item_selector = "ytd-comment-thread-renderer #content-text"
        for _ in range(18):
            # 페이지 스크롤로 댓글 더보기 유도
            await page.evaluate("window.scrollBy(0, Math.floor(window.innerHeight * 1.4));")
            await asyncio.sleep(1.2)

            # 중간중간 현재까지의 댓글 수를 확인해 목표치에 도달하면 조기 종료
            current_count = await page.locator(comment_item_selector).count()
            if current_count >= max_comments:
                break
            
        # 3. DOM 구조에서 댓글 텍스트 레이어 추출 (예시는 유튜브 selector 기준)
        # 실제 플랫폼별 태그 구조에 맞게 코파일럿에게 수정을 지시할 수 있음
        comment_elements = []
        selectors = [
            "ytd-comment-thread-renderer #content-text",
            "ytd-comment-view-model #content-text",
            "#content-text"
        ]

        try:
            for selector in selectors:
                if await page.locator(selector).count() > 0:
                    comment_elements = await page.locator(selector).all_inner_texts()
                    print(f"[Module 1] 댓글 셀렉터 사용: {selector}")
                    break
        except Exception:
            comment_elements = []

        if not comment_elements:
            print("[Module 1] 댓글 텍스트 셀렉터를 찾지 못했습니다. YouTube UI 변경 가능성이 있습니다.")
            await browser.close()
            return []

        seen = set()
        for text in comment_elements:
            cleaned = text.strip()
            if not cleaned:
                continue
            if cleaned in seen:
                continue
            seen.add(cleaned)

            if text.strip():
                comments_data.append({
                    "source_url": url,
                    "raw_text": cleaned
                })

            if len(comments_data) >= max_comments:
                break
                
        await browser.close()
        
    print(f"[Module 1] 성공적으로 {len(comments_data)}개의 댓글을 수집하여 Raw Data DB에 적재 준비 완료.")
    return comments_data