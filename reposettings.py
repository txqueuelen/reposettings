import os
import sys
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
        repo = gh.get_repo(name)

        print(f"Processing {repo.name}")
        branch_protection_hook(repo, repoconfig)
        # Other hooks would be here...


# Handler function for changing settings.
def branch_protection_hook(repo: Repository, config):
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
