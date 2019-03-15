# networks-project

To see a breakdown of domains in the majestic million by TLD, run:

```bash
tail -n +2 majestic_million.csv | cut -d, -f4 | sort | uniq -c | sort -r -n | less
```

## Zone file access

Governed by ICANN, all gtlds must provide some form of access:

https://www.icann.org/resources/pages/zfa-2013-06-28-en

There are many anecdotes that registries will try to force extra terms, in which case a complaint should be filed:

https://forms.icann.org/en/resources/compliance/registries/zfa/form

## Data collection from MM

```bash
cat majestic_million.csv | python3 script.alldomains.py | pv -l -s $(wc -l majestic_all_possible_domains) | parallel --will-cite -j 20 -- dig {} @127.0.0.1 NS | gzip > dig.output.gz
```

## Ranking statistics.csv

```bash
gzcat dig.output.gz | pv -l | python3 script.zone.py
tail -n+2 raw_results.csv | sort -t, -k1 | pv -l | cat > sorted_results.csv
tail -n+2 majestic_million.csv | sort -t, -k3 | pv -l | cat > sorted_majestic.csv
join -t, -o 2.1,0,1.2,1.3,1.4,1.5 -1 1 -2 3 sorted_results.csv sorted_majestic.csv | sort -t, -k1 -n | pv -l | cat <(echo $'Majestic Million Rank,Domain,Num NS records,Num glue records,Num out-of-bailiwick glue,Num loose-out-bailiwick glue') - > collated_results.csv
```

## Sanity checks

```bash
# check the number of NS records
zgrep -E -e '^[^;]+(\t| )NS(\t| )' dig.output.gz | wc -l
# check the most common nameservers
zgrep -E -e '^[^;]+(\t| )NS(\t| )' dig.output.gz | tr ' ' $'\t' | tr -s $'\t' | cut -f 5 | sort | uniq -c | sort -r -n > ns.popular
# check for NS records that are actually IP addresses
zgrep -E -e '^[^;]+(\t| )NS(\t| )' dig.output.gz | tr ' ' $'\t' | tr -s $'\t' | cut -f 5 | grep -E -e '^[0-9.]*$' | sort | wc -l
```
