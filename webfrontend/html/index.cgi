#!/usr/bin/perl

# Einbinden von Module
use CGI;
use LoxBerry::System;
use LoxBerry::Web;
use LoxBerry::Log;
use LoxBerry::JSON;
use IO::Socket::INET;
use LWP::Simple;
use Net::Ping;


print "Content-type: text/html\n\n";

# Konfig auslesen
my %pcfg;
my %miniservers;
tie %pcfg, "Config::Simple", "$lbpconfigdir/pluginconfig.cfg";
$UDP_Port = %pcfg{'MAIN.UDP_Port'};
#$UDP_Send_Enable = %pcfg{'MAIN.UDP_Send_Enable'};
$HTTP_TEXT_Send_Enable = %pcfg{'MAIN.HTTP_TEXT_Send_Enable'};
$MINISERVER = %pcfg{'MAIN.MINISERVER'};
%miniservers = LoxBerry::System::get_miniservers();


# Miniserver konfig auslesen
#print "\n".substr($MINISERVER, 10, length($MINISERVER))."\n";
$i = substr($MINISERVER, 10, length($MINISERVER));
$LOX_Name = $miniservers{$i}{Name};
$LOX_IP = $miniservers{$i}{IPAddress};
$LOX_User = $miniservers{$i}{Admin};
$LOX_PW = $miniservers{$i}{Pass};

print "Miniserver\@".$LOX_Name."<br>";
#print $LOX_IP."<br>";
#print $LOX_User."<br>";
#print $LOX_PW."<br>";

# Mit dieser Konstruktion lesen wir uns alle POST-Parameter in den Namespace R.
my $cgi = CGI->new;
$cgi->import_names('R');
# Ab jetzt kann beispielsweise ein POST-Parameter 'form' ausgelesen werden mit $R::form.


# POST request
$VZug_IP = $R::ip;
# $VZug_IP = "172.16.200.105";



# Create my logging object
my $log = LoxBerry::Log->new ( 
	name => 'cronjob',
	filename => "$lbplogdir/kostal.log",
	append => 1
	);
LOGSTART "Kostal cronjob start";

# UDP-Port Erstellen für Loxone
my $sock = new IO::Socket::INET(PeerAddr => $LOX_IP,
                PeerPort => $UDP_Port,
                Proto => 'udp', Timeout => 1) or die('Error opening socket.');
			

# Loxone HA-Miniserver by Marcel Zoller	
if($LOX_Name eq "lxZoller1"){
	# Loxone Minisever ping test
	LOGOK " Loxone Zoller HA-Miniserver";
	#$LOX_IP="172.16.200.7"; #Testvariable
	#$LOX_IP='172.16.200.6'; #Testvariable
	$p = Net::Ping->new();
	$p->port_number("80");
	if ($p->ping($LOX_IP,2)) {
				LOGOK "Ping Loxone: Miniserver1 is online.";
				LOGOK "Ping Loxone: $p->ping($LOX_IP)";
				$p->close();
			} else{ 
				LOGALERT "Ping Loxone: Miniserver1 not online!";
				LOGDEB "Ping Loxone: $p->ping($LOX_IP)";
				$p->close();
				
				$p = Net::Ping->new();
				$p->port_number("80");
				$LOX_IP = $miniservers{2}{IPAddress};
				$LOX_User = $miniservers{2}{Admin};
				$LOX_PW = $miniservers{2}{Pass};
				#$LOX_IP="172.16.200.6"; #Testvariable
				if ($p->ping($LOX_IP,2)) {
					LOGOK "Ping Loxone: Miniserver2 is online.";
					LOGOK "Ping Loxone: $p->ping($LOX_IP)";
				} else {
					LOGALERT "Ping Loxone: Miniserver2 not online!";
					LOGDEB "Ping Loxone: $p->ping($LOX_IP)";
					#Failback Variablen !!!
					$LOX_IP = $miniservers{1}{IPAddress};
					$LOX_User = $miniservers{1}{Admin};
					$LOX_PW = $miniservers{1}{Pass};	
				} 
			}
		$p->close();			
}

my @vzugIP;
# Alle VZUG IPs aus der Konfig
my $hisIP;	
my $k;


$k = 1;
$dev1ip = %pcfg{"Device$k.IP"};
push @vzugIP, $dev1ip;
#print "$vzugIP[$i]<br>";

LOGDEB "Loxone Name: $LOX_Name";			
# $dev1ip = %pcfg{'Device1.IP'};
if ($VZug_IP ne "") {
	$dev1ip = $VZug_IP;
}

