import unittest
from unittest.mock import MagicMock, call
from github import GithubObject

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
    def test_set_global(self):
        bh = rs.BranchProtectionHook()

        branchmock = MagicMock()
        branchmock.name = 'branchmock'
        branchmock.protected = True
        branchmock.dismiss_stale_reviews = False
        branchmock.required_approving_review_count = 0

        unprotectedmock = MagicMock()
        unprotectedmock.name = 'unprotected'
        unprotectedmock.protected = False

        repomock = MagicMock()
        repomock.default_branch = 'main'
        repomock.get_branches.return_value = [
            branchmock,
            unprotectedmock,
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

        unprotectedmock.edit_protection.assert_not_called()

    def test_set_override_overrides(self):
        bh = rs.BranchProtectionHook()

        branchmock = MagicMock()
        branchmock.name = 'branchmock'
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
            },
            "branch-protection-overrides": {
                "branchmock": {
                    "required-review-count": 3,
                }
            }
        })

        branchmock.edit_protection.assert_called_with(
            required_approving_review_count=3,
        )

    def test_set_override_does_not_override(self):
        bh = rs.BranchProtectionHook()

        branchmock = MagicMock()
        branchmock.name = 'branchmock'
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
            },
            "branch-protection-overrides": {
                "different": {
                    "required-review-count": 3,
                }
            }
        })

        branchmock.edit_protection.assert_called_with(
            dismiss_stale_reviews=True,
            required_approving_review_count=2,
        )

    def test_set_override_only(self):
        bh = rs.BranchProtectionHook()

        branchmock = MagicMock()
        branchmock.name = 'branchmock'
        branchmock.protected = True
        branchmock.dismiss_stale_reviews = False
        branchmock.required_approving_review_count = 0

        repomock = MagicMock()
        repomock.get_branches.return_value = [
            branchmock
        ]

        bh.set(repomock, {
            "branch-protection-overrides": {
                "branchmock": {
                    "required-review-count": 3,
                }
            }
        })

        branchmock.edit_protection.assert_called_with(
            required_approving_review_count=3,
        )

    def test_protect_default_branch(self):
        bh = rs.BranchProtectionHook()

        defaultbranchmock = MagicMock()
        defaultbranchmock.name = 'default'
        defaultbranchmock.protected = False

        branchmock = MagicMock()
        branchmock.name = 'branchmock'
        branchmock.protected = True

        unprotectedbranchmock = MagicMock()
        unprotectedbranchmock.name = 'unprotected'
        unprotectedbranchmock.protected = False


        repomock = MagicMock()
        repomock.default_branch = 'default'
        repomock.get_branches.return_value = [
            defaultbranchmock, branchmock, unprotectedbranchmock
        ]

        bh.set(repomock, {
            "branch-protection": {
                "dissmiss-stale-reviews": True,
                "required-review-count": 2,
            },
            "protect-default-branch": True
        })

        for branch in (defaultbranchmock, branchmock):
            branch.edit_protection.assert_called_with(
                dismiss_stale_reviews=True,
                required_approving_review_count=2,
            )
        unprotectedbranchmock.edit_protection.assert_not_called()


