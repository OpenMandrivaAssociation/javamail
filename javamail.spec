%{?_javapackages_macros:%_javapackages_macros}
Name:           javamail
Version:        1.5.0
Release:        6.1%{?dist}
Summary:        Java Mail API
License:        CDDL or GPLv2 with exceptions
URL:            http://www.oracle.com/technetwork/java/javamail
BuildArch:      noarch

# hg clone http://kenai.com/hg/javamail~mercurial
# (cd ./javamail~mercurial && hg archive -r JAVAMAIL-%(sed s/\\./_/g <<<"%{version}") ../%{name}-%{version})
# tar caf %{name}-%{version}.tar.xz %{name}-%{version}
Source:         %{name}-%{version}.tar.xz

BuildRequires:  maven-local
BuildRequires:  jvnet-parent
BuildRequires:  maven-assembly-plugin
BuildRequires:  maven-dependency-plugin
BuildRequires:  maven-resources-plugin
BuildRequires:  maven-plugin-bundle
BuildRequires:  maven-plugin-build-helper

# Adapted from the classpathx-mail (and JPackage glassfish-javamail) Provides.
Provides:       javamail-monolithic = %{version}-%{release}

Provides:       javax.mail

%description
The JavaMail API provides a platform-independent and protocol-independent
framework to build mail and messaging applications.


%package javadoc
Summary:        Javadoc for %{name}

%description javadoc
%{summary}.


%prep
%setup -q

add_dep() {
    %pom_xpath_inject pom:project "<dependencies/>" ${2}
    %pom_add_dep com.sun.mail:${1}:%{version}:provided ${2}
}

add_dep smtp mailapi
add_dep javax.mail smtp
add_dep javax.mail pop3
add_dep javax.mail imap
add_dep javax.mail mailapijar

# Remove profiles containing demos and other stuff that is not
# supposed to be deployable.
%pom_xpath_remove /pom:project/pom:profiles

# osgiversion-maven-plugin is used to set ${mail.osgiversion} property
# based on ${project.version}. We don't have osgiversion plugin in
# Fedora so we'll set ${mail.osgiversion} explicitly.
%pom_remove_plugin org.glassfish.hk2:osgiversion-maven-plugin
%pom_xpath_inject /pom:project/pom:properties "<mail.osgiversion>%{version}</mail.osgiversion>"

# Alternative names for super JAR containing API and implementation.
%mvn_alias com.sun.mail:mailapi javax.mail:mailapi
%mvn_alias com.sun.mail:javax.mail javax.mail:mail \
           org.eclipse.jetty.orbit:javax.mail.glassfish
%mvn_file "com.sun.mail:{javax.mail}" %{name}/@1 %{name}/mail

%build
%mvn_build -- -Dmaven.test.skip=true

%install
%mvn_install

install -d -m 755 %{buildroot}%{_javadir}/javax.mail/
ln -sf ../%{name}/javax.mail.jar %{buildroot}%{_javadir}/javax.mail/

%files -f .mfiles
%doc mail/src/main/java/overview.html
%doc mail/src/main/resources/META-INF/LICENSE.txt
%{_javadir}/javax.mail/

%files javadoc -f .mfiles-javadoc
%doc mail/src/main/resources/META-INF/LICENSE.txt

%changelog
* Mon Aug 12 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 1.5.0-6
- Add forgotten provides

* Mon Aug 12 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 1.5.0-5
- Add javax.mail provides and directory

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.5.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Fri Jun 28 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.5.0-3
- Add compat symlink for javax.mail:mail

* Mon Jun 24 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.5.0-2
- Add Maven alias for javax.mail:mail

* Mon Jun 24 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.5.0-1
- Update to upstream version 1.5.0

* Thu Mar  7 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.4.6-1
- Update to upstream version 1.4.6

* Mon Mar  4 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.4.3-16
- Add depmap for org.eclipse.jetty.orbit
- Resolves: rhbz#917624

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.3-15
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Feb 06 2013 Java SIG <java-devel@lists.fedoraproject.org> - 1.4.3-14
- Update for https://fedoraproject.org/wiki/Fedora_19_Maven_Rebuild
- Replace maven BuildRequires with maven-local

* Thu Oct 11 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.4.3-13
- Fix URL

* Thu Jul 19 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.3-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Jun 11 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.4.3-11
- Update OSGi manifest patch

* Tue May 29 2012 Gerard Ryan <galileo@fedoraproject.org> - 1.4.3-10
- Add extra information to OSGi manifest
- Fix rpmlint error about mavendepmapfragdir

* Wed Mar 21 2012 Alexander Kurtakov <akurtako@redhat.com> 1.4.3-9
- Drop tomcat6-jsp-api requires - it's dependency management not dependency, hence not needed.

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.3-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Nov 29 2011 Alexander Kurtakov <akurtako@redhat.com> 1.4.3-7
- Build with maven3.
- Adapt to current guidelines.

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.3-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Wed Dec  8 2010 Stanislav Ochotnicky <sochotnicky@redhat.com> - 1.4.3-5
- Fix pom filenames (#655806)
- Versionless jars/javadocs (new guidelines)
- Migrate to tomcat6 (#652004)
- Other cleanups

* Wed Sep 8 2010 Alexander Kurtakov <akurtako@redhat.com> 1.4.3-4
- Add surefire provider BR.

* Wed Sep 8 2010 Alexander Kurtakov <akurtako@redhat.com> 1.4.3-3
- Drop gcj_support.
- Use javadoc:aggregate.

* Fri Jan  8 2010 Mary Ellen Foster <mefoster at gmail.com> 1.4.3-2
- Remove unnecessary (build)requirement tomcat5-servlet-2.4-api
- Move jar files into subdirectory

* Wed Dec  2 2009 Mary Ellen Foster <mefoster at gmail.com> 1.4.3-1
- Initial package
