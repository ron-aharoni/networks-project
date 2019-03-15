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


def main2():
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
    output_file = 'raw_results.csv'
    f = open(output_file, 'w')
    writer = csv.writer(f)
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
                    print('Anomolous NXDOMAIN with results: %s' % ns_records.values()[0].name)
            if not ns_records and not glue_records:
                num_emptys += 1

            if has_soa:
                if has_only_soa:
                    num_soa_only += 1
                else:
                    print('Got SOA record in nonempty zone: %s' % current_domain)

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

    f.close()
    print('Number of domains: %s' % num_domains)
    print('NXDOMAINs: %s' % num_nxdomain)
    print('Number of empty domains: %s' % num_emptys)
    print('Number of NS records: %s' % num_ns_records)
    print('Number of glue records: %s' % num_glue_records)
    print('Number of improper glue records: %s' % improper_glue)
    print('Out of bailiwick glue: %s' % num_out_of_bailiwick_glue)
    print('Loosely out of bailiwick glue: %s' % num_loose_out_bailiwick_glue)
    print('Number of SOA-only records: %s' % num_soa_only)


@dataclass()
class Statistics:
    num_ns: int = 0
    missing_ns: int = 0
    missing_glue: int = 0
    missing_ipv4_glue: int = 0
    missing_ipv6_glue: int = 0
    in_bailiwick_ns: int = 0
    out_of_bailiwick_ns: int = 0
    ancestral_bailiwick_ns: int = 0

    strictly_in_bailiwick: int = 0
    strictly_out_of_bailiwick: int = 0
    strictly_mixed_bailiwick: int = 0

    loosely_in_bailiwick: int = 0
    loosely_out_of_bailiwick: int = 0
    loosely_mixed_bailiwick: int = 0


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

    statistics = Statistics()

    popular_nameservers = Counter()
    popular_services = Counter()
    for name, records_by_type in records_by_name_and_type.items():
        ns_records = records_by_type.get('NS')
        if ns_records is None:
            statistics.missing_ns += 1
            continue

        statistics.num_ns += len(ns_records)
        strictly_has_in_bailiwick = False
        strictly_has_out_of_bailiwick = False
        loosely_has_in_bailiwick = False
        loosely_has_out_of_bailiwick = False
        for ns in ns_records:
            missing_ipv4 = False
            missing_ipv6 = False

            if ns.is_in_bailiwick():
                statistics.in_bailiwick_ns += 1
                strictly_has_in_bailiwick = True
                loosely_has_in_bailiwick = True
            else:
                if ns.shared_prefix() != '':
                    statistics.ancestral_bailiwick_ns += 1
                    loosely_has_in_bailiwick = True
                else:
                    loosely_has_out_of_bailiwick = True
                statistics.out_of_bailiwick_ns += 1
                strictly_has_out_of_bailiwick = True

            popular_nameservers.update({ns.nameserver: 1})
            popular_services.update({'.'.join(ns.nameserver.split('.')[1:]): 1})

            records_by_type = records_by_name_and_type.get(ns.nameserver)
            if records_by_type is None:
                records_by_type = defaultdict(set)

            a_records = records_by_type.get('A')
            if a_records is None:
                missing_ipv4 = True
                statistics.missing_ipv4_glue += 1

            aaaa_records = records_by_type.get('AAAA')
            if aaaa_records is None:
                missing_ipv6 = True
                statistics.missing_ipv6_glue += 1

            if missing_ipv4 and missing_ipv6:
                statistics.missing_glue += 1

        if strictly_has_in_bailiwick and strictly_has_out_of_bailiwick:
            statistics.strictly_mixed_bailiwick += 1
        elif strictly_has_in_bailiwick:
            statistics.strictly_in_bailiwick += 1
        elif strictly_has_out_of_bailiwick:
            statistics.strictly_out_of_bailiwick += 1
        else:
            assert False, 'cannot happen'

        if loosely_has_in_bailiwick and loosely_has_out_of_bailiwick:
            statistics.loosely_mixed_bailiwick += 1
        elif loosely_has_in_bailiwick:
            statistics.loosely_in_bailiwick += 1
        elif loosely_has_out_of_bailiwick:
            statistics.loosely_out_of_bailiwick += 1
        else:
            assert False, 'cannot happen'

    print('Out of %d domains:' % (len(records_by_name_and_type) - statistics.missing_ns))
    print('NS records total: %d' % statistics.num_ns)
    print('missing glue records: %d' % statistics.missing_glue)
    print('ipv4 only NS records: %d' % statistics.missing_ipv6_glue)
    print('ipv6 only NS glue: %d' % statistics.missing_ipv4_glue)
    print('')
    print('in bailiwick NS: %d' % statistics.in_bailiwick_ns)
    print('ancestral bailiwick NS: %d' % statistics.ancestral_bailiwick_ns)
    print('out of bailiwick NS: %d' % statistics.out_of_bailiwick_ns)
    print('')
    print('strictly in domains: %d' % statistics.strictly_in_bailiwick)
    print('strictly mixed domains: %d' % statistics.strictly_mixed_bailiwick)
    print('strictly out domains: %d' % statistics.strictly_out_of_bailiwick)
    print('')
    print('loosely in domains: %d' % statistics.loosely_in_bailiwick)
    print('loosely mixed domains: %d' % statistics.loosely_mixed_bailiwick)
    print('loosely out domains: %d' % statistics.loosely_out_of_bailiwick)
    print('')
    NUM_POPULAR=5
    print('%d most popular nameservers:' % NUM_POPULAR)
    for ns, count in popular_nameservers.most_common(NUM_POPULAR):
        print('%d %s' % (count, ns))
    print('%d most popular services:' % NUM_POPULAR)
    for ns, count in popular_services.most_common(NUM_POPULAR):
        print('%d %s' % (count, ns))


if __name__ == '__main__':
    main2()