class TestLabelHook(unittest.TestCase):
    def test_missing(self):
        lh = rs.LabelHook()

        labels = []
        for i in range(5):
            label = MagicMock()
            label.color = f"aabb{i}{i}"
            label.name = f"Test label {i}"
            label.edit.return_value = None
            label.delete.return_value = None
            labels.append(label)

        repomock = MagicMock()
        repomock.get_labels.return_value = labels
        repomock.create_label.return_value = None

        lh.set(repomock, {
            "labels": {
                "Test label 2": {
                    "description": "",
                    "color": "",
                },
                "Test label 3": {
                    "description": "",
                    "color": "",
                },
            }
        })

        repomock.create_label.assert_has_calls([])
        for i in range(5):
            if i == 2 or i == 3:
                labels[i].delete.assert_has_calls([])
            else:
                labels[i].delete.assert_called_once()

    def test_edited(self):
        lh = rs.LabelHook()

        labels = []
        for i in range(5):
            label = MagicMock()
            label.color = f"aabb{i}{i}"
            label.name = f"Test label {i}"
            label.description = f"Test description {i}"
            label.edit.return_value = None
            label.delete.return_value = None
            labels.append(label)

        repomock = MagicMock()
        repomock.get_labels.return_value = labels
        repomock.create_label.return_value = None

        lh.set(repomock, {
            "labels": {
                "Test label 1": {
                    "description": f"New description 1",
                    "color": "111111",
                },
                "Test label 2": {
                    "color": None
                },
                "Test label 3": {
                    "description": "New Description 3",
                    "color": None,
                },
            }
        })

        repomock.create_label.assert_has_calls([])
        for i in range(5):
            if i == 1:
                labels[i].edit.assert_called_once_with(
                    name=f"Test label 1",
                    color="111111",
                    description="New description 1"
                )
            elif i == 3:
                labels[i].edit.assert_called_once_with(
                    name=f"Test label 3",
                    color=None,
                    description="New Description 3",
                )
            else:
                labels[i].edit.assert_has_calls([])

    def test_created(self):
        lh = rs.LabelHook()

        labels = []
        for i in range(1):
            label = MagicMock()
            label.color = f"aabb{i}{i}"
            label.name = f"Test label {i}"
            label.description = f"Test description {i}"
            label.edit.return_value = None
            label.delete.return_value = None
            labels.append(label)

        repomock = MagicMock()
        repomock.get_labels.return_value = labels
        repomock.create_label.return_value = None

        lh.set(repomock, {
            "labels": {
                "Test label 0": {
                    "description": f"New description 1",
                    "color": "111111",
                },
                "Test label 1": {
                    "description": f"New description 1",
                    "color": "111111",
                },
                "Test label 2": {
                },
            }
        })

        repomock.create_label.assert_has_calls([
            call(
                name="Test label 1",
                description="New description 1",
                color="111111"
            ),
            call(
                name="Test label 2",
                description=GithubObject.NotSet,
                color=GithubObject.NotSet
            )
        ])

    def test_replacements(self):
        lh = rs.LabelHook()

        labels = []
        for i in range(5):
            label = MagicMock()
            label.color = f"aabb{i}{i}"
            label.name = f"Test label {i}"
            label.description = f"Test description {i}"
            label.edit.return_value = None
            label.delete.return_value = None
            labels.append(label)

        repomock = MagicMock()
        repomock.get_labels.return_value = labels
        repomock.create_label.return_value = None

        lh.set(repomock, {
            "labels": {
                "Replaces TL1": {
                    "description": f"Replaced 1",
                    "color": "111111",
                    "replaces": ["Test label 1"]
                },
                "Replaces TL2": {
                    "replaces": ["Test label 2"]
                },
                "Test label 3": {
                    "description": None,
                    "color": None,
                },
            }
        })

        repomock.create_label.assert_has_calls([])
        for i in range(5):
            if i in (0, 4):
                labels[i].delete.assert_called_once()
            if i == 1:
                labels[i].edit.assert_called_once_with(
                    name=f"Replaces TL1",
                    color="111111",
                    description="Replaced 1"
                )
            elif i == 2:
                labels[i].edit.assert_called_once_with(
                    name=f"Replaces TL2",
                    color="aabb22",
                    description="Test description 2",
                )
            else:
                labels[i].edit.assert_has_calls([])

    def test_replacement_by_existent(self):
        lh = rs.LabelHook()

        labels = []
        for i in range(2):
            label = MagicMock()
            label.color = f"aabb{i}{i}"
            label.name = f"Test label {i}"
            label.description = f"Test description {i}"
            label.edit.return_value = None
            label.delete.return_value = None
            labels.append(label)

        repomock = MagicMock()
        repomock.get_labels.return_value = labels
        repomock.create_label.return_value = None

        lh.set(repomock, {
            "labels": {
                "Replaces TL0 and TL1": {
                    "description": "Replaced",
                    "color": "111111",
                    "replaces": ["Test label 0", "Test label 1"]
                },
            }
        })

        repomock.create_label.assert_has_calls([])
        for i in range(2):
            if i == 0:
                labels[i].edit.assert_called_once_with(
                    name=f"Replaces TL0 and TL1",
                    color="111111",
                    description="Replaced"
                )
            else:
                labels[i].delete.assert_called_once()
                labels[i].edit.assert_has_calls([])


if __name__ == '__main__':
    unittest.main()
