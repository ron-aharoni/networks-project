#!/usr/bin/env python3

# this script requires python 3.7.2 at a minimum
#
# Usage: cat dig.results | python script.dig.py
# Usage: python script.dig.py dig.results 

import fileinput
from dataclasses import dataclass
import typing
import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

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


@dataclass(frozen=True)
class SOA(RR):
    rrtype = 'SOA'
    mname: str
    rname: str
    serial: int
    refresh: int
    retry: int
    expire: int
    neg_ttl: int

    @classmethod
    def parse_zone_line(cls, line):
        name, ttl, rrclass, rrtype, mname, rname, serial, refresh, retry, expire, neg_ttl = line.split(maxsplit=10)
        return cls(name=name, ttl=int(ttl), rrclass=rrclass, mname=mname, rname=rname, serial=int(serial), refresh=int(refresh), retry=int(retry), expire=int(expire), neg_ttl=int(neg_ttl))


def main():
    num_ns_records = 0
    num_glue_records = 0
    num_out_of_bailiwick_glue = 0
    num_loose_out_bailiwick_glue = 0
    num_domains = 0
    improper_glue = 0
    ns_records = {}
    glue_records = []
    is_nx = False
    num_nxdomain = 0
    num_emptys = 0
    has_soa = False
    has_only_soa = True
    num_soa_only = 0
    import csv
    writer = csv.writer(sys.stdout)
    writer.writerow(['Domain', 'Num NS records', 'Num glue records', 'Num out-of-bailiwick glue', 'Num loose-out-bailiwick glue'])
    current_domain = None
    for line in fileinput.input():
        if line.startswith('; <<>> DiG 9.12.3 <<>> '):
            current_domain = line.split()[5]

        if line.startswith(';; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN'):
            is_nx = True

        if line.startswith(';; MSG SIZE'):
            if is_nx:
                num_nxdomain += 1
                if ns_records or glue_records:
                    eprint('Anomolous NXDOMAIN with results: %s' % ns_records.values()[0].name)
            if not ns_records and not glue_records:
                num_emptys += 1

            if has_soa:
                if has_only_soa:
                    num_soa_only += 1
                else:
                    eprint('Got SOA record in nonempty zone: %s' % current_domain)

            num_domains += 1
            domain_ns_records = len(ns_records)
            num_ns_records += domain_ns_records

            domain_glue_records = len(glue_records)
            num_glue_records += domain_glue_records
            domain_out_of_bailiwick_glue = 0
            domain_loose_out_bailiwick_glue = 0
            for glue in glue_records:
                ns_record = ns_records.get(glue.name.lower())
                if ns_record is None:
                    improper_glue += 1
                elif ns_record.is_in_bailiwick():
                    pass
                else:
                    domain_out_of_bailiwick_glue += 1
                    if ns_record.shared_prefix() == '':
                        domain_loose_out_bailiwick_glue += 1

            num_out_of_bailiwick_glue += domain_out_of_bailiwick_glue
            num_loose_out_bailiwick_glue += domain_loose_out_bailiwick_glue

            writer.writerow([current_domain, domain_ns_records, domain_glue_records, domain_out_of_bailiwick_glue, domain_loose_out_bailiwick_glue])

            current_domain = None
            has_soa = False
            has_only_soa = True
            is_nx = False
            ns_records.clear()
            glue_records = []

        if line.startswith(';') or not line.strip():
            continue

        record = RR.from_zone_line(line.strip())
        if record is None:
            continue

        if record.rrtype == NS.rrtype:
            ns_records[record.nameserver.lower()] = record
            has_only_soa = False

        if record.rrtype == A.rrtype:
            glue_records.append(record)
            has_only_soa = False

        if record.rrtype == SOA.rrtype:
            has_soa = True

    eprint('Number of domains: %s' % num_domains)
    eprint('NXDOMAINs: %s' % num_nxdomain)
    eprint('Number of empty domains: %s' % num_emptys)
    eprint('Number of NS records: %s' % num_ns_records)
    eprint('Number of glue records: %s' % num_glue_records)
    eprint('Number of improper glue records: %s' % improper_glue)
    eprint('Out of bailiwick glue: %s' % num_out_of_bailiwick_glue)
    eprint('Loosely out of bailiwick glue: %s' % num_loose_out_bailiwick_glue)
    eprint('Number of SOA-only records: %s' % num_soa_only)


if __name__ == '__main__':
    main()
