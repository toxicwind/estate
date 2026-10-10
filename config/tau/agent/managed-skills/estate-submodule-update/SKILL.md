---
name: estate-submodule-update
description: Procedure for adding a submodule to estate repository and updating README with infrastructure changes
---

# Estate Submodule and Documentation Update Procedure

## When to use this skill
When you need to:
1. Add a new submodule to the estate repository
2. Update estate README with infrastructure changes (daemon counts, service maps, etc.)
3. Push changes to both estate and submodule repositories

## Prerequisites
- Access to estate repository (https://github.com/toxicwind/estate.git)
- GitHub CLI (`gh`) installed and authenticated
- Local estate repository cloned

## Steps

### 1. Prepare the submodule repository
```bash
# Create the submodule directory and initialize as git repo
cd /path/to/estate
mkdir -p path/to/submodule
cd path/to/submodule
git init
# Add files, commit
git add -A
git commit -m "Initial commit: [description]"
git branch -M main
# Create GitHub repository
gh repo create toxicwind/[repo-name] --public --source=. --remote=origin --push
```

### 2. Add submodule to estate
```bash
cd /path/to/estate
git submodule add https://github.com/toxicwind/[repo-name].git path/to/submodule
git add .gitmodules path/to/submodule
git commit -m "chore: add [repo-name] as submodule"
```

### 3. Update estate README
Update the following sections in estate/README.md:
- Daemon count: Update "**86 supervised daemons**" (or current count)
- Service map: Add new services to the table
- Getting started: Update health check commands if needed
- Roadmap: Update completed items

### 4. Commit and push estate changes
```bash
cd /path/to/estate
git add README.md
git commit -m "docs: update README with [changes]"
git push origin main
```

### 5. Verify submodule status
```bash
cd /path/to/estate
git submodule status
git submodule update --init --recursive
```

## Verification
- Check that submodule shows correct commit hash in `git submodule status`
- Verify estate README renders correctly on GitHub
- Confirm both repositories are accessible and up-to-date

## Tips
- Always commit estate changes before pushing
- Use descriptive commit messages following conventional commits
- After adding submodule, run `git submodule update --init` to populate it
- If getting submodule URL errors, check .gitmodules for correct URL
