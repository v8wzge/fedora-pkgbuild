# Snapshot values are rewritten by scripts/render_spec.py at build time.
%global commit 0000000000000000000000000000000000000000
%global commitdate 19700101
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Name:           kdesvn
# Epoch 1 keeps this master-branch snapshot higher than Fedora's 2.1.0-18.fc45.
Epoch:          1
Version:        2.1.0
Release:        0.1.%{commitdate}git%{shortcommit}%{?dist}
Summary:        KDE Subversion client
License:        GPL-2.0-or-later
URL:            https://invent.kde.org/sdk/kdesvn
Source0:        %{name}-%{version}.tar.gz
Source1:        kdesvn-zh_CN.po

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  extra-cmake-modules
BuildRequires:  gettext
BuildRequires:  git
BuildRequires:  apr-devel
BuildRequires:  apr-util-devel
BuildRequires:  subversion-devel
BuildRequires:  qt6-qtbase-devel
BuildRequires:  qt6-qt5compat-devel
BuildRequires:  kf6-kbookmarks-devel
BuildRequires:  kf6-kcodecs-devel
BuildRequires:  kf6-kcompletion-devel
BuildRequires:  kf6-kconfig-devel
BuildRequires:  kf6-kconfigwidgets-devel
BuildRequires:  kf6-kcoreaddons-devel
BuildRequires:  kf6-kdbusaddons-devel
BuildRequires:  kf6-kdoctools-devel
BuildRequires:  kf6-ki18n-devel
BuildRequires:  kf6-kiconthemes-devel
BuildRequires:  kf6-kitemviews-devel
BuildRequires:  kf6-kjobwidgets-devel
BuildRequires:  kf6-kio-devel
BuildRequires:  kf6-knotifications-devel
BuildRequires:  kf6-kparts-devel
BuildRequires:  kf6-kservice-devel
BuildRequires:  kf6-ktextwidgets-devel
BuildRequires:  kf6-kwallet-devel
BuildRequires:  kf6-kwidgetsaddons-devel
BuildRequires:  kf6-kxmlgui-devel

Requires:       subversion

%description
kdesvn is a graphical Subversion client for KDE. It integrates with KDE
applications through a KPart and a KIO slave.

This package tracks the Qt 6 / KDE Frameworks 6 master branch of kdesvn.

%prep
%autosetup -n %{name}-%{version}
# Complete Simplified Chinese translation maintained in this repository.
install -Dpm644 %{SOURCE1} po/zh_CN/kdesvn.po

%build
%cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_TESTING=OFF
%cmake_build

%install
%cmake_install
%find_lang %{name}
install -d %{buildroot}%{_licensedir}/%{name}
install -pm644 COPYING COPYING.OpenSSL %{buildroot}%{_licensedir}/%{name}/
install -d %{buildroot}%{_docdir}/%{name}
install -pm644 AUTHORS ChangeLog %{buildroot}%{_docdir}/%{name}/

%files -f %{name}.lang
%license %{_licensedir}/%{name}/COPYING
%license %{_licensedir}/%{name}/COPYING.OpenSSL
%doc %{_docdir}/%{name}/AUTHORS
%doc %{_docdir}/%{name}/ChangeLog
%{_bindir}/kdesvn
%{_bindir}/kdesvnaskpass
%{_libdir}/qt6/plugins/kf6/kded/kdesvnd.so
%{_libdir}/qt6/plugins/kf6/kfileitemaction/ksvn_fileitemactions.so
%{_libdir}/qt6/plugins/kf6/kio/kio_ksvn.so
%{_libdir}/qt6/plugins/kf6/parts/kdesvnpart.so
%{_datadir}/applications/org.kde.kdesvn.desktop
%{_datadir}/config.kcfg/kdesvn_part.kcfg
%{_datadir}/dbus-1/interfaces/kf6_org.kde.kdesvnd.xml
%{_datadir}/dbus-1/services/org.kde.kdesvnd.service
%{_datadir}/doc/HTML/*/kdesvn/
%{_datadir}/icons/hicolor/*/actions/kdesvn*
%{_datadir}/icons/hicolor/*/apps/kdesvn*
%{_datadir}/icons/hicolor/*/places/kdesvn*
%{_datadir}/kdesvn/
%{_mandir}/man1/kdesvn*
%{_mandir}/*/man1/kdesvn*
%{_datadir}/metainfo/org.kde.kdesvn.appdata.xml

%changelog
* Sat Nov 21 2026 v8wzge <v8wzge@users.noreply.github.com> - 2.1.0-0.1
- Automated snapshot build from upstream master
