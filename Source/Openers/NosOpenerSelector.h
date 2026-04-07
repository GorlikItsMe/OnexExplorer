#pragma once

#include <QByteArray>

enum class NosOpenerKind {
    Text,
    Zlib,
    CCInf,
};

NosOpenerKind selectNosOpenerKind(const QByteArray &header);

