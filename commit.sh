#!/bin/bash
titolo=$(date +%Y-%m-%d_%H:%M:%S)
echo $titolo
git add *
git commit -m $titolo
git push -u origin master
git add -u
git commit -m "old files removed"
git push -u origin master