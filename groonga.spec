%global php_extdir  %(php-config --extension-dir 2>/dev/null || echo "undefined")

Name:		groonga
Version:	1.0.4
Release:	1%{?dist}
Summary:	An Embeddable Fulltext Search Engine

Group:		Applications/Text
License:	LGPLv2
URL:		http://groonga.org/
Source0:	http://groonga.org/files/groonga/groonga-%{version}.tar.gz

BuildRequires:	mecab-devel
BuildRequires:	python2-devel
BuildRequires:	php-devel
Requires:	%{name}-libs = %{version}-%{release}
Requires(pre):	shadow-utils
Requires(post):	/sbin/chkconfig
Requires(preun):	/sbin/chkconfig
Requires(preun):	/sbin/service
Requires(postun):	/sbin/service

%description
Groonga is an embeddable full-text search engine library.  It can
integrate with DBMS and scripting languages to enhance their search
functionality.  It also provides a standalone data store server based
on relational data model.

%package libs
Summary:	Runtime libraries for groonga
Group:		System Environment/Libraries
License:	LGPLv2 and (MIT or GPLv2)
Requires(post):	/sbin/ldconfig
Requires(postun):	/sbin/ldconfig

%description libs
This package contains the libraries for groonga

%package doc
Summary:	Documentation for groonga
Group:		Documentation
License:	LGPLv2 and BSD
Requires:	%{name}-libs = %{version}-%{release}

%description doc
Documentation for groonga

%package devel
Summary:	Libraries and header files for groonga
Group:		Development/Libraries
Requires:	%{name}-libs = %{version}-%{release}

%description devel
Libraries and header files for groonga

%package tokenizer-mecab
Summary:	MeCab tokenizer for groonga
Group:		Applications/Text
Requires:	%{name}-libs = %{version}-%{release}
Requires:	mecab

%description tokenizer-mecab
MeCab tokenizer for groonga

%package munin-plugins
Summary:	Munin plugins for groonga
Group:		Applications/System
Requires:	%{name}-libs = %{version}-%{release}
Requires:	munin-node
Requires(post):	munin-node
Requires(post):	/sbin/service
Requires(postun):	/sbin/service

%description munin-plugins
Munin plugins for groonga

%package python
Summary:	Python language binding for groonga
Group:		Development/Libraries
Requires:	%{name}-libs = %{version}-%{release}

%description python
Python language binding for groonga

%package php
Summary:	PHP language binding for groonga
Group:		Development/Libraries
Requires:	%{name}-libs = %{version}-%{release}

%description php
PHP language binding for groonga


%prep
#% define optflags -O0
%setup -q


%build
%configure --disable-static
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool
make %{?_smp_mflags}

# build python binding
cd %{_builddir}/%{name}-%{version}/bindings/python/ql
python setup.py config
sed -i.cflags -e 's|^cflags =.*|cflags = []|' setup.py
CFLAGS=-I%{_builddir}/%{name}-%{version}/include
export CFLAGS
LDFLAGS=-L%{_builddir}/%{name}-%{version}/lib/.libs
export LDFLAGS
python setup.py build

# build php binding
cd %{_builddir}/%{name}-%{version}/bindings/php
sed -i.ldflags -e 's|PHP_ADD_LIBRARY_WITH_PATH(groonga, .*)|PHP_ADD_LIBRARY(groonga, GROONGA_SHARED_LIBADD)|' config.m4
phpize
CFLAGS="%{optflags}"
export CFLAGS
LDFLAGS=-L%{_builddir}/%{name}-%{version}/lib/.libs
export LDFLAGS
# --with-groonga is only necessary to avoid error in configure
%configure --disable-static --with-groonga=%{_builddir}/%{name}-%{version}
make %{?_smp_mflags}


