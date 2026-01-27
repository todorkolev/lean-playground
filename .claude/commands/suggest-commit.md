# Suggest Commit Message

Analyze the currently staged git changes and propose a well-structured commit message.

## Instructions

1. Run `git diff --staged` to see all staged changes
2. Run `git log --oneline -10` to understand the repository's commit message style
3. Analyze the staged changes to understand:
   - What files are modified, added, or deleted
   - The nature of the changes (feature, fix, refactor, docs, test, chore, etc.)
   - The scope of the changes (which module/component is affected)
   - The purpose and impact of the changes

4. Propose a commit message following these guidelines:
   - Use conventional commit format: `type(scope): description`
   - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `style`, `build`, `ci`
   - Keep the first line under 72 characters
   - Add a blank line after the subject if including a body
   - Use bullet points in the body for multiple related changes
   - Focus on "why" rather than "what" when it adds clarity
   - Match the style of existing commits in the repository

5. Present the suggested commit message in a code block that can be easily copied

6. If the changes are too large or unrelated, suggest splitting into multiple commits
