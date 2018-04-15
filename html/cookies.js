/*
function addCookie(name,value,expireHours){
         var cookieString=name+"="+escape(value);
         //判断是否设置过期时间
         if(expireHours>0){
                var date=new Date();
                date.setTime(date.getTime()+expireHours*3600*1000);
                cookieString=cookieString+"; expires="+date.toGMTString();
         }
   alert(cookieString);
         document.cookie=cookieString;
}
//获取指定name的Cookie值
function getCookie(name){
         var strCookie=document.cookie;
         var arrCookie=strCookie.split("; ");
         for(var i=0;i<arrCookie.length;i++){
               var arr=arrCookie[i].split("=");
               if(arr[0]==name)return arr[1];
         }
         return "";
}
//删除指定名称的Cookie,cookie对象过期会自动删除
function deleteCookie(name){
          var date=new Date();
          date.setTime(date.getTime()-10000);
          document.cookie=name+"=v; expire="+date.toGMTString();
}
*/
var base64EncodeChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
var base64DecodeChars = new Array(
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1, 63,
    52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1, -1, -1, -1, -1,
    -1,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14,
    15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, -1, -1, -1, -1, -1,
    -1, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
    41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, -1, -1, -1, -1, -1);

function getCookie(c_name)
{
	//alert("c_name"+c_name)
	//alert("length:"+document.cookie.length)
  if (document.cookie.length>0)
  { 
    c_start=document.cookie.indexOf(c_name + "=")
    if (c_start!=-1)
    { 
      c_start=c_start + c_name.length+1 
      c_end=document.cookie.indexOf(";",c_start)
      if (c_end==-1) c_end=document.cookie.length
      return unescape(document.cookie.substring(c_start,c_end))
    } 
  }
  return ""
}

function setCookie(c_name,value,expireMillsec)
{
  var exdate=new Date()
  exdate.setTime(exdate.getTime()+expireMillsec)
  document.cookie=c_name+ "=" +escape(value)+
  ((expireMillsec==null) ? "" : "; expires="+exdate.toGMTString())
}

function checkCookie()
{
  uuid=getCookie('uuid')
  //alert(uuid)
  if (uuid!=null && uuid!="")
    {
    	
    }
  else 
  {
  	/*
    username=prompt('Please enter your name:',"")
    if (username!=null && username!="")
    {
      setCookie('username',username,365)
    }
    */
    document.write("<script language=javascript>alert('sorry, please login first,thank you!');window.location.href='login.html';</script>");
  }
}

  function redirect()
  {
	  document.write("<script language=javascript>window.location.href='index.html';</script>");
  }

<!-- Begin
function encrypt(str, pwd) {
  if(pwd == null || pwd.length <= 0) {
    alert("Please enter a password with which to encrypt the message.");
    return null;
  }
  var prand = "";
  for(var i=0; i<pwd.length; i++) {
    prand += pwd.charCodeAt(i).toString();
  }
  var sPos = Math.floor(prand.length / 5);
  var mult = parseInt(prand.charAt(sPos) + prand.charAt(sPos*2) + prand.charAt(sPos*3) + prand.charAt(sPos*4));
  var incr = Math.ceil(pwd.length / 2);
  var modu = Math.pow(2, 31) - 1;
  if(mult < 2) {
    alert("Algorithm cannot find a suitable hash. Please choose a different password. \nPossible considerations are to choose a more complex or longer password.");
    return null;
  }
  var salt = Math.round(Math.random() * 1000000000) % 100000000;
  prand += salt;
  while(prand.length > 10) {
    prand = (parseInt(prand.substring(0, 10)) + parseInt(prand.substring(prand.length-10, prand.length))).toString();
  }
  prand = (mult * prand + incr) % modu;
  var enc_chr = "";
  var enc_str = "";
  for(var i=0; i<str.length; i++) {
    enc_chr = parseInt(str.charCodeAt(i) ^ Math.floor((prand / modu) * 255));
    if(enc_chr < 16) {
      enc_str += "0" + enc_chr.toString(16);
    } else enc_str += enc_chr.toString(16);
    prand = (mult * prand + incr) % modu;
  }
  salt = salt.toString(16);
  while(salt.length < 8)salt = "0" + salt;
  enc_str += salt;
  return enc_str;
}
function decrypt(str, pwd) {
  if(str == null || str.length < 8) {
    alert("A salt value could not be extracted from the encrypted message because it's length is too short. The message cannot be decrypted.");
    return;
  }
  if(pwd == null || pwd.length <= 0) {
    alert("Please enter a password with which to decrypt the message.");
    return;
  }
  var prand = "";
  for(var i=0; i<pwd.length; i++) {
    prand += pwd.charCodeAt(i).toString();
  }
  var sPos = Math.floor(prand.length / 5);
  var mult = parseInt(prand.charAt(sPos) + prand.charAt(sPos*2) + prand.charAt(sPos*3) + prand.charAt(sPos*4));
  var incr = Math.round(pwd.length / 2);
  var modu = Math.pow(2, 31) - 1;
  var salt = parseInt(str.substring(str.length - 8, str.length), 16);
  str = str.substring(0, str.length - 8);
  prand += salt;
  while(prand.length > 10) {
    prand = (parseInt(prand.substring(0, 10)) + parseInt(prand.substring(prand.length-10, prand.length))).toString();
  }
  prand = (mult * prand + incr) % modu;
  var enc_chr = "";
  var enc_str = "";
  for(var i=0; i<str.length; i+=2) {
    enc_chr = parseInt(parseInt(str.substring(i, i+2), 16) ^ Math.floor((prand / modu) * 255));
    enc_str += String.fromCharCode(enc_chr);
    prand = (mult * prand + incr) % modu;
  }
  return enc_str;
}


