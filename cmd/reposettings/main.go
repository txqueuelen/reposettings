package main

import (
	"fmt"
	"io"
	"os"
	"runtime"

	"github.com/txqueuelen/reposettings/config"

	log "github.com/sirupsen/logrus"
	flag "github.com/spf13/pflag"
	yaml "gopkg.in/yaml.v3"
)

var (
	version   = "0.0.0"
	gitCommit = ""
	buildDate = ""
)

func main() {
	configFile := flag.String("config", "", "File where to read the repository settings to set")
	verboseLog := flag.Bool("verbose", false, "Sets log level to debug.")
	flag.Parse()

	logger := log.StandardLogger()
	if *verboseLog {
		logger.SetLevel(log.DebugLevel)
	}

	logger.Infof(
		"reposettings action Version: %s, Platform: %s, GoVersion: %s, GitCommit: %s, BuildDate: %s",
		version,
		fmt.Sprintf("%s/%s", runtime.GOOS, runtime.GOARCH),
		runtime.Version(),
		gitCommit,
		buildDate,
	)

	if *configFile == "" && len(os.Args) == 2 {
		logger.Warn("repoSettings config not set by flag. Going fallback to legacy usage")
		*configFile = os.Args[1]
	}

	fileReader, err := os.Open(*configFile)
	if err != nil {
		logger.Logf(log.FatalLevel, "could not open file %s: %s", *configFile, err)
		logger.Exit(1)
	}

	data, err := io.ReadAll(fileReader)
	if err != nil {
		logger.Logf(log.FatalLevel, "could not read from the config file %s: %s", *configFile, err)
		logger.Exit(2)
	}

	if err = fileReader.Close(); err != nil {
		logger.Logf(log.FatalLevel, "could not close the file %s: %s", *configFile, err)
		// As we are incrementally rising the error level as errors are found but I keep the ERRNO 3 as the error
		// for not being able to read $GITHUB_TOKEN as legacy.
		logger.Exit(4)
	}

	token := os.Getenv("GITHUB_TOKEN")
	if token == "" {
		logger.Logf(log.FatalLevel, "could not read $GITHUB_TOKEN")
		logger.Exit(3)
	}

	var yml config.RepoSettings
	if err = yaml.Unmarshal(data, &yml); err != nil {
		logger.Logf(log.FatalLevel, "error unmarshalling YAML (%s): %s", *configFile, err)
		logger.Exit(5)
	}
}
