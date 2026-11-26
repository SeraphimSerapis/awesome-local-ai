# SPDX-License-Identifier: MIT
"""Vendored SPDX OSI-approved license IDs and license exceptions. Python 3.11+, no dependencies.

Generated from spdx/license-list-data v3.29.0:
- OSI_LICENSES: non-deprecated SPDX identifiers with isOsiApproved == true (excludes CC0-1.0).
- SPDX_EXCEPTIONS: non-deprecated SPDX license exception identifiers.
"""

SPDX_LIST_VERSION = "v3.29.0"

OSI_LICENSES = frozenset({
    "0BSD", "AAL", "AFL-1.1", "AFL-1.2", "AFL-2.0", "AFL-2.1", "AFL-3.0", "AGPL-3.0-only",
    "AGPL-3.0-or-later", "ALGLIB-Documentation", "APL-1.0", "APSL-1.0", "APSL-1.1", "APSL-1.2",
    "APSL-2.0", "Apache-1.1", "Apache-2.0", "Artistic-1.0", "Artistic-1.0-Perl",
    "Artistic-1.0-cl8", "Artistic-2.0", "BSD-1-Clause", "BSD-2-Clause", "BSD-2-Clause-Patent",
    "BSD-3-Clause", "BSD-3-Clause-LBNL", "BSD-3-Clause-Open-MPI", "BSD-ask-to-endorse",
    "BSL-1.0", "BlueOak-1.0.0", "CAL-1.0", "CAL-1.0-Combined-Work-Exception", "CATOSL-1.1",
    "CDDL-1.0", "CDDL-1.1", "CECILL-2.1", "CERN-OHL-P-2.0", "CERN-OHL-S-2.0", "CERN-OHL-W-2.0",
    "CNRI-Python", "CNRI-Python-GPL-Compatible", "CPAL-1.0", "CPL-1.0", "CUA-OPL-1.0",
    "ECL-1.0", "ECL-2.0", "EFL-1.0", "EFL-2.0", "EPL-1.0", "EPL-2.0", "EUDatagrid", "EUPL-1.1",
    "EUPL-1.2", "Entessa", "Fair", "Frameworx-1.0", "GPL-2.0-only", "GPL-2.0-or-later",
    "GPL-3.0-only", "GPL-3.0-or-later", "HPND", "ICU", "IPA", "IPL-1.0", "ISC", "Intel", "Jam",
    "LGPL-2.0-only", "LGPL-2.0-or-later", "LGPL-2.1-only", "LGPL-2.1-or-later", "LGPL-3.0-only",
    "LGPL-3.0-or-later", "LPL-1.0", "LPL-1.02", "LPPL-1.3c", "LiLiQ-P-1.1", "LiLiQ-R-1.1",
    "LiLiQ-Rplus-1.1", "MIT", "MIT-0", "MIT-Modern-Variant", "MPL-1.0", "MPL-1.1", "MPL-2.0",
    "MPL-2.0-no-copyleft-exception", "MS-PL", "MS-RL", "MirOS", "Motosoto", "MulanPSL-2.0",
    "Multics", "NASA-1.3", "NCSA", "NGPL", "NPOSL-3.0", "NTP", "Naumen", "Nokia", "OCLC-2.0",
    "OFL-1.1", "OFL-1.1-RFN", "OFL-1.1-no-RFN", "OGTSL", "OLDAP-2.8", "OLFL-1.3", "OSC-1.0",
    "OSET-PL-2.1", "OSL-1.0", "OSL-2.0", "OSL-2.1", "OSL-3.0", "PHP-3.0", "PHP-3.01",
    "PostgreSQL", "Python-2.0", "Python-2.0.1", "QPL-1.0", "RPL-1.1", "RPL-1.5", "RPSL-1.0",
    "RSCPL", "SISSL", "SPL-1.0", "SimPL-2.0", "Sleepycat", "UCL-1.0", "UPL-1.0", "Unicode-3.0",
    "Unicode-DFS-2016", "Unlicense", "VSL-1.0", "W3C", "W3C-20150513", "Watcom-1.0", "WordNet",
    "Xnet", "ZPL-2.0", "ZPL-2.1", "Zlib", "curl",
})

SPDX_EXCEPTIONS = frozenset({
    "389-exception", "Asterisk-exception", "Asterisk-linking-protocols-exception",
    "Autoconf-exception-2.0", "Autoconf-exception-3.0", "Autoconf-exception-generic",
    "Autoconf-exception-generic-3.0", "Autoconf-exception-macro", "Bison-exception-1.24",
    "Bison-exception-2.2", "Bootloader-exception", "CGAL-linking-exception",
    "CLISP-exception-2.0", "Classpath-exception-2.0", "Classpath-exception-2.0-short",
    "DigiRule-FOSS-exception", "Digia-Qt-LGPL-exception-1.1", "FLTK-exception",
    "Fawkes-Runtime-exception", "Font-exception-2.0", "GCC-exception-2.0",
    "GCC-exception-2.0-note", "GCC-exception-3.1", "GNAT-exception", "GNOME-examples-exception",
    "GNU-compiler-exception", "GPL-3.0-389-ds-base-exception", "GPL-3.0-interface-exception",
    "GPL-3.0-linking-exception", "GPL-3.0-linking-source-exception", "GPL-CC-1.0",
    "GStreamer-exception-2005", "GStreamer-exception-2008", "Gmsh-exception",
    "Google-Patent-WebM", "Independent-modules-exception", "KiCad-libraries-exception",
    "LGPL-3.0-linking-exception", "LLGPL", "LLVM-exception", "LZMA-exception",
    "Libtool-exception", "Linux-syscall-note", "OCCT-exception-1.0",
    "OCaml-LGPL-linking-exception", "OpenJDK-assembly-exception-1.0", "PCRE2-exception",
    "PS-or-PDF-font-exception-20170817", "QPL-1.0-INRIA-2004-exception", "Qt-GPL-exception-1.0",
    "Qt-LGPL-exception-1.1", "Qwt-exception-1.0", "RRDtool-FLOSS-exception-2.0",
    "SANE-exception", "SHL-2.0", "SHL-2.1", "SWI-exception", "Simple-Library-Usage-exception",
    "Spelling-Provider-LGPL-exception", "Swift-exception", "Texinfo-exception",
    "UBDL-exception", "Universal-FOSS-exception-1.0", "WxWindows-exception-3.1",
    "cryptsetup-OpenSSL-exception", "eCos-exception-2.0", "erlang-otp-linking-exception",
    "fmt-exception", "freertos-exception-2.0", "gnu-javamail-exception", "harbour-exception",
    "i2p-gpl-java-exception", "kvirc-openssl-exception", "libpri-OpenH323-exception",
    "mif-exception", "mxml-exception", "openvpn-openssl-exception", "polyparse-exception",
    "romic-exception", "rsync-linking-exception", "sqlitestudio-OpenSSL-exception",
    "stunnel-exception", "u-boot-exception-2.0", "vsftpd-openssl-exception",
    "x11vnc-openssl-exception",
})
