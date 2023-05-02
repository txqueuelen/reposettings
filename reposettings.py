from cProfile import label
import os
import sys
import re
from collections.abc import Container
from github import Github, Repository, Label, GithubObject
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
    rs.use(LabelHook())

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
    def set(repo: Repository.Repository, config):
        print(" Processing branch protection settings...")

        if 'branch-protection' not in config and 'branch-protection-overrides' not in config:
            print(" Nothing to do.")
            return

        should_protect_default_branch = config.get('protect-default-branch')

        for branch in repo.get_branches():
            if not (branch.protected or (should_protect_default_branch and repo.default_branch == branch.name)):
                continue

            rules = BranchProtectionHook.rules_for(branch.name, config)

            newsettings = {}
            # Historically dismiss has been misspelled as "dissmiss". To avoid breaking config, we read that too and
            # print a warning.
            if 'dissmiss-stale-reviews' in rules:
                print(" Warning: using deprecated 'dissmiss-stale-reviews', please replace it with 'dismiss-stale-reviews'")
                newsettings['dismiss_stale_reviews'] = bool(rules['dissmiss-stale-reviews'])
            if 'dismiss-stale-reviews' in rules:
                newsettings['dismiss_stale_reviews'] = bool(rules['dismiss-stale-reviews'])
            if 'required-review-count' in rules:
                newsettings['required_approving_review_count'] = int(rules['required-review-count'])

            if 'required-pull-request-reviews' in rules:
                if 'dismissal-restrictions' in rules["required-pull-request-reviews"]:
                    dismissal_restrictions = rules["required-pull-request-reviews"]["dismissal-restrictions"]
                    # PyGithub uses the parameter `dismissal_users`
                    # GitHub API uses `required_pull_request_reviews.dismissal_restrictions.users`
                    # Same for teams and apps.
                    if 'users' in dismissal_restrictions:
                        newsettings['dismissal_users'] = dismissal_restrictions['users']
                    if 'teams' in dismissal_restrictions:
                        newsettings['dismissal_teams'] = dismissal_restrictions['teams']
                    if 'apps' in dismissal_restrictions:
                        newsettings['dismissal_apps'] = dismissal_restrictions['apps']
                if 'bypass-pull-request-allowances' in rules["required-pull-request-reviews"]:
                    bypass_pull_request_allowances = rules["required-pull-request-reviews"]["bypass-pull-request-allowances"]
                    # PyGithub uses the parameter `users_bypass_pull_request_allowances`
                    # GitHub API uses `required_pull_request_reviews.bypass_pull_request_allowances.users`
                    # Same for teams and apps.
                    if 'users' in bypass_pull_request_allowances:
                        newsettings['users_bypass_pull_request_allowances'] = bypass_pull_request_allowances['users']
                    if 'teams' in bypass_pull_request_allowances:
                        newsettings['teams_bypass_pull_request_allowances'] = bypass_pull_request_allowances['teams']
                    if 'apps' in bypass_pull_request_allowances:
                        newsettings['apps_bypass_pull_request_allowances'] = bypass_pull_request_allowances['apps']
            if 'push-restrictions' in rules:
                # PyGithub uses the parameter `user_push_restrictions`
                # GitHub API uses `push_restrictions.users`
                # Same for teams and apps.
                if 'users' in rules['push-restrictions']:
                    newsettings['user_push_restrictions'] = rules['push-restrictions']['users']
                if 'teams' in rules['push-restrictions']:
                    newsettings['team_push_restrictions'] = rules['push-restrictions']['teams']
                if 'apps' in rules['push-restrictions']:
                    newsettings['app_push_restrictions'] = rules['push-restrictions']['apps']
            if 'enforce-admins' in rules:
                newsettings['enforce_admins'] = bool(rules['enforce-admins'])
            if 'block-creations' in rules:
                newsettings['block_creations'] = bool(rules['block-creations'])
            if 'required-linear-history' in rules:
                newsettings['required_linear_history'] = bool(rules['required-linear-history'])
            if 'allow-force-pushes' in rules:
                newsettings['allow_force_pushes'] = bool(rules['allow-force-pushes'])
            if 'required-conversation-resolution' in rules:
                newsettings['required_conversation_resolution'] = bool(rules['required-conversation-resolution'])
            if 'lock-branch' in rules:
                newsettings['lock_branch'] = bool(rules['lock-branch'])
            if 'allow-fork-syncing' in rules:
                newsettings['allow_fork_syncing'] = bool(rules['allow-fork-syncing'])

            # If branch is not protected we cannot get current protection settings, so we cannot call has_changes and must apply changes blindly
            if branch.protected:
                if not RepoSetter.has_changes(newsettings, branch.get_protection()):
                    print(f" Branch protection settings for {branch.name} unchanged.")
                    continue

            print(f" Applying branch protection settings to '{branch.name}'...")
            branch.edit_protection(**newsettings)

    @staticmethod
    def rules_for(branch_name: str, config):
        if 'branch-protection-overrides' in config:
            overrides = config['branch-protection-overrides']
            if branch_name in overrides:
                return overrides[branch_name]

        if 'branch-protection' in config:
            return config['branch-protection']

        return {}


