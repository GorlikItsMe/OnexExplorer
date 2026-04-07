#include "MainWindow.h"
#include "cli.h"

#include <QApplication>
#include <QCoreApplication>
#include <QStringList>

int main(int argc, char *argv[]) {
    // Make CLI work in headless CI by default.
    const bool isCli = Cli::argvContainsCli(argc, argv);
    if (isCli && qEnvironmentVariableIsEmpty("DISPLAY") && qEnvironmentVariableIsEmpty("QT_QPA_PLATFORM"))
        qputenv("QT_QPA_PLATFORM", QByteArrayLiteral("offscreen"));

    QApplication a(argc, argv);
    a.setApplicationName("OnexExplorer");
    const int cliRc = Cli::run(a);
    if (cliRc != -1)
        return cliRc;

    MainWindow w;
    w.show();
    return a.exec();
}
