#!/bin/ash

#This script is called by WebLCM to find the quietest channel for AP mode.
#The ACS algorithm is based on the BSS load data returned by `iw scan`. To test
#it, we can run it manually by setting the `band` and a scanning channel list


wlan="wlan0"
reg_db="/tmp/regulatory-for-acs.db"

BG_CHANNELS="1 6 11"
BG_FREQUENCIES="2412 2437 2462"
#2_4g channels utilisation initialization
for ch in $BG_CHANNELS
do
  eval bg_channel_"$ch"=0
  eval count_bg_channel_"$ch"=0
done


A_CHANNELS="36 40 44 48 52 56 60 64 100 104 108 112 116 \
			120 124 128 132 136 140 144 149 153 157 161 165"

A_FREQUENCIES="5180 5200 5220 5240 5260 5280 5300 5320 5500 5520 5540 5560 5580 \
			   5600 5620 5640 5660 5680 5700 5720 5745 5765 5785 5805 5845"

#5g channels utilisation/count initialization
for ch in $A_CHANNELS
do
  eval a_channel_"$ch"=0
  eval count_a_channel_"$ch"=0
done

#Valid channel list for the band per regulatory domain/country
a_channel_list=""
bg_channel_list=""
min_utilisation=0
quietest_channel=0
bssid_count=0
bssload_count=0


function make_valid_bg_channel_list(){

  local __cnt=0

  for freq in $BG_FREQUENCIES
  do
    __cnt=$(($__cnt+1))
    if [ $(($freq-10)) -ge $1 ] && [ $(($freq+10)) -le $2 ]
    then
      __chan=`echo "$__cnt $BG_CHANNELS" | awk '{ split($0, a," "); print a[a[1]+1] }'`
      bg_channel_list="$bg_channel_list $__chan"
    fi
  done
}

function make_valid_a_channel_list() {

  local __cnt=0

  for freq in $A_FREQUENCIES
  do
    __cnt=$(($__cnt+1))
    if [ $(($freq-10)) -ge $1 ] && [ $(($freq+10)) -le $2 ]
    then
      __chan=`echo "$__cnt $A_CHANNELS" | awk '{ split($0, a," "); print a[a[1]+1] }'`
      a_channel_list="$a_channel_list $__chan"
    fi
  done
}

function make_valid_channel_list(){

  if [ $2 -lt 3000 ]
  then
    make_valid_bg_channel_list $1 $2
  elif [ $1 -gt 3000 ]
  then
    make_valid_a_channel_list $1 $2
  fi
}

function get_valid_channel_list() {

  local __phy_found=0
  local __country=""

  while read line <&3
  do
    if [ -z "${line##*#phy*}" ]
    then
      __phy_found=1
    elif [ $__phy_found -eq 1 ] && [ -z $__country ]
    then
        __country=`echo $line | awk '{ print $2 }'`
        __country=${__country::-1}
    elif [ ! -z $__country ]
    then
      if [ -z "$line" ]
      then
        __phy_found=0
        __country=0
      elif [ ! -z "${line##*DFS*}" ] &&  [ ! -z "${line##*PASSIVE*}" ]
      then
        __start=`echo $line | awk '{ print $1 }'`
        __start=${__start:1}
        __end=`echo $line | awk '{ print $3 }'`
        make_valid_channel_list $__start $__end
      fi
    fi
  done 3<"$reg_db"

}

#Adjust channel utilization/count based on a look-up table of signal strength.
function adjust_weight(){

  local  __weight=0

  if [ $1 -gt -30 ]
  then
    __weight=10
  elif [ $1 -gt -50 ]
  then
    __weight=8
  elif [ $1 -gt -60 ]
  then
    __weight=7
  elif [ $1 -gt -67 ]
  then
    __weight=6
  elif [ $1 -gt -70 ]
  then
    __weight=4
  elif [ $1 -gt -80 ]
  then
    __weight=2
  elif [ $1 -gt -90 ]
  then
    __weight=1
  fi

  return $__weight
}