if ($dev1ip ne "") {
	LOGDEB "Kostal IP: $dev1ip";
	
	# Erstellen eines neuen Socket-Objekts
	my $socket = new IO::Socket::INET (
		#PeerHost => '172.16.200.241', # Die IP-Adresse des Servers
		PeerHost => $dev1ip,
		PeerPort => '81',      # Der Port des Servers
		Proto => 'tcp',          # Protokoll
	) or die "Fehler beim Verbinden: $!\n";

	#print "Verbunden zum Server.\n";

	# Hex-Text, den Sie senden möchten, z.B. '48656C6C6F' für "Hello"
	my $hex_MESSAGE_Spannung 		= "6203030300435200";
	my $hex_MESSAGE_Gesamt 			= "6203030300455000";
	my $hex_MESSAGE_WR_Status 		= "6203030300573E00";
	my $hex_MESSAGE_Tagesenergie 	= "62030303009DF800";

	# Kostal Gesamtenergie 
	my $binary_data = pack('H*', $hex_MESSAGE_Gesamt);
	print $socket $binary_data;
	my $response = "";
	$socket->recv($response, 1024);
	my $hex_response = unpack('H*', $response);
	#print "Antwort vom Server (Hex): $hex_response\n";

	$data_Gesamt = $hex_response;
	my $str_Gesamt = substr($data_Gesamt, 16, 2) . substr($data_Gesamt, 14, 2) . substr($data_Gesamt, 12, 2) . substr($data_Gesamt, 10, 2);
	$str_Gesamt = hex($str_Gesamt) / 1000;
	#print "Kostal Gesamt: $str_Gesamt kWh\n";


	# Kostal Tagesenergie 
	my $binary_data = pack('H*', $hex_MESSAGE_Tagesenergie);
	print $socket $binary_data;
	my $response = "";
	$socket->recv($response, 1024);
	my $hex_response = unpack('H*', $response);
	#print "Antwort vom Server (Hex): $hex_response\n";

	$data_Tagesenergie = $hex_response;
	my $str_Tagesenergie = substr($data_Tagesenergie, 16, 2) . substr($data_Tagesenergie, 14, 2) . substr($data_Tagesenergie, 12, 2). substr($data_Tagesenergie, 10, 2) ;
	$str_Tagesenergie =  hex($str_Tagesenergie) / 1000;
	#print "Kostal Tagesenergie: $str_Tagesenergie kWh\n";


	# Kostal Spannung 
	my $binary_data = pack('H*', $hex_MESSAGE_Spannung);
	print $socket $binary_data;
	my $response = "";
	$socket->recv($response, 1024);
	my $hex_response = unpack('H*', $response);
	#print "Antwort vom Server (Hex): $hex_response\n";

	$data_Spannung = $hex_response;
	my $str_Spannung_String1 = substr($data_Spannung, 20, 2) . substr($data_Spannung, 18, 2) ;
	$str_Spannung_String1 = hex($str_Spannung_String1);
	my $str_Spannung_String2 = substr($data_Spannung, 40, 2) . substr($data_Spannung, 38, 2) ;
	$str_Spannung_String2 = hex($str_Spannung_String2);
	my $str_Spannung_Phase1 = substr($data_Spannung, 80, 2) . substr($data_Spannung, 78, 2) ;
	$str_Spannung_Phase1 = hex($str_Spannung_Phase1);
	my $str_Spannung_Phase2 = substr($data_Spannung, 96, 2) . substr($data_Spannung, 94, 2) ;
	$str_Spannung_Phase2 = hex($str_Spannung_Phase2);
	my $str_Spannung_Phase3 = substr($data_Spannung, 112, 2) . substr($data_Spannung, 110, 2) ;
	$str_Spannung_Phase3 = hex($str_Spannung_Phase3);
	$str_Spannung_Aktuell = $str_Spannung_Phase1+$str_Spannung_Phase2+$str_Spannung_Phase3;
	#print "Kostal Spannung String 1: $str_Spannung_String1 Watt\n";
	#print "Kostal Spannung String 2: $str_Spannung_String2 Watt\n";
	#print "Kostal Spannung Phase 1: $str_Spannung_Phase1 Watt\n";
	#print "Kostal Spannung Phase 2: $str_Spannung_Phase2 Watt\n";
	#print "Kostal Spannung Phase 3: $str_Spannung_Phase3 Watt\n";
	#print "Kostal Spannung Aktuell: $str_Spannung_Aktuell Watt\n";


	# Kostal Status 
	my $binary_data = pack('H*', $hex_MESSAGE_WR_Status);
	print $socket $binary_data;
	my $response = "";
	$socket->recv($response, 1024);
	my $hex_response = unpack('H*', $response);
	#print "Antwort vom Server (Hex): $hex_response\n";

	$data_WR_Status = $hex_response;
	my $str_WR_Status_Status = hex(substr($data_WR_Status, 10, 2));
	my $str_WR_Status_Stoerung = hex(substr($data_WR_Status, 12, 2));
	my $str_WR_Status_Stoerung_Code;

	if ($str_WR_Status_Stoerung == 0) {
		$str_WR_Status_Stoerung_Code = 0;
	} else {
		$str_WR_Status_Stoerung_Code = hex(substr($data_WR_Status, 14, 4));
	}
	#print "Kostal Status: $str_WR_Status_Status\n";
	#print "Kostal Störung: $str_WR_Status_Stoerung\n";
	#print "Kostal Störung Code : $str_WR_Status_Stoerung_Code\n";


	# Schließen des Sockets
	close($socket);

	print "KostalGesamt\@$str_Gesamt<br>";
	print "KostalTagesenergie\@$str_Tagesenergie<br>";
	print "KostalStatus\@$str_WR_Status_Status<br>";
	print "KostalStoerung\@$str_WR_Status_Stoerung<br>";
	print "KostalStoerungCode\@$str_WR_Status_Stoerung_Code<br>";
	print "KostalSpannungString1\@$str_Spannung_String1<br>";
	print "KostalSpannungString2\@$str_Spannung_String2<br>";
	print "KostalSpannungPhase1\@$str_Spannung_Phase1<br>";
	print "KostalSpannungPhase2\@$str_Spannung_Phase2<br>";
	print "KostalSpannungPhase3\@$str_Spannung_Phase3<br>";
	print "KostalSpannungAktuell\@$str_Spannung_Aktuell<br><br>";



	if ($HTTP_TEXT_Send_Enable == 1) {
		LOGDEB "Loxone IP: $LOX_IP";
		LOGDEB "User: $LOX_User";
		LOGDEB "Password: $LOX_PW";
		# wgetstr = "wget --quiet --output-document=temp http://"+loxuser+":"+loxpw+"@"+loxip+"/dev/sps/io/VZUG_Adora_Programm/" + str(ProgrammStr) 
		$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_aktuell/$str_Spannung_Aktuell");
		$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_gesamtenergie/$str_Gesamt");
		$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_Phase1/$str_Spannung_Phase1");
		$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_Phase2/$str_Spannung_Phase2");
		$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_Phase3/$str_Spannung_Phase3");
		$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_Status/$str_WR_Status_Status");
		$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_Stoerung/$str_WR_Status_Stoerung");
		$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_Stoerungs_Code/$str_WR_Status_Stoerung_Code");
		$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_String1/$str_Spannung_String1");
		$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_String2/$str_Spannung_String2");
		$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_tagesenergie/$str_Tagesenergie");


		LOGDEB "URL: http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_aktuell/$str_Spannung_Aktuell";
		LOGDEB "URL: http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_gesamtenergie/$str_Gesamt";
		LOGDEB "URL: http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_Phase1/$str_Spannung_Phase1";
		LOGDEB "URL: http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_Phase2/$str_Spannung_Phase1";
		LOGDEB "URL: http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_Phase3/$str_Spannung_Phase3";
		LOGDEB "URL: http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_Status/$str_WR_Status_Status";
		LOGDEB "URL: http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_Stoerung/$str_WR_Status_Stoerung";
		LOGDEB "URL: http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_Stoerungs_Code/$str_WR_Status_Stoerung_Code";
		LOGDEB "URL: http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_String1/$str_Spannung_String1";
		LOGDEB "URL: http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_String2/$str_Spannung_String2";
		LOGDEB "URL: http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/PV_Kostal_tagesenergie/$str_Tagesenergie";
	
		}
	else {
		LOGDEB "HTTP_TEXT_Send_Enable: 0";
	}
		
	if ($UDP_Send_Enable == 1) {
		print $sock "PV_Kostal_aktuell\@$str_Spannung_Aktuell\;";
		LOGDEB "Loxone IP: $LOX_IP";

		LOGDEB "UDP Port: $UDP_Port";
		LOGDEB "UDP Send: PV_Kostal_aktuell\@$str_Spannung_Aktuell\;";
		
	}
}
# Schließen des Sockets
close($sock);

# We start the log. It will print and store some metadata like time, version numbers
# LOGSTART "V-ZUG cronjob start";
  
# Now we really log, ascending from lowest to highest:
# LOGDEB "This is debugging";                 # Loglevel 7
# LOGINF "Infos in your log";                 # Loglevel 6
# LOGOK "Everything is OK";                   # Loglevel 5
# LOGWARN "Hmmm, seems to be a Warning";      # Loglevel 4
# LOGERR "Error, that's not good";            # Loglevel 3
# LOGCRIT "Critical, no fun";                 # Loglevel 2
# LOGALERT "Alert, ring ring!";               # Loglevel 1
# LOGEMERGE "Emergency, for really really hard issues";   # Loglevel 0
  
LOGEND "Operation finished sucessfully.";
