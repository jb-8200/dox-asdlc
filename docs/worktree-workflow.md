# Worktree Feature Workflow

One worktree = one bounded context (feature). Multiple subagent roles (backend, frontend) work in the same worktree, but each feature gets its own isolated branch.

## 1. Plan the feature (PM CLI, on main)

```bash
./scripts/new-feature.sh Pnn Fnn "feature-name"
```

This creates the work item skeleton at `.workitems/Pnn-Fnn-feature-name/`. The planner agent fills in `design.md`, `user_stories.md`, and `tasks.md`. The reviewer agent validates the design before implementation begins.

## 2. Create the worktree session

```bash
./scripts/start-session.sh pnn-fnn-feature-name
```

Creates `.worktrees/pnn-fnn-feature-name/` on branch `feature/pnn-fnn-feature-name`.

## 3. Start a new Claude CLI in that worktree

```bash
cd .worktrees/pnn-fnn-feature-name
export CLAUDE_INSTANCE_ID=pnn-fnn-feature-name
claude
```

The session gets its own git branch, isolated from main and other worktrees.

## 4. Build (in the worktree CLI)

Backend and frontend subagents implement against `tasks.md`. All commits go to the feature branch.

## 5. Merge back (when done)

```bash
./scripts/worktree/merge-worktree.sh pnn-fnn-feature-name
```

Creates a PR for human review and merge to main.

## 6. Teardown

```bash
./scripts/worktree/teardown-worktree.sh pnn-fnn-feature-name --merge
```

Removes the worktree and cleans up the local branch.
