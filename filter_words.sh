cat wordlist.txt | grep -P "^[a-z]{3,16}$" | grep -P "[aeiouy]+" | grep -P "[^aeiouy]+" > list_filtered.txt
