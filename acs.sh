#!/bin/ash

#This script is called by WebLCM to find the quietest channel for AP mode.
#The ACS algorithm is based on the BSS load data returned by `iw scan`. To test
#it, we can run it manually by setting the `band` and a scanning channel list


wlan="wlan0"
acs_db="/tmp/regulatory-for-acs.db"

BG_CHANNELS="1 2 3 4 5 6 7 8 9 10 11 12 13 14"
BG_FREQUENCIES="2412 2417 2422 2427 2432 2437 2442 2447 2452 2457 2462 2467 2472 2484"
#2_4g channels utilisation initialization
for ch in $BG_CHANNELS
do
  eval bg_channel_"$ch"=0
done


A_CHANNELS="36 40 44 48 52 56 60 64 100 104 108 112 116 \
			120 124 128 132 136 140 144 149 153 157 161 165"

A_FREQUENCIES="5180 5200 5220 5240 5260 5280 5300 5320 5500 5520 5540 5560 5580 \
			   5600 5620 5640 5660 5680 5700 5720 5745 5765 5785 5805 5845"

#5g channels utilisation initialization
for ch in $A_CHANNELS
do
  eval a_channel_"$ch"=0
done

#Valid channel list for the band per regulatory domain/country
a_channel_list=""
bg_channel_list=""

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

  if [ $3 -lt 3000 ] && [ $1 == "bg" ]
  then
    make_valid_bg_channel_list $2 $3 $4
  elif [ $2 -gt 3000 ] && [ $1 == "a" ]
  then
    make_valid_a_channel_list $2 $3 $4
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
        __width=`echo $line | awk '{ print $5 }'`
        __width=${__width::-2}
        make_valid_channel_list $1 $__start $__end $__width
      fi
    fi
  done 3<"$acs_db"

}

#Adjust channel utilisation based on a look-up table of signal strength.
function adjust_utilisation(){

  local  __weigh=0

  if [ $1 -gt -30 ]
  then
    __weigh=10
  elif [ $1 -gt -50 ]
  then
    __weigh=8
  elif [ $1 -gt -60 ]
  then
    __weigh=7
  elif [ $1 -gt -67 ]
  then
    __weigh=6
  elif [ $1 -gt -70 ]
  then
    __weigh=4
  elif [ $1 -gt -80 ]
  then
    __weigh=2
  elif [ $1 -gt -90 ]
  then
    __weigh=1
  fi

  return $__weigh
}

#Parameters:
#  $1: freq
#  S2: signal
#  $3: channel utilisation
function cal_channel_utilization(){


  case $1 in
	2412)
      bg_channel_1=$(($bg_channel_1+$2))
      ;;
    2417)
      bg_channel_2=$(($bg_channel_2+$2))
      ;;
    2422)
      bg_channel_3=$(($bg_channel_3+$2))
      ;;
    2427)
      bg_channel_4=$(($bg_channel_4+$2))
      ;;
    2432)
      bg_channel_5=$(($bg_channel_5+$2))
      ;;
    2437)
      bg_channel_6=$(($bg_channel_6+$2))
      ;;
    2442)
      bg_channel_7=$(($bg_channel_7+$2))
      ;;
    2447)
      bg_channel_8=$(($bg_channel_8+$2))
      ;;
    2452)
      bg_channel_9=$(($bg_channel_9+$2))
      ;;
    2457)
      bg_channel_10=$(($bg_channel_10+$2))
      ;;
    2462)
      bg_channel_11=$(($bg_channel_11+$2))
      ;;
    2467)
      bg_channel_12=$(($bg_channel_12+$2))
      ;;
    2472)
      bg_channel_13=$(($bg_channel_13+$2))
      ;;
    2484)
      bg_channel_14=$(($bg_channel_14+$2))
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

function find_quietest_channel(){

  local __quietest_channel=0
  local __min_utilisation=-1

  #If scanning_channels is not set, just use the generated valid channel list for the band;
  #If scanning_channels is set, need to check whether channels are valid for the band
  if [ x"$band" == x"bg" ]
  then
    if [ -z "$scanning_channels" ]
    then
      scanning_channels=$bg_channel_list
    else
      __tmp=""
      for c in $bg_channel_list
      do
        for k in $scanning_channels
        do
           if [ $c == $k ]
           then
             __tmp="$__tmp $c"
           fi
         done
      done
      scanning_channels=$__tmp
    fi
  else
    if [ -z "$scanning_channels" ]
    then
      scanning_channels=$a_channel_list
    else
      __tmp=""
      for c in $a_channel_list
      do
        for k in $scanning_channels
        do
           if [ $c == $k ]
           then
             __tmp="$tmp $c"
           fi
         done
      done
      scanning_channels=$__tmp
    fi
  fi

  for i in $scanning_channels
  do
    __ch=`eval echo "$""$band"_channel_"$i"`
    utilisation=$__ch
    if [ $__quietest_channel -eq 0 ] || [ $__min_utilisation -gt $utilisation ]
    then
       __min_utilisation=$utilisation
       __quietest_channel=$i
    fi
  done

  return $__quietest_channel
}

#In each data frame returned by iw scan, "freq" always comes first, and then "signal".
#"channel utilisation" comes last if it is advertized.
function do_scan() {

  iw $wlan scan | grep -E "freq|channel utilisation|signal" | {
  #For testing, we can save the result of `iw scan` first and then 'cat' it
  #cat aps | grep -E "freq|channel utilisation|signal" | {
    while read line
    do
      __first=`echo "$line" | awk '{ print $1 }'`
      __second=`echo "$line" | awk '{ print $2 }'`
      if [ "$__first" == "signal:" ]
      then
        __signal=`echo $line | awk '{ print $2 }' | awk '{ split($0, a,"."); print a[1] }'`
      elif [ "$__first" == "freq:" ]
      then
        __freq=$__second
      elif [ "$__second" == "channel" ]
      then
        __utilisation=`echo "$line" | awk '{ print $4 }' | awk '{ split($0, a,"/"); print a[1] }'`
        adjust_utilisation $__signal
        __adjusted_utilisation=$(($?*$__utilisation))
        __adjacent_utilisation=$((85*${__adjusted_utilisation}/100))
        __next_adjacent_utilisation=$((${__adjusted_utilisation}/2))

        cal_channel_utilization $(($__freq-10)) $__next_adjacent_utilisation
        cal_channel_utilization $(($__freq-5)) $__adjacent_utilisation
        cal_channel_utilization $__freq $__adjusted_utilisation
        cal_channel_utilization $(($__freq+5)) $__adjacent_utilisation
        cal_channel_utilization $(($__freq+10)) $__next_adjacent_utilisation
      fi
    done

    #No valid BSS load found
    if [ -z ${__utilisation+x} ]
    then
        exit 255
    fi

    find_quietest_channel
    return $?
  }
}

function help(){
  echo 'Help: you have to specify the band[a|bg], and/or a scanning channel list if needed'
  echo './acs bg'
  echo './acs bg "1 6 11"'
  echo './acs a "32 52 100 112 161"'
  echo 'It will return the first channel with min utilisation.'
  exit 0
}

if [ $# -eq 0 ]
then
  help
fi

band=$1
if [ $band != "a" ] && [ $band != "bg" ]
then
  help
fi

scanning_channels=$2

iw reg get > $acs_db

get_valid_channel_list $1
do_scan

#Pipe it to weblcm
echo $?

exit 0
