%global rime_data %{_datadir}/rime-data

Name:           rime-wanxiang-ibus-dicts
Version:        18.2.0
Release:        1%{?dist}
Summary:        Wanxiang octagram language model for IBus Rime
License:        CC-BY-4.0
URL:            https://github.com/amzxyz/RIME-LMDG
Source0:        wanxiang-lts-zh-hans.gram
Source1:        RIME-LMDG-LICENSE

BuildArch:      noarch
Requires:       librime-octagram

%description
The Wanxiang LTS Simplified Chinese octagram language model
(wanxiang-lts-zh-hans.gram), published by the amzxyz/RIME-LMDG project. It is
loaded from the rime-data root by `grammar: language:` in the Wanxiang schemas.
Install alongside rime-wanxiang-ibus-base.

%prep
# Upstream ships a pre-built language model; nothing to prepare.

%build
# Upstream ships a pre-built language model; nothing to build.

%install
rm -rf %{buildroot}
install -d %{buildroot}%{rime_data}
install -pm644 %{SOURCE0} %{buildroot}%{rime_data}/wanxiang-lts-zh-hans.gram
install -d %{buildroot}%{_licensedir}/%{name}
install -pm644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/LICENSE

%files
%license %{_licensedir}/%{name}/LICENSE
%{rime_data}/wanxiang-lts-zh-hans.gram

%changelog
* Sun Nov 22 2026 v8wzge <v8wzge@users.noreply.github.com> - 18.2.0-1
- Automated build from the upstream LTS grammar model release
