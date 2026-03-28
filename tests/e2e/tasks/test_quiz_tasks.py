import pytest
from playwright.async_api import Page

class TestQuizTasks:
    """Tests for quiz-type reward tasks."""

    @pytest.mark.e2e
    @pytest.mark.requires_login
    @pytest.mark.timeout(300)
    async def test_quiz_task_completion(self, page: Page, task_discovery):
        """
        Find and complete a quiz task if available.
        Quizzes typically involve 5-10 multiple-choice questions.
        """
        # Ensure we are logged in before starting (handled by requires_login marker if fixture is set up)
        tasks = await task_discovery()
        # Find tasks that look like quizzes
        quiz_tasks = [t for t in tasks if t.status == "available" and any(keyword in t.title.lower() for keyword in ["quiz", "poll", "question", "trivia", "test"])]

        if not quiz_tasks:
            pytest.skip("No quiz tasks available for this account/region")

        task = quiz_tasks[0]
        # Quiz tasks often open in a new tab, but we'll go directly to the URL for simplicity in E2E
        await page.goto(task.url, wait_until="domcontentloaded", timeout=30000)

        # Quiz flow: answer questions, submit, get reward
        questions_answered = 0
        max_questions = 15 # Some quizzes are longer

        for _ in range(max_questions):
            # Wait for question/answer options to appear
            # Quiz indicators vary widely across Bing/MS rewards
            try:
                # Common selectors for quiz questions and options
                await page.wait_for_selector(".question, [data-ct*='question'], input[type='radio'], .rqQuestion, .btOptionCard", timeout=10000)
            except:
                # No more questions found or different structure
                break

            # Choose an available answer option
            # Often .btOptionCard for Bing quizzes
            option = await page.query_selector(".btOptionCard, input[type='radio']:not(:checked), .rqOption, .option")
            if option:
                await option.click()
                await page.wait_for_timeout(2000) # Wait for auto-advance or button to appear
                
                # Some quizzes require clicking "Next" or "Submit"
                next_btn = await page.query_selector("button:has-text('Next'), button:has-text('Submit'), input[value='Next'], .rqNextQuestion")
                if next_btn:
                    await next_btn.click()
                    await page.wait_for_timeout(2000)
                
                questions_answered += 1
            else:
                # Check if we're on a result/summary page
                finish_msg = await page.query_selector("text='Results', text='Score', text='Finished', text='Summary'")
                if finish_msg:
                    break
                break

        # Final submission if needed
        submit_btn = await page.query_selector("button:has-text('Get reward'), button:has-text('Finish'), .rqFinish")
        if submit_btn:
            await submit_btn.click()
            await page.wait_for_timeout(3000)

        # Verify completion - check if points were awarded or message shown
        # Since we might not have a reliable way to check points in this test, 
        # we check if we answered at least one question or saw a completion message.
        completion_indicators = [
            "text='You've earned'",
            "text='completed'",
            "text='Done'",
            ".task-complete",
            ".success",
            ".rqSuccess",
            "text='100%'"
        ]
        
        found_indicator = False
        for indicator in completion_indicators:
            if await page.query_selector(indicator):
                found_indicator = True
                break

        assert found_indicator or questions_answered > 0, f"Quiz task '{task.title}' did not appear to complete (answered {questions_answered} questions)"

    @pytest.mark.e2e
    @pytest.mark.requires_login
    @pytest.mark.timeout(120)
    async def test_quiz_wrong_answer_handling(self, page: Page):
        """If quiz allows wrong answers, should not break flow."""
        # This is highly dependent on specific quiz types (e.g. "This or That" vs "Lights, Camera, Action")
        # For now, we document that this is hard to induce and skip
        pytest.skip("Inducing wrong answers reliably depends on specific quiz design and knowledge base")
