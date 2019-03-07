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
cat majestic_all_possible_domains | pv -l -s $(wc -l majestic_all_possible_domains) | parallel --will-cite -j 20 -- dig {} @127.0.0.1 NS | gzip > dig.output.gz
```