%install
make install DESTDIR=$RPM_BUILD_ROOT INSTALL="install -p"
rm $RPM_BUILD_ROOT%{_libdir}/groonga/plugins/*/*.la
rm $RPM_BUILD_ROOT%{_libdir}/*.la

mkdir -p $RPM_BUILD_ROOT%{_initddir}
mv $RPM_BUILD_ROOT%{_sysconfdir}/groonga/init.d/redhat/groonga \
	$RPM_BUILD_ROOT%{_initddir}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}
mv $RPM_BUILD_ROOT%{_sysconfdir}/groonga/init.d/redhat/sysconfig \
	$RPM_BUILD_ROOT%{_sysconfdir}/

rm -rf $RPM_BUILD_ROOT%{_sysconfdir}/groonga/init.d/

mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/run/groonga
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/groonga/db
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/log/groonga

rm $RPM_BUILD_ROOT%{_datadir}/groonga/doc/ja/html/.buildinfo

mv $RPM_BUILD_ROOT%{_datadir}/groonga/munin/ $RPM_BUILD_ROOT%{_datadir}/
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/munin/plugin-conf.d/
cat <<EOC > $RPM_BUILD_ROOT%{_sysconfdir}/munin/plugin-conf.d/groonga
[groonga_*]
  user groonga
  group groonga
  env.PATH %{_bindir}
  env.pid_file %{_localstatedir}/run/groonga/groonga.pid
  env.path %{_localstatedir}/lib/groonga/db/db
  env.host 127.0.0.1
  env.port 10041
  env.log_path %{_localstatedir}/log/groonga/query.log
EOC

# install python binding
cd %{_builddir}/%{name}-%{version}/bindings/python/ql
python setup.py install --root=$RPM_BUILD_ROOT

# install php binding
cd %{_builddir}/%{name}-%{version}/bindings/php
make install INSTALL_ROOT=$RPM_BUILD_ROOT INSTALL="install -p"


%pre
getent group groonga >/dev/null || groupadd -r groonga
getent passwd groonga >/dev/null || \
       useradd -r -g groonga -d %{_localstatedir}/lib/groonga -s /sbin/nologin \
	-c 'groonga' groonga
exit 0

%post
/sbin/chkconfig --add groonga

%post libs -p /sbin/ldconfig

%post munin-plugins
%{_sbindir}/munin-node-configure --shell --remove-also | grep -e 'groonga_' | sh
[ -f %{_localstatedir}/lock/subsys/munin-node ] && \
	/sbin/service munin-node restart > /dev/null 2>&1
:

%preun
if [ $1 = 0 ] ; then
	/sbin/service groonga stop >/dev/null 2>&1 || :
	/sbin/chkconfig --del groonga
fi

%postun
if [ $1 -ge 1 ] ; then
	/sbin/service groonga condrestart >/dev/null 2>&1 || :
fi

%postun libs -p /sbin/ldconfig

%postun munin-plugins
if [ $1 -eq 0 ]; then
	[ -f %{_localstatedir}/lock/subsys/munin-node ] && \
		/sbin/service munin-node restart >/dev/null 2>&1
	:
fi


%files
%defattr(-,root,root,-)
%{_datadir}/man/man1/*
%config(noreplace) %{_sysconfdir}/groonga/
%config(noreplace) %{_sysconfdir}/sysconfig/groonga
%{_bindir}/*
%{_initddir}/*
%ghost %dir %{_localstatedir}/run/%{name}
%attr(0755,groonga,groonga) %dir %{_localstatedir}/lib/%{name}
%attr(0755,groonga,groonga) %dir %{_localstatedir}/lib/%{name}/db

%files libs
%defattr(-,root,root,-)
%doc README AUTHORS COPYING
%{_libdir}/*.so.*
%dir %{_libdir}/groonga
%dir %{_libdir}/groonga/plugins
%dir %{_libdir}/groonga/plugins/suggest
%{_libdir}/groonga/plugins/suggest/*.so
%dir %{_libdir}/groonga/plugins/tokenizers
%dir %{_datadir}/groonga
%{_datadir}/groonga/

%files doc
%defattr(-,root,root,-)
%doc %{_datadir}/groonga/doc/

%files devel
%defattr(-,root,root,-)
%{_includedir}/groonga/
%{_libdir}/*.so
%{_libdir}/pkgconfig/groonga*.pc

%files tokenizer-mecab
%defattr(-,root,root,-)
%{_libdir}/groonga/plugins/tokenizers/mecab.so

%files munin-plugins
%defattr(-,root,root,-)
%{_datadir}/munin/plugins/*
%config(noreplace) %{_sysconfdir}/munin/plugin-conf.d/*

%files python
%defattr(-,root,root,-)
%{python_sitearch}/groongaql*

%files php
%defattr(-,root,root,-)
%{php_extdir}/groonga.so

%changelog
* Mon Nov 29 2010 Kouhei Sutou <kou@clear-code.com> - 1.0.4-1
- new upstream release

* Wed Nov 24 2010 Daiki Ueno <dueno@redhat.com> - 1.0.3-2
- %%ghost /var/run/*.

* Fri Oct 09 2010 Kouhei Sutou <kou@clear-code.com> - 1.0.3-1
- new upstream release.

* Thu Oct  7 2010 Daiki Ueno <dueno@redhat.com> - 1.0.2-7
- own %%_localstatedir/lib/%%name/db.
- use %%_sbindir RPM macro.

* Wed Oct  6 2010 Daiki Ueno <dueno@redhat.com> - 1.0.2-6
- use %%python_sitearch and %%php_extdir macros.
- correct directory ownership for -munin-plugins subpackage.
- supply %%optflags when building PHP binding.
- don't set CGROUP_DAEMON in initscript.

* Tue Oct  5 2010 Daiki Ueno <dueno@redhat.com> - 1.0.2-5
- correct directory ownership for -munin-plugins subpackage.
- make -doc subpackage require -libs.
- correct directory ownership for directories under %%_localstatedir.
- make initscript disabled by default
- move "build process" of Python and PHP bindings to %%build from %%install
- build against Python 2.7
- fix naming of Python and PHP bindings (python-%%{name} to %%{name}-python)

* Mon Oct  4 2010 Daiki Ueno <dueno@redhat.com> - 1.0.2-4
- package Python and PHP bindings.

* Mon Oct  4 2010 Daiki Ueno <dueno@redhat.com> - 1.0.2-3
- fix License.
- pass "-p" to the install command to preserve timestamps.
- use RPM macros %%_initddir, %%_localstatedir, %%_prefix, etc.
- use the standard snippet to creating user/group for groonga; don't
  call userdel/groupdel.
- add missing "Require(foo): bar" for /sbin/service, /sbin/chkconfig,
  /sbin/ldconfig, and /usr/sbin/munin-node-configure.
- fix attributes in %%files.
- correct directory ownership.

* Fri Oct  1 2010 Daiki Ueno <dueno@redhat.com> - 1.0.2-2
- don't require autotools when building
- pass --disable-static to %%configure

* Thu Sep 09 2010 Kouhei Sutou <kou@clear-code.com> - 1.0.2-1
- new upstream release.

* Thu Sep 06 2010 Kouhei Sutou <kou@clear-code.com> - 1.0.1-1
- new upstream release.

* Thu Sep 02 2010 Kouhei Sutou <kou@clear-code.com> - 1.0.0-1
- split packages.

* Tue Aug 24 2010 Daiki Ueno <dueno@redhat.com> - 0.7.6-1
- initial packaging for Fedora
