#pragma once

class QApplication;

namespace Cli {
// CLI exit codes (kept stable for automation).
enum ExitCode : int {
    Ok = 0,
    BadArgs = 2,
    CannotOpenInput = 3,
    UnpackFailed = 4,
    CannotWriteTarget = 5,
};

// Returns true if argv contains --cli (used before QApplication init).
bool argvContainsCli(int argc, char *argv[]);

// Runs the CLI mode. Assumes QApplication is already constructed.
int run(QApplication &app);
} // namespace Cli

