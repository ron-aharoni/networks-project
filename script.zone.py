#!/usr/bin/env python3

# this script requires python 3.7.2 at a minimum
#
# Usage: cat zone.file | python script.zone.py
# Usage: python script.zone.py zone.file 

import fileinput
from dataclasses import dataclass
import typing
from collections import defaultdict


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
        if not line:
            continue

        record = RR.from_zone_line(line.strip())
        if record is None:
            continue

        zone_records.append(record)

    print('read %s records out of %s lines' % (len(zone_records), num_lines))
    records_by_name_and_type = defaultdict(lambda: defaultdict(set))
    for record in zone_records:
        records_by_name_and_type[record.name][record.rrtype].add(record)

    missing_ns = 0
    missing_glue = 0
    missing_ipv4_glue = 0
    missing_ipv6_glue = 0
    for name, records_by_type in records_by_name_and_type.items():
        ns_records = records_by_type.get('NS')
        if ns_records is None:
            missing_ns += 1
            continue

        for ns in ns_records:
            missing_ipv4 = False
            missing_ipv6 = False

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

        if missing_glue > 0:
            break

    print('Out of %d domains:' % (len(records_by_name_and_type) - missing_ns))
    print('missing glue records: %d' % missing_glue)
    print('ipv4 only NS records: %d' % missing_ipv6_glue)
    print('ipv6 only NS glue: %d' % missing_ipv4_glue)


if __name__ == '__main__':
    main()
