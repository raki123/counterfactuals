reach(0).
0.1::delayed(0).
0.1::delayed(Y) :- take(X,Y).
reach(Y) :- take(X,Y).
0.5::take(0,40);0.5::take(0,1):- reach(0), \+ delayed(0).
1.0::take(40,42):- reach(40), \+ delayed(40).
0.3333333333333333::take(1,40);0.3333333333333333::take(1,25);0.3333333333333333::take(1,24):- reach(1), \+ delayed(1).
0.5::take(25,40);0.5::take(25,13):- reach(25), \+ delayed(25).
0.5::take(24,40);0.5::take(24,38):- reach(24), \+ delayed(24).
1.0::take(2,40):- reach(2), \+ delayed(2).
1.0::take(3,40):- reach(3), \+ delayed(3).
1.0::take(4,40):- reach(4), \+ delayed(4).
0.5::take(5,40);0.5::take(5,2):- reach(5), \+ delayed(5).
0.3333333333333333::take(6,40);0.3333333333333333::take(6,4);0.3333333333333333::take(6,36):- reach(6), \+ delayed(6).
0.5::take(36,40);0.5::take(36,5):- reach(36), \+ delayed(36).
1.0::take(7,40):- reach(7), \+ delayed(7).
1.0::take(8,40):- reach(8), \+ delayed(8).
1.0::take(9,40):- reach(9), \+ delayed(9).
0.3333333333333333::take(10,40);0.3333333333333333::take(10,22);0.3333333333333333::take(10,37):- reach(10), \+ delayed(10).
1.0::take(22,40):- reach(22), \+ delayed(22).
1.0::take(37,40):- reach(37), \+ delayed(37).
0.5::take(11,40);0.5::take(11,17):- reach(11), \+ delayed(11).
1.0::take(17,40):- reach(17), \+ delayed(17).
0.16666666666666666::take(12,40);0.16666666666666666::take(12,15);0.16666666666666666::take(12,16);0.16666666666666666::take(12,19);0.16666666666666666::take(12,31);0.16666666666666666::take(12,32):- reach(12), \+ delayed(12).
1.0::take(15,40):- reach(15), \+ delayed(15).
0.5::take(16,40);0.5::take(16,8):- reach(16), \+ delayed(16).
1.0::take(19,40):- reach(19), \+ delayed(19).
1.0::take(31,40):- reach(31), \+ delayed(31).
0.3333333333333333::take(32,40);0.3333333333333333::take(32,29);0.3333333333333333::take(32,27):- reach(32), \+ delayed(32).
1.0::take(13,40):- reach(13), \+ delayed(13).
0.5::take(14,40);0.5::take(14,11):- reach(14), \+ delayed(14).
0.5::take(18,40);0.5::take(18,33):- reach(18), \+ delayed(18).
1.0::take(33,40):- reach(33), \+ delayed(33).
0.5::take(20,40);0.5::take(20,3):- reach(20), \+ delayed(20).
0.5::take(21,40);0.5::take(21,6):- reach(21), \+ delayed(21).
0.3333333333333333::take(23,40);0.3333333333333333::take(23,12);0.3333333333333333::take(23,39):- reach(23), \+ delayed(23).
0.5::take(39,40);0.5::take(39,14):- reach(39), \+ delayed(39).
0.5::take(38,40);0.5::take(38,23):- reach(38), \+ delayed(38).
0.3333333333333333::take(26,40);0.3333333333333333::take(26,34);0.3333333333333333::take(26,10):- reach(26), \+ delayed(26).
0.25::take(34,40);0.25::take(34,20);0.25::take(34,35);0.25::take(34,30):- reach(34), \+ delayed(34).
0.3333333333333333::take(27,40);0.3333333333333333::take(27,7);0.3333333333333333::take(27,26):- reach(27), \+ delayed(27).
0.5::take(28,40);0.5::take(28,9):- reach(28), \+ delayed(28).
1.0::take(29,40):- reach(29), \+ delayed(29).
0.25::take(30,40);0.25::take(30,28);0.25::take(30,18);0.25::take(30,21):- reach(30), \+ delayed(30).
1.0::take(35,40):- reach(35), \+ delayed(35).
