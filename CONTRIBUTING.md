# Contributing

Every change reaches `main` through a pull request.

## The flow

1. Branch from an up-to-date `main`, one branch per change (`claude/<topic>` for changes made by Claude Code):

   ```
   git switch main
   git pull
   git switch -c claude/<topic>
   ```

2. Commit in small, focused steps, one logical step each. VIs, libraries and the project stay saved for LabVIEW 2020 (CLAUDE.md, "Save version").
3. Push the branch and open a pull request into `main`. The template (`.github/pull_request_template.md`) asks what changed, why, and what was tested.
4. CI runs on the pull request (docs/ci.md). The check **Protocol, client and generated tests** must pass; the LabVIEW jobs run too once the self-hosted runner is set up.
5. Review: comment on lines or on the whole pull request. Fixes come as new commits on the same branch, without force pushes, so earlier comments keep their context. Resolve each conversation once it is settled.
6. Merge with **Create a merge commit**: the commits of the change stay visible in `main`'s history. GitHub then deletes the branch.

## Branch protection on `main`

* Changes only through a pull request, for administrators too: nobody pushes to `main` directly.
* The check **Protocol, client and generated tests** must pass.
* All conversations must be resolved before merging.
* No force pushes, no deletion.
* No approval is required: the pull requests are opened from the owner's account, and GitHub does not let an author approve their own pull request. Merging is the approval.

Releases are tags on `main` (docs/ci.md, "Release").
