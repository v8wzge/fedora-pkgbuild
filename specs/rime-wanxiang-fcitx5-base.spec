%global rime_data %{_datadir}/rime-data

Name:           rime-wanxiang-fcitx5-base
Version:        18.2.0
Release:        1%{?dist}
Summary:        Wanxiang Rime schemas and Lua extensions for Fcitx5
License:        CC-BY-4.0
URL:            https://github.com/amzxyz/rime-wanxiang
Source0:        rime-wanxiang-base.zip
Source1:        rime-wanxiang-LICENSE

BuildArch:      noarch
BuildRequires:  unzip
Requires:       fcitx5-rime
Requires:       librime-lua
Requires:       librime-octagram
Requires:       rime-wanxiang-fcitx5-dicts = %{version}-%{release}
Conflicts:      rime-wanxiang-ibus-base
Conflicts:      rime-wanxiang-ibus-dicts

%description
Wanxiang Pinyin standard (Base) Rime schemas, Lua extensions and OpenCC data
for Fcitx5 Rime. Requires the companion rime-wanxiang-fcitx5-dicts package,
which provides the dictionary tables referenced by the schemas.

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
# Dictionary tables come from the companion -dicts package.
rm -rf %{buildroot}%{rime_data}/dicts
install -d %{buildroot}%{_licensedir}/%{name}
install -pm644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/LICENSE

%files
%license %{_licensedir}/%{name}/LICENSE
%{rime_data}/*

%changelog
* Sun Nov 22 2026 v8wzge <v8wzge@users.noreply.github.com> - 18.2.0-1
- Automated build from the upstream standard (Base) release
