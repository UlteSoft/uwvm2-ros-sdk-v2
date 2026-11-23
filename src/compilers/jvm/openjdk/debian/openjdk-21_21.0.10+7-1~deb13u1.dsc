-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA512

Format: 3.0 (quilt)
Source: openjdk-21
Binary: openjdk-21-jdk-headless, openjdk-21-jre-headless, openjdk-21-jdk, openjdk-21-jre, openjdk-21-demo, openjdk-21-source, openjdk-21-doc, openjdk-21-dbg, openjdk-21-testsupport, openjdk-21-jre-zero
Architecture: alpha amd64 arc armel armhf arm64 i386 loong64 mips64el powerpc ppc64 ppc64el m68k riscv64 sh4 sparc sparc64 s390x x32 all
Version: 21.0.10+7-1~deb13u1
Maintainer: OpenJDK Team <openjdk-21@packages.debian.org>
Uploaders: Matthias Klose <doko@ubuntu.com>
Homepage: https://openjdk.java.net/
Standards-Version: 4.6.2
Vcs-Browser: https://salsa.debian.org/openjdk-team/openjdk/tree/openjdk-21
Vcs-Git: https://salsa.debian.org/openjdk-team/openjdk.git -b openjdk-21
Testsuite: autopkgtest
Testsuite-Triggers: bash, build-essential, dbus-x11, jtreg7, libatk-wrapper-java, libatk-wrapper-java-jni, libtestng7-java, lsb-release, xauth, xfwm4, xvfb
Build-Depends: debhelper (>= 11), m4, lsb-release, zip, unzip, sharutils, gawk, cpio, procps, wdiff, pkgconf, fastjar (>= 2:0.96-0ubuntu2), time, strip-nondeterminism, debugedit (>= 4.16), jtreg7 (>= 7.3.1+1~) <!nocheck>, libtestng7-java <!nocheck>, xvfb <!nocheck>, xauth <!nocheck>, xfonts-base <!nocheck>, libgl1-mesa-dri [!x32] <!nocheck>, xfwm4 <!nocheck>, x11-xkb-utils <!nocheck>, dbus-x11 <!nocheck>, libasmtools-java <!nocheck>, autoconf, automake, ant, ant-optional, g++-14 <!cross>, openjdk-21-jdk-headless:native | openjdk-20-jdk-headless:native, libxtst-dev, libxi-dev, libxt-dev, libxaw7-dev, libxrender-dev, libcups2-dev, libasound2-dev, liblcms2-dev, libxinerama-dev, libkrb5-dev, xsltproc, libpcsclite-dev, libxrandr-dev, libelf-dev, libfontconfig-dev, libfreetype-dev, libharfbuzz-dev, libffi-dev, libffi-dev:native, zlib1g-dev:native, zlib1g-dev, libattr1-dev, libpng-dev, libjpeg-dev, libgif-dev, systemtap-sdt-dev [!powerpc !ppc64 !ppc64el !sh4 !s390x], libnss3-dev (>= 2:3.17.1), openjdk-21-jdk-headless <cross>
Build-Depends-Indep: graphviz, pandoc
Package-List:
 openjdk-21-dbg deb debug optional arch=alpha,amd64,arc,armel,armhf,arm64,i386,loong64,mips64el,powerpc,ppc64,ppc64el,m68k,riscv64,sh4,sparc,sparc64,s390x,x32
 openjdk-21-demo deb java optional arch=alpha,amd64,arc,armel,armhf,arm64,i386,loong64,mips64el,powerpc,ppc64,ppc64el,m68k,riscv64,sh4,sparc,sparc64,s390x,x32
 openjdk-21-doc deb doc optional arch=all
 openjdk-21-jdk deb java optional arch=alpha,amd64,arc,armel,armhf,arm64,i386,loong64,mips64el,powerpc,ppc64,ppc64el,m68k,riscv64,sh4,sparc,sparc64,s390x,x32
 openjdk-21-jdk-headless deb java optional arch=alpha,amd64,arc,armel,armhf,arm64,i386,loong64,mips64el,powerpc,ppc64,ppc64el,m68k,riscv64,sh4,sparc,sparc64,s390x,x32
 openjdk-21-jre deb java optional arch=alpha,amd64,arc,armel,armhf,arm64,i386,loong64,mips64el,powerpc,ppc64,ppc64el,m68k,riscv64,sh4,sparc,sparc64,s390x,x32
 openjdk-21-jre-headless deb java optional arch=alpha,amd64,arc,armel,armhf,arm64,i386,loong64,mips64el,powerpc,ppc64,ppc64el,m68k,riscv64,sh4,sparc,sparc64,s390x,x32
 openjdk-21-jre-zero deb java optional arch=amd64,i386,arm64,armhf,ppc64,ppc64el,riscv64,s390x
 openjdk-21-source deb java optional arch=all
 openjdk-21-testsupport deb java optional arch=alpha,amd64,arc,armel,armhf,arm64,i386,loong64,mips64el,powerpc,ppc64,ppc64el,m68k,riscv64,sh4,sparc,sparc64,s390x,x32
