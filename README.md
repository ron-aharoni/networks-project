# networks-project

To see a breakdown of domains in the majestic million by TLD, run:

```bash
tail -n +2 majestic_million.csv | cut -d, -f4 | sort | uniq -c | sort -r -n | less
```
