A library to compare Magic: the Gathering mana Costs
====================================================
This is a small library for comparing MTG mana costs.

Usage
-----
This library uses a format similar to what the MTG Comprehensive rules use to signify mana costs

For example:

- {R}, {B}, {U}, {W}, {G} represent Red, Black, Blue, White and Green mana, respectively
- {P/R} represents Phyrexian mana (Either pay 2 life or 1 Red mana)
- {2/R} represents a mana cost you can pay with 1 mana of any color, or 1 red mana
- {R/B} represents a mana cost you can pay with either red or black maa

Because the primary purpose of this library is to search through mana costs, {P}, {C} and {X}
are treated as their own types of mana (even though they are not types of mana). Please dont file
a bug about it.

Snow Mana ({S}) isn't supported, since I don't like {S}

Disclaimer
----------
Right now this project should be considered to be alpha, which means that some comparisons might return
unintuitive results. Results of comparisons will likely change in the future as I add more test cases.
The way mana is compared is probably subject to change as well, as I suspect there are better ways to
do the comparison.
