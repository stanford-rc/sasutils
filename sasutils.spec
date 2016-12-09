%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:          sasutils
Version:       0.2.5
Release:       1%{?dist}
Summary:       Serial Attached SCSI (SAS) Linux utilities

Group:         System Environment/Base
License:       ASL 2.0
URL:           https://github.com/stanford-rc/sasutils
Source0:       https://files.pythonhosted.org/packages/source/s/%{name}/%{name}-%{version}.tar.gz

BuildRoot:     %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch:     noarch
BuildRequires: python-devel python-setuptools
Requires:      python-setuptools sg3_utils smp_utils

%description
sasutils is a set of command-line tools and a Python library to ease the
administration of Serial Attached SCSI (SAS) fabrics.

%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%doc README.rst
%{python_sitelib}/sasutils/
%{python_sitelib}/sasutils-*-py?.?.egg-info
%{_bindir}/sas_devices
%{_bindir}/sas_discover
%{_bindir}/sas_mpath_snic_alias
%{_bindir}/sas_sd_snic_alias
%{_bindir}/ses_report

%changelog
* Fri Dec  9 2016 Stephane Thiell <sthiell@stanford.edu> 0.2.5-1
- update version

* Mon Dec  5 2016 Stephane Thiell <sthiell@stanford.edu> 0.2.4-1
- update version

* Tue Nov  8 2016 Stephane Thiell <sthiell@stanford.edu> 0.2.3-1
- update version

* Mon Oct 31 2016 Stephane Thiell <sthiell@stanford.edu> 0.2.1-1
- update version

* Mon Oct 17 2016 Stephane Thiell <sthiell@stanford.edu> 0.1.7-1
- inception
