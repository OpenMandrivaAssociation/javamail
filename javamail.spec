%define uversion %(echo %{version} |sed -e 's,\\.,_,g')

Name:		javamail
Version:	1.6.2
Release:	2
Summary:	Java Mail API
Group:		Development/Java
License:	CDDL-1.1 OR GPL-2.0-only WITH Classpath-exception-2.0
URL:		https://javaee.github.io/javamail/
BuildArch:	noarch

Source0:	https://github.com/javaee/javamail/archive/JAVAMAIL-%{uversion}.tar.gz

BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	mvn(javax.activation:activation)

Obsoletes:	javamail-javadoc < 1.6.2-2

%description
JavaMail 1.6.2, built from source. The java.mail jar is the API plus
com.sun.mail util, auth and handlers. imap, smtp, pop3, dsn and gimap
are separate modules, which is what module-info.java describes. The
main jar provides mvn(com.sun.mail:javax.mail), the legacy
mvn(javax.mail:mail) coordinate, and mvn(com.sun.mail:all).

%prep
%autosetup -n javamail-JAVAMAIL-%{uversion}
find . -name '*.jar' -delete
# dsn ships no module-info. javac only accepts this file name.
if [ -e dsn/src/main/java/module-info.java ]; then
	echo "dsn module-info arrived upstream; drop the generated one."
	exit 1
fi
cat > dsn/src/main/java/module-info.java <<'EOF'
module com.sun.mail.dsn {
	exports com.sun.mail.dsn;
	requires java.mail;
	requires java.logging;
	requires java.desktop;
}
EOF
python - <<'PY'
from pathlib import Path
source = Path("mail/src/main/resources/javax/mail/Version.java")
dest = Path("mail/src/main/java/javax/mail/Version.java")
text = source.read_text(encoding="utf-8").replace("${mail.version}", "%{version}")
if "${mail.version}" in text:
    raise SystemExit("Version.java was not filtered")
dest.write_text(text, encoding="utf-8")
PY

%build
# No -u: rpm's script trailer reads DONT_CLEANUP, which is unset.
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH

ROOT=$PWD
rm -rf "$ROOT/modpath" "$ROOT/out" "$ROOT/classes"
mkdir -p "$ROOT/modpath" "$ROOT/out" "$ROOT/classes"
# The installed jar's automatic name is javax.activation. module-info
# requires java.activation, which is the name of this symlink.
ln -s /usr/share/java/javax.activation.jar "$ROOT/modpath/java.activation.jar"

compile_module() {
	dest=$1
	module_info=$2
	shift 2
	rm -rf "$dest"
	mkdir -p "$dest"
	javac --release 11 -encoding UTF-8 -d "$dest" -p "$ROOT/modpath" \
		"$module_info" "$@"
}

cd "$ROOT/mail/src/main/java"
mapfile -t api_sources < <(find javax com/sun/mail/util com/sun/mail/auth com/sun/mail/handlers -name '*.java')
compile_module "$ROOT/classes/java.mail" \
	"$ROOT/mailapi/src/main/java/module-info.java" \
	"${api_sources[@]}"
cp -a "$ROOT/mail/src/main/resources/META-INF" "$ROOT/classes/java.mail/"
jar --create --file "$ROOT/out/java.mail.jar" -C "$ROOT/classes/java.mail" .
ln -s "$ROOT/out/java.mail.jar" "$ROOT/modpath/java.mail.jar"

for proto in imap smtp pop3; do
	if [ "$proto" = imap ]; then
		mapfile -t sources < <(find com/sun/mail/imap com/sun/mail/iap -name '*.java')
	else
		mapfile -t sources < <(find "com/sun/mail/$proto" -name '*.java')
	fi
	compile_module "$ROOT/classes/$proto" \
		"$ROOT/$proto/src/main/java/module-info.java" \
		"${sources[@]}"
	cp -a "$ROOT/$proto/src/main/resources/META-INF" "$ROOT/classes/$proto/"
	jar --create --file "$ROOT/out/$proto.jar" -C "$ROOT/classes/$proto" .
	ln -s "$ROOT/out/$proto.jar" "$ROOT/modpath/$proto.jar"
done

cd "$ROOT/dsn/src/main/java"
mapfile -t dsn_sources < <(find . -name '*.java' ! -name 'module-info.java')
compile_module "$ROOT/classes/dsn" \
	"$ROOT/dsn/src/main/java/module-info.java" \
	"${dsn_sources[@]}"
cp -a "$ROOT/dsn/src/main/resources/META-INF" "$ROOT/classes/dsn/"
jar --create --file "$ROOT/out/dsn.jar" -C "$ROOT/classes/dsn" .
ln -s "$ROOT/out/dsn.jar" "$ROOT/modpath/dsn.jar"

cd "$ROOT/gimap/src/main/java"
mapfile -t gimap_sources < <(find . -name '*.java' ! -name 'module-info.java')
compile_module "$ROOT/classes/gimap" \
	"$ROOT/gimap/src/main/java/module-info.java" \
	"${gimap_sources[@]}"
