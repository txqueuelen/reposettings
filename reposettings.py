import os
import sys
import re
from github import Github, Repository
import yaml


def main():
    config = yaml.safe_load(open('reposettings.yml', 'r'))

    ghtoken = os.environ.get('GITHUB_TOKEN')
    if ghtoken == "":
        print("Could not read $GITHUB_TOKEN")
        sys.exit(1)

    gh = Github(ghtoken)

    for name in config['repos']:
        repoconfig = config['repos'][name]
        name = re.sub(r'(https?://)?github\.com/?', '', name)
        repo = gh.get_repo(name)

        print(f"Processing {repo.name}")
        repo_hook(repo, repoconfig)
        branch_protection_hook(repo, repoconfig)
        # Other hooks would be here...


# Handler function for branch protection settings.
def repo_hook(repo: Repository, config):
    print("Processing repo settings")
    newsettings = {}

    if 'features' in config:
        for feat in config['features']:
            newsettings[f"has_{feat}"] = config['features'][feat]
    if 'allow' in config:
        for allow in config['allow']:
            newsettings[f"allow_{allow.replace('-', '_')}"] = config['allow'][allow]
    if 'delete-branch-on-merge' in config:
        newsettings['delete_branch_on_merge'] = config['delete-branch-on-merge']

    repo.edit(**newsettings)

# Handler function for branch protection settings.
def branch_protection_hook(repo: Repository, config):
    print("Processing branch protection settings")

    if 'branch-protection' not in config:
        return
    prot_settings = config['branch-protection']

    for branch in repo.get_branches():
        if not branch.protected:
            continue
        if 'dissmiss-stale-reviews' not in prot_settings:
            continue

        newprot = prot_settings['dissmiss-stale-reviews']
        print(f" Setting stale review dismissal to {newprot}")
        branch.edit_protection(dismiss_stale_reviews=bool(newprot))


if __name__ == '__main__':
    main()
