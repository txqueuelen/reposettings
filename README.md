# Reposettings

Python tool to batch-update repo settings.

## Supported settings

See `reposettings.yml`, which includes an object with all settings that can be configured.

## Github action

Reposettings can also be run as a Github action!

```yaml
  reposettings:
    name: Sync repository settings
    runs-on: ubuntu-latest
    steps:
      - uses: roobre/reposettings@v1
        with:
          github_token: ${{ secrets.ACTUAL_TOKEN }}
          config: |
            # My custom settings
            my-settings: &my-settings
              features:
                issues: true
              allow:
                squash-merge: true
                merge-commit: true
                rebase-merge: true
              delete-branch-on-merge: true

            # List of repos to update. This is the only key actually accessed by reposettings
            repos:
              roobre/reposettings: *my-settings
```
