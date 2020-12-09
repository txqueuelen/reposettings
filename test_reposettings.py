import unittest
from unittest.mock import MagicMock

import reposettings as rs


class TestRepoSettings(unittest.TestCase):
    def test_validate(self):
        self.assertFalse(rs.RepoSettings._validate({}))
        self.assertFalse(rs.RepoSettings._validate({
            "repos": None
        }))
        self.assertFalse(rs.RepoSettings._validate({
            "repos": True
        }))
        self.assertFalse(rs.RepoSettings._validate({
            "repos": {}
        }))
        self.assertTrue(rs.RepoSettings._validate({
            "repos": {"a": {}}
        }))

    def test_apply(self):
        ghmock = MagicMock()
        r = rs.RepoSettings(ghmock)
        r.apply({
            "repos": {
                "test": {}
            }
        })
        ghmock.get_repo.assert_called_with("test")

        settermock = MagicMock()
        settermock.name.return_value = "mock"
        r.use(settermock)
        r.apply({
            "repos": {
                "test": {}
            }
        })
        settermock.set.assert_called_once()


if __name__ == '__main__':
    unittest.main()
