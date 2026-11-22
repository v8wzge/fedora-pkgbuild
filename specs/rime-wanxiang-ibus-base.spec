%global rime_data %{_datadir}/rime-data

Name:           rime-wanxiang-ibus-base
Version:        18.2.0
Release:        1%{?dist}
Summary:        Wanxiang Rime schemas and dictionaries for IBus
License:        CC-BY-4.0
URL:            https://github.com/amzxyz/rime-wanxiang
Source0:        rime-wanxiang-base.zip
Source1:        rime-wanxiang-LICENSE

BuildArch:      noarch
BuildRequires:  unzip
Requires:       ibus-rime
Requires:       librime-lua
Requires:       librime-octagram
Requires:       rime-wanxiang-ibus-dicts = %{version}-%{release}
Conflicts:      rime-wanxiang-fcitx5-base
Conflicts:      rime-wanxiang-fcitx5-dicts

%description
Wanxiang Pinyin standard (Base) Rime schemas, Lua extensions, OpenCC data and
dictionary tables for IBus Rime. The companion rime-wanxiang-ibus-dicts package
provides the octagram grammar model referenced by the schemas.

%prep
rm -rf wanxiang-base
mkdir wanxiang-base
unzip -q %{SOURCE0} -d wanxiang-base

%build
# Upstream ships pre-built Rime configuration data.

%install
rm -rf %{buildroot}
install -d %{buildroot}%{rime_data}
cp -a wanxiang-base/. %{buildroot}%{rime_data}/
install -d %{buildroot}%{_licensedir}/%{name}
install -pm644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/LICENSE

%files
%license %{_licensedir}/%{name}/LICENSE
%{rime_data}/*

%changelog
* Sun Nov 22 2026 v8wzge <v8wzge@users.noreply.github.com> - 18.2.0-1
- Automated build from the upstream standard (Base) release