function UUID(){  
    this.id = this.createUUID();  
}  
  
// When asked what this Object is, lie and return it's value  
UUID.prototype.valueOf = function(){ return this.id; }  
UUID.prototype.toString = function(){ return this.id; }  
  
//  
// INSTANCE SPECIFIC METHODS  
//  
  
UUID.prototype.createUUID = function(){  
    //  
    // Loose interpretation of the specification DCE 1.1: Remote Procedure Call  
    // described at http://www.opengroup.org/onlinepubs/009629399/apdxa.htm#tagtcjh_37  
    // since JavaScript doesn't allow access to internal systems, the last 48 bits   
    // of the node section is made up using a series of random numbers (6 octets long).  
    //    
    var dg = new Date(1582, 10, 15, 0, 0, 0, 0);  
    var dc = new Date();  
    var t = dc.getTime() - dg.getTime();  
    var tl = UUID.getIntegerBits(t,0,31);  
    var tm = UUID.getIntegerBits(t,32,47);  
    var thv = UUID.getIntegerBits(t,48,59) + '1'; // version 1, security version is 2  
    var csar = UUID.getIntegerBits(UUID.rand(4095),0,7);  
    var csl = UUID.getIntegerBits(UUID.rand(4095),0,7);  
  
    // since detection of anything about the machine/browser is far to buggy,   
    // include some more random numbers here  
    // if NIC or an IP can be obtained reliably, that should be put in  
    // here instead.  
    var n = UUID.getIntegerBits(UUID.rand(8191),0,7) +   
            UUID.getIntegerBits(UUID.rand(8191),8,15) +   
            UUID.getIntegerBits(UUID.rand(8191),0,7) +   
            UUID.getIntegerBits(UUID.rand(8191),8,15) +   
            UUID.getIntegerBits(UUID.rand(8191),0,15); // this last number is two octets long  
    return tl + tm  + thv  + csar + csl + n;   
}  
  
  
//  
// GENERAL METHODS (Not instance specific)  
//  
  
  
// Pull out only certain bits from a very large integer, used to get the time  
// code information for the first part of a UUID. Will return zero's if there   
// aren't enough bits to shift where it needs to.  
UUID.getIntegerBits = function(val,start,end){  
    var base16 = UUID.returnBase(val,16);  
    var quadArray = new Array();  
    var quadString = '';  
    var i = 0;  
    for(i=0;i<base16.length;i++){  
        quadArray.push(base16.substring(i,i+1));      
    }  
    for(i=Math.floor(start/4);i<=Math.floor(end/4);i++){  
        if(!quadArray[i] || quadArray[i] == '') quadString += '0';  
        else quadString += quadArray[i];  
    }  
    return quadString;  
}  
  
// Replaced from the original function to leverage the built in methods in  
// JavaScript. Thanks to Robert Kieffer for pointing this one out  
UUID.returnBase = function(number, base){  
    return (number).toString(base).toUpperCase();  
}  
  
// pick a random number within a range of numbers  
// int b rand(int a); where 0 <= b <= a  
UUID.rand = function(max){  
    return Math.floor(Math.random() * (max + 1));  
}


