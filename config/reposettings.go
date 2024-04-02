package config

import (
	"encoding/json"
	"fmt"

	"github.com/google/go-github/v60/github"

	yaml "gopkg.in/yaml.v3"
)

type RepoSetting []*github.Ruleset

type RepoSettings struct {
	Common    RepoSetting
	Overrides map[string]RepoSetting
}

func (rs *RepoSettings) UnmarshalYAML(node *yaml.Node) error {
	var i interface{}
	if err := node.Decode(&i); err != nil {
		return fmt.Errorf("parsing reposetting: %w", err)
	}

	test1, err := json.Marshal(i)
	test2, err := json.Marshal(yamlToJson(i))

	_, _ = test1, test2

	return err
}

func yamlToJson(i interface{}) interface{} {
	switch x := i.(type) {
	case map[string]interface{}:
		return yamlToJsonMap(x)
	case []interface{}:
		return yamlToJsonSlice(x)
	default:
		return i
	}
}

func yamlToJsonMap(origin map[string]interface{}) interface{} {
	mapsi := map[string]interface{}{}
	for k, v := range origin {
		mapsi[k] = yamlToJson(v)
	}
	return mapsi
}

func yamlToJsonSlice(origin []interface{}) interface{} {
	for k, v := range origin {
		origin[k] = yamlToJson(v)
	}
	return origin
}
