#include "NosOpenerSelector.h"

NosOpenerKind selectNosOpenerKind(const QByteArray &header) {
    if (header.mid(0, 7) == "NT Data" || header.mid(0, 10) == "32GBS V1.0" || header.mid(0, 10) == "ITEMS V1.0")
        return NosOpenerKind::Zlib;
    if (header.mid(0, 11) == "CCINF V1.20")
        return NosOpenerKind::CCInf;
    return NosOpenerKind::Text;
}