cp -a "$ROOT/gimap/src/main/resources/META-INF" "$ROOT/classes/gimap/"
jar --create --file "$ROOT/out/gimap.jar" -C "$ROOT/classes/gimap" .

dep() {
	echo "    <dependency>"
	echo "      <groupId>$1</groupId>"
	echo "      <artifactId>$2</artifactId>"
	echo "      <version>$3</version>"
	echo "    </dependency>"
}

write_pom() {
	stem=$1
	artifact=$2
	shift 2
	{
		echo '<?xml version="1.0" encoding="UTF-8"?>'
		echo '<project xmlns="http://maven.apache.org/POM/4.0.0">'
		echo '  <modelVersion>4.0.0</modelVersion>'
		echo '  <groupId>com.sun.mail</groupId>'
		echo "  <artifactId>${artifact}</artifactId>"
		echo '  <version>%{version}</version>'
		echo "  <name>${artifact}</name>"
		echo '  <description>JavaMail %{version}, built from source.</description>'
		echo '  <url>https://javaee.github.io/javamail/</url>'
		if [ "$#" -gt 0 ]; then
			echo '  <dependencies>'
			while [ "$#" -gt 0 ]; do
				dep "$1" "$2" "$3"
				shift 3
			done
			echo '  </dependencies>'
		fi
		echo '</project>'
	} > "$ROOT/out/${stem}.pom"
}

write_pom java.mail javax.mail \
	javax.activation activation 1.2.0
write_pom imap imap com.sun.mail javax.mail %{version}
write_pom smtp smtp com.sun.mail javax.mail %{version}
write_pom pop3 pop3 com.sun.mail javax.mail %{version}
write_pom dsn dsn com.sun.mail javax.mail %{version}
write_pom gimap gimap \
	com.sun.mail javax.mail %{version} \
	com.sun.mail imap %{version}

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH
javap -verbose -p -classpath out/java.mail.jar javax.mail.Version > out/version.txt
grep -q 'String %{version}' out/version.txt
for pair in "java.mail java.mail" "smtp com.sun.mail.smtp" "imap com.sun.mail.imap" \
	"pop3 com.sun.mail.pop3" "dsn com.sun.mail.dsn" "gimap com.sun.mail.gimap"
do
	set -- $pair
	jar --describe-module -f "out/$1.jar" > "out/$1.module"
	grep -q "^$2 " "out/$1.module"
done
mkdir -p check
cat > check/Check.java <<'EOF'
public class Check {
	public static void main(String[] args) throws Exception {
		java.util.Properties props = new java.util.Properties();
		javax.mail.Session session = javax.mail.Session.getInstance(props);
		javax.mail.Transport transport = session.getTransport("smtp");
		javax.mail.Store store = session.getStore("imap");
		String transportName = transport.getClass().getName();
		String storeName = store.getClass().getName();
		if (!"com.sun.mail.smtp.SMTPTransport".equals(transportName)) {
			throw new RuntimeException(transportName);
		}
		if (!"com.sun.mail.imap.IMAPStore".equals(storeName)) {
			throw new RuntimeException(storeName);
		}
		System.out.println("javamail_ok " + transportName + " " + storeName);
	}
}
EOF
CP="out/java.mail.jar:out/smtp.jar:out/imap.jar:/usr/share/java/javax.activation.jar"
javac --release 11 -encoding UTF-8 -cp "$CP" -d check check/Check.java
java -cp "check:$CP" Check > out/check.txt
grep -q 'javamail_ok com.sun.mail.smtp.SMTPTransport com.sun.mail.imap.IMAPStore' out/check.txt

%install
# No -u: rpm's install trailer reads DONT_CLEANUP, which is unset.
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact out/java.mail.pom:out/java.mail.jar \
	--file-name java.mail \
	--alias javax.mail:mail \
	--alias com.sun.mail:all \
	--link java.mail-%{version} \
	--filelist .mfiles
for name in imap smtp pop3 dsn gimap; do
	sysjar install --buildroot %{buildroot} \
		--artifact "out/$name.pom:out/$name.jar" \
		--file-name "$name" \
		--link "$name-%{version}" \
		--filelist ".mfiles-$name"
	grep -v '%%dir /usr/share/sysjar/index/com.sun.mail' ".mfiles-$name" >> .mfiles
done
mkdir -p %{buildroot}%{_javadir}/modules
for name in java.mail imap smtp pop3 dsn gimap; do
	ln -s "../$name.jar" "%{buildroot}%{_javadir}/modules/$name.jar"
	ln -s "../$name.jar" "%{buildroot}%{_javadir}/modules/$name-%{version}.jar"
	echo "%{_javadir}/modules/$name.jar" >> .mfiles
	echo "%{_javadir}/modules/$name-%{version}.jar" >> .mfiles
done
echo "%%dir %{_javadir}/modules" >> .mfiles

%files -f .mfiles
%doc LICENSE.txt README.md
