#include "cli.h"

#include "Openers/NosCCInfOpener.h"
#include "Openers/NosOpenerSelector.h"
#include "Openers/NosTextOpener.h"
#include "Openers/NosZlibOpener.h"

#include <QApplication>
#include <QCommandLineParser>
#include <QDebug>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QStringList>

namespace {
static bool argvContains(int argc, char *argv[], const char *needle) {
    for (int i = 1; i < argc; ++i) {
        if (qstrcmp(argv[i], needle) == 0)
            return true;
    }
    return false;
}

static INosFileOpener *selectOpener(const QByteArray &header, NosTextOpener &textOpener, NosZlibOpener &zlibOpener,
                                    NosCCInfOpener &ccinfOpener) {
    switch (selectNosOpenerKind(header)) {
        case NosOpenerKind::Zlib:
            return &zlibOpener;
        case NosOpenerKind::CCInf:
            return &ccinfOpener;
        case NosOpenerKind::Text:
        default:
            return &textOpener;
    }
}

static int runCliUnpack(const QString &unpackFile, const QString &targetDir) {
    if (unpackFile.isEmpty() || targetDir.isEmpty())
        return Cli::BadArgs;

    QFileInfo inInfo(unpackFile);
    if (!inInfo.exists() || !inInfo.isFile())
        return Cli::CannotOpenInput;

    QDir outDir(targetDir);
    if (!outDir.exists()) {
        if (!QDir().mkpath(targetDir))
            return Cli::CannotWriteTarget;
    }

    QString normalizedTarget = QDir::cleanPath(targetDir);
    if (!normalizedTarget.endsWith('/'))
        normalizedTarget += '/';

    QFile file(unpackFile);
    if (!file.open(QIODevice::ReadOnly))
        return Cli::CannotOpenInput;

    QByteArray header = file.read(0x0B);
    file.seek(0);

    NosTextOpener textOpener;
    NosZlibOpener zlibOpener;
    NosCCInfOpener ccinfOpener;

    INosFileOpener *opener = selectOpener(header, textOpener, zlibOpener, ccinfOpener);
    OnexTreeItem *root = opener->decrypt(file);
    file.close();

    if (root == nullptr) {
        qDebug() << "CLI unpack failed: decrypt returned null";
        return Cli::UnpackFailed;
    }

    qDebug() << "CLI unpack decrypt ok, exporting to:" << normalizedTarget;
    const int written = root->onExport(normalizedTarget);
    qDebug() << "CLI unpack done, onExport returned:" << written;
    return Cli::Ok;
}
} // namespace

namespace Cli {
bool argvContainsCli(int argc, char *argv[]) {
    return argvContains(argc, argv, "--cli");
}

int run(QApplication &app) {
    QCommandLineParser parser;
    parser.setApplicationDescription("OnexExplorer (GUI + CLI). Use --cli to run headless commands.");
    parser.addHelpOption();
    parser.addVersionOption();

    QCommandLineOption cliOpt(QStringList() << "cli", "Run in CLI mode (no GUI).");
    QCommandLineOption unpackOpt(QStringList() << "unpack", "Unpack a .NOS file.", "filepath");
    QCommandLineOption targetOpt(QStringList() << "target", "Target folder for --unpack output.", "folder");

    parser.addOption(cliOpt);
    parser.addOption(unpackOpt);
    parser.addOption(targetOpt);
    parser.process(app);

    if (!parser.isSet(cliOpt))
        return -1; // not CLI mode

    if (!parser.isSet(unpackOpt) || !parser.isSet(targetOpt)) {
        parser.showHelp(BadArgs);
    }

    return runCliUnpack(parser.value(unpackOpt), parser.value(targetOpt));
}
} // namespace Cli

