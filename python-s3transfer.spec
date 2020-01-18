%if 0%{?rhel} && 0%{?rhel} <= 7
%bcond_with python3
# Minimum nose version is 1.3.3, while EL7 has 1.3.0
%bcond_with tests
%else
%bcond_without python3
%bcond_without tests
%endif

%global pypi_name s3transfer

%global bundled_lib_dir    bundled
# python-futures
%global futures_version    3.0.3
%global futures_dir        %{bundled_lib_dir}/futures
# python-botocore
%global botocore_version   1.8.35
%global botocore_dir       %{bundled_lib_dir}/botocore
# python-jmespath
%global jmespath_version   0.9.0
%global jmespath_dir       %{bundled_lib_dir}/jmespath

Name:           python-%{pypi_name}
Version:        0.1.10
Release:        8%{?dist}
Summary:        An Amazon S3 Transfer Manager

License:        ASL 2.0
URL:            https://github.com/boto/s3transfer
Source0:        %{pypi_name}-%{version}.tar.gz
Source1:        https://pypi.python.org/packages/source/f/futures/futures-%{futures_version}.tar.gz
Source2:        https://pypi.io/packages/source/b/botocore/botocore-%{botocore_version}.tar.gz
Source3:        https://pypi.python.org/packages/source/j/jmespath/jmespath-%{jmespath_version}.tar.gz
Patch0:         bundled-futures-botocore-jmespath.patch
Patch1:         botocore-1.8.35-fix_dateutil_version.patch

BuildArch:      noarch

BuildRequires:  python-devel
BuildRequires:  python-setuptools
%if %{with tests}
BuildRequires:  python-nose
BuildRequires:  python-mock
BuildRequires:  python-wheel
BuildRequires:  python-botocore
BuildRequires:  python-coverage
BuildRequires:  python-unittest2
%endif # tests
# python-futures bundle
#Requires:       python-futures
# python-botocore bundle
#Requires:       python-botocore

# python-futures bundle
Provides:       bundled(python-futures) = %{futures_version}
# python-botocore bundle
Provides:       bundled(python-botocore) = %{botocore_version}
# python-jmespath bundle
#Requires:       python-jmespath >= 0.7.1
Provides:       bundled(python-jmespath) = %{jmespath_version}
Requires:       python-dateutil >= 1.4
Requires:       python-docutils >= 0.10

%description
S3transfer is a Python library for managing Amazon S3 transfers.

%if %{with python3}
%package -n     python3-%{pypi_name}
Summary:        An Amazon S3 Transfer Manager
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
%if %{with tests}
BuildRequires:  python3-nose
BuildRequires:  python3-mock
BuildRequires:  python3-wheel
BuildRequires:  python3-botocore
BuildRequires:  python3-coverage
BuildRequires:  python3-unittest2
%endif # tests
Requires:       python3-botocore
%{?python_provide:%python_provide python3-%{pypi_name}}

%description -n python3-%{pypi_name}
S3transfer is a Python library for managing Amazon S3 transfers.
%endif # python3

%prep
%setup -q -n %{pypi_name}-%{version}
# Remove online tests (see https://github.com/boto/s3transfer/issues/8)
rm -rf tests/integration

# bundles
mkdir -p %{bundled_lib_dir}

# python-futures bundle
tar -xzf %SOURCE1 -C %{bundled_lib_dir}
mv %{bundled_lib_dir}/futures-%{futures_version} %{futures_dir}
cp %{futures_dir}/LICENSE futures_LICENSE

# python-botocore bundle
tar -xzf %SOURCE2 -C %{bundled_lib_dir}
mv %{bundled_lib_dir}/botocore-%{botocore_version} %{botocore_dir}
cp %{botocore_dir}/LICENSE.txt botocore_LICENSE.txt
cp %{botocore_dir}/README.rst botocore_README.rst

# python-jmespath bundle
tar -xzf %SOURCE3 -C %{bundled_lib_dir}
mv %{bundled_lib_dir}/jmespath-%{jmespath_version} %{jmespath_dir}
cp %{botocore_dir}/LICENSE.txt jmespath_LICENSE.txt
cp %{botocore_dir}/README.rst jmespath_README.rst

# append bundled-directory to search path
%patch0 -p1

pushd %{botocore_dir}
%patch1 -p1
sed -i -e '1 d' botocore/vendored/requests/packages/chardet/chardetect.py
sed -i -e '1 d' botocore/vendored/requests/certs.py
rm -rf botocore.egg-info
# Remove online tests
rm -rf tests/integration
popd

pushd %{jmespath_dir}
rm -rf jmespath.egg-info
popd

