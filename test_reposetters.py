import unittest
from unittest.mock import MagicMock

import reposettings as rs


class TestRepoSetter(unittest.TestCase):
    def test_has_changes(self):
        r = rs.RepoSetter()
        self.assertTrue(r.has_changes(
            {"missing": "new"},
            {"old": "old"}
        ))
        self.assertTrue(r.has_changes(
            {"same": "new"},
            {"same": "old"}
        ))
        self.assertFalse(r.has_changes(
            {},
            {"old": "old"}
        ))
        self.assertFalse(r.has_changes(
            {},
            {}
        ))
        self.assertFalse(r.has_changes(
            {"old": "old"},
            {"old": "old"}
        ))


class TestRepoHook(unittest.TestCase):
    def test_set(self):
        rh = rs.RepoHook()

        repomock = MagicMock()
        repomock.has_issues = False
        repomock.has_wiki = False
        repomock.allow_merge_commit = False
        repomock.delete_branch_on_merge = False

        rh.set(repomock, {
            "features": {
                "issues": True,
                "wiki": True,
            },
            "allow": {
                "merge-commit": True,
            },
            "delete-branch-on-merge": True
        })

        repomock.edit.assert_called_with(
            has_issues=True,
            has_wiki=True,
            allow_merge_commit=True,
            delete_branch_on_merge=True,
        )


class TestBranchProtectionHook(unittest.TestCase):
    def test_set(self):
        bh = rs.BranchProtectionHook()

        branchmock = MagicMock()
        branchmock.protected = True
        branchmock.dismiss_stale_reviews = False
        branchmock.required_approving_review_count = 0

        repomock = MagicMock()
        repomock.get_branches.return_value = [
            branchmock
        ]

        bh.set(repomock, {
            "branch-protection": {
                "dissmiss-stale-reviews": True,
                "required-review-count": 2,
            }
        })

        branchmock.edit_protection.assert_called_with(
            dismiss_stale_reviews=True,
            required_approving_review_count=2,
        )


if __name__ == '__main__':
    unittest.main()
