from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.schemas.review import ReviewResult

class CodeReviewService :

    def __init__(self):
        self.llm = ChatOpenAI(
            model = "gpt-oss-120b",
            api_key=settings.openai_api_key,
            temperature=0,
            base_url=settings.openai_base_url,
        )

    async def review_diff(
            self,
            diff : str, 
    ) -> ReviewResult : 
        prompt = f"""
You are an expert software code reviewer.

Review the following GitHub pull request diff.

Focus only on:
- bugs
- security vulnerabilities
- incorrect logic
- serious performance problems
- maintainability problems that can cause real issues

Do not report:
- formatting preferences
- minor style issues
- subjective opinions
- issues unrelated to the changed code

For every real issue, provide:
- severity: low, medium, or high
- file
- line number if identifiable
- clear explanation
- concrete suggestion

If there are no meaningful issues, return an empty findings list.

Pull request diff:

{diff}
"""

        structured_llm = self.llm.with_structured_output(
            ReviewResult
        )

        result = await structured_llm.ainvoke(prompt)

        return result