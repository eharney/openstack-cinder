%global with_doc %{!?_without_doc:1}%{?_without_doc:0}

Name:             openstack-cinder
Version:          2013.2
Release:          0.2.b1%{?dist}
Summary:          OpenStack Volume service

Group:            Applications/System
License:          ASL 2.0
URL:              http://www.openstack.org/software/openstack-storage/
Source0:          https://launchpad.net/cinder/havana/havana-1/+download/cinder-%{version}.b1.tar.gz
Source1:          cinder.conf
Source2:          cinder.logrotate
Source3:          cinder-tgt.conf

Source10:         openstack-cinder-api.init
Source100:        openstack-cinder-api.upstart
Source11:         openstack-cinder-scheduler.init
Source110:        openstack-cinder-scheduler.upstart
Source12:         openstack-cinder-volume.init
Source120:        openstack-cinder-volume.upstart

Source20:         cinder-sudoers

#
# patches_base=2013.2.b1
#
Patch0001: 0001-Ensure-we-don-t-access-the-net-when-building-docs.patch
Patch0002: 0002-Use-updated-parallel-install-versions-of-epel-packag.patch
Patch0003: 0003-Remove-runtime-dep-on-python-pbr-python-d2to1.patch
Patch0004: 0004-Adjust-pip-requires-for-EL6.patch

BuildArch:        noarch
BuildRequires:    intltool
BuildRequires:    python-d2to1
BuildRequires:    python-pbr
BuildRequires:    python-sphinx10
BuildRequires:    python-setuptools
BuildRequires:    python-netaddr
BuildRequires:    openstack-utils
BuildRequires:    python-paste-deploy1.5
BuildRequires:    python-routes1.12
BuildRequires:    python-sqlalchemy0.7
BuildRequires:    python-webob1.2

Requires:         openstack-utils
Requires:         python-cinder = %{version}-%{release}

# as convenience
Requires:         python-cinderclient

Requires(post):   chkconfig
Requires(postun): initscripts
Requires(preun):  chkconfig
Requires(pre):    shadow-utils

Requires:         lvm2
Requires:         scsi-target-utils

%description
OpenStack Volume (codename Cinder) provides services to manage and
access block storage volumes for use by Virtual Machine instances.


%package -n       python-cinder
Summary:          OpenStack Volume Python libraries
Group:            Applications/System

Requires:         sudo

Requires:         MySQL-python

Requires:         python-paramiko

Requires:         python-qpid
Requires:         python-kombu
Requires:         python-amqplib

Requires:         python-eventlet
Requires:         python-greenlet
Requires:         python-iso8601
Requires:         python-netaddr
Requires:         python-lxml
Requires:         python-anyjson
Requires:         python-cheetah
Requires:         python-stevedore
Requires:         python-suds

Requires:         python-sqlalchemy0.7
Requires:         python-migrate

Requires:         python-paste-deploy1.5
Requires:         python-routes1.12
Requires:         python-webob1.2

Requires:         python-glanceclient >= 1:0
Requires:         python-swiftclient >= 1.2

Requires:         python-oslo-config
Requires:         python-six

Requires:         python-babel
Requires:         python-lockfile

%description -n   python-cinder
OpenStack Volume (codename Cinder) provides services to manage and
access block storage volumes for use by Virtual Machine instances.

This package contains the cinder Python library.

%if 0%{?with_doc}
%package doc
Summary:          Documentation for OpenStack Volume
Group:            Documentation

Requires:         %{name} = %{version}-%{release}

BuildRequires:    graphviz

# Required to build module documents
BuildRequires:    python-eventlet
BuildRequires:    python-routes1.12
BuildRequires:    python-sqlalchemy0.7
BuildRequires:    python-webob1.2
# while not strictly required, quiets the build down when building docs.
BuildRequires:    python-migrate, python-iso8601

%description      doc
OpenStack Volume (codename Cinder) provides services to manage and
access block storage volumes for use by Virtual Machine instances.

This package contains documentation files for cinder.
%endif

%prep
%setup -q -n cinder-%{version}.b1

%patch0001 -p1
%patch0002 -p1
%patch0003 -p1
%patch0004 -p1

find . \( -name .gitignore -o -name .placeholder \) -delete

find cinder -name \*.py -exec sed -i '/\/usr\/bin\/env python/{d;q}' {} +

# TODO: Have the following handle multi line entries
sed -i '/setup_requires/d; /install_requires/d; /dependency_links/d' setup.py

# Remove the requirements file so that pbr hooks don't add it
# to distutils requires_dist config
rm -rf {test-,}requirements.txt tools/{pip,test}-requires

