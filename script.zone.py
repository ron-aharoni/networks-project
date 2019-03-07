#!/usr/bin/env python3

# this script requires python 3.7.2 at a minimum
#
# Usage: cat zone.file | python script.zone.py
# Usage: python script.zone.py zone.file 

import fileinput
from dataclasses import dataclass
import typing
from collections import defaultdict
from collections import Counter


@dataclass(frozen=True)
class RR:
    rrtype: typing.ClassVar[str] = NotImplemented
    name: str
    ttl: int
    rrclass: str

    @classmethod
    def from_zone_line(cls, line):
        try:
            tokens = line.split()
            # name ttl class rrtype rdata
            line_rrtype = tokens[3]
            for rrtype in cls.__subclasses__():
                if rrtype.rrtype == line_rrtype:
                    return rrtype.parse_zone_line(line)

            # We ignore record types we don't care about
            return None
        except Exception:
            print('Error parsing %s' % line)
            return None


@dataclass(frozen=True)
class A(RR):
    rrtype = 'A'
    ip: str

    @classmethod
    def parse_zone_line(cls, line):
        name, ttl, rrclass, rrtype, ip = line.split(maxsplit=4)
        return cls(name=name, ttl=int(ttl), rrclass=rrclass, ip=ip)


@dataclass(frozen=True)
class AAAA(RR):
    rrtype = 'AAAA'
    ip: str

    @classmethod
    def parse_zone_line(cls, line):
        name, ttl, rrclass, rrtype, ip = line.split(maxsplit=4)
        return cls(name=name, ttl=int(ttl), rrclass=rrclass, ip=ip)


@dataclass(frozen=True)
class NS(RR):
    rrtype = 'NS'
    nameserver: str

    @classmethod
    def parse_zone_line(cls, line):
        name, ttl, rrclass, rrtype, nameserver = line.split(maxsplit=4)
        return cls(name=name, ttl=int(ttl), rrclass=rrclass, nameserver=nameserver)

    def is_in_bailiwick(self):
        return self.nameserver.endswith(self.name)

    def shared_prefix(self):
        result = []
        for lhs, rhs in zip(reversed(self.name.split('.')), reversed(self.nameserver.split('.'))):
            if lhs != rhs:
                break
            result.append(lhs)

        return '.'.join(reversed(result))


@dataclass(frozen=True)
class CNAME(RR):
    rrtype = 'CNAME'
    canonical_name: str

    @classmethod
    def parse_zone_line(cls, line):
        name, ttl, rrclass, rrtype, canonical_name = line.split(maxsplit=4)
        return cls(name=name, ttl=int(ttl), rrclass=rrclass, canonical_name=canonical_name)


def main():
    zone_records = []
    num_lines = 0
    for line in fileinput.input():
        num_lines += 1
        if not line.strip():
            continue

        record = RR.from_zone_line(line.strip())
        if record is None:
            continue

        zone_records.append(record)

    print('read %s records out of %s lines' % (len(zone_records), num_lines))
    records_by_name_and_type = defaultdict(lambda: defaultdict(set))
    for record in zone_records:
        records_by_name_and_type[record.name][record.rrtype].add(record)

    num_ns = 0
    missing_ns = 0
    missing_glue = 0
    missing_ipv4_glue = 0
    missing_ipv6_glue = 0
    in_bailiwick_ns = 0
    out_of_bailiwick_ns = 0
    ancestral_bailiwick_ns = 0
    popular_nameservers = Counter()
    for name, records_by_type in records_by_name_and_type.items():
        ns_records = records_by_type.get('NS')
        if ns_records is None:
            missing_ns += 1
            continue

        num_ns += len(ns_records)
        for ns in ns_records:
            missing_ipv4 = False
            missing_ipv6 = False

            if ns.is_in_bailiwick():
                in_bailiwick_ns += 1
            else:
                if ns.shared_prefix() != '':
                    ancestral_bailiwick_ns += 1
                out_of_bailiwick_ns += 1

            popular_nameservers.update({ns.nameserver: 1})

            records_by_type = records_by_name_and_type.get(ns.nameserver)
            if records_by_type is None:
                records_by_type = defaultdict(set)

            a_records = records_by_type.get('A')
            if a_records is None:
                missing_ipv4 = True
                missing_ipv4_glue += 1

            aaaa_records = records_by_type.get('AAAA')
            if aaaa_records is None:
                missing_ipv6 = True
                missing_ipv6_glue += 1

            if missing_ipv4 and missing_ipv6:
                missing_glue += 1

    print('Out of %d domains:' % (len(records_by_name_and_type) - missing_ns))
    print('NS records total: %d' % num_ns)
    print('missing glue records: %d' % missing_glue)
    print('ipv4 only NS records: %d' % missing_ipv6_glue)
    print('ipv6 only NS glue: %d' % missing_ipv4_glue)
    print('')
    print('in bailiwick NS: %d' % in_bailiwick_ns)
    print('ancestral bailiwick NS: %d' % ancestral_bailiwick_ns)
    print('out of bailiwick NS: %d' % out_of_bailiwick_ns)
    print('')
    print('10 most popular nameservers:')
    for ns, count in popular_nameservers.most_common(10):
        print('%d %s' % (count, ns))


if __name__ == '__main__':
    main()
