import os
import sys
import re
from github import Github, Repository
import yaml


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <reposettings.yml>")
        sys.exit(1)

    config = yaml.safe_load(open('reposettings.yml', 'r'))

    ghtoken = os.environ.get('GITHUB_TOKEN')
    if ghtoken == "":
        print("Could not read $GITHUB_TOKEN")
        sys.exit(1)

    gh = Github(ghtoken)

    if 'repos' not in config:
        print("Could not find 'repos' key in reposettings.yml")
        sys.exit(2)

    for name in config['repos']:
        repoconfig = config['repos'][name]
        name = re.sub(r'(https?://)?github\.com/?', '', name)
        repo = gh.get_repo(name)

        print(f"Processing {repo.name}...")
        repo_hook(repo, repoconfig)
        branch_protection_hook(repo, repoconfig)
        # Other hooks would be here...


# Handler function for branch protection settings.
def repo_hook(repo: Repository, config):
    print(" Processing repo settings...")
    newsettings = {}

    if 'features' in config:
        for feat in config['features']:
            newsettings[f"has_{feat}"] = config['features'][feat]
    if 'allow' in config:
        for allow in config['allow']:
            newsettings[f"allow_{allow.replace('-', '_')}"] = config['allow'][allow]
    if 'delete-branch-on-merge' in config:
        newsettings['delete_branch_on_merge'] = config['delete-branch-on-merge']

    if len(newsettings) == 0:
        return

    if not has_changes(newsettings, repo):
        print(" Repo settings unchanged.")
        return

    print(" Applying new repo settings...")
    repo.edit(**newsettings)


# Handler function for branch protection settings.
def branch_protection_hook(repo: Repository, config):
    print(" Processing branch protection settings...")

    if 'branch-protection' not in config:
        return
    prot_settings = config['branch-protection']

    newsettings = {}
    for branch in repo.get_branches():
        if not branch.protected:
            continue
        if 'dissmiss-stale-reviews' in prot_settings:
            newsettings['dismiss_stale_reviews'] = bool(prot_settings['dissmiss-stale-reviews'])
        if 'required-review-count' in prot_settings:
            newsettings['required_approving_review_count'] = int(prot_settings['required-review-count'])

        if len(newsettings) == 0:
            return

        if not has_changes(newsettings, branch.get_protection().__dict__):
            print(" Branch protection settings unchanged.")
            return

        print(" Applying branch protection settings...")
        branch.edit_protection(**newsettings)


def has_changes(new: dict, old) -> bool:
    for k in new:
        if old.__getattribute__(k) != new[k]:
            return True
    return False


if __name__ == '__main__':
    main()