# We add REDHATCINDERVERSION/RELEASE with the pbr removal patch
sed -i s/REDHATCINDERVERSION/%{version}/ cinder/version.py
sed -i s/REDHATCINDERRELEASE/%{release}/ cinder/version.py

%build

# Move authtoken configuration out of paste.ini
openstack-config --del etc/cinder/api-paste.ini filter:authtoken admin_tenant_name
openstack-config --del etc/cinder/api-paste.ini filter:authtoken admin_user
openstack-config --del etc/cinder/api-paste.ini filter:authtoken admin_password
openstack-config --del etc/cinder/api-paste.ini filter:authtoken auth_host
openstack-config --del etc/cinder/api-paste.ini filter:authtoken auth_port
openstack-config --del etc/cinder/api-paste.ini filter:authtoken auth_protocol

%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

# docs generation requires everything to be installed first
export PYTHONPATH="$( pwd ):$PYTHONPATH"

pushd doc

%if 0%{?with_doc}
SPHINX_DEBUG=1 sphinx-1.0-build -b html source build/html
# Fix hidden-file-or-dir warnings
rm -fr build/html/.doctrees build/html/.buildinfo
%endif

# Create dir link to avoid a sphinx-build exception
mkdir -p build/man/.doctrees/
ln -s .  build/man/.doctrees/man
SPHINX_DEBUG=1 sphinx-1.0-build -b man -c source source/man build/man
mkdir -p %{buildroot}%{_mandir}/man1
install -p -D -m 644 build/man/*.1 %{buildroot}%{_mandir}/man1/

popd

# Setup directories
install -d -m 755 %{buildroot}%{_sharedstatedir}/cinder
install -d -m 755 %{buildroot}%{_sharedstatedir}/cinder/tmp
install -d -m 755 %{buildroot}%{_localstatedir}/log/cinder

# Install config files
install -d -m 755 %{buildroot}%{_sysconfdir}/cinder
install -p -D -m 640 %{SOURCE1} %{buildroot}%{_sysconfdir}/cinder/cinder.conf
install -d -m 755 %{buildroot}%{_sysconfdir}/cinder/volumes
install -p -D -m 644 %{SOURCE3} %{buildroot}%{_sysconfdir}/tgt/conf.d/cinder.conf
install -p -D -m 640 etc/cinder/rootwrap.conf %{buildroot}%{_sysconfdir}/cinder/rootwrap.conf
install -p -D -m 640 etc/cinder/api-paste.ini %{buildroot}%{_sysconfdir}/cinder/api-paste.ini
install -p -D -m 640 etc/cinder/policy.json %{buildroot}%{_sysconfdir}/cinder/policy.json

# Install initscripts for services
install -p -D -m 755 %{SOURCE10} %{buildroot}%{_initrddir}/openstack-cinder-api
install -p -D -m 755 %{SOURCE11} %{buildroot}%{_initrddir}/openstack-cinder-scheduler
install -p -D -m 755 %{SOURCE12} %{buildroot}%{_initrddir}/openstack-cinder-volume

# Install sudoers
install -p -D -m 440 %{SOURCE20} %{buildroot}%{_sysconfdir}/sudoers.d/cinder

# Install logrotate
install -p -D -m 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/openstack-cinder

# Install pid directory
install -d -m 755 %{buildroot}%{_localstatedir}/run/cinder

# Install upstart jobs examples
install -d -m 755 %{buildroot}%{_datadir}/cinder
install -p -m 644 %{SOURCE100} %{buildroot}%{_datadir}/cinder/
install -p -m 644 %{SOURCE110} %{buildroot}%{_datadir}/cinder/
install -p -m 644 %{SOURCE120} %{buildroot}%{_datadir}/cinder/

# Install rootwrap files in /usr/share/cinder/rootwrap
mkdir -p %{buildroot}%{_datarootdir}/cinder/rootwrap/
install -p -D -m 644 etc/cinder/rootwrap.d/* %{buildroot}%{_datarootdir}/cinder/rootwrap/

# Remove unneeded in production stuff
rm -f %{buildroot}%{_bindir}/cinder-debug
rm -fr %{buildroot}%{python_sitelib}/cinder/tests/
rm -fr %{buildroot}%{python_sitelib}/run_tests.*
rm -f %{buildroot}/usr/share/doc/cinder/README*

%pre
getent group cinder >/dev/null || groupadd -r cinder --gid 165
if ! getent passwd cinder >/dev/null; then
  useradd -u 165 -r -g cinder -G cinder,nobody -d %{_sharedstatedir}/cinder -s /sbin/nologin -c "OpenStack Cinder Daemons" cinder
fi
exit 0

%post
if [ $1 -eq 1 ] ; then
    # Initial installation
    for svc in volume api scheduler; do
        /sbin/chkconfig --add openstack-cinder-$svc
    done
fi

%preun
if [ $1 -eq 0 ] ; then
    for svc in volume api scheduler; do
        /sbin/service openstack-cinder-${svc} stop > /dev/null 2>&1
        /sbin/chkconfig --del openstack-cinder-${svc}
    done
fi

%postun
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    for svc in volume api scheduler; do
        /sbin/service openstack-cinder-${svc} condrestart > /dev/null 2>&1 || :
    done
fi

%files
%doc LICENSE

%dir %{_sysconfdir}/cinder
%config(noreplace) %attr(-, root, cinder) %{_sysconfdir}/cinder/cinder.conf
%config(noreplace) %attr(-, root, cinder) %{_sysconfdir}/cinder/api-paste.ini
%config(noreplace) %attr(-, root, cinder) %{_sysconfdir}/cinder/rootwrap.conf
%config(noreplace) %attr(-, root, cinder) %{_sysconfdir}/cinder/policy.json
%config(noreplace) %{_sysconfdir}/logrotate.d/openstack-cinder
%config(noreplace) %{_sysconfdir}/sudoers.d/cinder
%config(noreplace) %{_sysconfdir}/tgt/conf.d/cinder.conf

%dir %attr(0755, cinder, root) %{_localstatedir}/log/cinder
%dir %attr(0755, cinder, root) %{_localstatedir}/run/cinder
%dir %attr(0755, cinder, root) %{_sysconfdir}/cinder/volumes

%{_bindir}/cinder-*
%{_initrddir}/openstack-cinder-*
%{_datarootdir}/cinder
%{_mandir}/man1/cinder*.1.gz

%defattr(-, cinder, cinder, -)
%dir %{_sharedstatedir}/cinder
%dir %{_sharedstatedir}/cinder/tmp

%files -n python-cinder
%doc LICENSE
%{python_sitelib}/cinder
%{python_sitelib}/cinder-%{version}*.egg-info

%if 0%{?with_doc}
%files doc
%doc doc/build/html
%endif

%changelog
* Thu Jun 13 2013 Eric Harney <eharney@redhat.com> - 2013.2-0.2.b1
- Update to Havana milestone 1

* Fri May 10 2013 Eric Harney <eharney@redhat.com> - 2013.1.1-1
- Update to Grizzly stable release 1

* Mon Apr 08 2013 Eric Harney <eharney@redhat.com> - 2013.1-2
- Backport fix for GlusterFS driver get_volume_stats
- Adjust to support sqlalchemy-0.8.0

* Thu Apr 04 2013 Eric Harney <eharney@redhat.com> - 2013.1-1
- Update to Grizzly final release

* Mon Mar 27 2013 Eric Harney <eharney@redhat.com> - 2013.1-0.5.rc3
- Update to Grizzly RC3 release

* Mon Mar 25 2013 Eric Harney <eharney@redhat.com> - 2013.1-0.5.rc2
- Update to Grizzly RC2 release

* Mon Mar 18 2013 Eric Harney <eharney@redhat.com> - 2013.1-0.5.rc1
- Update to Grizzly RC1 release

* Tue Mar 05 2013 Pádraig Brady <P@draigBrady.com> - 2013.1-0.4.g3
- Add dependency on python-stevedore

* Wed Feb 27 2013 Eric Harney <eharney@redhat.com> - 2013.1-0.2.g3
- Update to Grizzly milestone 3

* Thu Jan 10 2013 Eric Harney <eharney@redhat.com> - 2013.1-0.1.g2
- Update to Grizzly milestone 2

* Thu Dec 20 2012 Eric Harney <eharney@redhat.com> - 2013.1-0.1.g1
- Update to Grizzly milestone 1

* Mon Dec 03 2012 Eric Harney <eharney@redhat.com> - 2012.2.1-1
- Update to Folsom stable release 1

* Wed Nov 14 2012 Eric Harney <eharney@redhat.com> - 2012.2-4
- Remove unused dependency on python-daemon

* Wed Oct 31 2012 Pádraig Brady <P@draigBrady.com> - 2012.2-3
- Adjust to be compatible with python-migrate-0.6

* Wed Oct 24 2012 Pádraig Brady <P@draigBrady.com> - 2012.2-2
- Initial Folsom release
