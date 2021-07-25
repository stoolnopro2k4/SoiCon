/****
Bản Quyền					:		🅢-🅣🅞🅞🅛
Loại Code.					:		Tool Traodoisub.com Kháng 95% Block Tính Năng
Ngôn Ngữ Lập Trình.  :		PHP
Facebook  					:		https://facebook.com/dvfb.coder
Telegram   					:		t.me/stoolnopro
SĐT - MOMO				:		0765826980
_____________________________________________________________________________

🆃🅾🅾🅻 ＜￣｀ヽ、　　　　　　／￣＞🆃🅳🆂
				　ゝ、　　＼　／⌒ヽ,ノ 　/´
				　　　ゝ、　`（ ( ͡° ͜ʖ ͡°) ／
					　　  　 >、　 　,)
					　　　　　∠_,,,/
***/
error_reporting(0);
session_start();
date_default_timezone_set("Asia/Ho_Chi_Minh");
$xnhac = "\033[1;36m";
$den = "\033[1;30m";
$do = "\033[1;31m";
$luc = "\033[1;32m";
$vang = "\033[1;33m";
$xduong = "\033[1;34m";
$hong = "\033[1;35m";
$trang = "\033[1;37m";
$_SESSION['useragent'] = 'Mozilla/5.0 (Linux; Android 10; CPH1819) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.101 Mobile Safari/537.36';
$thanh_xau= $trang."≈ ".$do."[".$luc."●".$do."] ".$trang."➩ ";
$thanh_dep= $trang."≈ ".$do."[".$luc."✓".$do."] ".$trang."➩ ";
$banner = "\n$xduong     ███████╗   ████████╗ ██████╗  ██████╗ ██╗     \n$trang     ██╔════╝   ╚══██╔══╝██╔═══██╗██╔═══██╗██║     \n$xduong     ███████╗█████╗██║   ██║   ██║██║   ██║██║     \n$trang     ╚════██║╚════╝██║   ██║   ██║██║   ██║██║     \n$xduong     ███████║      ██║   ╚██████╔╝╚██████╔╝███████╗\n$trang     ╚══════╝      ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝\n\n";
gioithieu($banner, $vang, $thanh_xau);
//nhập token tds
if (!file_exists('listacc.txt')){ $k = fopen("listacc.txt","a+"); }
	$in_file = file_get_contents("listacc.txt");
	$file = explode(PHP_EOL,$in_file);
	while ($a < count($file)){
$unique = array_unique($file); 
$dupes = array_diff_key( $file, $unique ); 
 foreach ($dupes as $lock => $key){
 	array_splice($file, $lock, 1);
 }
$a++; }
for($xz = 0;$xz <= count($file);$xz++){ $x++;
$data = $file[$xz];
$token_tds = explode('|',$data)[0];
$trangthai = explode('|',$data)[1];
if ($trangthai == 'y'){ $trangthai = $vang."Hoạt Động"; }
$info = REQUEST('https://traodoisub.com/api/?fields=profile&access_token='.$token_tds);
$user = $info["data"]["user"];
$xu = $info["data"]["xu"];
if(isset($user)){ print $thanh_dep.$luc."Nhập ".$do."[".$vang.$x.$do."]".$luc." SD User ".$vang.$user.$luc." Số Xu: ".$vang.$xu.$luc." Trạng Thái: ".$do.$trangthai."\n"; } else { $x--; }
unset($user, $token_tds,$xu); }
print $thanh_dep.$luc."Nhập ".$do."[".$vang."add".$do."]".$luc." Thêm Tài Khoản TDS \n";
while (true){
print $thanh_dep.$luc."Nhập Lựa Chọn: $vang";
	$acc = trim(fgets(STDIN));
if ($acc == ''){ continue; }
if (strtolower($acc) == 'add'){
chay(35);
print $thanh_dep.$luc."Nhập Access Token Traodoisub: $vang";
	$token_tds = trim(fgets(STDIN));
	$info = REQUEST('https://traodoisub.com/api/?fields=profile&access_token='.$token_tds);
	$user = $info["data"]["user"];
if (isset($user)){ $gh = fopen('listacc.txt', 'a+'); fwrite($gh, $token_tds.'|
');
}} else if ($acc < count($file)){
  	$token_tds = explode('|',$file[($acc - 1)])[0];
$info = REQUEST('https://traodoisub.com/api/?fields=profile&access_token='.$token_tds);
$user = $info["data"]["user"]; break;
} else { print($do." Lựa Chọn Không Xác Định \n"); continue; }
}
//nhập token Facebook
chay(35);
echo $thanh_xau.$luc."Tài Khoản Hiện Tại Là: ".$vang.$user."\n";
$khotk = [];
$list_id = [];
$list_name = [];
$x = 0;
while (true){ $x++;
echo $thanh_dep.$luc."Nhập Token Facebook Thứ $x: $vang";
	$nhaptk = trim(fgets(STDIN));
	if ($nhaptk == ''){ break; }
	$token = REQUEST('https://graph.facebook.com/me/?access_token='.$nhaptk);
	if ($token["error"]["code"] == 368){
	echo $do.$token["error"]["message"]."\n"; $x--; continue;
} else if ($token["error"]){ echo $do."Access Token Die !!!                          \n"; $x--; continue; 
}
	$idfb = $token["id"];
	$tenfb = $token["name"];
	array_push($list_id, $idfb);
	array_push($list_name, $tenfb);
	array_push($khotk, $nhaptk);
	}
//dữ liệu
$user = REQUEST('https://traodoisub.com/api/?fields=profile&access_token='.$token_tds)["data"]["user"];
$xu = REQUEST('https://traodoisub.com/api/?fields=profile&access_token='.$token_tds)["data"]["xu"];
chay(35);
echo $thanh_dep.$luc."Bạn Có Muốn Kích Hoạt Tính Năng Kháng Block Không (y/n): $vang";
	$kick_hoat = trim(fgets(STDIN));
if (strtolower($kick_hoat) == 'y'){
$delay = 0; $BLOCK = 50; $delaybl = 60; $doinick = 20; 
} else {
chay(35);
echo $thanh_dep.$luc."Nhập Thời Gian Làm Nhiệm Vụ: $vang";
$delay = trim(fgets(STDIN));
echo $thanh_dep.$luc."Sau ____ Nhiệm Vụ Thì Kích Hoạt Chống Block.     \r".$thanh_dep.$luc."Sau $vang";
$BLOCK = trim(fgets(STDIN));
echo $thanh_dep.$luc."Sau ".$vang.$BLOCK.$luc." Nhiệm Vụ Nghỉ Ngơi ____ Giây       \r".$thanh_dep.$luc."Sau ".$vang.$BLOCK.$luc." Nhiệm Vụ Nghỉ Ngơi $vang";
$delaybl = trim(fgets(STDIN));
if (count($khotk) > 0){
echo $thanh_dep.$luc."Chuyển Nick Sau ____ Nhiệm Vụ    \r".$thanh_dep.$luc."Chuyển Nick Sau $vang";
$doinick = trim(fgets(STDIN));
}
}
while (true){
chay(35);
$xu = REQUEST('https://traodoisub.com/api/?fields=profile&access_token='.$token_tds)["data"]["xu"];
echo $xnhac." Số Xu Hiện Tại: ".$vang.$xu.$xnhac." Số Tài Khoản Facebook: ".$vang.count($khotk)." \n";
chay(35);
if (count($khotk) == 0){
$x = 0;
echo $do." Tất Cả Access Token Đã Bị Lỗi, Vui Lòng Nhập Lại !!! \n";
chay(35);
while (true){ $x++;
echo $thanh_dep.$luc."Nhập Token Facebook Thứ $x: $vang";
	$nhaptk = trim(fgets(STDIN));
	if ($nhaptk == ''){ break; }
	$token = REQUEST('https://graph.facebook.com/me/?access_token='.$nhaptk);
	if ($token["error"]["code"] == 368){
	echo $do.$token["error"]["message"]."\n"; $x--; continue;
	} else if ($token["error"]){ echo $do."Access Token Die !!!                          \n"; $x--; continue; 
	}
	$idfb = $token["id"];
	$tenfb = $token["name"];
	array_push($list_id, $idfb);
	array_push($list_name, $tenfb);
	array_push($khotk, $nhaptk);
	}
chay(35);
}
for($xx = 0; $xx < count($khotk); $xx++){
	$access_token = $khotk[$xx];
	$idfb = $list_id[$xx];
	$tenfb = $list_name[$xx];
	$lap_ch = 0;
	while ($lap_ch < 3){ $lap_ch++;
	$datnick = REQUEST("https://traodoisub.com/api/?fields=run&id=$idfb&access_token=$token_tds");
//print_r($datnick);
if ($datnick["data"]["msg"] == "Cấu hình thành công!") { echo $vang."Đang Cấu Hình ID: ".$luc.$idfb." ".$vang."Tên FB: ".$luc.$tenfb."\n"; break; } 
}
if ($datnick["error"]) { echo $do.$datnick["error"]["message"]." \r";  continue; }
	$vuot = 0;
	while (true){
		if ($vuot == 1){ break; }
		$list = REQUEST("https://traodoisub.com/api/?fields=like&access_token=".$token_tds);
		//print_r($list);
		if (json_encode($list) == "[]"){ echo $do." Đã Hết Nhiệm Vụ like\r"; sleep (1); }
		for($lap = 0; $lap <= 20; $lap++){
			$id = $list[$lap]["id"];
			if(isset($id)){ $type1 = ' LIKE ';
        	$g = REQUEST('https://graph.facebook.com/'.$id.'/likes?method=post&access_token='.$access_token);
            $nhan = REQUEST("https://traodoisub.com/api/coin/?type=LIKE&id=".$id."&access_token=".$token_tds);
		if ($nhan["success"] == 200) { $xu = $nhan["data"]["xu"]; $xujob = $nhan["data"]["msg"]; $stt_job++; $id = substr("$id",0,14); $maui="\033[1;".rand(31,37)."m";
			$kl = "\e[1;32m⌠\e[1;33mS-TOOL\e[1;32m⌡\e[1;35m❯\e[1;36m❯\e[1;31m❯\033[1;34m[\033[1;33m".$stt_job."\033[1;34m]\033[1;91m ● \033[1;36m".date("H:i:s")."\033[1;31m ● ".$maui.$type1."\033[1;31m ● \033[1;37m".$id."\033[1;31m ● \033[1;32m$xujob \033[1;31m●$xnhac Delay $delay\n";
			for($i = 0; $i < strlen($kl); $i++){echo $kl[$i];usleep(2500);}
			if ($stt_job % $doinick == 0 and (count($khotk) > 0)){ $vuot = 1; break; }
//kháng block
			if (($delay < 11) and (strtolower($kick_hoat) == 'y')){
					//echo $do."Kick Hoạt Chống Block ".count($listnv)."\r"; sleep (1);
					$cong_them = 0;
					if ($stt_job % 200 == 0){$cong_them = 1; $delay++; }
				if($cong_them != 0) { echo $do." Hệ Thống Đã Tăng Delay Thêm ".$cong_them."s Nhằm Mục Đích Chống Spam \n"; }
			}
			if($stt_job % $BLOCK == 0){ for ($i = $delaybl; $i > 0; $i--) { echo "\r\033[1;97m Đang hoạt động chống block sẽ chạy lại sau $i giây"; sleep(1); echo "\r                                                     \r"; } } else { delay($delay); }
		} else {
                if ($g["error"]["code"]== 190) {
                	echo "\033[1;91m Token Tài Khoản $tenfb Đã Bị Out , Đã Xoá Tài Khoản                           ";
                    array_splice($khotk, $xx, 1);
                    array_splice($list_id, $xx, 1);
                    array_splice($list_name, $xx, 1);
                    break;
					}
               if ($g["error"]["code"] == 368 and $g["error"]["error_subcode"] == 1404078) { 
					echo "\033[1;91m Tài Khoản $tenfb Đã Bị Block Tính Năng Like                ";
					array_splice($khotk, $xx, 1);
					array_splice($list_id, $xx, 1);
                    array_splice($list_name, $xx, 1);
					break;
				}}}}}}}
function REQUEST($url) {
        $data = array(
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => TRUE,
            CURLOPT_HEADER => FALSE,
            CURLOPT_FOLLOWLOCATION => TRUE,
            CURLOPT_ENCODING => '',
            CURLOPT_USERAGENT => $_SESSION['useragent'],
            CURLOPT_AUTOREFERER => TRUE,
            CURLOPT_CONNECTTIMEOUT => 15,
            CURLOPT_TIMEOUT => 15,
            CURLOPT_MAXREDIRS => 5,
            CURLOPT_SSL_VERIFYHOST => 2,
            CURLOPT_SSL_VERIFYPEER => 0 );
        $ch = curl_init();
        curl_setopt_array($ch, $data);
        $access = curl_exec($ch);
        return json_decode($access, true); }
function delay ($delay){
	for($tt = $delay ;$tt>= 1;$tt--){
        echo "\r\033[1;33m   S-TOOl \033[1;31m ~>       \033[1;32m LO      \033[1;31m | $tt | "; usleep(150000);
        echo "\r\033[1;31m   S-TOOl \033[0;33m   ~>     \033[0;37m LOA     \033[0;31m | $tt | "; usleep(150000);
        echo "\r\033[1;32m   S-TOOl \033[0;33m     ~>   \033[0;37m LOAD    \033[0;31m | $tt | "; usleep(150000);
        echo "\r\033[1;34m   S-TOOl \033[0;33m       ~> \033[0;37m LOADI   \033[0;31m | $tt | "; usleep(150000);
        echo "\r\033[1;35m   S-TOOl \033[0;33m        ~>\033[0;37m LOADIN  \033[0;31m | $tt | "; usleep(150000);
        echo "\r\033[1;35m   S-TOOl \033[0;33m        ~>\033[0;37m LOADING \033[0;31m | $tt | "; usleep(150000);
        echo "\r\033[1;35m   S-TOOl \033[0;33m        ~>\033[0;37m LOADING.\033[0;31m | $tt | ";usleep(150000);} 
echo "\r\e[1;95m    ⚡SÓI CON⚡                       \r"; }
function chay($t) { for ($x = 0; $x <= $t; $x++) { echo "\033[1;37m= ";usleep(4000); } echo"\n";}
function gioithieu($banner, $vang, $thanh_xau){ @system('clear');
for($i = 0; $i < strlen($banner); $i++){echo $banner[$i];usleep(2000);}
echo "\033[1;33m@PowerBySTOOL\n";
echo "\033[1;37m~\033[1;32m Mua Clone Tại:\033[1;37m shopqvinh.com\n"; chay(35);
echo $thanh_xau."\033[1;35mTOOL TDS ĐA TÀI KHOẢN ĐA TOKEN\n"; usleep(2000);
echo $thanh_xau."\033[1;33mBản Quyền:\033[1;34m S-TOOl\n"; usleep(2000);
echo $thanh_xau."\033[1;32mAdmin:\033[1;36m Sói Con\n"; usleep(2000);
echo $thanh_xau."\033[1;31mDonate MoMo: \033[1;34m0765826980\n"; usleep(2000);
chay(35);}
