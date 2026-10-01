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
- file: the exact file path from the provided diff
- line: the exact NEW-file line number of a changed line in the diff
- clear explanation
- concrete suggestion

IMPORTANT RULES FOR file AND line:
- Only use files that actually appear in the provided diff.
- Only report a line that was added or modified in the provided diff.
- The line must be a NEW-file line number shown by the @@ hunk header.
- Never invent a file path.
- Never invent a line number.
- If you cannot confidently map the issue to an added or modified line, set line to null.

If there are no meaningful issues, return an empty findings list.

Pull request diff:

{diff}
"""

        structured_llm = self.llm.with_structured_output(
            ReviewResult
        )

        result = await structured_llm.ainvoke(prompt)

        return result