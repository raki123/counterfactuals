reach(0).
0.1::delayed(0).
0.1::delayed(Y) :- take(X,Y).
reach(Y) :- take(X,Y).
0.25::take(0,30);0.25::take(0,5);0.25::take(0,24);0.25::take(0,22):- reach(0), \+ delayed(0).
1.0::take(30,32):- reach(30), \+ delayed(30).
1.0::take(5,30):- reach(5), \+ delayed(5).
1.0::take(24,30):- reach(24), \+ delayed(24).
0.5::take(22,30);0.5::take(22,8):- reach(22), \+ delayed(22).
0.5::take(1,30);0.5::take(1,3):- reach(1), \+ delayed(1).
1.0::take(3,30):- reach(3), \+ delayed(3).
0.5::take(2,30);0.5::take(2,15):- reach(2), \+ delayed(2).
0.5::take(15,30);0.5::take(15,6):- reach(15), \+ delayed(15).
1.0::take(4,30):- reach(4), \+ delayed(4).
1.0::take(6,30):- reach(6), \+ delayed(6).
0.5::take(7,30);0.5::take(7,12):- reach(7), \+ delayed(7).
1.0::take(12,30):- reach(12), \+ delayed(12).
0.25::take(8,30);0.25::take(8,20);0.25::take(8,14);0.25::take(8,29):- reach(8), \+ delayed(8).
0.5::take(20,30);0.5::take(20,7):- reach(20), \+ delayed(20).
0.25::take(14,30);0.25::take(14,13);0.25::take(14,23);0.25::take(14,16):- reach(14), \+ delayed(14).
1.0::take(29,30):- reach(29), \+ delayed(29).
0.5::take(9,30);0.5::take(9,17):- reach(9), \+ delayed(9).
0.25::take(17,30);0.25::take(17,1);0.25::take(17,25);0.25::take(17,28):- reach(17), \+ delayed(17).
0.3333333333333333::take(10,30);0.3333333333333333::take(10,2);0.3333333333333333::take(10,19):- reach(10), \+ delayed(10).
0.3333333333333333::take(19,30);0.3333333333333333::take(19,4);0.3333333333333333::take(19,18):- reach(19), \+ delayed(19).
0.5::take(11,30);0.5::take(11,27):- reach(11), \+ delayed(11).
1.0::take(27,30):- reach(27), \+ delayed(27).
0.5::take(13,30);0.5::take(13,21):- reach(13), \+ delayed(13).
1.0::take(21,30):- reach(21), \+ delayed(21).
0.5::take(23,30);0.5::take(23,11):- reach(23), \+ delayed(23).
0.3333333333333333::take(16,30);0.3333333333333333::take(16,10);0.3333333333333333::take(16,9):- reach(16), \+ delayed(16).
0.5::take(25,30);0.5::take(25,26):- reach(25), \+ delayed(25).
1.0::take(28,30):- reach(28), \+ delayed(28).
1.0::take(18,30):- reach(18), \+ delayed(18).
1.0::take(26,30):- reach(26), \+ delayed(26).
