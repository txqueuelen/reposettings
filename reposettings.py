import os
import sys
import re
from github import Github, Repository
import yaml


class RepoSetter:
    """
    Changes settings given a config file
    """

    @staticmethod
    def set(repo: Repository, config: dict):
        pass

    @staticmethod
    def name() -> str:
        return "Unnamed reposetter"

    @staticmethod
    def has_changes(new: dict, old) -> bool:
        if len(new) == 0:
            return False

        for k in new:
            if type(old) == dict:
                if k not in old:
                    return True
                old_val = old[k]
            else:
                try:
                    old_val = old.__getattribute__(k)
                except Exception as e:
                    old_val = None

            if old_val != new[k]:
                return True
        return False


class RepoSettings:
    def __init__(self, githubclient: Github):
        self._gh = githubclient
        self._setters = []

    def use(self, setter: RepoSetter):
        self._setters.append(setter)

    def apply(self, config: dict):
        if not self._validate(config):
            raise Exception("Invalid config supplied")

        for name in config['repos']:
            repoconfig = config['repos'][name]
            name = re.sub(r'(https?://)?github\.com/?', '', name)
            repo = self._gh.get_repo(name)

            print(f"Processing repo '{repo.name}'...")
            for setter in self._setters:
                print(f"Using setter '{setter.name()}'")
                setter.set(repo, repoconfig)
            print()

    @staticmethod
    def _validate(config: dict):
        return type(config) == dict \
               and 'repos' in config \
               and type(config['repos']) == dict \
               and len(config['repos']) > 0


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <reposettings.yml>")
        sys.exit(1)

    try:
        config = yaml.safe_load(open(sys.argv[1], 'r'))
    except Exception as e:
        print(f"Could not load settings from {sys.argv[1]}")
        sys.exit(2)

    ghtoken = os.environ.get('GITHUB_TOKEN')
    if ghtoken == "":
        print("Could not read $GITHUB_TOKEN")
        sys.exit(3)

    gh = Github(ghtoken)
    rs = RepoSettings(gh)
    rs.use(RepoHook())
    rs.use(BranchProtectionHook())

    try:
        rs.apply(config)
    except Exception as e:
        print(str(e))
        exit(10)


class RepoHook(RepoSetter):
    """
    RepoHook handles changing repository settings
    """

    @staticmethod
    def name():
        return "Repo settings hook"

    @staticmethod
    def set(repo: Repository, config):
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

        if not RepoSetter.has_changes(newsettings, repo):
            print(" Repo settings unchanged.")
            return

        print(" Applying new repo settings...")
        repo.edit(**newsettings)


class BranchProtectionHook(RepoSetter):
    """
    BranchProtectionHook handles changing branch protection settings
    """

    @staticmethod
    def name():
        return "Branch protection settings hook"

    @staticmethod
    def set(repo: Repository, config):
        print(" Processing branch protection settings...")

        if 'branch-protection' not in config:
            print(" Nothing to do.")
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

            if not RepoSetter.has_changes(newsettings, branch.get_protection()):
                print(" Branch protection settings unchanged.")
                return

            print(" Applying branch protection settings...")
            branch.edit_protection(**newsettings)


if __name__ == '__main__':
    main()