#Parameters:
#  $1: freq
#  $2: adjusted weight
function cal_bssid_count(){

  case $1 in
    2412)
      count_bg_channel_1=$(($count_bg_channel_1+$2))
      ;;
    2437)
      count_bg_channel_6=$(($count_bg_channel_6+$2))
      ;;
    2462)
      count_bg_channel_11=$(($count_bg_channel_11+$2))
      ;;
    5180)
      count_a_channel_36=$(($count_a_channel_36+$2))
      ;;
    5200)
      count_a_channel_40=$(($count_a_channel_40+$2))
      ;;
    5220)
      count_a_channel_44=$(($count_a_channel_44+$2))
      ;;
    5240)
      count_a_channel_48=$(($count_a_channel_48+$2))
      ;;
    5260)
      count_a_channel_52=$(($count_a_channel_52+$2))
      ;;
    5280)
      count_a_channel_56=$(($count_a_channel_56+$2))
      ;;
    5300)
      count_a_channel_60=$(($count_a_channel_60+$2))
      ;;
    5320)
      count_a_channel_64=$(($count_a_channel_64+$2))
      ;;
    5500)
      count_a_channel_100=$(($count_a_channel_100+$2))
      ;;
    5520)
      count_a_channel_104=$(($count_a_channel_104+$2))
      ;;
    5540)
      count_a_channel_108=$(($count_a_channel_108+$2))
      ;;
    5560)
      count_a_channel_112=$(($count_a_channel_112+$2))
      ;;
    5580)
      count_a_channel_116=$(($count_a_channel_116+$2))
      ;;
    5600)
      count_a_channel_120=$(($count_a_channel_120+$2))
      ;;
    5620)
      count_a_channel_124=$(($count_a_channel_124+$2))
      ;;
    5640)
      count_a_channel_128=$(($count_a_channel_128+$2))
      ;;
    5660)
      count_a_channel_132=$(($count_a_channel_132+$2))
      ;;
    5680)
      count_a_channel_136=$(($count_a_channel_136+$2))
      ;;
    5700)
      count_a_channel_140=$(($count_a_channel_140+$2))
      ;;
    5720)
      count_a_channel_144=$(($count_a_channel_144+$2))
      ;;
    5745)
      count_a_channel_149=$(($count_a_channel_149+$2))
      ;;
    5765)
      count_a_channel_153=$(($count_a_channel_153+$2))
      ;;
    5785)
      count_a_channel_157=$(($count_a_channel_157+$2))
      ;;
    5805)
      count_a_channel_161=$(($count_a_channel_161+$2))
      ;;
    5825)
      count_a_channel_165=$(($count_a_channel_165+$2))
      ;;
    *)
      ;;
  esac
}

#Parameters:
#  $1: freq
#  $2: adjusted channel utilisation
function cal_channel_utilization(){


  case $1 in
    2412)
      bg_channel_1=$(($bg_channel_1+$2))
      ;;
    2437)
      bg_channel_6=$(($bg_channel_6+$2))
      ;;
    2462)
      bg_channel_11=$(($bg_channel_11+$2))
      ;;
    5180)
      a_channel_36=$(($a_channel_36+$2))
      ;;
    5200)
      a_channel_40=$(($a_channel_40+$2))
      ;;
    5220)
      a_channel_44=$(($a_channel_44+$2))
      ;;
    5240)
      a_channel_48=$(($a_channel_48+$2))
      ;;
    5260)
      a_channel_52=$(($a_channel_52+$2))
      ;;
    5280)
      a_channel_56=$(($a_channel_56+$2))
      ;;
    5300)
      a_channel_60=$(($a_channel_60+$2))
      ;;
    5320)
      a_channel_64=$(($a_channel_64+$2))
      ;;
    5500)
      a_channel_100=$(($a_channel_100+$2))
      ;;
    5520)
      a_channel_104=$(($a_channel_104+$2))
      ;;
    5540)
      a_channel_108=$(($a_channel_108+$2))
      ;;
    5560)
      a_channel_112=$(($a_channel_112+$2))
      ;;
    5580)
      a_channel_116=$(($a_channel_116+$2))
      ;;
    5600)
      a_channel_120=$(($a_channel_120+$2))
      ;;
    5620)
      a_channel_124=$(($a_channel_124+$2))
      ;;
    5640)
      a_channel_128=$(($a_channel_128+$2))
      ;;
    5660)
      a_channel_132=$(($a_channel_132+$2))
      ;;
    5680)
      a_channel_136=$(($a_channel_136+$2))
      ;;
    5700)
      a_channel_140=$(($a_channel_140+$2))
      ;;
    5720)
      a_channel_144=$(($a_channel_144+$2))
      ;;
    5745)
      a_channel_149=$(($a_channel_149+$2))
      ;;
    5765)
      a_channel_153=$(($a_channel_153+$2))
      ;;
    5785)
      a_channel_157=$(($a_channel_157+$2))
      ;;
    5805)
      a_channel_161=$(($a_channel_161+$2))
      ;;
    5825)
      a_channel_165=$(($a_channel_165+$2))
      ;;
    *)
      ;;
  esac
}

