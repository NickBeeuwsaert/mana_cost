A library to compant Magic: the Gathering|trade| Mana Costs
===========================================================
This is a small library for comparing MTG mana costs.

Usage
-----
This library uses a format similar to what the MTG Comprehensive rules use to signify mana costs

For example:

- {R}, {B}, {U}, {W}, {G} represent Red, Black, Blue, White and Green mana, respectively
- {P/R} represents Phyrexian mana (Either pay 2 life or 1 Red mana)
- {2/R} represents a mana cost you can pay with 1 mana of any color, or 1 red mana
- {R/B} represents a mana cost you can pay with either red or black maa

Because the primary purpose of this library is to search through mana costs, {P} and {X}
are treated as their own types of mana (even though they are not types of mana). Please dont file
a bug about it.

Colorless mana {C} and Snow Mana {S} aren't current supported, since {C} can just be represented with {1}
and I don't like {S}
