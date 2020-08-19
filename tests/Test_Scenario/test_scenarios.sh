#!/bin/sh
# this is not a good solution, but it at least makes using test samples a bit easier
file_path=$1
file_name=$(basename "$file_path")
dir_name=$(dirname "$file_path")
#echo $file_name
#echo $dir_name
no_extension="${file_name%.*}"
#echo $no_extension
tmp_file="$dir_name/temp_$file_name"
cp $file_path $tmp_file
echo "### Please use the following input ###"
cat "$dir_name/$no_extension.input"
dyc start $tmp_file
output=`diff "$dir_name/$no_extension.verify" $tmp_file`
echo $output
if [ -z "$output" ];then
	echo "TEST PASSED";
else
	echo "TEST FAILED";
fi
rm $tmp_file