function find_quietest_channel_by_bssload(){

  __clist=`eval echo "$""$1"_channel_list`
  for i in $__clist
  do
    __utilisation=`eval echo "$""$1"_channel_"$i"`
    if [ $quietest_channel -eq 0 ] || [ $min_utilisation -gt $__utilisation ]
    then
       min_utilisation=$__utilisation
       quietest_channel=$i
    fi
  done
}

function find_quietest_channel_by_bssid_counting(){

  __clist=`eval echo "$""$1"_channel_list`
  for i in $__clist
  do
    __bssid_count=`eval echo "$"count_"$1"_channel_"$i"`
    if [ $quietest_channel -eq 0 ] || [ $min_utilisation -gt $__bssid_count ]
    then
       min_utilisation=$__bssid_count
       quietest_channel=$i
    fi
  done
}

function print_statistics() {
  log="/tmp/acs.log"

  echo "BAND $1" >> $log
  __clist=`eval echo "$""$1"_channel_list`
  for i in $__clist
  do
    c1=`eval echo "$""$1"_channel_"$i"`
    c2=`eval echo "$"count_"$1"_channel_"$i"`
    echo "channel $i utilization $c1 count $c2" >> $log
  done
}

#In each data frame returned by iw scan, "freq" always comes first, and then "signal".
#"channel utilisation" comes last if it is advertized.
function do_scan() {

  iw $wlan scan | grep -E "freq|channel utilisation|signal" | {
  #For testing, we can save the result of `iw scan` first and then 'cat' it
  #cat ap_list.db | grep -E "freq|channel utilisation|signal" | {
    while read line
    do
      __first=`echo "$line" | awk '{ print $1 }'`
      __second=`echo "$line" | awk '{ print $2 }'`
      if [ "$__first" == "signal:" ]
      then
        __signal=`echo $line | awk '{ print $2 }' | awk '{ split($0, a,"."); print a[1] }'`
		adjust_weight $__signal
        __weight=$?
        cal_bssid_count $__freq $__weight
        bssid_count=$(($bssid_count+1))
      elif [ "$__first" == "freq:" ]
      then
        __freq=$__second
      elif [ "$__second" == "channel" ]
      then
        __utilisation=`echo "$line" | awk '{ print $4 }' | awk '{ split($0, a,"/"); print a[1] }'`
        __adjusted_utilisation=$(($__weight*$__utilisation))
        cal_channel_utilization $__freq $__adjusted_utilisation
        bssload_count=$(($bssload_count+1))
      fi
    done

    #Debug
    #print_statistics "a"
    #print_statistics "bg"

    bssid_count=$(($bssid_count-$bssload_count))

    if [ $bssid_count -gt $bssload_count  ]
    then
        if [ -z "${band##*bg*}" ]
        then
            find_quietest_channel_by_bssid_counting "bg"
        fi

        if [ -z "${band##*a*}" ]
        then
            find_quietest_channel_by_bssid_counting "a"
        fi
    else
        if [ -z "${band##*bg*}" ]
        then
            find_quietest_channel_by_bssload "bg"
        fi

        if [ -z "${band##*a*}" ]
        then
            find_quietest_channel_by_bssload "a"
		fi
    fi
    return $quietest_channel
  }
}

function help(){
	echo 'Help: you have to specify the band[a|bg|abg]'
	echo './acs bg'
	echo './acs a'
	echo './acs abg'
	echo 'It will return the first channel with min utilisation.'
	exit 0
}

if [ $# -eq 0 ]
then
	band="abg"
else
	band=$1
fi

if [ "$band" != "a" ] && [ "$band" != "bg" ] && [ "$band" != "abg" ]
then
	echo 0
	exit 0
fi


iw reg get > $reg_db
get_valid_channel_list
rm -f $reg_db

do_scan
#Send the result to script ACS
echo $?

exit 0