function base64encode(str) {
    var out, i, len;
    var c1, c2, c3;
    len = str.length;
    i = 0;
    out = "";
    while(i < len) {
    c1 = str.charCodeAt(i++) & 0xff;
    if(i == len)
    {
        out += base64EncodeChars.charAt(c1 >> 2);
        out += base64EncodeChars.charAt((c1 & 0x3) << 4);
        out += "==";
        break;
    }
    c2 = str.charCodeAt(i++);
    if(i == len)
    {
        out += base64EncodeChars.charAt(c1 >> 2);
        out += base64EncodeChars.charAt(((c1 & 0x3)<< 4) | ((c2 & 0xF0) >> 4));
        out += base64EncodeChars.charAt((c2 & 0xF) << 2);
        out += "=";
        break;
    }
    c3 = str.charCodeAt(i++);
    out += base64EncodeChars.charAt(c1 >> 2);
    out += base64EncodeChars.charAt(((c1 & 0x3)<< 4) | ((c2 & 0xF0) >> 4));
    out += base64EncodeChars.charAt(((c2 & 0xF) << 2) | ((c3 & 0xC0) >>6));
    out += base64EncodeChars.charAt(c3 & 0x3F);
    }
    return out;
}
function base64decode(str) {
    var c1, c2, c3, c4;
    var i, len, out;
    len = str.length;
    i = 0;
    out = "";
    while(i < len) {
    /* c1 */
    do {
        c1 = base64DecodeChars[str.charCodeAt(i++) & 0xff];
    } while(i < len && c1 == -1);
    if(c1 == -1)
        break;
    /* c2 */
    do {
        c2 = base64DecodeChars[str.charCodeAt(i++) & 0xff];
    } while(i < len && c2 == -1);
    if(c2 == -1)
        break;
    out += String.fromCharCode((c1 << 2) | ((c2 & 0x30) >> 4));
    /* c3 */
    do {
        c3 = str.charCodeAt(i++) & 0xff;
        if(c3 == 61)
        return out;
        c3 = base64DecodeChars[c3];
    } while(i < len && c3 == -1);
    if(c3 == -1)
        break;
    out += String.fromCharCode(((c2 & 0XF) << 4) | ((c3 & 0x3C) >> 2));
    /* c4 */
    do {
        c4 = str.charCodeAt(i++) & 0xff;
        if(c4 == 61)
        return out;
        c4 = base64DecodeChars[c4];
    } while(i < len && c4 == -1);
    if(c4 == -1)
        break;
    out += String.fromCharCode(((c3 & 0x03) << 6) | c4);
    }
    return out;
}
function utf16to8(str) {
    var out, i, len, c;
    out = "";
    len = str.length;
    for(i = 0; i < len; i++) {
    c = str.charCodeAt(i);
    if ((c >= 0x0001) && (c <= 0x007F)) {
        out += str.charAt(i);
    } else if (c > 0x07FF) {
        out += String.fromCharCode(0xE0 | ((c >> 12) & 0x0F));
        out += String.fromCharCode(0x80 | ((c >>  6) & 0x3F));
        out += String.fromCharCode(0x80 | ((c >>  0) & 0x3F));
    } else {
        out += String.fromCharCode(0xC0 | ((c >>  6) & 0x1F));
        out += String.fromCharCode(0x80 | ((c >>  0) & 0x3F));
    }
    }
    return out;
}
function utf8to16(str) {
    var out, i, len, c;
    var char2, char3;
    out = "";
    len = str.length;
    i = 0;
    while(i < len) {
    c = str.charCodeAt(i++);
    switch(c >> 4)
    { 
      case 0: case 1: case 2: case 3: case 4: case 5: case 6: case 7:
        // 0xxxxxxx
        out += str.charAt(i-1);
        break;
      case 12: case 13:
        // 110x xxxx   10xx xxxx
        char2 = str.charCodeAt(i++);
        out += String.fromCharCode(((c & 0x1F) << 6) | (char2 & 0x3F));
        break;
      case 14:
        // 1110 xxxx  10xx xxxx  10xx xxxx
        char2 = str.charCodeAt(i++);
        char3 = str.charCodeAt(i++);
        out += String.fromCharCode(((c & 0x0F) << 12) |
                       ((char2 & 0x3F) << 6) |
                       ((char3 & 0x3F) << 0));
        break;
    }
    }
    return out;
}