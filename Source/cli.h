#pragma once

#include <QStringList>

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

// Runs CLI/help parsing. Pass the argv snapshot taken *before* QApplication(argc, argv) — Qt may strip flags
// like --help from argv, which would otherwise fall through to the GUI.
int run(QApplication &app, const QStringList &arguments);
} // namespace Cli