class LabelHook(RepoSetter):
    """
    LabelHook handles creating and updating labels for repos
    """

    @staticmethod
    def name():
        return "Repo labels settings hook"

    @staticmethod
    def set(repo: Repository, config):
        print(" Processing labels...")

        if 'labels' not in config:
            print(" Nothing to do.")
            return
        conf_labels = config['labels']
        unset_labels = conf_labels.copy()

        repo_labels = [l for l in repo.get_labels()]  # iter to avoid fetching labels more than once
        repo_label_names = {l.name for l in repo_labels}
        for label in repo_labels:
            newname, newsettings = LabelHook.replacement(conf_labels, label)

            if newname is None: # Not present in config, delete
                LabelHook.delete_label(label)

            elif label.name != newname and newname in repo_label_names:
                LabelHook.replace_label_with_existent(repo, label, newname)

            elif LabelHook.needs_update(label, newname, newsettings):
                print(f" Editing label {label.name}")
                try:
                    LabelHook.update_label(label, newname, newsettings)
                    repo_label_names.add(newname)
                except Exception as e:
                    print(f" Error editing label: {str(e)}")
                    continue

            # Processed, remove from pending
            if newname in unset_labels:
                del unset_labels[newname]

        for newname in unset_labels:
            newsettings = unset_labels[newname]
            LabelHook.create_label(repo, newname, newsettings)


    @staticmethod
    def needs_update(label: Label, newname :str, newsettings: dict):
        """
        Checks whether a label needs an update
        """
        newColor = newsettings.get('color') or label.color
        newDescription = newsettings.get('description') or label.description
        return label.name != newname or newColor != label.color or newDescription != label.description

    @staticmethod
    def replacement(newset: dict, label: Label):
        """
        Find in the config a suitable label for replacing the given one, checking keys and `replaces` property
        """
        # Fast path: dict has a key with the old label name
        if label.name in newset:
            return label.name, newset[label.name]

        # Otherwise check `replaces` key for all new label
        for name, new in newset.items():
            if label.name in new.get('replaces', []):
                return name, new

        return None, None

    @staticmethod
    def create_label(repo: Repository.Repository, newname: str, newsettings: dict):
        print(f" Creating label {newname}")
        try:
            repo.create_label(
                name=newname,
                color=newsettings.get('color') or GithubObject.NotSet,
                description=newsettings.get('description') or GithubObject.NotSet,
            )
        except Exception as e:
            print(f" Error creating label: {e}")

    @staticmethod
    def update_label(label: Label.Label, newname: str, newsettings: dict):
        label.edit(
            name=newname,
            color=newsettings.get('color', label.color),
            description=newsettings.get('description', label.description)
        )

    @staticmethod
    def delete_label(label: Label.Label):
        try:
            label.delete()
        except Exception as e:
            print(f"Error deleting '{label.name}' label: {e}")

    @staticmethod
    def replace_label_with_existent(repo: Repository.Repository, previous_label: Label.Label, new_label_name: str):
        """
        Updates all issues containing a label with its replacement and then removes the replaced one.
        """
        print(f" Replacing {previous_label.name} from all issues")
        issues = repo.get_issues(labels=[previous_label])
        for issue in issues:
            try:
                issue.add_to_labels(new_label_name)
            except Exception as e:
                print(f" Error adding label '{new_label_name}' to issue #{issue.number}")
        LabelHook.delete_label(previous_label)


if __name__ == '__main__':
    main()
