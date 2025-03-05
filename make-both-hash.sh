#!/bin/bash

input1="Processed/excludes-hash.txt"
input2="Others/Rick/FB/excludes-hash.txt"
output="Others/Both/fb/excludes-hash.txt"

{
  cat "$input1"
  # echo -e "\r"
  cat "$input2"
  # echo -e "\r"
} > "$output"
