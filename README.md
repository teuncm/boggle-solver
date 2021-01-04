
## A Solver For  Boggle
Boggle is a game where players attempt to find words in sequences of adjacent letters on lettered dice. Games are played on a 4x4 grid. The goal of the game is to score as many points as possible within the given timeframe. Words must contain at least 3 characters; more characters being worth more points. Further information is to be found on [Wikipedia](https://en.wikipedia.org/wiki/Boggle).

In this project we create a solver for the Dutch variation of the game using a Dutch word list. The list was obtained from [OpenTaal](https://github.com/OpenTaal/opentaal-wordlist). The main OpenTaal file (*wordlist.txt*) contains many words and their inflections. In total there are 413283 entries. As inflections are allowed in the game (and often allow one to score the most points!), this word list is perfect for our implementation. However, the list also contains many abbreviations, proper nouns and words with non-alphabetic characters or spaces. Therefore, we preprocess it using Bash:
```bash
cat wordlist.txt | grep -P "^[a-z]{3,16}$" | grep -P "[aeiouy]+" | grep -P "[^aeiouy]+" > list_filtered.txt
```
Now, the list only contains lowercase words between 3 and 16 characters (inclusive). All words contain at least one vowel and at least one consonant. This amounts to a total of 308991 entries.

Even now, some OpenTaal entries are still abbreviations, but we have no way of mass distinguishing them against our target words. As this originates from the OpenTaal list itself, we cannot do anything to further filter the final undesired words.

The user will be able to specify the board size, and whether to use diagonals in the search. Additionally, the user is able to specify a fixed or random Boggle board of arbitrary size. The random implementation draws from the 16 dice in the original game.

## Implementation
The word search is done iteratively using a depth-first strategy. We maintain a stack of possible character sets throughout the run. We first push a list of all grid cells on the stack (these are our possible starting points).

We further utilize the stack by retrieving the next character for our search each iteration. At any iteration, we will have a tentative character sequence and a list of options for the next character cells. Once we are done exploring a sequence, we use the stack to backtrack to a sequence with a different ending and start exploring all options from there.

Note that it is disallowed to use the same die twice in one sequence. After the first character, we can thus explore at most 7 options every step. Logically, the overall state space will grow exponentially for bigger grids and larger sequence lengths. We therefore have to implement some way of pruning in order to run the program efficiently.

Luckily, our word list contains many inflections. We can thus heavily prune our search by saving all possible word truncations (up to the full words themselves), stopping our search as soon as we don't match any of these truncations. Example: *aalfuik* and *aaltje* truncate the same up to *aal*. Similarly, *lopend* and *lopende* truncate the same up to *lopend*. As many inflections and similar words contain similar subsets of letters, the memory overhead of this approach will likely not be large.

### Pseudocode
```python
options_stack = [initial_cells]
cur_path = [None]
# Once the options stack is empty, we no longer have any options to explore for our first character position. Our search will be done.
while not options_stack.empty():
	# Retrieve all options for the current character position.
	cell_options = options_stack[-1]
	if not cell_options:
		options_stack.pop()
		cur_path.pop()
		continue

	# Obtain the first option for the current character position.
	cur_cell = cell_options.pop()
	cur_path[-1] = cur_cell

	# Insert this option into the word and check against the dictionary.
	cur_word = get_cur_word(cur_path)
	if cur_word not in truncations:
		continue
	elif cur_word in dictionary:
		print('Found a word!')

	# Retrieve all options for the next character position.
	neighbors = get_valid_neighbors(cur_path)
	if neighbors:
		options_stack.append(neighbors)
		cur_path.append(None)
```
### Complexity analysis
The actual implementation keeps a character list at every step and thus constructing a word takes $O(1)$ steps instead of $O(n)$. For all steps of the pathfinding:
* Retrieving next cell (stack peek / pop): $O(1)$
* Constructing current word (using current character list): $O(1)$
* Current word lookup (using Python dictionary): $O(1)$
* Retrieving valid neighbors (always <= 8 options): $O(1)$

Even though the individual steps are efficient, the number of iterations the program needs to run for is bounded by the size of the state space. We calculate this exactly in the results. Using the truncation pruning method, the number of steps is now further bounded by the size and complexity of the words inside the word list instead.

Finally we will attempt to find the highest and lowest scoring boards using a greedy search. We can reuse the truncation dictionary while slightly modifying our board setup to run our algorithm efficiently each iteration.

To perform the search, we make use of one board mutation: we randomly change the face of one of the dice and then swap this modified die with a random, different die on the board. We then calculate the board score. If the current board score is larger than the best board score so far, we save the current board instead. As the search space is non-convex, this algorithm will not guarantee a global optimum.

## Results
The total number of entries in our filtered word list is 308991. Assuming that every truncation is unique, the truncation dictionary should contain $n+1 \choose 2$ entries per word of length $n$. The truncation dictionary should then contain 21004363 entries. As the words overlap in many cases (and therefore many truncations are not unique), the truncation dictionary in practice only contains a total of 978676 entries! I found it consumes about 0.1GB of RAM on my machine, so it is viable on the modern day computer.

### Sample runs
#### Random board, default settings
```
$ python3 main.py

Board: EICE JAAI VSKR BREP

E I C E
J A A I
V S K R
B R E P

101 word(s), 139 point(s)!
-------------------------
aak - 1
aar - 1
aas - 1
[...]
vaasje - 3
karpers - 5
vakpers - 5
```
#### No diagonal neighbors
```
$ python3 main.py --board ap en --neighbors no_diag

Board: AP EN

A P
E N

0 word(s), 0 point(s)!
-------------------------
```
#### Larger grid, random characters (no dice)
```
$ python3 main.py --size 7 --gen random

Board: OIPYXSR PABDENA EYXNUNA XLTNDHG VCALKDS ISGQURI WYKGEMM

O I P Y X S R
P A B D E N A
E Y X N U N A
X L T N D H G
V C A L K D S
I S G Q U R I
W Y K G E M M

244 word(s), 364 point(s)!
-------------------------
aan - 1
aar - 1
aas - 1
[...]
handdruk - 11
scannend - 11
simulant - 11
```

### State Space
We can calculate the size of the state space by disabling any pruning. The program will explore every possible sequence of states with any length using the game rules. By counting these steps, we obtain the state space for several grid sizes.

First, we find the state space using all neighbors:

#### Using --neighbors all
grid|state space
-|-
1x1|1
2x2|64
3x3|10305
4x4|12029640
5x5|...

It is also possible to calculate the state space using the *--neighbors no_diag* option. Clearly, the state space size still exponentially increases with the grid size, albeit less extremely than before:

#### Using --neighbors no_diag
grid|state space
-|-
1x1|1
2x2|28
3x3|653
4x4|28512
5x5|3060417
6x6|873239772
7x7|...

We can limit the maximum sequence length in our search. This gives us a better picture of the number of steps the algorithm involves. We do this on the traditional 4x4 grid and obtain:

#### Using --neighbors all, 4x4 grid
max seq. length|state space
-|-
1|16
2|100
3|508
4|2272
5|8984
6|31656
7|99928
8|283400
9|720384
10|1626160
11|3220808
12|5531072
13|8175592
14|10425784
15|11686456
16|12029640

#### Using --neighbors no_diag, 4x4 grid
max seq. length|state space
-|-
1|16
2|64
3|168
4|400
5|832
6|1632
7|2880
8|4856
9|7496
10|11192
11|15288
12|20040
13|23816
14|26728
15|27960
16|28512

We can see that the state space stops increasing rapidly towards a larger maximum sequence length. Note that the results for a maximum sequence length of 16 correspond to our grid size experiments for a 4x4 grid (as this is trivially the largest possible sequence).

### Highscores
The highest scores so far were found to be obtained by the following boards:
```
3675 points: EDAS NLRT IEEO GNVB
3432 points: BGNS EIET VLRE OEDN
3313 points: VERS NLET EDIG GNER
```
It turns out that there exist many boards that don't score any points at all. Examples are:
```
0 points: LPRH DSWG JZMZ NWSX
0 points: EIXI EIAI EEEO EIEO
0 points: PSNB DDHK IFGY OZCO
```

### Path plots
The *--display fancy* option generates these fancy command-line plots to help find the word paths.
![](https://i.imgur.com/j8FlCEV_d.webp)
