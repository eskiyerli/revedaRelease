*
.SUBCKT newckt a b c
+ PARAM: res = 1k
* new subckt
R a b {res}
C b c 1pF
.ENDS
