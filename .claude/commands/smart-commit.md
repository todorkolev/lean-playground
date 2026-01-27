# Smart Commit

Analyze staged git changes and commit them properly, splitting into multiple focused commits if necessary.

## Critical Rules

**ONE-TIME OPERATION.** This command commits only what is currently staged, then STOPS. Do NOT automatically commit any subsequent changes. Future commits require the user to explicitly run this command again.

**NEVER delete, skip, or exclude any staged files.** All staged changes MUST be committed. Your job is to organize and commit what the user staged, not to judge whether files belong.

**ONLY work with staged changes.** Do not touch, stage, or modify unstaged files. If splitting commits, stash unstaged changes first to prevent mixing.

## Instructions

1. **Gather context** by running these commands in parallel:
   - `git diff --staged --name-only` to get the list of staged files (save this list!)
   - `git diff --staged` to see all staged changes
   - `git log --oneline -10` to understand the repository's commit message style

2. **Save the original staged file list** - you MUST commit ALL of these files, no exceptions.

3. **Analyze and group changes** by examining:
   - File paths and their logical groupings (e.g., tests/, docs/, src/module/)
   - The nature of changes (feature, fix, refactor, docs, test, chore)
   - Dependencies between changes (changes that must go together)

4. **Decide on commit strategy**:
   - If all changes are related to a single purpose: create one commit
   - If changes span multiple unrelated purposes: split into multiple commits
   - Group by: functionality > module > change type

   Common groupings:
   - Source code changes + their corresponding tests = one commit
   - Documentation updates = separate commit
   - Configuration/tooling changes = separate commit
   - Refactoring = separate commit from features/fixes

5. **Execute commits**:
   - If creating a single commit: commit directly without unstaging
   - If splitting into multiple commits:
     a. Run `git stash --keep-index` to stash unstaged changes (keeps staged intact)
     b. Run `git reset HEAD` to unstage the staged changes
     c. For each commit group, stage files with `git add <files>`
     d. Commit with a well-formed message
     e. Repeat until ALL originally staged files are committed
     f. Run `git stash pop` to restore unstaged changes
   - Use heredoc format for commit messages:
     ```bash
     git commit -m "$(cat <<'EOF'
     type: short description

     - Detail 1
     - Detail 2

     Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
     EOF
     )"
     ```

6. **Commit message guidelines**:
   - Use conventional commit format: `type: description` (no scope for single-project repos)
   - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `style`, `build`, `ci`, `spec`
   - Use `spec` for specification and planning artifacts (e.g., buildforce sessions with spec.yaml, research.yaml, plan.yaml)
   - Keep the first line under 72 characters
   - Add bullet points in body for multiple related changes
   - Focus on "why" rather than "what"
   - Always end with `Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>`

7. **Verify results**:
   - Run `git status` to confirm all originally staged files are now committed
   - Run `git log --oneline -N` (where N = number of commits created) to show the new commits
   - Verify that NO originally staged files remain uncommitted
   - Verify unstaged changes are restored (if stash was used)
   - Report the results to the user

## Examples of Good Groupings

**Example 1**: Feature with tests
```
Commit 1: "feat: add user authentication endpoint"
  - src/auth/login.py
  - src/auth/middleware.py
  - tests/auth/test_login.py
```

**Example 2**: Mixed changes
```
Commit 1: "refactor: extract validation helpers"
  - src/utils/validation.py
  - src/handlers/form.py

Commit 2: "docs: update API documentation"
  - docs/api.md
  - README.md

Commit 3: "chore: update linter configuration"
  - .eslintrc
  - pyproject.toml
```

**Example 3**: Buildforce session
```
Commit 1: "spec: microstructure alpha pipeline"
  - .buildforce/sessions/*/spec.yaml
  - .buildforce/sessions/*/research.yaml
  - .buildforce/sessions/*/plan.yaml
```

## Split Commit Flow (with unstaged changes protection)

```bash
# 1. Save staged file list
STAGED_FILES=$(git diff --staged --name-only)

# 2. Stash unstaged changes (staged changes remain)
git stash --keep-index

# 3. Reset to unstage (now only originally-staged changes exist in working dir)
git reset HEAD

# 4. Stage and commit each group
git add file1.py file2.py
git commit -m "feat: first change"

git add file3.py
git commit -m "fix: second change"

# 5. Restore unstaged changes
git stash pop
```

## Important Notes

- **Commit ALL staged files** - even if a file seems unrelated or temporary, commit it. The user staged it intentionally.
- Never commit files that appear to contain secrets (.env, credentials, API keys) - warn the user instead
- If unsure about grouping, prefer fewer commits over many tiny ones
- Related test changes should go with their source code changes
- Configuration for a feature should go with that feature
- **Always use `git stash --keep-index` before `git reset HEAD`** when splitting commits to protect unstaged changes
- If stash pop has conflicts, warn the user and help resolve them
