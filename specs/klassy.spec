# Snapshot values are rewritten by scripts/render_spec.py at build time.
%global commit 0000000000000000000000000000000000000000
%global commitdate 19700101
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Name:           klassy
Version:        6.7.4
Release:        0.1.%{commitdate}git%{shortcommit}%{?dist}
Summary:        Highly customizable KDE Plasma theme and window decoration
License:        GPL-2.0-or-later
URL:            https://github.com/paulmcauley/klassy
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  extra-cmake-modules
BuildRequires:  gettext
BuildRequires:  kdecoration-devel
BuildRequires:  libplasma-devel
BuildRequires:  qt6-qtbase-devel
BuildRequires:  qt6-qtdeclarative-devel
BuildRequires:  qt6-qtsvg-devel
BuildRequires:  kf6-kcmutils-devel
BuildRequires:  kf6-kcolorscheme-devel
BuildRequires:  kf6-kconfig-devel
BuildRequires:  kf6-kcoreaddons-devel
BuildRequires:  kf6-frameworkintegration-devel
BuildRequires:  kf6-kguiaddons-devel
BuildRequires:  kf6-ki18n-devel
BuildRequires:  kf6-kiconthemes-devel
BuildRequires:  kf6-kpackage-devel
BuildRequires:  kf6-kservice-devel
BuildRequires:  kf6-kwindowsystem-devel

Requires:       plasma-desktop

%description
Klassy is a highly customizable window decoration, application style, colour
scheme and global theme for KDE Plasma.

This package tracks the Plasma 6.8 development branch and builds the Qt 6
components only.

%prep
%autosetup -n %{name}-%{version}

%build
%cmake -DBUILD_QT5=OFF -DBUILD_QT6=ON -DCMAKE_BUILD_TYPE=RelWithDebInfo
%cmake_build

%install
%cmake_install
%find_lang %{name}
install -d %{buildroot}%{_licensedir}/%{name}
cp -a LICENSES/. %{buildroot}%{_licensedir}/%{name}/
install -d %{buildroot}%{_docdir}/%{name}
install -pm644 README.md AUTHORS %{buildroot}%{_docdir}/%{name}/

%files -f %{name}.lang
%license %{_licensedir}/%{name}/
%doc %{_docdir}/%{name}/README.md %{_docdir}/%{name}/AUTHORS
%{_bindir}/klassy-settings
%{_libdir}/cmake/Klassy/
%{_libdir}/libklassycommon*.so
%{_libdir}/qt6/plugins/styles/klassy*.so
%{_libdir}/qt6/plugins/kf6/kdecoration/klassydecoration.so
%{_libdir}/qt6/plugins/org.kde.kdecoration3.kcm/klassydecoration/
%{_datadir}/applications/klassy-settings.desktop
%{_datadir}/color-schemes/*.colors
%{_datadir}/icons/klassy*/
%{_datadir}/kcfg/*klassy*
%{_datadir}/kstyle/themes/klassy.themerc
%{_datadir}/plasma/layout-templates/*
%{_datadir}/plasma/look-and-feel/*
%{_datadir}/themes/klassy*/

%changelog
* Sat Nov 21 2026 v8wzge <v8wzge@users.noreply.github.com> - 6.7.4-0.1
- Automated snapshot build from upstream 6.8temp branch
