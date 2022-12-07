0.5::u1.
0.7::u2.
0.1::u3.
0.6::u4.
szn_spr_sum :- u1.
sprinkler :- szn_spr_sum, u2.
rain :- szn_spr_sum, u3.
rain :- \+szn_spr_sum, u4.
wet :- rain.
wet :- sprinkler.
slippery :- wet.
