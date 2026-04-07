#include "MainWindow.h"
#include "cli.h"

#include <QApplication>
#include <QCoreApplication>
#include <QStringList>

#ifdef Q_OS_WIN
#include <windows.h>
#endif

int main(int argc, char *argv[]) {
    // Snapshot before QApplication: Qt may remove e.g. --help/--version from argc/argv; without this,
    // help would not be detected and the GUI (or Qt's dialogs) could appear instead of console output.
    QStringList argsForCli;
    argsForCli.reserve(argc);
    for (int i = 0; i < argc; ++i)
        argsForCli << QString::fromLocal8Bit(argv[i]);

#ifdef Q_OS_WIN
    // Linked as a console process: a console exists when useful (CLI args). For plain GUI launch
    // (double-click / no arguments) detach so a stray terminal window does not stay open.
    if (argsForCli.size() <= 1)
        FreeConsole();
#endif

    const bool isCli = argsForCli.contains(QStringLiteral("--cli"));
    // Linux CI: no DISPLAY unless using offscreen. On Windows do not default to offscreen — portable folders
    // usually ship qwindows.dll only; forcing offscreen breaks --cli without qoffscreen.dll.
    if (isCli && qEnvironmentVariableIsEmpty("QT_QPA_PLATFORM")) {
#if !defined(Q_OS_WIN)
        if (qEnvironmentVariableIsEmpty("DISPLAY"))
            qputenv("QT_QPA_PLATFORM", QByteArrayLiteral("offscreen"));
#endif
    }

    QApplication a(argc, argv);
    a.setApplicationName("OnexExplorer");
    a.setApplicationVersion(QStringLiteral("1.0"));
    const int cliRc = Cli::run(a, argsForCli);
    if (cliRc != -1)
        return cliRc;

    MainWindow w;
    w.show();
    return a.exec();
}
