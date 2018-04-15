#!/bin/bash
chmod u+x ./fr
./fr if=patch.img of=/dev/$1 len=4 of_offset=440
./fr if=patch.img of=/dev/$1 len=1 of_offset=466 if_offset=4