Checksums-Sha1:
 f757f831f55051a51c3dd670ea0368111b23c53a 613408 openjdk-21_21.0.10+7.orig-googletest.tar.xz
 d7908899b92be621d2fa420645e96cf178c4ffea 67584308 openjdk-21_21.0.10+7.orig.tar.xz
 77216f94d7f827c58cf04c55d4da65913ca61b54 216804 openjdk-21_21.0.10+7-1~deb13u1.debian.tar.xz
Checksums-Sha256:
 6e6699c442cd6bc008140d159b43a7a39bb811d1ecd380cf3b707cc535e04393 613408 openjdk-21_21.0.10+7.orig-googletest.tar.xz
 cd66eb8091406d663f040fe476ea9b077e7c77b6b6742d8ae338dcbb6d01a0d8 67584308 openjdk-21_21.0.10+7.orig.tar.xz
 15f65f39a08ed6d949265d26be0b212e37cc110bea790b139a518a1dbc13577a 216804 openjdk-21_21.0.10+7-1~deb13u1.debian.tar.xz
Files:
 ae1c58d38d39133ebcdc47e09d77a661 613408 openjdk-21_21.0.10+7.orig-googletest.tar.xz
 2463a5f860b7f1d1db9f489092d9fd06 67584308 openjdk-21_21.0.10+7.orig.tar.xz
 6f811eda0382cae74b23db2219df0d3b 216804 openjdk-21_21.0.10+7-1~deb13u1.debian.tar.xz

-----BEGIN PGP SIGNATURE-----

iQIzBAEBCgAdFiEEtuYvPRKsOElcDakFEMKTtsN8TjYFAmlyoKoACgkQEMKTtsN8
Tja8qA//d7WXemjJ1QbYgChybsDw7qpFqfRw1YZLzmqs92D/RtAutk0lZ5ZHCHha
91hpqmqKaD1pAXEXtMd8GfDSgmjsOzonVqCFvUrbIMa96J0/iRLIoKTSpwmjYvMV
gklEGFI7TEmqaqwokjS+8TvOImsll0nN6nIiijqiaKQrwqX7YSFoXqs8f1UyhWPt
xp7OHG2s0AXrGUkB3BLu1ZFSdHn5fpd44dy3SsoU7GGCsk97dddgvj0ZouqDOBI6
0ufRrxesmyVaGHRpyWtP0Pvo/0NNbyvREArd1aO5Ammy3P90vv2sryleCa3Ctawt
gusXe11xyzVM3yMO8oG0GGgBvlaqYqbAMw6u36nzB9zPkR3mU+N/NoUEwkHMJ2as
6MWVmySK5qER1R97d7yr32xsh6lytqnDmOT1QY/HcMYVhZYPQp82sfqpwexc4xA3
zo2LECoN57uEUFCAGaSdNAVnGj6yLBF4qTWwqC0Fjm3M4bVvhj/VwQ8VfPEnUW/f
2eVkEH/0EMCJNFx6helUmIUG3Jsktfy+ntPlBorvjJWzn6HYq8pUy8J4qmcJbAvy
uPi3LFd2odo2aGHFxgs33LkTCaD3pllRJzBWbDTXFR8OLs2iamC6cVuwa6IpTr6g
yXtpCD0n2xy8UPf7Lw5YhmcU5ElzWCk0y/oyrNZuReHDhsCUN1s=
=WX+u
-----END PGP SIGNATURE-----
