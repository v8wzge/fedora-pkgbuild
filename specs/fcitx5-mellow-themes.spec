%global commit 0000000000000000000000000000000000000000
%global commitdate 19700101
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Name:           fcitx5-mellow-themes
Version:        20260101
Release:        0.1.%{commitdate}git%{shortcommit}%{?dist}
Summary:        Mellow rounded-rectangle themes for Fcitx5
License:        BSD-2-Clause
URL:            https://github.com/sanweiya/fcitx5-mellow-themes
Source0:        %{name}-%{version}.tar.gz
Source1:        fcitx5-mellow-themes-LICENSE

BuildArch:      noarch
Requires:       fcitx5

%description
A set of aesthetic, modern Fcitx5 input method themes featuring rounded
rectangle designs, including graphite, sakura, vermilion, wechat and youlan
variants in light and dark flavours.

%prep
%autosetup -n %{name}-%{version}

%build
# Themes are pure QML/SVG data.

%install
rm -rf %{buildroot}
install -d %{buildroot}%{_datadir}/fcitx5/themes
for theme in mellow-*; do
    [[ -d "$theme" ]] || continue
    cp -a "$theme" %{buildroot}%{_datadir}/fcitx5/themes/
done
install -d %{buildroot}%{_licensedir}/%{name}
install -pm644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/LICENSE
install -d %{buildroot}%{_docdir}/%{name}
install -pm644 README.md %{buildroot}%{_docdir}/%{name}/README.md

%files
%license %{_licensedir}/%{name}/LICENSE
%doc %{_docdir}/%{name}/README.md
%{_datadir}/fcitx5/themes/mellow-*

%changelog
* Sun Nov 22 2026 v8wzge <v8wzge@users.noreply.github.com> - 20260101-0.1
- Automated snapshot build from upstream main
