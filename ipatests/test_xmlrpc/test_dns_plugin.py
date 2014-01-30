# Authors:
#   Pavel Zuna <pzuna@redhat.com>
#
# Copyright (C) 2010  Red Hat
# see file 'COPYING' for use and warranty information
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Test the `ipalib/plugins/dns.py` module.
"""

import nose
from ipalib import api, errors
from ipapython.dn import DN
from ipatests.test_xmlrpc import objectclasses
from xmlrpc_test import Declarative, fuzzy_digits, fuzzy_uuid

zone1 = u'dnszone.test'
zone1_ip = u'172.16.29.111'
zone1_dn = DN(('idnsname',zone1), api.env.container_dns, api.env.basedn)
zone1_ns = u'ns1.%s.' % zone1
zone1_ns_dn = DN(('idnsname','ns1'), zone1_dn)
zone1_rname = u'root.%s.' % zone1
zone1_permission = u'Manage DNS zone %s' % zone1
zone1_permission_dn = DN(('cn',zone1_permission),
                            api.env.container_permission,api.env.basedn)
zone1_txtrec_dn = DN(('idnsname', '_kerberos'), zone1_dn)

zone2 = u'zone2.test'
zone2_dn = DN(('idnsname', zone2), api.env.container_dns, api.env.basedn)
zone2_ns = u'ns1.%s.' % zone2
zone2_rname = u'root.%s.' % zone2

revzone1 = u'31.16.172.in-addr.arpa.'
revzone1_ip = u'172.16.31.0'
revzone1_ipprefix = u'172.16.31.'
revzone1_dn = DN(('idnsname', revzone1), api.env.container_dns, api.env.basedn)

revzone2 = u'30.15.172.in-addr.arpa.'
revzone2_ip = u'172.15.30.0/24'
revzone2_dn = DN(('idnsname',revzone2), api.env.container_dns, api.env.basedn)

name1 = u'testdnsres'
name1_dn = DN(('idnsname',name1), zone1_dn)
name1_renamed = u'testdnsres-renamed'

revname1 = u'80'
revname1_ip = revzone1_ipprefix + revname1
revname1_dn = DN(('idnsname',revname1), revzone1_dn)

revname2 = u'81'
revname2_ip = revzone1_ipprefix + revname2
revname2_dn = DN(('idnsname',revname2), revzone1_dn)

cname = u'testcnamerec'
cname_dn = DN(('idnsname',cname), zone1_dn)

dname = u'testdns-dname'
dname_dn = DN(('idnsname',dname), zone1_dn)

arec1 = u'172.16.29.111'
arec2 = u'172.31.254.222'
arec3 = u'172.16.250.123'

fwd_ip = u'172.16.31.80'
allowtransfer_tofwd = u'%s;' % fwd_ip

allowquery_restricted_in = u'!192.0.2/24;any;'
allowquery_restricted_out = u'!192.0.2.0/24;any;'

class test_dns(Declarative):

    @classmethod
    def setUpClass(cls):
        super(test_dns, cls).setUpClass()

        if not api.Backend.rpcclient.isconnected():
            api.Backend.rpcclient.connect(fallback=False)
        try:
           api.Command['dnszone_add'](zone1,
               idnssoamname = zone1_ns,
               idnssoarname = zone1_rname,
               force = True,
           )
           api.Command['dnszone_del'](zone1)
        except errors.NotFound:
            raise nose.SkipTest('DNS is not configured')
        except errors.DuplicateEntry:
            pass

    cleanup_commands = [
        ('dnszone_del', [zone1, zone2, revzone1, revzone2],
            {'continue': True}),
        ('dnsconfig_mod', [], {'idnsforwarders' : None,
                               'idnsforwardpolicy' : None,
                               'idnsallowsyncptr' : None,
                               }),
        ('permission_del', [zone1_permission], {'force': True}),
    ]

    tests = [

        dict(
            desc='Try to retrieve non-existent zone %r' % zone1,
            command=('dnszone_show', [zone1], {}),
            expected=errors.NotFound(
                reason=u'%s: DNS zone not found' % zone1),
        ),


        dict(
            desc='Try to update non-existent zone %r' % zone1,
            command=('dnszone_mod', [zone1], {'idnssoaminimum': 3500}),
            expected=errors.NotFound(
                reason=u'%s: DNS zone not found' % zone1),
        ),


        dict(
            desc='Try to delete non-existent zone %r' % zone1,
            command=('dnszone_del', [zone1], {}),
            expected=errors.NotFound(
                reason=u'%s: DNS zone not found' % zone1),
        ),


        dict(
            desc='Try to create zone with invalid name',
            command=(
                'dnszone_add', [u'invalid zone'], {
                    'idnssoamname': zone1_ns,
                    'idnssoarname': zone1_rname,
                    'ip_address' : zone1_ip,
                }
            ),
            expected=errors.ValidationError(name='name',
                error=u'only letters, numbers, and - are allowed. ' +
                    u'DNS label may not start or end with -'),
        ),


        dict(
            desc='Create zone %r' % zone1,
            command=(
                'dnszone_add', [zone1], {
                    'idnssoamname': zone1_ns,
                    'idnssoarname': zone1_rname,
                    'ip_address' : zone1_ip,
                }
            ),
            expected={
                'value': zone1,
                'summary': None,
                'result': {
                    'dn': zone1_dn,
                    'idnsname': [zone1],
                    'idnszoneactive': [u'TRUE'],
                    'idnssoamname': [zone1_ns],
                    'nsrecord': [zone1_ns],
                    'idnssoarname': [zone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowdynupdate': [u'FALSE'],
                    'idnsupdatepolicy': [u'grant %(realm)s krb5-self * A; '
                                         u'grant %(realm)s krb5-self * AAAA; '
                                         u'grant %(realm)s krb5-self * SSHFP;'
                                         % dict(realm=api.env.realm)],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                    'objectclass': objectclasses.dnszone,
                },
            },
        ),


        dict(
            desc='Try to create duplicate zone %r' % zone1,
            command=(
                'dnszone_add', [zone1], {
                    'idnssoamname': zone1_ns,
                    'idnssoarname': zone1_rname,
                    'ip_address' : zone1_ip,
                }
            ),
            expected=errors.DuplicateEntry(
                message=u'DNS zone with name "%s" already exists' % zone1),
        ),

        dict(
            desc='Try to create a zone with nonexistent NS entry',
            command=(
                'dnszone_add', [zone2], {
                    'idnssoamname': zone2_ns,
                    'idnssoarname': zone2_rname,
                }
            ),
            expected=errors.NotFound(reason='Nameserver \'%s\' does not have a corresponding A/AAAA record' % (zone2_ns)),
        ),

        dict(
            desc='Create a zone with nonexistent NS entry with --force',
            command=(
                'dnszone_add', [zone2], {
                    'idnssoamname': zone2_ns,
                    'idnssoarname': zone2_rname,
                    'force'       : True,
                }
            ),
            expected={
                'value': zone2,
                'summary': None,
                'result': {
                    'dn': zone2_dn,
                    'idnsname': [zone2],
                    'idnszoneactive': [u'TRUE'],
                    'idnssoamname': [zone2_ns],
                    'nsrecord': [zone2_ns],
                    'idnssoarname': [zone2_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowdynupdate': [u'FALSE'],
                    'idnsupdatepolicy': [u'grant %(realm)s krb5-self * A; '
                                         u'grant %(realm)s krb5-self * AAAA; '
                                         u'grant %(realm)s krb5-self * SSHFP;'
                                         % dict(realm=api.env.realm)],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                    'objectclass': objectclasses.dnszone,
                },
            },
        ),


        dict(
            desc='Retrieve zone %r' % zone1,
            command=('dnszone_show', [zone1], {}),
            expected={
                'value': zone1,
                'summary': None,
                'result': {
                    'dn': zone1_dn,
                    'idnsname': [zone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [zone1_ns],
                    'idnssoamname': [zone1_ns],
                    'idnssoarname': [zone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                },
            },
        ),


        dict(
            desc='Update zone %r' % zone1,
            command=('dnszone_mod', [zone1], {'idnssoarefresh': 5478}),
            expected={
                'value': zone1,
                'summary': None,
                'result': {
                    'idnsname': [zone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [zone1_ns],
                    'idnssoamname': [zone1_ns],
                    'idnssoarname': [zone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [u'5478'],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                },
            },
        ),


        dict(
            desc='Try to create reverse zone %r with NS record in it' % revzone1,
            command=(
                'dnszone_add', [revzone1], {
                    'idnssoamname': u'ns',
                    'idnssoarname': zone1_rname,
                }
            ),
            expected=errors.ValidationError(name='name-server',
                error=u"Nameserver for reverse zone cannot be a relative DNS name"),
        ),


        dict(
            desc='Create reverse zone %r' % revzone1,
            command=(
                'dnszone_add', [revzone1], {
                    'idnssoamname': zone1_ns,
                    'idnssoarname': zone1_rname,
                }
            ),
            expected={
                'value': revzone1,
                'summary': None,
                'result': {
                    'dn': revzone1_dn,
                    'idnsname': [revzone1],
                    'idnszoneactive': [u'TRUE'],
                    'idnssoamname': [zone1_ns],
                    'nsrecord': [zone1_ns],
                    'idnssoarname': [zone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowdynupdate': [u'FALSE'],
                    'idnsupdatepolicy': [u'grant %(realm)s krb5-subdomain %(zone)s PTR;'
                                         % dict(realm=api.env.realm, zone=revzone1)],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                    'objectclass': objectclasses.dnszone,
                },
            },
        ),


        dict(
            desc='Search for zones with name server %r' % (zone1_ns),
            command=('dnszone_find', [], {'idnssoamname': zone1_ns}),
            expected={
                'summary': None,
                'count': 2,
                'truncated': False,
                'result': [{
                    'dn': revzone1_dn,
                    'idnsname': [revzone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [zone1_ns],
                    'idnssoamname': [zone1_ns],
                    'idnssoarname': [zone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                },
                {
                    'dn': zone1_dn,
                    'idnsname': [zone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [zone1_ns],
                    'idnssoamname': [zone1_ns],
                    'idnssoarname': [zone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [u'5478'],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                }],
            },
        ),


        dict(
            desc='Search for zones with name server %r with --forward-only' % zone1_ns,
            command=('dnszone_find', [], {'idnssoamname': zone1_ns, 'forward_only' : True}),
            expected={
                'summary': None,
                'count': 1,
                'truncated': False,
                'result': [{
                    'dn': zone1_dn,
                    'idnsname': [zone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [zone1_ns],
                    'idnssoamname': [zone1_ns],
                    'idnssoarname': [zone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [u'5478'],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                }],
            },
        ),


        dict(
            desc='Delete reverse zone %r' % revzone1,
            command=('dnszone_del', [revzone1], {}),
            expected={
                'value': revzone1,
                'summary': u'Deleted DNS zone "%s"' % revzone1,
                'result': {'failed': u''},
            },
        ),


        dict(
            desc='Disable zone %r' % zone1,
            command=('dnszone_disable', [zone1], {}),
            expected={
                'value': zone1,
                'summary': u'Disabled DNS zone "%s"' % zone1,
                'result': True,
            },
        ),


        dict(
            desc='Check if zone %r is really disabled' % zone1,
            command=('dnszone_show', [zone1], {}),
            expected={
                'value': zone1,
                'summary': None,
                'result': {
                    'dn': zone1_dn,
                    'idnsname': [zone1],
                    'idnszoneactive': [u'FALSE'],
                    'nsrecord': [zone1_ns],
                    'idnssoamname': [zone1_ns],
                    'idnssoarname': [zone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                },
            },
        ),


        dict(
            desc='Enable zone %r' % zone1,
            command=('dnszone_enable', [zone1], {}),
            expected={
                'value': zone1,
                'summary': u'Enabled DNS zone "%s"' % zone1,
                'result': True,
            },
        ),


        dict(
            desc='Check if zone %r is really enabled' % zone1,
            command=('dnszone_show', [zone1], {}),
            expected={
                'value': zone1,
                'summary': None,
                'result': {
                    'dn': zone1_dn,
                    'idnsname': [zone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [zone1_ns],
                    'idnssoamname': [zone1_ns],
                    'idnssoarname': [zone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                },
            },
        ),


        dict(
            desc='Try to retrieve non-existent record %r in zone %r' % (name1, zone1),
            command=('dnsrecord_show', [zone1, name1], {}),
            expected=errors.NotFound(
                reason=u'%s: DNS resource record not found' % name1),
        ),


        dict(
            desc='Try to delete non-existent record %r in zone %r' % (name1, zone1),
            command=('dnsrecord_del', [zone1, name1], {'del_all' : True}),
            expected=errors.NotFound(
                reason=u'%s: DNS resource record not found' % name1),
        ),


        dict(
            desc='Try to delete root zone record \'@\' in %r' % (zone1),
            command=('dnsrecord_del', [zone1, u'@'], {'del_all' : True}),
            expected=errors.ValidationError(name='del_all',
                error=u"Zone record '@' cannot be deleted"),
        ),


        dict(
            desc='Try to create record with invalid name in zone %r' % zone1,
            command=('dnsrecord_add', [zone1, u'invalid record'], {'arecord': arec2}),
            expected=errors.ValidationError(name='name',
                error=u'only letters, numbers, _, and - are allowed. ' +
                    u'DNS label may not start or end with -'),
        ),


        dict(
            desc='Create record %r in zone %r' % (zone1, name1),
            command=('dnsrecord_add', [zone1, name1], {'arecord': arec2}),
            expected={
                'value': name1,
                'summary': None,
                'result': {
                    'dn': name1_dn,
                    'idnsname': [name1],
                    'objectclass': objectclasses.dnsrecord,
                    'arecord': [arec2],
                },
            },
        ),


        dict(
            desc='Search for all records in zone %r' % zone1,
            command=('dnsrecord_find', [zone1], {}),
            expected={
                'summary': None,
                'count': 4,
                'truncated': False,
                'result': [
                    {
                        'dn': zone1_dn,
                        'nsrecord': (zone1_ns,),
                        'idnsname': [u'@'],
                    },
                    {
                        'dn': zone1_txtrec_dn,
                        'txtrecord': [api.env.realm],
                        'idnsname': [u'_kerberos'],
                    },
                    {
                        'dn': zone1_ns_dn,
                        'idnsname': [u'ns1'],
                        'arecord': [zone1_ip],
                    },
                    {
                        'dn': name1_dn,
                        'idnsname': [name1],
                        'arecord': [arec2],
                    },
                ],
            },
        ),


        dict(
            desc='Add A record to %r in zone %r' % (name1, zone1),
            command=('dnsrecord_add', [zone1, name1], {'arecord': arec3}),
            expected={
                'value': name1,
                'summary': None,
                'result': {
                    'dn': name1_dn,
                    'idnsname': [name1],
                    'arecord': [arec2, arec3],
                    'objectclass': objectclasses.dnsrecord,
                },
            },
        ),


        dict(
            desc='Remove A record from %r in zone %r' % (name1, zone1),
            command=('dnsrecord_del', [zone1, name1], {'arecord': arec2}),
            expected={
                'value': name1,
                'summary': None,
                'result': {
                    'idnsname': [name1],
                    'arecord': [arec3],
                },
            },
        ),


        dict(
            desc='Add AAAA record to %r in zone %r using dnsrecord_mod' % (name1, zone1),
            command=('dnsrecord_mod', [zone1, name1], {'aaaarecord': u'::1'}),
            expected={
                'value': name1,
                'summary': None,
                'result': {
                    'idnsname': [name1],
                    'arecord': [arec3],
                    'aaaarecord': [u'::1'],
                },
            },
        ),


        dict(
            desc='Try to modify nonexistent record in zone %r' % zone1,
            command=('dnsrecord_mod',
                [zone1, u'ghostname'],
                {'aaaarecord': u'f001:baad::1'}),
            expected=errors.NotFound(
                reason=u'ghostname: DNS resource record not found'),
        ),


        dict(
            desc='Modify AAAA record in %r in zone %r' % (name1, zone1),
            command=('dnsrecord_mod', [zone1, name1], {'aaaarecord': u'ff02::1'}),
            expected={
                'value': name1,
                'summary': None,
                'result': {
                    'idnsname': [name1],
                    'arecord': [arec3],
                    'aaaarecord': [u'ff02::1'],
                },
            },
        ),


        dict(
            desc='Remove AAAA record from %r in zone %r using dnsrecord_mod' % (name1, zone1),
            command=('dnsrecord_mod', [zone1, name1], {'aaaarecord': u''}),
            expected={
                'value': name1,
                'summary': None,
                'result': {
                    'idnsname': [name1],
                    'arecord': [arec3],
                },
            },
        ),

        dict(
            desc='Try to add invalid MX record to zone %r using dnsrecord_add' % (zone1),
            command=('dnsrecord_add', [zone1, u'@'], {'mxrecord': zone1_ns }),
            expected=errors.ValidationError(name='mx_rec',
                error=u'format must be specified as "PREFERENCE EXCHANGER" ' +
                    u' (see RFC 1035 for details)'),
        ),

        dict(
            desc='Add MX record to zone %r using dnsrecord_add' % (zone1),
            command=('dnsrecord_add', [zone1, u'@'], {'mxrecord': u"0 %s" % zone1_ns }),
            expected={
                'value': u'@',
                'summary': None,
                'result': {
                    'objectclass': objectclasses.dnszone,
                    'dn': zone1_dn,
                    'idnsname': [u'@'],
                    'mxrecord': [u"0 %s" % zone1_ns],
                    'nsrecord': [zone1_ns],
                },
            },
        ),

        dict(
            desc='Try to add invalid SRV record to zone %r using dnsrecord_add' % (zone1),
            command=('dnsrecord_add', [zone1, u'_foo._tcp'], {'srvrecord': zone1_ns}),
            expected=errors.ValidationError(name='srv_rec',
                error=u'format must be specified as "PRIORITY WEIGHT PORT TARGET" ' +
                    u' (see RFC 2782 for details)'),
        ),

        dict(
            desc='Try to add invalid SRV record via parts to zone %r using dnsrecord_add' % (zone1),
            command=('dnsrecord_add', [zone1, u'_foo._tcp'], {'srv_part_priority': 0,
                                                                 'srv_part_weight' : 0,
                                                                 'srv_part_port' : 123,
                                                                 'srv_part_target' : u'foo bar'}),
            expected=errors.ValidationError(name='srv_target',
                error=u'invalid domain-name: only letters, numbers, _, and - ' +
                    u'are allowed. DNS label may not start or end with -'),
        ),

        dict(
            desc='Try to add SRV record to zone %r both via parts and a raw value' % (zone1),
            command=('dnsrecord_add', [zone1, u'_foo._tcp'], {'srv_part_priority': 0,
                                                                 'srv_part_weight' : 0,
                                                                 'srv_part_port' : 123,
                                                                 'srv_part_target' : u'foo.bar.',
                                                                 'srvrecord': [u"1 100 1234 %s" \
                                                                     % zone1_ns]}),
            expected=errors.ValidationError(name='srv_target',
                error=u'Raw value of a DNS record was already set by ' +
                    u'"srv_rec" option'),
        ),

        dict(
            desc='Add SRV record to zone %r using dnsrecord_add' % (zone1),
            command=('dnsrecord_add', [zone1, u'_foo._tcp'], {'srvrecord': u"0 100 1234 %s" % zone1_ns}),
            expected={
                'value': u'_foo._tcp',
                'summary': None,
                'result': {
                    'objectclass': objectclasses.dnsrecord,
                    'dn': DN(('idnsname', u'_foo._tcp'), zone1_dn),
                    'idnsname': [u'_foo._tcp'],
                    'srvrecord': [u"0 100 1234 %s" % zone1_ns],
                },
            },
        ),

        dict(
            desc='Try to modify SRV record in zone %r without specifying modified value' % (zone1),
            command=('dnsrecord_mod', [zone1, u'_foo._tcp'], {'srv_part_priority': 1,}),
            expected=errors.RequirementError(name='srvrecord'),
        ),

        dict(
            desc='Try to modify SRV record in zone %r with non-existent modified value' % (zone1),
            command=('dnsrecord_mod', [zone1, u'_foo._tcp'], {'srv_part_priority': 1,
                                                  'srvrecord' : [u"0 100 1234 does.not.exist."] }),
            expected=errors.AttrValueNotFound(attr='SRV record',
                value=u'0 100 1234 does.not.exist.'),
        ),

        dict(
            desc='Try to modify SRV record in zone %r with invalid part value' % (zone1),
            command=('dnsrecord_mod', [zone1, u'_foo._tcp'], {'srv_part_priority': 100000,
                                                  'srvrecord' : [u"0 100 1234 %s" % zone1_ns] }),
            expected=errors.ValidationError(name='srv_priority', error=u'can be at most 65535'),
        ),

        dict(
            desc='Modify SRV record in zone %r using parts' % (zone1),
            command=('dnsrecord_mod', [zone1, u'_foo._tcp'], {'srv_part_priority': 1,
                                                  'srvrecord' : [u"0 100 1234 %s" % zone1_ns] }),
            expected={
                'value': u'_foo._tcp',
                'summary': None,
                'result': {
                    'idnsname': [u'_foo._tcp'],
                    'srvrecord': [u"1 100 1234 %s" % zone1_ns],
                },
            },
        ),

        dict(
            desc='Try to add invalid LOC record to zone %r using dnsrecord_add' % (zone1),
            command=('dnsrecord_add', [zone1, u'@'], {'locrecord': u"91 11 42.4 N 16 36 29.6 E 227.64" }),
            expected=errors.ValidationError(name='lat_deg',
                error=u'can be at most 90'),
        ),

        dict(
            desc='Add LOC record to zone %r using dnsrecord_add' % (zone1),
            command=('dnsrecord_add', [zone1, u'@'], {'locrecord': u"49 11 42.4 N 16 36 29.6 E 227.64" }),
            expected={
                'value': u'@',
                'summary': None,
                'result': {
                    'objectclass': objectclasses.dnszone,
                    'dn': zone1_dn,
                    'idnsname': [u'@'],
                    'mxrecord': [u"0 %s" % zone1_ns],
                    'nsrecord': [zone1_ns],
                    'locrecord': [u"49 11 42.400 N 16 36 29.600 E 227.64"],
                },
            },
        ),

        dict(
            desc='Try to add CNAME record to %r using dnsrecord_add' % (name1),
            command=('dnsrecord_add', [zone1, name1], {'cnamerecord': u'foo-1.example.com.'}),
            expected=errors.ValidationError(name='cnamerecord',
                error=u'CNAME record is not allowed to coexist with any other '
                      u'record (RFC 1034, section 3.6.2)'),
        ),

        dict(
            desc='Try to add invalid CNAME record %r using dnsrecord_add' % (cname),
            command=('dnsrecord_add', [zone1, cname], {'cnamerecord': u'-.example.com'}),
            expected=errors.ValidationError(name='hostname',
                error=u'invalid domain-name: only letters, numbers, _, and - ' +
                    u'are allowed. DNS label may not start or end with -'),
        ),

        dict(
            desc='Try to add multiple CNAME record %r using dnsrecord_add' % (cname),
            command=('dnsrecord_add', [zone1, cname], {'cnamerecord':
                [u'1.example.com.', u'2.example.com.']}),
            expected=errors.ValidationError(name='cnamerecord',
                error=u'only one CNAME record is allowed per name (RFC 2136, section 1.1.5)'),
        ),

        dict(
            desc='Add CNAME record to %r using dnsrecord_add' % (cname),
            command=('dnsrecord_add', [zone1, cname], {'cnamerecord': u'foo-1.example.com.'}),
            expected={
                'value': cname,
                'summary': None,
                'result': {
                    'objectclass': objectclasses.dnsrecord,
                    'dn': cname_dn,
                    'idnsname': [cname],
                    'cnamerecord': [u'foo-1.example.com.'],
                },
            },
        ),

        dict(
            desc='Try to add other record to CNAME record %r using dnsrecord_add' % (cname),
            command=('dnsrecord_add', [zone1, cname], {'arecord': arec1}),
            expected=errors.ValidationError(name='cnamerecord',
                error=u'CNAME record is not allowed to coexist with any other '
                      u'record (RFC 1034, section 3.6.2)'),
        ),

        dict(
            desc='Try to add other record to CNAME record %r using dnsrecord_mod' % (cname),
            command=('dnsrecord_mod', [zone1, cname], {'arecord': arec1}),
            expected=errors.ValidationError(name='cnamerecord',
                error=u'CNAME record is not allowed to coexist with any other '
                      u'record (RFC 1034, section 3.6.2)'),
        ),

        dict(
            desc='Add A record and delete CNAME record in %r with dnsrecord_mod' % (cname),
            command=('dnsrecord_mod', [zone1, cname], {'arecord': arec1,
                                                                'cnamerecord': None}),
            expected={
                'value': cname,
                'summary': None,
                'result': {
                    'idnsname': [cname],
                    'arecord': [arec1],
                },
            },
        ),

        dict(
            desc='Try to add multiple DNAME records to %r using dnsrecord_add' % (dname),
            command=('dnsrecord_add', [zone1, name1], {'dnamerecord':
                [u'foo-1.example.com.', u'foo-2.example.com.']}),
            expected=errors.ValidationError(name='dnamerecord',
                error=u'only one DNAME record is allowed per name (RFC 6672, section 2.4)'),
        ),

        dict(
            desc='Try to add invalid DNAME record %r using dnsrecord_add' % (dname),
            command=('dnsrecord_add', [zone1, dname], {'dnamerecord': u'-.example.com.'}),
            expected=errors.ValidationError(name='target',
                error=u'invalid domain-name: only letters, numbers, _, and - ' +
                    u'are allowed. DNS label may not start or end with -'),
        ),

        dict(
            desc='Add DNAME record to %r using dnsrecord_add' % (dname),
            command=('dnsrecord_add', [zone1, dname],
                {'dnamerecord': u'd.example.com.', 'arecord': arec1}),
            expected={
                'value': dname,
                'summary': None,
                'result': {
                    'objectclass': objectclasses.dnsrecord,
                    'dn': dname_dn,
                    'idnsname': [dname],
                    'dnamerecord': [u'd.example.com.'],
                    'arecord': [arec1],
                },
            },
        ),

        dict(
            desc='Try to add CNAME record to %r using dnsrecord_add' % (dname),
            command=('dnsrecord_add', [zone1, dname], {'cnamerecord': u'foo-1.example.com.'}),
            expected=errors.ValidationError(name='cnamerecord',
                error=u'CNAME record is not allowed to coexist with any other '
                      u'record (RFC 1034, section 3.6.2)'),
        ),

        dict(
            desc='Try to add NS record to %r using dnsrecord_add' % (dname),
            command=('dnsrecord_add', [zone1, dname],
                {'nsrecord': u'%s.%s.' % (name1, zone1)}),
            expected=errors.ValidationError(name='dnamerecord',
                error=u'DNAME record is not allowed to coexist with an NS '
                      u'record except when located in a zone root record (RFC 6672, section 2.3)'),
        ),

        dict(
            desc='Add NS+DNAME record to %r zone record using dnsrecord_add' % (zone2),
            command=('dnsrecord_add', [zone2, u'@'],
                {'dnamerecord': u'd.example.com.',
                 'nsrecord': zone1_ns}),
            expected = {
                'value': u'@',
                'summary': None,
                'result': {
                    'objectclass': objectclasses.dnszone,
                    'dnamerecord': [u'd.example.com.'],
                    'dn': zone2_dn,
                    'nsrecord': [zone2_ns, zone1_ns],
                    'idnsname': [u'@']
                }
            },
        ),


        dict(
            desc='Delete zone %r' % zone2,
            command=('dnszone_del', [zone2], {}),
            expected={
                'value': zone2,
                'summary': u'Deleted DNS zone "%s"' % zone2,
                'result': {'failed': u''},
            },
        ),

        dict(
            desc='Try to add invalid KX record %r using dnsrecord_add' % (name1),
            command=('dnsrecord_add', [zone1, name1], {'kxrecord': u'foo-1.example.com' }),
            expected=errors.ValidationError(name='kx_rec',
                error=u'format must be specified as "PREFERENCE EXCHANGER" ' +
                    u' (see RFC 2230 for details)'),
        ),

        dict(
            desc='Add KX record to %r using dnsrecord_add' % (name1),
            command=('dnsrecord_add', [zone1, name1], {'kxrecord': u'1 foo-1' }),
            expected={
                'value': name1,
                'summary': None,
                'result': {
                    'objectclass': objectclasses.dnsrecord,
                    'dn': name1_dn,
                    'idnsname': [name1],
                    'arecord': [arec3],
                    'kxrecord': [u'1 foo-1'],
                },
            },
        ),

        dict(
            desc='Add TXT record to %r using dnsrecord_add' % (name1),
            command=('dnsrecord_add', [zone1, name1], {'txtrecord': u'foo bar' }),
            expected={
                'value': name1,
                'summary': None,
                'result': {
                    'objectclass': objectclasses.dnsrecord,
                    'dn': name1_dn,
                    'idnsname': [name1],
                    'arecord': [arec3],
                    'kxrecord': [u'1 foo-1'],
                    'txtrecord': [u'foo bar'],
                },
            },
        ),

        dict(
            desc='Add NSEC record to %r using dnsrecord_add' % (name1),
            command=('dnsrecord_add', [zone1, name1], {
                'nsec_part_next': zone1,
                'nsec_part_types' : [u'TXT', u'A']}),
            expected={
                'value': name1,
                'summary': None,
                'result': {
                    'objectclass': objectclasses.dnsrecord,
                    'dn': name1_dn,
                    'idnsname': [name1],
                    'arecord': [arec3],
                    'kxrecord': [u'1 foo-1'],
                    'txtrecord': [u'foo bar'],
                    'nsecrecord': [zone1 + u' TXT A'],
                },
            },
        ),

        dict(
            desc='Try to add unresolvable absolute NS record to %r using dnsrecord_add' % (name1),
            command=('dnsrecord_add', [zone1, name1], {'nsrecord': u'does.not.exist.'}),
            expected=errors.NotFound(reason=u"Nameserver 'does.not.exist.' does not have a corresponding A/AAAA record"),
        ),

        dict(
            desc='Try to add unresolvable relative NS record to %r using dnsrecord_add' % (name1),
            command=('dnsrecord_add', [zone1, name1], {'nsrecord': u'does.not.exist'}),
            expected=errors.NotFound(reason=u"Nameserver 'does.not.exist.%s.' does not have a corresponding A/AAAA record" % zone1),
        ),

        dict(
            desc='Add unresolvable NS record with --force to %r using dnsrecord_add' % (name1),
            command=('dnsrecord_add', [zone1, name1], {'nsrecord': u'does.not.exist.',
                                                            'force' : True}),
            expected={
                'value': name1,
                'summary': None,
                'result': {
                    'objectclass': objectclasses.dnsrecord,
                    'dn': name1_dn,
                    'idnsname': [name1],
                    'arecord': [arec3],
                    'kxrecord': [u'1 foo-1'],
                    'txtrecord': [u'foo bar'],
                    'nsecrecord': [zone1 + u' TXT A'],
                    'nsrecord': [u'does.not.exist.'],
                },
            },
        ),

        dict(
            desc='Try to to rename DNS zone %r root record' % (zone1),
            command=('dnsrecord_mod', [zone1, u'@'], {'rename': name1_renamed,}),
            expected=errors.ValidationError(name='rename',
                           error=u'DNS zone root record cannot be renamed')
        ),

        dict(
            desc='Rename DNS record %r to %r' % (name1, name1_renamed),
            command=('dnsrecord_mod', [zone1, name1], {'rename': name1_renamed,}),
            expected={
                'value': name1,
                'summary': None,
                'result': {
                    'idnsname': [name1_renamed],
                    'arecord': [arec3],
                    'kxrecord': [u'1 foo-1'],
                    'txtrecord': [u'foo bar'],
                    'nsecrecord': [zone1 + u' TXT A'],
                    'nsrecord': [u'does.not.exist.'],
                },
            },
        ),


        dict(
            desc='Delete record %r in zone %r' % (name1_renamed, zone1),
            command=('dnsrecord_del', [zone1, name1_renamed], {'del_all': True }),
            expected={
                'value': name1_renamed,
                'summary': u'Deleted record "%s"' % name1_renamed,
                'result': {'failed': u''},
            },
        ),


        dict(
            desc='Try to create a reverse zone from invalid IP',
            command=(
                'dnszone_add', [], {
                    'name_from_ip': u'foo',
                    'idnssoamname': zone1_ns,
                    'idnssoarname': zone1_rname,
                }
            ),
            expected=errors.ValidationError(name='name_from_ip',
                error=u'invalid IP network format'),
        ),

        dict(
            desc='Create reverse zone from IP/netmask %r using name_from_ip option' % revzone1_ip,
            command=(
                'dnszone_add', [], {
                    'name_from_ip': revzone1_ip,
                    'idnssoamname': zone1_ns,
                    'idnssoarname': zone1_rname,
                }
            ),
            expected={
                'value': revzone1,
                'summary': None,
                'result': {
                    'dn': revzone1_dn,
                    'idnsname': [revzone1],
                    'idnszoneactive': [u'TRUE'],
                    'idnssoamname': [zone1_ns],
                    'nsrecord': [zone1_ns],
                    'idnssoarname': [zone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowdynupdate': [u'FALSE'],
                    'idnsupdatepolicy': [u'grant %(realm)s krb5-subdomain %(zone)s PTR;'
                                         % dict(realm=api.env.realm, zone=revzone1)],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                    'objectclass': objectclasses.dnszone,
                },
            },
        ),


        dict(
            desc='Create reverse zone from IP %r using name_from_ip option' % revzone2_ip,
            command=(
                'dnszone_add', [], {
                    'name_from_ip': revzone2_ip,
                    'idnssoamname': zone1_ns,
                    'idnssoarname': zone1_rname,
                }
            ),
            expected={
                'value': revzone2,
                'summary': None,
                'result': {
                    'dn': revzone2_dn,
                    'idnsname': [revzone2],
                    'idnszoneactive': [u'TRUE'],
                    'idnssoamname': [zone1_ns],
                    'nsrecord': [zone1_ns],
                    'idnssoarname': [zone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowdynupdate': [u'FALSE'],
                    'idnsupdatepolicy': [u'grant %(realm)s krb5-subdomain %(zone)s PTR;'
                                         % dict(realm=api.env.realm, zone=revzone2)],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                    'objectclass': objectclasses.dnszone,
                },
            },
        ),


        dict(
            desc='Try to add invalid PTR %r to %r using dnsrecord_add' % (revname1, revzone1),
            command=('dnsrecord_add', [revzone1, revname1], {'ptrrecord': u'-.example.com' }),
            expected=errors.ValidationError(name='hostname',
                error=u'invalid domain-name: only letters, numbers, and - ' +
                    u'are allowed. DNS label may not start or end with -'),
        ),

        dict(
            desc='Add PTR record %r to %r using dnsrecord_add' % (revname1, revzone1),
            command=('dnsrecord_add', [revzone1, revname1], {'ptrrecord': u'foo-1.example.com' }),
            expected={
                'value': revname1,
                'summary': None,
                'result': {
                    'objectclass': objectclasses.dnsrecord,
                    'dn': revname1_dn,
                    'idnsname': [revname1],
                    'ptrrecord': [u'foo-1.example.com.'],
                },
            },
        ),

        dict(
            desc='Show record %r in zone %r with --structured and --all options'\
                    % (revname1, revzone1),
            command=('dnsrecord_show', [revzone1, revname1],
                {'structured': True, 'all': True}),
            expected={
                'value': revname1,
                'summary': None,
                'result': {
                    'dn': revname1_dn,
                    'idnsname': [revname1],
                    'objectclass': objectclasses.dnsrecord,
                    'dnsrecords': [
                        {
                            'dnstype': u'PTR',
                            'dnsdata': u'foo-1.example.com.',
                            'ptr_part_hostname': u'foo-1.example.com.'
                        },
                    ],
                },
            },
        ),

        dict(
            desc='Update global DNS settings',
            command=('dnsconfig_mod', [], {'idnsforwarders' : [fwd_ip],}),
            expected={
                'value': u'',
                'summary': None,
                'result': {
                    'idnsforwarders': [fwd_ip],
                },
            },
        ),


        dict(
            desc='Try to add invalid allow-query to zone %r' % zone1,
            command=('dnszone_mod', [zone1], {'idnsallowquery': u'foo'}),
            expected=errors.ValidationError(name='allow_query',
                error=u"failed to detect a valid IP address from 'foo'"),
        ),

        dict(
            desc='Add allow-query ACL to zone %r' % zone1,
            command=('dnszone_mod', [zone1], {'idnsallowquery': allowquery_restricted_in}),
            expected={
                'value': zone1,
                'summary': None,
                'result': {
                    'idnsname': [zone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [zone1_ns],
                    'mxrecord': [u'0 ns1.dnszone.test.'],
                    'locrecord': [u"49 11 42.400 N 16 36 29.600 E 227.64"],
                    'idnssoamname': [zone1_ns],
                    'idnssoarname': [zone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [u'5478'],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowquery': [allowquery_restricted_out],
                    'idnsallowtransfer': [u'none;'],
                },
            },
        ),


        dict(
            desc='Try to add invalid allow-transfer to zone %r' % zone1,
            command=('dnszone_mod', [zone1], {'idnsallowtransfer': u'10.'}),
            expected=errors.ValidationError(name='allow_transfer',
                error=u"failed to detect a valid IP address from '10.'"),
        ),

        dict(
            desc='Add allow-transer ACL to zone %r' % zone1,
            command=('dnszone_mod', [zone1], {'idnsallowtransfer': fwd_ip}),
            expected={
                'value': zone1,
                'summary': None,
                'result': {
                    'idnsname': [zone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [zone1_ns],
                    'mxrecord': [u'0 ns1.dnszone.test.'],
                    'locrecord': [u"49 11 42.400 N 16 36 29.600 E 227.64"],
                    'idnssoamname': [zone1_ns],
                    'idnssoarname': [zone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [u'5478'],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowquery': [allowquery_restricted_out],
                    'idnsallowtransfer': [allowtransfer_tofwd],
                },
            },
        ),


        dict(
            desc='Set SOA serial of zone %r to high number' % zone1,
            command=('dnszone_mod', [zone1], {'idnssoaserial': 4294967295L}),
            expected={
                'value': zone1,
                'summary': None,
                'result': {
                    'idnsname': [zone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [zone1_ns],
                    'mxrecord': [u'0 ns1.dnszone.test.'],
                    'locrecord': [u"49 11 42.400 N 16 36 29.600 E 227.64"],
                    'idnssoamname': [zone1_ns],
                    'idnssoarname': [zone1_rname],
                    'idnssoaserial': [u'4294967295'],
                    'idnssoarefresh': [u'5478'],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowquery': [allowquery_restricted_out],
                    'idnsallowtransfer': [allowtransfer_tofwd],
                },
            },
        ),


        dict(
            desc='Try to create duplicate PTR record for %r with --a-create-reverse' % name1,
            command=('dnsrecord_add', [zone1, name1], {'arecord': revname1_ip,
                                                            'a_extra_create_reverse' : True}),
            expected=errors.DuplicateEntry(message=u'Reverse record for IP '
                'address %s already exists in reverse zone '
                '%s.' % (revname1_ip, revzone1)),
        ),


        dict(
            desc='Create A record %r in zone %r with --a-create-reverse' % (name1, zone1),
            command=('dnsrecord_add', [zone1, name1], {'arecord': revname2_ip,
                                                            'a_extra_create_reverse' : True}),
            expected={
                'value': name1,
                'summary': None,
                'result': {
                    'dn': name1_dn,
                    'idnsname': [name1],
                    'objectclass': objectclasses.dnsrecord,
                    'arecord': [revname2_ip],
                },
            },
        ),


        dict(
            desc='Check reverse record for %r created via --a-create-reverse' % name1,
            command=('dnsrecord_show', [revzone1, revname2], {}),
            expected={
                'value': revname2,
                'summary': None,
                'result': {
                    'dn': revname2_dn,
                    'idnsname': [revname2],
                    'ptrrecord': [name1 + '.' + zone1 + '.'],
                },
            },
        ),


        dict(
            desc='Try to add per-zone permission for unknown zone',
            command=('dnszone_add_permission', [u'does.not.exist'], {}),
            expected=errors.NotFound(reason=u'does.not.exist: DNS zone not found')
        ),


        dict(
            desc='Add per-zone permission for zone %r' % zone1,
            command=(
                'dnszone_add_permission', [zone1], {}
            ),
            expected=dict(
                result=True,
                value=zone1_permission,
                summary=u'Added system permission "%s"' % zone1_permission,
            ),
        ),


        dict(
            desc='Try to add duplicate per-zone permission for zone %r' % zone1,
            command=(
                'dnszone_add_permission', [zone1], {}
            ),
            expected=errors.DuplicateEntry(message=u'permission with name '
                '"%s" already exists' % zone1_permission)
        ),

        dict(
            desc='Make sure the permission was created %r' % zone1,
            command=(
                'permission_show', [zone1_permission], {}
            ),
            expected=dict(
                value=zone1_permission,
                summary=None,
                result={
                    'dn': zone1_permission_dn,
                    'cn': [zone1_permission],
                    'objectclass': objectclasses.system_permission,
                    'ipapermissiontype': [u'SYSTEM'],
                },
            ),
        ),

        dict(
            desc='Retrieve the permission %r with --all --raw' % zone1,
            command=(
                'permission_show', [zone1_permission], {}
            ),
            expected=dict(
                value=zone1_permission,
                summary=None,
                result={
                    'dn': zone1_permission_dn,
                    'cn': [zone1_permission],
                    'objectclass': objectclasses.system_permission,
                    'ipapermissiontype': [u'SYSTEM'],
                },
            ),
        ),

        dict(
            desc='Try to remove per-zone permission for unknown zone',
            command=('dnszone_remove_permission', [u'does.not.exist'], {}),
            expected=errors.NotFound(reason=u'does.not.exist: DNS zone not found')
        ),

        dict(
            desc='Remove per-zone permission for zone %r' % zone1,
            command=(
                'dnszone_remove_permission', [zone1], {}
            ),
            expected=dict(
                result=True,
                value=zone1_permission,
                summary=u'Removed system permission "%s"' % zone1_permission,
            ),
        ),


        dict(
            desc='Make sure the permission for zone %r was deleted' % zone1,
            command=(
                'permission_show', [zone1_permission], {}
            ),
            expected=errors.NotFound(reason=u'%s: permission not found'
                                     % zone1_permission)
        ),


        dict(
            desc='Delete zone %r' % zone1,
            command=('dnszone_del', [zone1], {}),
            expected={
                'value': zone1,
                'summary': u'Deleted DNS zone "%s"' % zone1,
                'result': {'failed': u''},
            },
        ),


        dict(
            desc='Try to create zone %r nameserver not in it' % zone1,
            command=(
                'dnszone_add', [zone1], {
                    'idnssoamname': u'not.in.this.zone.',
                    'idnssoarname': zone1_rname,
                    'ip_address' : zone1_ip,
                }
            ),
            expected=errors.ValidationError(name='ip_address',
                error=u"Nameserver DNS record is created only for nameservers"
                      u" in current zone"),
        ),


        dict(
            desc='Create zone %r with relative nameserver' % zone1,
            command=(
                'dnszone_add', [zone1], {
                    'idnssoamname': u'ns',
                    'idnssoarname': zone1_rname,
                    'ip_address' : zone1_ip,
                }
            ),
            expected={
                'value': zone1,
                'summary': None,
                'result': {
                    'dn': zone1_dn,
                    'idnsname': [zone1],
                    'idnszoneactive': [u'TRUE'],
                    'idnssoamname': [u'ns'],
                    'nsrecord': [u'ns'],
                    'idnssoarname': [zone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowdynupdate': [u'FALSE'],
                    'idnsupdatepolicy': [u'grant %(realm)s krb5-self * A; '
                                         u'grant %(realm)s krb5-self * AAAA; '
                                         u'grant %(realm)s krb5-self * SSHFP;'
                                         % dict(realm=api.env.realm)],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                    'objectclass': objectclasses.dnszone,
                },
            },
        ),


        dict(
            desc='Delete zone %r' % zone1,
            command=('dnszone_del', [zone1], {}),
            expected={
                'value': zone1,
                'summary': u'Deleted DNS zone "%s"' % zone1,
                'result': {'failed': u''},
            },
        ),


        dict(
            desc='Create zone %r with nameserver in the zone itself' % zone1,
            command=(
                'dnszone_add', [zone1], {
                    'idnssoamname': zone1 + u'.',
                    'idnssoarname': zone1_rname,
                    'ip_address' : zone1_ip,
                }
            ),
            expected={
                'value': zone1,
                'summary': None,
                'result': {
                    'dn': zone1_dn,
                    'idnsname': [zone1],
                    'idnszoneactive': [u'TRUE'],
                    'idnssoamname': [zone1 + u'.'],
                    'nsrecord': [zone1 + u'.'],
                    'idnssoarname': [zone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowdynupdate': [u'FALSE'],
                    'idnsupdatepolicy': [u'grant %(realm)s krb5-self * A; '
                                         u'grant %(realm)s krb5-self * AAAA; '
                                         u'grant %(realm)s krb5-self * SSHFP;'
                                         % dict(realm=api.env.realm)],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                    'objectclass': objectclasses.dnszone,
                },
            },
        ),

    ]