%build
%py2_build
%if %{with python3}
%py3_build
%endif # python3

# python-futures bundle
pushd %{futures_dir}
%{__python2} setup.py build
popd

# python-botocore bundle
pushd %{botocore_dir}
%{__python2} setup.py build
popd

# python-jmespath bundle
pushd %{jmespath_dir}
CFLAGS="%{optflags}" %{__python} setup.py %{?py_setup_args} build --executable="%{__python2} -s"
popd

%install
%py2_install
%if %{with python3}
%py3_install
%endif # python3

# python-futures bundle
pushd %{futures_dir}
%{__python2} setup.py install -O1 --skip-build --root %{buildroot} --install-lib %{_libdir}/fence-agents/bundled
popd

# python-botocore bundle
pushd %{botocore_dir}
%{__python2} setup.py install -O1 --skip-build --root %{buildroot} --install-lib %{_libdir}/fence-agents/bundled
popd

# python-jmespath bundle
pushd %{jmespath_dir}
CFLAGS="%{optflags}" %{__python} setup.py %{?py_setup_args} install -O1 --skip-build --root %{buildroot} --install-lib %{_libdir}/fence-agents/bundled
mv %{buildroot}/%{_bindir}/jp.py %{buildroot}/%{_bindir}/jp.py-%{python2_version}
ln -sf %{_bindir}/jp.py-%{python2_version} %{buildroot}/%{_bindir}/jp.py-2
ln -sf %{_bindir}/jp.py-%{python2_version} %{buildroot}/%{_bindir}/jp.py
popd

%if %{with tests}
%check
nosetests-%{python2_version} --with-coverage --cover-erase --cover-package s3transfer --with-xunit --cover-xml -v tests/unit/ tests/functional/
%if %{with python3}
nosetests-%{python3_version} --with-coverage --cover-erase --cover-package s3transfer --with-xunit --cover-xml -v tests/unit/ tests/functional/
%endif # python3
%endif # tests

%files -n python-%{pypi_name} 
%{!?_licensedir:%global license %doc}
%doc README.rst botocore_README.rst jmespath_README.rst
%license LICENSE.txt futures_LICENSE botocore_LICENSE.txt jmespath_LICENSE.txt
%{python_sitelib}/%{pypi_name}
%{python_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info
# python-futures and python-botocore bundles
%{_libdir}/fence-agents/bundled
%exclude %{_bindir}/jp.py*

%if %{with python3}
%files -n python3-%{pypi_name} 
%doc README.rst
%license LICENSE.txt
%{python3_sitelib}/%{pypi_name}
%{python3_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info
%endif # python3

%changelog
* Mon Feb 12 2018 Oyvind Albrigtsen <oalbrigt@redhat.com> - 0.1.10-8
- Bundle python-futures, python-botocore and python-jmespath

  Resolves: rhbz#1509441

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.10-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.10-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Wed Dec 28 2016 Fabio Alessandro Locati <fale@fedoraproject.org> - 0.1.10-1
- Update to 0.1.10

* Mon Dec 19 2016 Miro Hrončok <mhroncok@redhat.com> - 0.1.9-2
- Rebuild for Python 3.6

* Thu Oct 27 2016 Fabio Alessandro Locati <fale@fedoraproject.org> - 0.1.9-1
- Update to 0.1.9

* Mon Oct 10 2016 Fabio Alessandro Locati <fale@fedoraproject.org> - 0.1.7-1
- Uodate to 0.1.7

* Sun Oct 02 2016 Fabio Alessandro Locati <fale@fedoraproject.org> - 0.1.5-1
- Update to 0.1.5

* Wed Sep 28 2016 Fabio Alessandro Locati <fale@fedoraproject.org> - 0.1.4-1
- Update to 0.1.4

* Wed Sep 07 2016 Fabio Alessandro Locati <fale@fedoraproject.org> - 0.1.3-1
- Update to 0.1.3

* Thu Aug 04 2016 Fabio Alessandro Locati <fale@fedoraproject.org> - 0.1.1-1
- Update to 0.1.1

* Tue Aug 02 2016 Fabio Alessandro Locati <fale@fedoraproject.org> - 0.1.0-1
- Update to 0.1.0

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.0.1-4
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Wed Feb 24 2016 Fabio Alessandro Locati <fale@fedoraproject.org> - 0.0.1-3
- Cleanup the spec a little bit
- Remove patch

* Tue Feb 23 2016 Fabio Alessandro Locati <fale@fedoraproject.org> - 0.0.1-2
- Add patch to remove tests needing web connection

* Tue Feb 23 2016 Fabio Alessandro Locati <fale@fedoraproject.org> - 0.0.1-1
- Initial package.
